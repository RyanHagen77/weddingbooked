# contracts/views.py
# Standard Library Imports

import logging
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from collections import defaultdict
import json
from django.http import HttpResponse
from django.template.loader import render_to_string

# Django Imports
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponseRedirect
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import datetime


# Django Form Imports

# DRF Imports
from rest_framework import viewsets

# Models
from bookings.models import EventStaffBooking
from communication.models import UnifiedCommunication, Task
from formalwear.models import ContractFormalwearProduct


from .models import Contract, Discount, TaxRate, ChangeLog, ServiceFee

from payments.models import Payment, PaymentPurpose, PaymentSchedule
from services.models import AdditionalEventStaffOption, EngagementSessionOption, OvertimeOption, Package, ServiceType
from wedding_day_guide.models import WeddingDayGuide

# Forms
from bookings.forms import EventStaffBookingForm
from communication.forms import CommunicationForm, TaskForm
from documents.forms import ContractDocumentForm
from payments.forms import PaymentForm, PaymentScheduleForm, SchedulePaymentFormSet
from products.forms import ContractProductFormset
from .forms import (
    ContractSearchForm, NewContractForm, ContractInfoEditForm,
    ContractClientEditForm, ContractEventEditForm, ContractServicesForm, ServiceFeeFormSet
)
from formalwear.forms import ContractFormalwearProductFormset

# Serializers
from .serializers import ContractSerializer

# Views from other apps
from communication.views import send_email_to_client
from payments.views import create_schedule_a_payments

# Logging setup
logger = logging.getLogger(__name__)


class EventViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all().order_by('-contract_date', '-contract_id')
    serializer_class = ContractSerializer

def get_decimal(value):
    try:
        return Decimal(value) if value is not None else Decimal('0.00')
    except (InvalidOperation, ValueError, TypeError):
        return Decimal('0.00')


def success_view(request):
    return render(request, 'success.html')  # Replace 'success.html' with the actual template name for your success page


@login_required
def contract_search(request):
    form = ContractSearchForm(request.GET or None)
    contracts = Contract.objects.all()

    # Clear filters if "clear" flag is in the query string.
    if "clear" in request.GET:
        return redirect(request.path)

    # Apply filters if the form is valid.
    if form.is_valid():
        if form.cleaned_data.get('location'):
            contracts = contracts.filter(location=form.cleaned_data['location'])
        if form.cleaned_data.get('ceremony_site'):
            contracts = contracts.filter(ceremony_site__icontains=form.cleaned_data['ceremony_site'])
        if form.cleaned_data.get('reception_site'):
            contracts = contracts.filter(reception_site__icontains=form.cleaned_data['reception_site'])

        event_date_start = form.cleaned_data.get('event_date_start')
        event_date_end = form.cleaned_data.get('event_date_end')
        if event_date_start and event_date_end:
            contracts = contracts.filter(event_date__range=[event_date_start, event_date_end])

        contract_date_start = form.cleaned_data.get('contract_date_start')
        contract_date_end = form.cleaned_data.get('contract_date_end')
        if contract_date_start and contract_date_end:
            contracts = contracts.filter(contract_date__range=[contract_date_start, contract_date_end])

        if form.cleaned_data.get('contract_number'):
            contracts = contracts.filter(
                Q(custom_contract_number__icontains=form.cleaned_data['contract_number']) |
                Q(old_contract_number__icontains=form.cleaned_data['contract_number'])
            )

        if form.cleaned_data.get('primary_contact'):
            contracts = contracts.filter(client__primary_contact__icontains=form.cleaned_data['primary_contact'])

        if form.cleaned_data.get('status'):
            contracts = contracts.filter(status=form.cleaned_data['status'])

        if form.cleaned_data.get('csr'):
            contracts = contracts.filter(csr=form.cleaned_data['csr'])

        # --- Photographer Filter ---
        if form.cleaned_data.get('photographer'):
            photographer = form.cleaned_data['photographer']
            contracts = contracts.filter(
                Q(photographer1_id=photographer.pk) | Q(photographer2_id=photographer.pk)
            )

        # --- Videographer Filter ---
        if form.cleaned_data.get('videographer'):
            videographer = form.cleaned_data['videographer']
            contracts = contracts.filter(
                Q(videographer1_id=videographer.pk) | Q(videographer2_id=videographer.pk)
            )

        # --- Photobooth Operator Filter ---
        if form.cleaned_data.get('photobooth_operator'):
            operator = form.cleaned_data['photobooth_operator']
            contracts = contracts.filter(
                Q(photobooth_op1_id=operator.pk) | Q(photobooth_op2_id=operator.pk)
            )

        # --- DJ Filter ---
        if form.cleaned_data.get('dj'):
            dj = form.cleaned_data['dj']
            contracts = contracts.filter(
                Q(dj1_id=dj.pk) | Q(dj2_id=dj.pk)
            )

    # Quick Search Logic (q Parameter)
    query = request.GET.get('q')
    if query:
        filters = (
            Q(custom_contract_number__icontains=query) |
            Q(old_contract_number__icontains=query) |
            Q(client__primary_contact__icontains=query) |
            Q(client__partner_contact__icontains=query) |
            Q(client__primary_email__icontains=query) |
            Q(client__primary_phone1__icontains=query) |
            Q(client__primary_phone2__icontains=query)
        )
        # Try to parse the query as a date in multiple formats.
        date_obj = None
        for fmt in ("%m/%d/%Y", "%m-%d-%Y"):
            try:
                date_obj = datetime.strptime(query, fmt).date()
                break
            except ValueError:
                continue
        if date_obj:
            filters |= Q(event_date=date_obj)
        contracts = contracts.filter(filters)

    # Always sort results by soonest event date.
    contracts = contracts.order_by('event_date')

    # Paginate results.
    paginator = Paginator(contracts, 25)
    page_number = request.GET.get('page')
    contracts = paginator.get_page(page_number)

    return render(request, 'contracts/contract_search.html', {
        'form': form,
        'contracts': contracts,
    })



@login_required
def new_contract(request):
    contract_form = NewContractForm(request.POST or None)

    if request.method == 'POST':
        if contract_form.is_valid():
            try:
                with transaction.atomic():
                    # Save the contract and related client
                    contract = contract_form.save()

                    # Automatically create a WeddingDayGuide for the contract
                    WeddingDayGuide.objects.create(contract=contract)

                    # Automatically create Schedule A payments
                    create_schedule_a_payments(contract.contract_id)

                    # Set the contract status
                    contract.status = 'pipeline'
                    contract.save()

                    logger.info(f"New contract created successfully: {contract.contract_id}")
                    return JsonResponse({'redirect_url': reverse('contracts:contract_detail', kwargs={'id': contract.contract_id})})

            except ValidationError as e:
                logger.error(f"Validation error while creating contract: {e}")
                return JsonResponse({'errors': str(e)}, status=400)

            except Exception as e:
                logger.error(f"Unexpected error during contract creation: {e}")
                return JsonResponse({'errors': 'An unexpected error occurred. Please try again later.'}, status=500)

        else:
            # Log form errors
            logger.warning(f"Form validation failed: {contract_form.errors}")
            return JsonResponse({'errors': contract_form.errors.as_json()}, status=400)

    return render(request, 'contracts/contract_new.html', {
        'contract_form': contract_form,
    })


@login_required
def contract_detail(request, id):
    contract = get_object_or_404(Contract, pk=id)
    contract_url = request.build_absolute_uri(reverse('contracts:contract_detail', args=[contract.contract_id]))
    roles = [
        "PHOTOGRAPHER1",
        "PHOTOGRAPHER2",
        "VIDEOGRAPHER1",
        "VIDEOGRAPHER2",
        "DJ1",
        "DJ2",
        "PHOTOBOOTH_OP1",
        "PHOTOBOOTH_OP2",
        "ENGAGEMENT",
        "PROSPECT_PHOTOGRAPHER1",
        "PROSPECT_PHOTOGRAPHER2",
        "PROSPECT_PHOTOGRAPHER3",
    ]

    booking = EventStaffBooking.objects.filter(contract=contract, role__in=roles).first()
    client = contract.client  # Assuming there's a ForeignKey relationship to the Client model

    # Define forms for editing
    contract_info_edit_form = ContractInfoEditForm(instance=contract, prefix='contract_info')
    client_edit_form = ContractClientEditForm(instance=client, prefix='client_info')
    event_edit_form = ContractEventEditForm(instance=contract, prefix='event_details')

    # Check if the user is in the "Office Staff" group
    is_office_staff = request.user.groups.filter(name='Office Staff').exists()

    booking_form = EventStaffBookingForm()
    schedule, created = PaymentSchedule.objects.get_or_create(contract=contract,
                                                              defaults={'schedule_type': 'schedule_a'})
    schedule_id = schedule.id
    schedule_form = PaymentScheduleForm(instance=schedule)
    schedule_payment_formset = SchedulePaymentFormSet(instance=schedule)
    service_fee_formset = ServiceFeeFormSet(instance=contract)
    payment_purposes = PaymentPurpose.objects.all()
    discounts = contract.other_discounts.all()
    service_types = ServiceType.objects.all()

    current_tab = request.GET.get('tab', 'Photography')  # Determine the current tab dynamically


    changelogs = ChangeLog.objects.filter(contract=contract).order_by('-timestamp')

    communication_form = CommunicationForm()
    task_form = TaskForm()
    tasks = Task.objects.filter(contract=contract)

    documents = contract.documents.all()
    for document in documents:
        document.badges = []
        if document.is_client_visible:
            document.badges.append(('badge-success', 'Visible to Client'))
        if document.is_event_staff_visible:
            document.badges.append(('badge-warning', 'Visible to Event Staff'))
        if not document.is_client_visible and not document.is_event_staff_visible:
            document.badges.append(('badge-secondary', 'Internal Use'))

    document_form = ContractDocumentForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and document_form.is_valid():
        contract_document = document_form.save(commit=False)
        contract_document.contract = contract
        contract_document.save()
        return redirect('contracts:contract_detail', id=id)

    all_messages = UnifiedCommunication.objects.filter(contract=contract)
    messages_by_type = defaultdict(list)
    for message in all_messages:
        messages_by_type[message.note_type].append(message)

    if request.method == 'POST':
        communication_form = CommunicationForm(request.POST)
        if communication_form.is_valid():
            print("Form is valid")

            # Create the UnifiedCommunication message
            new_message = UnifiedCommunication.objects.create(
                content=communication_form.cleaned_data['message'],
                note_type=communication_form.cleaned_data['message_type'],
                created_by=request.user,
                contract=contract,
            )
            print(f"Message saved. Note Type: {new_message.note_type}")

            # Check if the sender is an employee and the note type is PORTAL
            if request.user.user_type == 'employee' and new_message.note_type == UnifiedCommunication.PORTAL:
                print("Employee sent a PORTAL type message. Triggering email...")
                send_email_to_client(request, new_message, contract)
            else:
                print(f"Email not triggered. User Type: {request.user.user_type}, Note Type: {new_message.note_type}")

            return redirect('contracts:contract_detail', id=contract.contract_id)
        else:
            print("Form errors:", communication_form.errors)

    else:
        communication_form = CommunicationForm()

    photography_service_type = ServiceType.objects.get(name='Photography')
    photography_packages = Package.objects.filter(service_type=photography_service_type).order_by('name')
    videography_service_type = ServiceType.objects.get(name='Videography')
    dj_service_type = ServiceType.objects.get(name='Dj')
    videography_packages = Package.objects.filter(service_type__name='Videography').order_by('name')
    products_for_contract = contract.contract_products.all()
    payments_made = Payment.objects.filter(contract=contract)
    additional_photography_options = AdditionalEventStaffOption.objects.filter(service_type=photography_service_type,
                                                                               is_active=True)
    additional_videography_options = AdditionalEventStaffOption.objects.filter(service_type=videography_service_type,
                                                                               is_active=True)
    additional_dj_options = AdditionalEventStaffOption.objects.filter(service_type=dj_service_type, is_active=True)
    overtime_options = OvertimeOption.objects.all().values('id', 'role', 'rate_per_hour')
    engagement_session_options = EngagementSessionOption.objects.filter(is_active=True)

    total_overtime_cost = sum(
        overtime.hours * overtime.overtime_option.rate_per_hour
        for overtime in contract.overtimes.all()
    )

    # Prepare resolved data for prospect photographers
    prospect_photographer1 = {
        'label': 'Prospect Photographer 1',
        'name': getattr(contract.prospect_photographer1, 'get_full_name', lambda: "None")() or "None",
        'staff_id': getattr(contract.prospect_photographer1, 'id', None),
        'key': 'PROSPECT1',
    }

    prospect_photographer2 = {
        'label': 'Prospect Photographer 2',
        'name': getattr(contract.prospect_photographer2, 'get_full_name', lambda: "None")() or "None",
        'staff_id': getattr(contract.prospect_photographer2, 'id', None),
        'key': 'PROSPECT2',
    }

    prospect_photographer3 = {
        'label': 'Prospect Photographer 3',
        'name': getattr(contract.prospect_photographer3, 'get_full_name', lambda: "None")() or "None",
        'staff_id': getattr(contract.prospect_photographer3, 'id', None),
        'key': 'PROSPECT3',
    }

    photography_cost = contract.calculate_photography_cost()
    videography_cost = contract.calculate_videography_cost()
    dj_cost = contract.calculate_dj_cost()
    photobooth_cost = contract.calculate_photobooth_cost()

    products_formset = ContractProductFormset(instance=contract, prefix='contract_products')
    formalwear_formset = ContractFormalwearProductFormset(instance=contract, prefix='formalwear_contracts')

    product_subtotal = contract.calculate_product_subtotal()
    package_discount_amount = contract.calculate_package_discount()
    sunday_discount_amount = contract.calculate_sunday_discount()
    other_discounts_total = contract.other_discounts_total

    total_service_cost = contract.calculate_total_service_cost()
    total_discount = contract.calculate_discount()
    final_total = contract.final_total
    amount_paid = contract.amount_paid
    balance_due = contract.balance_due

    tax_rate_object = TaxRate.objects.filter(location=contract.location, is_active=True).first()
    tax_rate = tax_rate_object.tax_rate if tax_rate_object else Decimal('0.00')

    tax_amount = contract.calculate_tax()
    total_payments_received = sum(payment.amount for payment in contract.payments.all())

    balance_due_date = contract.event_date - timedelta(days=60)

    # Serialize the contract data using your serializer.
    serializer = ContractSerializer(contract)
    contract_data_json = json.dumps(serializer.data)

    context = {
        'contract': contract,
        'contract_url': contract_url,
        'booking': booking,
        'client_edit_form': client_edit_form,
        'event_edit_form': event_edit_form,
        'contract_info_edit_form': contract_info_edit_form,
        'packages': photography_packages,
        'photography_packages': photography_packages,
        'prospect_photographer1': prospect_photographer1,
        'prospect_photographer2': prospect_photographer2,
        'prospect_photographer3': prospect_photographer3,
        'videography_packages': videography_packages,
        'dj_packages': photography_packages,
        'booking_form': booking_form,
        'documents': documents,
        'document_form': document_form,
        'communication_form': communication_form,
        'task_form': task_form,
        'tasks': tasks,
        'messages_by_type': dict(messages_by_type),
        'total_discount': total_discount,
        'total_service_cost': total_service_cost,
        'tax_rate': tax_rate,
        'tax_amount': tax_amount,
        'final_total': final_total,
        'payment_form': PaymentForm(),
        'payment_purposes': payment_purposes,
        'total_payments_received': total_payments_received,
        'balance_due_date': balance_due_date,
        'balance_due': balance_due,
        'amount_paid': amount_paid,
        'products': products_for_contract,
        'payments': payments_made,
        'additional_photography_options': additional_photography_options,
        'additional_videography_options': additional_videography_options,
        'additional_dj_options': additional_dj_options,
        'engagement_session_options': engagement_session_options,
        'overtime_options': overtime_options,
        'total_overtime_cost': total_overtime_cost,
        'package_discount_amount': package_discount_amount,
        'sunday_discount_amount': sunday_discount_amount,
        'other_discounts_total': other_discounts_total,
        'photography_cost': photography_cost,
        'videography_cost': videography_cost,
        'dj_cost': dj_cost,
        'photobooth_cost': photobooth_cost,
        'products_formset': products_formset,
        'product_subtotal': product_subtotal,
        'formalwear_formset': formalwear_formset,
        'schedule_id': schedule_id,
        'schedule_form': schedule_form,
        'schedule_payment_formset': schedule_payment_formset,
        'service_fee_formset': service_fee_formset,
        'discounts': discounts,
        'service_types': service_types,
        'current_tab': current_tab,
        'service': current_tab,
        'changelogs': changelogs,
        'is_office_staff': is_office_staff,
        'contract_data_json': contract_data_json,


    }

    return render(request, 'contracts/contract_detail.html', context)


@login_required
def edit_contract(request, id):
    contract = get_object_or_404(Contract, pk=id)
    client = contract.client

    client_edit_form = ContractClientEditForm(request.POST or None, instance=client, prefix='client_info')
    event_edit_form = ContractEventEditForm(request.POST or None, instance=contract, prefix='event_details')
    contract_info_edit_form = ContractInfoEditForm(request.POST or None, instance=contract, prefix='contract_info')

    response_message = {'status': 'error', 'message': 'Invalid form submission.'}

    if request.method == 'POST':
        if 'client_info' in request.POST:
            if client_edit_form.is_valid():
                client_edit_form.save()
                response_message = {'status': 'success', 'message': 'Client info updated successfully.'}
            else:
                response_message = {'status': 'error', 'message': client_edit_form.errors}

        elif 'event_details' in request.POST:
            if event_edit_form.is_valid():
                event_edit_form.save()
                response_message = {'status': 'success', 'message': 'Event info updated successfully.'}
            else:
                response_message = {'status': 'error', 'message': event_edit_form.errors}

        elif 'contract_info' in request.POST:
            if contract_info_edit_form.is_valid():
                contract_info_edit_form.save()
                response_message = {'status': 'success', 'message': 'Contract info updated successfully.'}
            else:
                response_message = {'status': 'error', 'message': contract_info_edit_form.errors}

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(response_message)
        else:
            return redirect('contracts:contract_detail', id=id)

    return render(request, 'contracts/manage_staff.html', {
        'client_edit_form': client_edit_form,
        'event_edit_form': event_edit_form,
        'contract_info_edit_form': contract_info_edit_form,
        'contract': contract
    })

@login_required
def edit_services(request, id):
    contract = get_object_or_404(Contract, pk=id)

    if request.method == 'POST':
        section = request.POST.get('section')  # Identify the tab being updated

        try:
            # Update only the relevant fields for the specified section
            if section == 'photography':
                contract.photography_package = (
                    Package.objects.get(pk=request.POST.get('photography_package'))
                    if request.POST.get('photography_package') else None
                )
                contract.photography_additional = (
                    AdditionalEventStaffOption.objects.get(pk=request.POST.get('photography_additional'))
                    if request.POST.get('photography_additional') else None
                )
                contract.engagement_session = (
                    EngagementSessionOption.objects.get(pk=request.POST.get('engagement_session'))
                    if request.POST.get('engagement_session') else None
                )

            elif section == 'videography':
                contract.videography_package = (
                    Package.objects.get(pk=request.POST.get('videography_package'))
                    if request.POST.get('videography_package') else None
                )
                contract.videography_additional = (
                    AdditionalEventStaffOption.objects.get(pk=request.POST.get('videography_additional'))
                    if request.POST.get('videography_additional') else None
                )

            elif section == 'dj':
                contract.dj_package = (
                    Package.objects.get(pk=request.POST.get('dj_package'))
                    if request.POST.get('dj_package') else None
                )
                contract.dj_additional = (
                    AdditionalEventStaffOption.objects.get(pk=request.POST.get('dj_additional'))
                    if request.POST.get('dj_additional') else None
                )

            elif section == 'photobooth':
                contract.photobooth_package = (
                    Package.objects.get(pk=request.POST.get('photobooth_package'))
                    if request.POST.get('photobooth_package') else None
                )

            # Save the contract with the updated fields
            contract.save()

            # Return appropriate response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'message': 'Services updated successfully'})
            return redirect(reverse('contracts:contract_detail', args=[id]) + '#services')

        except (Package.DoesNotExist, AdditionalEventStaffOption.DoesNotExist, EngagementSessionOption.DoesNotExist) as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            return render(request, 'contracts/edit_services.html', {'error': str(e), 'contract': contract})

    # For GET requests, prepopulate the form with the contract's data
    initial_data = {
        'photography_package': contract.photography_package_id,
        'photography_additional': contract.photography_additional_id,
        'engagement_session': contract.engagement_session_id,
        'prospect_photographer1': contract.prospect_photographer1,
        'prospect_photographer2': contract.prospect_photographer2,
        'prospect_photographer3': contract.prospect_photographer3,
        'videography_package': contract.videography_package_id,
        'videography_additional': contract.videography_additional_id,
        'dj_package': contract.dj_package_id,
        'dj_additional': contract.dj_additional_id,
        'photobooth_package': contract.photobooth_package_id,
    }

    form = ContractServicesForm(initial=initial_data)
    context = {
        'contract': contract,
        'services_form': form,
    }
    return render(request, 'contracts/edit_services.html', context)

def get_contract_data(request, id):
    contract = get_object_or_404(Contract, pk=id)

    # Include client data in the response if available
    client_data = {}
    if contract.client:
        client_data = {
            'primary_contact': contract.client.primary_contact,
            'primary_email': contract.client.primary_email,
            # Convert PhoneNumber to string for JSON serialization
            'primary_phone1': str(contract.client.primary_phone1) if contract.client.primary_phone1 else '',
            'partner_contact': contract.client.partner_contact,
            'partner_email': contract.client.partner_email,
            'partner_phone1': str(contract.client.partner_phone1),
            'primary_address1': contract.client.primary_address1,
            'primary_address2': contract.client.primary_address2,
            'city': contract.client.city,
            'state': contract.client.state,
            'postal_code': contract.client.postal_code,
            'alt_contact': contract.client.alt_contact,
            'alt_email': contract.client.alt_email,
            'alt_phone': str(contract.client.alt_phone),
        }

    # Prepare the rest of the data
    data = {
        'location': contract.location.name if contract.location else '',
        'event_date': contract.event_date.strftime('%Y-%m-%d') if contract.event_date else '',
        'status': contract.get_status_display(),
        'csr': contract.csr.get_full_name() if contract.csr else '',
        'coordinator': contract.coordinator.get_full_name() if contract.coordinator else '',
        'lead_source': contract.get_lead_source_display(),
        'client': client_data,  # Add the client data here

        # Add individual event fields
        'bridal_party_qty': contract.bridal_party_qty,
        'guests_qty': contract.guests_qty,
        'ceremony_site': contract.ceremony_site,
        'ceremony_city': contract.ceremony_city,
        'ceremony_state': contract.ceremony_state,
        'ceremony_contact': contract.ceremony_contact,
        'ceremony_phone': str(contract.ceremony_phone) if contract.ceremony_phone else '',
        'ceremony_email': contract.ceremony_email,
        'reception_site': contract.reception_site,
        'reception_city': contract.reception_city,
        'reception_state': contract.reception_state,
        'reception_contact': contract.reception_contact,
        'reception_phone': str(contract.reception_phone) if contract.reception_phone else '',
        'reception_email': contract.reception_email,
        # Add any other event fields you have in your model...

        # Include custom_text
        'custom_text': contract.custom_text,
    }
    return JsonResponse(data)

def remove_discount(request, contract_id, discount_id):
    contract = get_object_or_404(Contract, contract_id=contract_id)
    discount = get_object_or_404(Discount, id=discount_id)
    contract.other_discounts.remove(discount)
    discount.delete()
    url = reverse('contracts:contract_detail', args=[contract_id]) + '#services'
    return redirect(url)


def discounts_view(request, contract_id):
    contract = get_object_or_404(Contract, contract_id=contract_id)

    if request.method == 'POST':
        # Handle form submission
        memo = request.POST.get('memo')
        amount = request.POST.get('amount')
        service_type_id = request.POST.get('service_type')

        service_type = None
        if service_type_id:
            service_type = ServiceType.objects.get(id=service_type_id)

        discount = Discount.objects.create(memo=memo, amount=amount, service_type=service_type)
        contract.other_discounts.add(discount)  # Associate the discount with the contract

        url = reverse('contracts:contract_detail', args=[contract_id]) + '#services'
        return redirect(url)

    # Fetch all discounts to display in the table
    discounts = contract.other_discounts.all()

    # Fetch all service types to populate the dropdown in the form
    service_types = ServiceType.objects.all()

    # Render the template with the discounts and service types
    return render(request, 'contracts/contract_detail.html',
                  {'contract': contract, 'discounts': discounts, 'service_types': service_types})


def get_tax_rate(request, location_id):
    try:
        tax_rate = TaxRate.objects.get(location_id=location_id)
        return JsonResponse({'tax_rate': float(tax_rate.tax_rate)})
    except TaxRate.DoesNotExist:
        return JsonResponse({'error': 'Tax rate not found'}, status=404)


@login_required
def create_or_update_service_fees(request, contract_id):
    """
    Create or update service fees for a contract.
    This view uses an inline formset for ServiceFee with can_delete=True.
    """
    contract = get_object_or_404(Contract, contract_id=contract_id)

    if request.method == 'POST':
        service_fee_formset = ServiceFeeFormSet(request.POST, instance=contract)
        if service_fee_formset.is_valid():
            service_fee_formset.save()
            # Optional: update contract totals based on service fees.
            contract.total_cost = sum(fee.amount for fee in contract.servicefees.all())
            contract.save()

            # If the request is AJAX, return a JSON response.
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            else:
                return HttpResponseRedirect(
                    reverse('contracts:contract_detail', kwargs={'id': contract_id}) + '#financial')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': service_fee_formset.errors}, status=400)
            # For non-AJAX requests, re-render the page with errors.
    else:
        # Always render at least one blank form by setting extra=1.
        service_fee_formset = ServiceFeeFormSet(instance=contract, extra=1)

    return render(request, 'contracts/service_fee_form.html', {
        'contract': contract,
        'service_fee_formset': service_fee_formset,
    })


def get_service_fees(request, contract_id):
    fees = ServiceFee.objects.filter(contract_id=contract_id)
    html = render_to_string("contracts/partials/financial/_service_fees.html", {"fees": fees})
    return HttpResponse(html, content_type="text/html")


def get_package_discounts(request, contract_id):
    # Assuming you have access to the contract ID or other identifiers
    contract = Contract.objects.get(pk=contract_id)
    package_discount = contract.calculate_package_discount()

    return JsonResponse({"packageDiscount": package_discount})

def get_financial_details(request, contract_id):
    contract = get_object_or_404(Contract, id=contract_id)

    # Calculate subtotal, service discount, and service total after discounts
    subtotal = contract.calculate_subtotal()


    context = {
        'photography_cost': contract.calculate_photography_cost(),
        'videography_cost': contract.calculate_videography_cost(),
        'dj_cost': contract.calculate_dj_cost(),
        'photobooth_cost': contract.calculate_photobooth_cost(),
        'subtotal': subtotal,
        'package_discount': contract.calculate_package_discount(),
        'sunday_discount': contract.calculate_sunday_discount(),
        'other_discount': contract.other_discounts.amount if contract.other_discounts else Decimal('0.00'),
        'total_discount': contract.calculate_discount(),
        'total_service_cost_after_discounts': contract.calculate_total_service_cost_after_discounts(),
        'total_product_cost': contract.calculate_total_product_cost()
        # Add more context as needed
    }

    return render(request, 'financial.html', context)

def financial_view(request, contract_id):
    # Assuming you have a function to get the contract and its associated data
    contract = Contract.objects.get(pk=contract_id)

    context = {
        'contract': contract,
        # Add other context variables as needed
    }
    return render(request, 'contract_detail.html', context)
