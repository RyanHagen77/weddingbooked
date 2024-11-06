# bookings/views.py
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.db.models import F, Q, CharField, Value
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from bookings.constants import SERVICE_ROLE_MAPPING
from contracts.models import Contract, ChangeLog
from contracts.forms import ContractClientEditForm, ContractEventEditForm
from communication.forms import BookingCommunicationForm
from communication.models import UnifiedCommunication
from communication.views import send_booking_email
from users.models import Role
from bookings.forms import EventStaffBookingForm
from bookings.models import Availability, EventStaffBooking
from collections import defaultdict
from django.db.models.functions import Concat
from datetime import datetime
from django.http import JsonResponse
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date
import logging

logger = logging.getLogger(__name__)


ROLE_DISPLAY_NAMES = {
    'PHOTOGRAPHER1': 'Photographer 1',
    'PHOTOGRAPHER2': 'Photographer 2',
    'VIDEOGRAPHER1': 'Videographer 1',
    'VIDEOGRAPHER2': 'Videographer 2',
    'DJ1': 'DJ 1',
    'DJ2': 'DJ 2',
    'PHOTOBOOTH_OP1': 'Photobooth Operator 1',
    'PHOTOBOOTH_OP2': 'Photobooth Operator 2'
}

@login_required
def booking_search(request):
    booking_search_query = request.GET.get('booking_q')
    event_date_start = request.GET.get('event_date_start')
    event_date_end = request.GET.get('event_date_end')
    service_type = request.GET.get('service_type')
    role_filter = request.GET.get('role_filter')
    status_filter = request.GET.get('status_filter')
    sort_by = request.GET.get('sort_by')
    order = request.GET.get('order')

    bookings = EventStaffBooking.objects.all()

    if booking_search_query:
        bookings = bookings.filter(
            Q(staff__username__icontains=booking_search_query) |
            Q(staff__first_name__icontains=booking_search_query) |
            Q(staff__last_name__icontains=booking_search_query) |
            Q(contract__custom_contract_number__icontains=booking_search_query) |
            Q(contract__client__primary_contact__icontains=booking_search_query) |
            Q(contract__client__partner_contact__icontains=booking_search_query) |
            Q(contract__old_contract_number__icontains=booking_search_query) |
            Q(contract__client__primary_email__icontains=booking_search_query) |
            Q(contract__client__primary_phone1__icontains=booking_search_query)
        )

    if event_date_start and event_date_end:
        try:
            start_date = parse_date(event_date_start)
            end_date = parse_date(event_date_end)
            if start_date and end_date:
                bookings = bookings.filter(contract__event_date__range=[start_date, end_date])
            else:
                raise ValidationError('Invalid date format')
        except ValidationError as e:
            # Handle error: log it or provide feedback to the user
            pass

    if service_type:
        service_role_map = {
            "PHOTOGRAPHER": ['PHOTOGRAPHER1', 'PHOTOGRAPHER2'],
            "VIDEOGRAPHER": ['VIDEOGRAPHER1', 'VIDEOGRAPHER2'],
            "DJ": ['DJ1', 'DJ2'],
            "PHOTOBOOTH": ['PHOTOBOOTH_OP1', 'PHOTOBOOTH_OP2'],
        }
        roles = service_role_map.get(service_type, [])
        if roles:
            bookings = bookings.filter(role__in=roles)

    if role_filter:
        bookings = bookings.filter(role=role_filter)

    if status_filter:
        bookings = bookings.filter(status=status_filter)

    allowed_sort_fields = ['staff__username', 'contract__event_date', 'role', 'status']
    if sort_by in allowed_sort_fields and order in ['asc', 'desc']:
        sort_expression = sort_by if order == 'asc' else '-' + sort_by
        bookings = bookings.order_by(sort_expression)

    return render(request, 'bookings/booking_search.html', {'bookings': bookings})


def get_available_staff(request):
    """
    Fetches available staff for a given event date and service type.

    Args:
        request (HttpRequest): The request object containing GET parameters 'event_date' and 'service_type'.

    Returns:
        JsonResponse: A JSON response containing lists of available staff for specified roles.
    """
    event_date_str = request.GET.get('event_date')
    service_type = request.GET.get('service_type')
    logger.debug("Service Type: %s", service_type)

    try:
        event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date() if event_date_str else None
    except ValueError:
        logger.error("Invalid date format: %s", event_date_str)
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    if not event_date:
        logger.error("Event date is required but not provided.")
        return JsonResponse({'error': 'Event date is required'}, status=400)

    available_staff = Availability.get_available_staff_for_date(event_date).distinct()
    combined_name = Concat(F('first_name'), Value(' '), F('last_name'), output_field=CharField())

    def get_staff_by_role(role_name):
        return list(available_staff.filter(
            Q(role__name=role_name) | Q(additional_roles__name=role_name)
        ).annotate(name=combined_name).values('id', 'name', 'rank').order_by('rank'))

    roles_dict = {
        'photographers': 'PHOTOGRAPHER',
        'videographers': 'VIDEOGRAPHER',
        'djs': 'DJ',
        'photobooth_operators': 'PHOTOBOOTH_OPERATOR',
        # Add any other event staff roles as needed...
    }

    data = {role_key: get_staff_by_role(role_name) for role_key, role_name in roles_dict.items()}

    if service_type:
        roles = Role.objects.filter(service_type__name=service_type).values_list('name', flat=True)
        staff_data = list(available_staff.filter(
            Q(role__name__in=roles) | Q(additional_roles__name__in=roles)
        ).annotate(name=combined_name).values('id', 'name', 'rank').order_by('rank'))
        data[f'{service_type.lower()}_staff'] = staff_data

    return JsonResponse(data)

def get_current_booking(request):
    contract_id = request.GET.get('contract_id')
    role = request.GET.get('role')
    event_date_str = request.GET.get('event_date')

    try:
        event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date() if event_date_str else None
    except ValueError:
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

def manage_staff_assignments(request, id):
    contract = get_object_or_404(Contract, contract_id=id)
    form = EventStaffBookingForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            booking_id = form.cleaned_data.get('booking_id')
            role = form.cleaned_data.get('role')
            staff = form.cleaned_data.get('staff')
            status = form.cleaned_data.get('status', 'BOOKED')  # Default to 'BOOKED' if not specified
            confirmed = form.cleaned_data.get('confirmed', False)
            hours_booked = form.cleaned_data.get('hours_booked', 0)
            is_update = bool(booking_id)

            print(f"Form valid. Booking ID: {booking_id}, Role: {role}, Staff: {staff}, Status: {status}, Confirmed: {confirmed}, Hours Booked: {hours_booked}")

            if booking_id:
                # Update existing booking
                booking = get_object_or_404(EventStaffBooking, id=booking_id)
                original_role = booking.role
                original_staff_name = booking.staff.get_full_name() if booking.staff else 'None'
                print(f"Updating existing booking. Original Role: {original_role}, Original Staff: {original_staff_name}")
                # Check for other bookings with the same role
                if EventStaffBooking.objects.filter(contract=contract, role=role).exclude(id=booking_id).exists():
                    print("Booking for this role already exists in this contract (update case).")
                    return JsonResponse({'success': False, 'message': 'A booking for this role already exists in this contract.'}, status=400)
            else:
                # Create new booking
                print("Creating new booking.")
                if EventStaffBooking.objects.filter(contract=contract, role=role).exists():
                    print("Booking for this role already exists in this contract (create case).")
                    return JsonResponse({'success': False, 'message': 'A booking for this role already exists in this contract.'}, status=400)
                booking = EventStaffBooking(contract=contract)

            booking.role = role
            booking.staff = staff
            booking.status = status
            booking.confirmed = confirmed
            booking.hours_booked = hours_booked
            booking._request = request  # Set the request as an instance attribute
            booking.save()

            print("Booking saved successfully.")

            # Update the corresponding field in the Contract model with the staff name
            booking.update_contract_role()

            # Update availability based on the booking status
            if status in ['BOOKED', 'PENDING']:
                Availability.objects.update_or_create(
                    staff=staff,
                    date=contract.event_date,
                    defaults={'available': False}
                )
            else:
                Availability.objects.update_or_create(
                    staff=staff,
                    date=contract.event_date,
                    defaults={'available': True}
                )

            # Determine change type and log accordingly
            if booking_id:
                print(f"Booking updated: {original_role} role from {original_staff_name} to {booking.staff.get_full_name()}")
                ChangeLog.objects.create(
                    user=request.user,
                    description=f"Updated booking: {original_role} role from {original_staff_name} to {booking.staff.get_full_name()}",
                    contract=contract
                )
            else:
                print(f"New booking created for {role} with {booking.staff.get_full_name()}")
                ChangeLog.objects.create(
                    user=request.user,
                    description=f"Created new booking for {role} with {booking.staff.get_full_name()}",
                    contract=contract
                )

            if 'PROSPECT' in role:
                prospect_field = f'prospect_photographer{role[-1]}'
                setattr(contract, prospect_field, booking.staff)
                contract.save()

            else:
                # Send email notification to the booked staff
                send_booking_email(request, booking.staff, contract, booking.get_role_display(), is_update)

            return JsonResponse({
                'success': True,
                'message': 'Staff booking saved successfully',
                'role': booking.role,
                'staff_name': booking.staff.get_full_name() if booking.staff else 'None',
                'hours_booked': booking.hours_booked
            })
        else:
            print("Form invalid.")
            print(form.errors)
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    return render(request, 'bookings/manage_staff.html', {'contract': contract, 'form': form})

@login_required
def confirm_booking(request, booking_id):
    booking = get_object_or_404(EventStaffBooking, id=booking_id)
    if request.method == 'POST':
        booking.confirmed = True
        booking.save()
        messages.success(request, 'Your attendance has been confirmed.')
    return redirect('bookings:booking_detail_staff', booking_id=booking_id)


@require_http_methods(["POST"])
def clear_booking(request, booking_id):
    booking = get_object_or_404(EventStaffBooking, id=booking_id)
    contract = booking.contract
    role = booking.role
    staff_name = booking.staff.get_full_name() if booking.staff else "Unknown Staff"
    status = booking.status
    hours_booked = booking.hours_booked

    print(f"Attempting to delete booking with ID: {booking_id}")

    # Update the staff availability for the date if necessary
    if booking.staff:
        availability, created = Availability.objects.get_or_create(
            staff=booking.staff,
            date=booking.contract.event_date
        )
        availability.available = True
        availability.save()

    # Clear the associated role in the contract before deleting the booking
    role_field = SERVICE_ROLE_MAPPING.get(role, None)
    if role_field and hasattr(contract, role_field):
        setattr(contract, role_field, None)
        contract.save()

    # Log the deletion with detailed information
    ChangeLog.objects.create(
        user=request.user,
        description=f"Deleted booking for {role} ({staff_name}). Status was {status}, with {hours_booked} hours booked.",
        contract=contract
    )

    # Delete the booking and inform the user
    booking.delete()
    messages.success(request, f'Booking for {staff_name} has been cleared!')

    # Redirect to the provided next URL or default to the contract details page
    next_url = request.POST.get('next', reverse('contracts:contract_detail', args=[contract.contract_id]) + "#services")
    return redirect(next_url)

@login_required
def booking_detail(request, booking_id):
    # Retrieve the booking instance
    booking = get_object_or_404(EventStaffBooking, id=booking_id)
    contract = booking.contract

    client_edit_form = ContractClientEditForm(instance=contract.client)
    event_edit_form = ContractEventEditForm(instance=contract)

    # Fetch specific bookings by role for each section
    photographer1 = EventStaffBooking.objects.filter(contract=contract, role='PHOTOGRAPHER1').first()
    photographer2 = EventStaffBooking.objects.filter(contract=contract, role='PHOTOGRAPHER2').first()
    engagement_session = EventStaffBooking.objects.filter(contract=contract, role='ENGAGEMENT').first()

    videographer1 = EventStaffBooking.objects.filter(contract=contract, role='VIDEOGRAPHER1').first()
    videographer2 = EventStaffBooking.objects.filter(contract=contract, role='VIDEOGRAPHER2').first()

    dj1 = EventStaffBooking.objects.filter(contract=contract, role='DJ1').first()
    dj2 = EventStaffBooking.objects.filter(contract=contract, role='DJ2').first()

    photobooth_op1 = EventStaffBooking.objects.filter(contract=contract, role='PHOTOBOOTH_OP1').first()
    photobooth_op2 = EventStaffBooking.objects.filter(contract=contract, role='PHOTOBOOTH_OP2').first()

    # Fetch all booking notes and portal messages using constants
    booking_notes = UnifiedCommunication.objects.filter(note_type=UnifiedCommunication.BOOKING, contract=contract)
    portal_messages = UnifiedCommunication.objects.filter(note_type=UnifiedCommunication.PORTAL, contract=contract)

    # Categorize notes by type
    notes_by_type = defaultdict(list)
    for note in booking_notes:
        notes_by_type[note.note_type].append(note)
    for message in portal_messages:
        notes_by_type[message.note_type].append(message)

    # Handle form submission for new notes
    if request.method == 'POST':
        communication_form = BookingCommunicationForm(request.POST)
        if communication_form.is_valid():
            new_note = UnifiedCommunication.objects.create(
                content=communication_form.cleaned_data['message'],
                note_type=UnifiedCommunication.BOOKING,  # Use the constant for booking note type
                created_by=request.user,
                contract=contract,
            )
            return redirect('bookings:booking_detail', booking_id=booking_id)
    else:
        communication_form = BookingCommunicationForm()

    # Prepare the overtime entries with roles mapped
    overtime_entries = [
        {
            'service_type': overtime.overtime_option.service_type.name,
            'role': ROLE_DISPLAY_NAMES.get(overtime.overtime_option.role, overtime.overtime_option.role),
            'hours': overtime.hours,
        }
        for overtime in contract.overtimes.all()
    ]

    # Filter documents that are visible to event staff only
    event_documents = contract.documents.filter(is_event_staff_visible=True)

    return render(request, 'bookings/booking_detail_office.html', {
        'contract': contract,
        'booking': booking,
        'photographer1': photographer1,
        'photographer2': photographer2,
        'engagement_session': engagement_session,
        'videographer1': videographer1,
        'videographer2': videographer2,
        'dj1': dj1,
        'dj2': dj2,
        'photobooth_op1': photobooth_op1,
        'photobooth_op2': photobooth_op2,
        'bookings': EventStaffBooking.objects.filter(contract=contract),
        'booking_notes': booking_notes,
        'portal_messages': portal_messages,
        'staff_member': request.user,
        'overtime_entries': overtime_entries,
        'event_documents': event_documents,
        'communication_form': communication_form,
        'client_edit_form': client_edit_form,
        'event_edit_form': event_edit_form,

    })


@login_required
def booking_detail_staff(request, booking_id):
    booking = get_object_or_404(EventStaffBooking, id=booking_id)
    contract = booking.contract

    client_edit_form = ContractClientEditForm(instance=contract.client)
    event_edit_form = ContractEventEditForm(instance=contract)

    # Fetch specific bookings by role for each section
    photographer1 = EventStaffBooking.objects.filter(contract=contract, role='PHOTOGRAPHER1').first()
    photographer2 = EventStaffBooking.objects.filter(contract=contract, role='PHOTOGRAPHER2').first()
    engagement_session = EventStaffBooking.objects.filter(contract=contract, role='ENGAGEMENT').first()

    videographer1 = EventStaffBooking.objects.filter(contract=contract, role='VIDEOGRAPHER1').first()
    videographer2 = EventStaffBooking.objects.filter(contract=contract, role='VIDEOGRAPHER2').first()

    dj1 = EventStaffBooking.objects.filter(contract=contract, role='DJ1').first()
    dj2 = EventStaffBooking.objects.filter(contract=contract, role='DJ2').first()

    photobooth_op1 = EventStaffBooking.objects.filter(contract=contract, role='PHOTOBOOTH_OP1').first()
    photobooth_op2 = EventStaffBooking.objects.filter(contract=contract, role='PHOTOBOOTH_OP2').first()

    # Fetch booking notes and portal notes
    booking_notes = UnifiedCommunication.objects.filter(note_type=UnifiedCommunication.BOOKING, contract=contract)
    portal_messages = UnifiedCommunication.objects.filter(note_type=UnifiedCommunication.PORTAL, contract=contract)

    # Categorize notes by type
    notes_by_type = defaultdict(list)
    for note in booking_notes:
        notes_by_type[note.note_type].append(note)
    for message in portal_messages:
        notes_by_type[message.note_type].append(message)

    # Prepare the overtime entries with roles mapped
    overtime_entries = [
        {
            'service_type': overtime.overtime_option.service_type.name,
            'role': ROLE_DISPLAY_NAMES.get(overtime.overtime_option.role, overtime.overtime_option.role),
            'hours': overtime.hours,
        }
        for overtime in contract.overtimes.all()
    ]

    # Filter documents that are visible to event staff only
    event_documents = contract.documents.filter(is_event_staff_visible=True)

    return render(request, 'bookings/booking_detail_staff.html', {
        'contract': contract,
        'booking': booking,
        'photographer1': photographer1,
        'photographer2': photographer2,
        'engagement_session': engagement_session,
        'videographer1': videographer1,
        'videographer2': videographer2,
        'dj1': dj1,
        'dj2': dj2,
        'photobooth_op1': photobooth_op1,
        'photobooth_op2': photobooth_op2,
        'bookings': EventStaffBooking.objects.filter(contract=contract),
        'booking_notes': booking_notes,
        'portal_messages': portal_messages,
        'staff_member': request.user,
        'overtime_entries': overtime_entries,
        'event_documents': event_documents,
        'client_edit_form': client_edit_form,
        'event_edit_form': event_edit_form
    })


@login_required
def booking_list(request):
    query = request.GET.get('q')
    event_date_start = request.GET.get('event_date_start')
    event_date_end = request.GET.get('event_date_end')
    service_type = request.GET.get('service_type')
    role_filter = request.GET.get('role_filter')
    status_filter = request.GET.get('status_filter')
    sort_by = request.GET.get('sort_by', 'contract__event_date')  # Note the change here
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
        bookings = bookings.order_by('-' + sort_by)

    return render(request, 'bookings/booking_search_results.html', {'bookings': bookings})