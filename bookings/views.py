import logging
from datetime import datetime

from django.core.paginator import Paginator

from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.db.models import Q, F, Value, CharField
from django.db.models.functions import Concat
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from bookings.forms import EventStaffBookingForm
from bookings.models import EventStaffBooking, Availability
from bookings.constants import SERVICE_ROLE_MAPPING
from communication.models import UnifiedCommunication
from communication.forms import BookingCommunicationForm
from communication.views import send_booking_email
from contracts.models import Contract, ChangeLog
from contracts.forms import ContractClientEditForm, ContractEventEditForm
from users.models import Role
from users.views import ROLE_DISPLAY_NAMES

logger = logging.getLogger(__name__)

# Helper Functions


def parse_date_safe(date_str, field_name="date"):
    """
    Safely parses a date string into a date object.
    Returns None if parsing fails.
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None
    except ValueError:
        logger.error("Invalid %s format: %s", field_name, date_str)
        return None


def validate_date_range(start_date, end_date):
    """
    Validates and returns a date range tuple.
    Returns None if either date is invalid or the range is logically incorrect.
    """
    start = parse_date_safe(start_date, "start_date")
    end = parse_date_safe(end_date, "end_date")
    if start and end and start <= end:
        return start, end
    logger.error("Invalid date range: %s to %s", start_date, end_date)
    return None


@login_required
def booking_search(request):
    """
    Search for event staff bookings based on various filters like date range,
    service type, role, and status, with pagination.
    """
    query = request.GET.get("booking_q")
    start_date = request.GET.get("event_date_start")
    end_date = request.GET.get("event_date_end")
    service_type = request.GET.get("service_type")
    role_filter = request.GET.get("role_filter")
    status_filter = request.GET.get("status_filter")
    sort_by = request.GET.get("sort_by")
    order = request.GET.get("order", "asc")

    bookings = EventStaffBooking.objects.all()

    # Apply text-based search
    if query:
        bookings = bookings.filter(
            Q(staff__username__icontains=query) |
            Q(staff__first_name__icontains=query) |
            Q(staff__last_name__icontains=query) |
            Q(contract__custom_contract_number__icontains=query) |
            Q(contract__client__primary_contact__icontains=query) |
            Q(contract__client__partner_contact__icontains=query) |
            Q(contract__old_contract_number__icontains=query) |
            Q(contract__client__primary_email__icontains=query) |
            Q(contract__client__primary_phone1__icontains=query)
        )

    # Filter by event date range
    date_range = validate_date_range(start_date, end_date)
    if date_range:
        bookings = bookings.filter(contract__event_date__range=date_range)
    elif start_date or end_date:
        messages.error(request, "Invalid date range. Please check your input.")

    # Filter by service type
    if service_type:
        roles = SERVICE_ROLE_MAPPING.get(service_type.upper(), [])
        if roles:
            bookings = bookings.filter(role__in=roles)

    # Filter by role
    if role_filter:
        bookings = bookings.filter(role=role_filter)

    # Filter by status
    if status_filter:
        # Allow multiple statuses, separated by commas
        status_list = status_filter.split(",")
        bookings = bookings.filter(status__in=status_list)

    # Sort results
    allowed_sort_fields = ["staff__username", "contract__event_date", "role", "status"]
    if sort_by in allowed_sort_fields:
        sort_expression = sort_by if order == "asc" else f"-{sort_by}"
        bookings = bookings.order_by(sort_expression)

    # Apply pagination
    paginator = Paginator(bookings, 25)  # Display 25 bookings per page
    page_number = request.GET.get("page")
    bookings_page = paginator.get_page(page_number)

    logger.info("Booking search completed with %d results.", bookings.count())
    return render(request, "bookings/booking_search.html", {
        "bookings": bookings_page,
        "query_params": request.GET.urlencode(),  # Pass query parameters to the template
    })


def get_available_staff(request):
    """
    Fetch available staff for a given event date and service type.
    Returns a JSON response with lists of available staff for specified roles.
    """
    event_date_str = request.GET.get("event_date")
    service_type = request.GET.get("service_type")
    logger.debug("Fetching available staff for service type: %s", service_type)

    event_date = parse_date_safe(event_date_str, "event_date")
    if not event_date:
        return JsonResponse({"error": "Invalid or missing event date"}, status=400)

    available_staff = Availability.get_available_staff_for_date(event_date).distinct()
    combined_name = Concat(F("first_name"), Value(" "), F("last_name"), output_field=CharField())

    def staff_by_role(role_name):
        return list(
            available_staff.filter(
                Q(role__name=role_name) | Q(additional_roles__name=role_name)
            ).annotate(name=combined_name)
            .values("id", "name", "rank")
            .order_by("rank")
        )

    roles_dict = {
        "photographers": "PHOTOGRAPHER",
        "videographers": "VIDEOGRAPHER",
        "djs": "DJ",
        "photobooth_operators": "PHOTOBOOTH_OPERATOR",
    }

    data = {role_key: staff_by_role(role_name) for role_key, role_name in roles_dict.items()}

    # Add specific service type data
    if service_type:
        service_roles = Role.objects.filter(service_type__name=service_type).values_list("name", flat=True)
        data[f"{service_type.lower()}_staff"] = list(
            available_staff.filter(Q(role__name__in=service_roles) | Q(additional_roles__name__in=service_roles))
            .annotate(name=combined_name)
            .values("id", "name", "rank")
            .order_by("rank")
        )

    logger.info("Available staff fetched for event date: %s", event_date)
    return JsonResponse(data)


@login_required
def get_current_booking(request):
    """
    Retrieves the current booking for a specific contract and role, as well as available staff for the event date.
    """
    contract_id = request.GET.get('contract_id')
    role = request.GET.get('role')
    event_date_str = request.GET.get('event_date')

    event_date = parse_date_safe(event_date_str, 'event_date')
    if event_date_str and not event_date:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    current_booking_data = {}
    try:
        current_booking = EventStaffBooking.objects.get(contract_id=contract_id, role=role)
        current_booking_data = {
            'id': current_booking.id,
            'staff_id': current_booking.staff.id,
            'staff_name': current_booking.staff.get_full_name(),
            'role': current_booking.role,
            'status': current_booking.status,
            'hours_booked': current_booking.hours_booked,
            'confirmed': current_booking.confirmed,
        }
    except EventStaffBooking.DoesNotExist:
        pass  # No current booking for this role

    available_staff = Availability.get_available_staff_for_date(event_date) if event_date else Availability.objects.none()
    available_staff_data = list(available_staff.annotate(
        name=Concat('staff__first_name', Value(' '), 'staff__last_name')
    ).values('id', 'name'))

    return JsonResponse({
        'current_booking': current_booking_data,
        'available_staff': available_staff_data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_prospect_photographers(request):
    contract_id = request.GET.get('contract_id')
    if contract_id:
        try:
            contract = Contract.objects.get(contract_id=contract_id)
            data = {
                'prospect_photographer1': {
                    'id': contract.prospect_photographer1.id,
                    'name': f"{contract.prospect_photographer1.first_name} {contract.prospect_photographer1.last_name}",
                    'profile_picture': contract.prospect_photographer1.profile_picture.url if contract.prospect_photographer1.profile_picture else None,
                    'website': contract.prospect_photographer1.website
                } if contract.prospect_photographer1 else None,
                'prospect_photographer2': {
                    'id': contract.prospect_photographer2.id,
                    'name': f"{contract.prospect_photographer2.first_name} {contract.prospect_photographer2.last_name}",
                    'profile_picture': contract.prospect_photographer2.profile_picture.url if contract.prospect_photographer2.profile_picture else None,
                    'website': contract.prospect_photographer2.website
                } if contract.prospect_photographer2 else None,
                'prospect_photographer3': {
                    'id': contract.prospect_photographer3.id,
                    'name': f"{contract.prospect_photographer3.first_name} {contract.prospect_photographer3.last_name}",
                    'profile_picture': contract.prospect_photographer3.profile_picture.url if contract.prospect_photographer3.profile_picture else None,
                    'website': contract.prospect_photographer3.website
                } if contract.prospect_photographer3 else None,
            }
            return JsonResponse(data)
        except Contract.DoesNotExist:
            return JsonResponse({'error': 'Contract not found'}, status=404)
    return JsonResponse({'error': 'Contract ID is required'}, status=400)


@login_required
def manage_staff_assignments(request, contract_id):
    """
    Handles staff assignments to roles within a specific contract.
    Supports the creation and updating of bookings.
    """
    contract = get_object_or_404(Contract, contract_id=contract_id)
    form = EventStaffBookingForm(request.POST or None)

    if form.is_valid():
        # Handle empty booking_id
        booking_id = form.cleaned_data.get('booking_id')
        booking_id = int(booking_id) if booking_id else None

        role = form.cleaned_data.get('role')
        staff = form.cleaned_data.get('staff')
        status = form.cleaned_data.get('status', 'BOOKED')
        confirmed = form.cleaned_data.get('confirmed', False)
        hours_booked = form.cleaned_data.get('hours_booked', 0)
        is_update = bool(booking_id)

        logger.debug(
            "Form valid. Booking ID: %s, Role: %s, Staff: %s, Status: %s, Confirmed: %s, Hours Booked: %s",
            booking_id, role, staff, status, confirmed, hours_booked
        )

        original_staff = None

        if booking_id:
            booking = get_object_or_404(EventStaffBooking, id=booking_id)
            original_staff = booking.staff
            logger.debug("Updating existing booking. Original Staff: %s", original_staff.get_full_name() if original_staff else "None")
        else:
            booking = EventStaffBooking(contract=contract)

        # Restore availability for the previously assigned staff
        if original_staff and original_staff != staff:
            Availability.objects.update_or_create(
                staff=original_staff,
                date=contract.event_date,
                defaults={'available': True}
            )
            logger.info("Restored availability for previous staff: %s", original_staff.get_full_name())

        # Check if the selected staff is already booked for another role on the same event date
        existing_booking = EventStaffBooking.objects.filter(
            staff=staff,
            contract__event_date=contract.event_date
        ).exclude(id=booking_id).first()

        if existing_booking:
            logger.info("Clearing existing booking for staff %s from role %s.", staff.get_full_name(), existing_booking.role)
            existing_booking.delete()

        booking.role = role
        booking.staff = staff
        booking.status = status
        booking.confirmed = confirmed
        booking.hours_booked = hours_booked
        booking._request = request
        booking.save()

        logger.info("Booking saved successfully.")

        booking.update_contract_role()

        # Update staff availability based on the new booking
        Availability.objects.update_or_create(
            staff=staff,
            date=contract.event_date,
            defaults={'available': status not in ['BOOKED', 'PENDING']}
        )

        change_description = (
            f"Updated booking: {booking.role} from {original_staff.get_full_name() if original_staff else 'None'} to {staff.get_full_name()}"
            if is_update else
            f"Created new booking for {role} with {staff.get_full_name()}"
        )
        ChangeLog.objects.create(user=request.user, description=change_description, contract=contract)

        # Handle prospect roles
        if 'PROSPECT' in role:
            prospect_field = f'prospect_photographer{role[-1]}'
            setattr(contract, prospect_field, staff)
            contract.save()
        else:
            send_booking_email(request, staff, contract, booking.get_role_display(), is_update)

        return JsonResponse({
            'success': True,
            'message': 'Staff booking saved successfully',
            'role': booking.role,
            'staff_name': staff.get_full_name() if staff else 'None',
            'hours_booked': booking.hours_booked
        })
    else:
        logger.error("Form invalid. Errors: %s", form.errors)
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@login_required
def confirm_booking(request, booking_id):
    """
    Confirms a booking for a specific event staff member.
    """
    booking = get_object_or_404(EventStaffBooking, id=booking_id)
    if request.method == 'POST':
        booking.confirmed = True
        booking.save()
        messages.success(request, 'Your attendance has been confirmed.')
    return redirect('bookings:booking_detail_staff', booking_id=booking_id)


from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["POST"])
@login_required
def clear_booking(request, booking_id):
    try:
        booking = get_object_or_404(EventStaffBooking, id=booking_id)
        contract = booking.contract

        # Update staff availability
        if booking.staff:
            Availability.objects.update_or_create(
                staff=booking.staff,
                date=contract.event_date,
                defaults={'available': True}
            )

        # Remove role assignment
        role_field = SERVICE_ROLE_MAPPING.get(booking.role, None)
        if role_field and hasattr(contract, role_field):
            setattr(contract, role_field, None)
            contract.save()

        # Delete booking
        booking.delete()

        # Log the change
        ChangeLog.objects.create(
            user=request.user,
            description=f"Deleted booking for {booking.role}.",
            contract=contract
        )

        return JsonResponse({'success': True, 'message': 'Booking cleared successfully!', 'role': booking.role})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


def get_booking_context(booking_id):
    """
    Gathers context data for displaying booking details.
    """
    booking = get_object_or_404(EventStaffBooking, id=booking_id)
    contract = booking.contract

    roles = ['PHOTOGRAPHER1', 'PHOTOGRAPHER2', 'ENGAGEMENT', 'VIDEOGRAPHER1', 'VIDEOGRAPHER2', 'DJ1', 'DJ2', 'PHOTOBOOTH_OP1', 'PHOTOBOOTH_OP2']
    role_bookings = {
        role: EventStaffBooking.objects.filter(contract=contract, role=role).first()
        for role in roles
    }

    booking_notes = UnifiedCommunication.objects.filter(note_type=UnifiedCommunication.BOOKING, contract=contract)
    portal_messages = UnifiedCommunication.objects.filter(note_type=UnifiedCommunication.PORTAL, contract=contract)

    overtime_entries = [
        {
            'service_type': overtime.overtime_option.service_type.name,
            'role': ROLE_DISPLAY_NAMES.get(overtime.overtime_option.role, overtime.overtime_option.role),
            'hours': overtime.hours,
        }
        for overtime in contract.overtimes.all()
    ]

    event_documents = contract.documents.filter(is_event_staff_visible=True)

    return {
        'booking': booking,
        'contract': contract,
        'role_bookings': role_bookings,
        'booking_notes': booking_notes,
        'portal_messages': portal_messages,
        'overtime_entries': overtime_entries,
        'event_documents': event_documents,
    }

@login_required
def booking_detail(request, booking_id):
    """
    Displays detailed information about a specific booking.
    """
    context = get_booking_context(booking_id)

    context.update({
        'photographer1': context['role_bookings'].get('PHOTOGRAPHER1'),
        'photographer2': context['role_bookings'].get('PHOTOGRAPHER2'),
        'engagement_session': context['role_bookings'].get('ENGAGEMENT'),
        'videographer1': context['role_bookings'].get('VIDEOGRAPHER1'),
        'videographer2': context['role_bookings'].get('VIDEOGRAPHER2'),
        'dj1': context['role_bookings'].get('DJ1'),
        'dj2': context['role_bookings'].get('DJ2'),
        'photobooth_op1': context['role_bookings'].get('PHOTOBOOTH_OP1'),
        'photobooth_op2': context['role_bookings'].get('PHOTOBOOTH_OP2'),
        'client_edit_form': ContractClientEditForm(instance=context['contract'].client),
        'event_edit_form': ContractEventEditForm(instance=context['contract']),
        'communication_form': BookingCommunicationForm(request.POST or None),
    })

    if request.method == 'POST' and context['communication_form'].is_valid():
        new_note = UnifiedCommunication.objects.create(
            content=context['communication_form'].cleaned_data['message'],
            note_type=UnifiedCommunication.BOOKING,
            created_by=request.user,
            contract=context['contract'],
        )
        logger.info("New note created: %s by %s", new_note.content, new_note.created_by)
        return redirect('bookings:booking_detail', booking_id=booking_id)

    return render(request, 'bookings/booking_detail_office.html', context)

@login_required
def booking_detail_staff(request, booking_id):
    """
    Displays a summary of booking details for staff members.
    """
    context = get_booking_context(booking_id)

    context.update({
        'photographer1': context['role_bookings'].get('PHOTOGRAPHER1'),
        'photographer2': context['role_bookings'].get('PHOTOGRAPHER2'),
        'engagement_session': context['role_bookings'].get('ENGAGEMENT'),
        'videographer1': context['role_bookings'].get('VIDEOGRAPHER1'),
        'videographer2': context['role_bookings'].get('VIDEOGRAPHER2'),
        'dj1': context['role_bookings'].get('DJ1'),
        'dj2': context['role_bookings'].get('DJ2'),
        'photobooth_op1': context['role_bookings'].get('PHOTOBOOTH_OP1'),
        'photobooth_op2': context['role_bookings'].get('PHOTOBOOTH_OP2'),
        'client_edit_form': ContractClientEditForm(instance=context['contract'].client),
        'event_edit_form': ContractEventEditForm(instance=context['contract']),
    })

    return render(request, 'bookings/booking_detail_staff.html', context)

@login_required
def booking_list(request):
    """
    Lists all bookings with filtering and sorting options.
    """
    query = request.GET.get('q')
    event_date_start = request.GET.get('event_date_start')
    event_date_end = request.GET.get('event_date_end')
    service_type = request.GET.get('service_type')
    role_filter = request.GET.get('role_filter')
    status_filter = request.GET.get('status_filter')
    sort_by = request.GET.get('sort_by', 'contract__event_date')
    order = request.GET.get('order', 'asc')

    bookings = EventStaffBooking.objects.all()

    if query:
        bookings = bookings.filter(
            Q(staff__first_name__icontains=query) |
            Q(staff__last_name__icontains=query) |
            Q(contract__client__primary_contact__icontains=query)
        )

    if event_date_start and event_date_end:
        bookings = bookings.filter(contract__event_date__range=[event_date_start, event_date_end])

    if service_type:
        bookings = bookings.filter(contract__service_type=service_type)

    if role_filter:
        bookings = bookings.filter(role=role_filter)

    if status_filter:
        bookings = bookings.filter(confirmed=status_filter)

    if order == 'asc':
        bookings = bookings.order_by(sort_by)
    else:
        bookings = bookings.order_by(f"-{sort_by}")

    logger.info("Total bookings found: %d", bookings.count())
    return render(request, 'bookings/booking_list.html', {'bookings': bookings})
