# contracts/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, F, Value, CharField, Sum
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from users.models import Role, CustomUser, Group
from communication.models import UnifiedCommunication, Task
from communication.views import send_task_assignment_email
from .forms import (ContractSearchForm, ClientForm, NewContractForm, ContractForm, ContractInfoEditForm, ContractClientEditForm,
                    ContractEventEditForm, ContractServicesForm, ContractDocumentForm,
                    EventStaffBookingForm, ContractProductFormset, PaymentForm, PaymentScheduleForm,
                    SchedulePaymentFormSet)
from communication.forms import CommunicationForm, TaskForm  # Importing from the communication app
from .models import (Contract, ServiceType, Availability, Payment, Package,
                     AdditionalEventStaffOption, EngagementSessionOption, Discount, EventStaffBooking, ContractOvertime, AdditionalProduct,
                     OvertimeOption, PaymentPurpose, PaymentSchedule, SchedulePayment,
                     TaxRate, ContractDocument, ChangeLog)
from django.db import transaction
from django.core.mail import send_mail
from django.db.models.functions import Concat
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal, InvalidOperation
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.sites.shortcuts import get_current_site
from .serializers import ContractSerializer
from rest_framework import viewsets
from datetime import datetime, timedelta
import math
import json
from django.utils.timezone import now
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from weasyprint import HTML
import logging
from django.contrib.auth.forms import PasswordResetForm
from django.http import HttpRequest, HttpResponseRedirect
from collections import defaultdict
from django.contrib.auth import logout
from .constants import SERVICE_ROLE_MAPPING  # Adjust the import path as needed

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

def search(request):
    form = ContractSearchForm(request.GET)
    contracts = Contract.objects.all().order_by('-event_date')  # Descending order by default
    tab = request.GET.get('tab', 'contracts')  # Default to 'contracts' if 'tab' is not specified

    order = request.GET.get('order', 'desc')
    if order == 'asc':
        contracts = contracts.order_by('event_date')
    else:
        contracts = contracts.order_by('-event_date')

    if form.is_valid():
        # Existing fields filtering
        if form.cleaned_data.get('location'):
            contracts = contracts.filter(location=form.cleaned_data['location'])
        if form.cleaned_data.get('ceremony_site'):
            contracts = contracts.filter(ceremony_site__icontains=form.cleaned_data['ceremony_site'])
        if form.cleaned_data.get('reception_site'):
            contracts = contracts.filter(reception_site__icontains=form.cleaned_data['reception_site'])

        # Event date range filter
        event_date_start = form.cleaned_data.get('event_date_start')
        event_date_end = form.cleaned_data.get('event_date_end')
        if event_date_start and event_date_end:
            contracts = contracts.filter(event_date__range=[event_date_start, event_date_end])

        # Contract date range filter
        contract_date_start = form.cleaned_data.get('contract_date_start')
        contract_date_end = form.cleaned_data.get('contract_date_end')
        if contract_date_start and contract_date_end:
            contracts = contracts.filter(contract_date__range=[contract_date_start, contract_date_end])

        # Custom contract number filter
        if form.cleaned_data.get('contract_number'):
            contracts = contracts.filter(custom_contract_number__icontains=form.cleaned_data['contract_number'])
        if form.cleaned_data.get('primary_contact'):
            contracts = contracts.filter(client__primary_contact__icontains=form.cleaned_data['primary_contact'])
        if form.cleaned_data.get('status'):
            contracts = contracts.filter(status=form.cleaned_data['status'])
        if form.cleaned_data.get('csr'):
            contracts = contracts.filter(csr=form.cleaned_data['csr'])

        # Filtering by staff roles
        if form.cleaned_data.get('photographer'):
            photographer_contracts = EventStaffBooking.objects.filter(
                staff=form.cleaned_data['photographer'],
                role__in=['PHOTOGRAPHER1', 'PHOTOGRAPHER2']
            ).values_list('contract_id', flat=True)
            contracts = contracts.filter(contract_id__in=photographer_contracts)

        if form.cleaned_data.get('videographer'):
            videographer_contracts = EventStaffBooking.objects.filter(
                staff=form.cleaned_data['videographer'],
                role__in=['VIDEOGRAPHER1', 'VIDEOGRAPHER2']
            ).values_list('contract_id', flat=True)
            contracts = contracts.filter(contract_id__in=videographer_contracts)

        if form.cleaned_data.get('photobooth_operator'):
            photobooth_operator_contracts = EventStaffBooking.objects.filter(
                staff=form.cleaned_data['photobooth_operator'],
                role='PHOTOBOOTH_OP'
            ).values_list('contract_id', flat=True)
            contracts = contracts.filter(contract_id__in=photobooth_operator_contracts)

    # Quick search logic
    query = request.GET.get('q')
    if query:
        contracts = contracts.filter(
            Q(custom_contract_number__icontains=query) |
            Q(client__primary_contact__icontains=query) |
            Q(client__partner_contact__icontains=query)
        )
    # Booking search
    booking_search_query = request.GET.get('booking_q')
    bookings = EventStaffBooking.objects.all()
    if booking_search_query:
        bookings = bookings.filter(
            Q(staff__username__icontains=booking_search_query) |
            Q(staff__first_name__icontains=booking_search_query) |
            Q(staff__last_name__icontains=booking_search_query)
        )

    # Additional filtering for bookings
    # ...

    return render(request, 'contracts/search.html',
                  {'form': form, "contracts": contracts, "bookings": bookings, 'active_tab': tab})
def search_contracts(request):
    form = ContractSearchForm(request.GET)
    contracts = Contract.objects.all()

    if form.is_valid():
        # Existing fields filtering
        if form.cleaned_data.get('location'):
            contracts = contracts.filter(location=form.cleaned_data['location'])
        if form.cleaned_data.get('ceremony_site'):
            contracts = contracts.filter(ceremony_site__icontains=form.cleaned_data['ceremony_site'])
        if form.cleaned_data.get('reception_site'):
            contracts = contracts.filter(reception_site__icontains=form.cleaned_data['reception_site'])

        # Event date range filter
        event_date_start = form.cleaned_data.get('event_date_start')
        event_date_end = form.cleaned_data.get('event_date_end')
        if event_date_start and event_date_end:
            contracts = contracts.filter(event_date__range=[event_date_start, event_date_end])

        # Contract date range filter
        contract_date_start = form.cleaned_data.get('contract_date_start')
        contract_date_end = form.cleaned_data.get('contract_date_end')
        if contract_date_start and contract_date_end:
            contracts = contracts.filter(contract_date__range=[contract_date_start, contract_date_end])

        # Custom contract number filter
        if form.cleaned_data.get('contract_number'):
            contracts = contracts.filter(custom_contract_number__icontains=form.cleaned_data['contract_number'])
        if form.cleaned_data.get('primary_contact'):
            contracts = contracts.filter(client__primary_contact__icontains=form.cleaned_data['primary_contact'])
        if form.cleaned_data.get('status'):
            contracts = contracts.filter(status=form.cleaned_data['status'])
        if form.cleaned_data.get('csr'):
            contracts = contracts.filter(csr=form.cleaned_data['csr'])

        # Filtering by staff roles
        if form.cleaned_data.get('photographer'):
            photographer_contracts = EventStaffBooking.objects.filter(
                staff=form.cleaned_data['photographer'],
                role__in=['PHOTOGRAPHER1', 'PHOTOGRAPHER2']
            ).values_list('contract_id', flat=True)
            contracts = contracts.filter(contract_id__in=photographer_contracts)

        if form.cleaned_data.get('videographer'):
            videographer_contracts = EventStaffBooking.objects.filter(
                staff=form.cleaned_data['videographer'],
                role__in=['VIDEOGRAPHER1', 'VIDEOGRAPHER2']
            ).values_list('contract_id', flat=True)
            contracts = contracts.filter(contract_id__in=videographer_contracts)

        if form.cleaned_data.get('photobooth_operator'):
            photobooth_operator_contracts = EventStaffBooking.objects.filter(
                staff=form.cleaned_data['photobooth_operator'],
                role='PHOTOBOOTH_OP'
            ).values_list('contract_id', flat=True)
            contracts = contracts.filter(contract_id__in=photobooth_operator_contracts)

    # Quick search logic
    query = request.GET.get('q')
    if query:
        contracts = contracts.filter(
            Q(custom_contract_number__icontains=query) |
            Q(client__primary_contact__icontains=query) |
            Q(client__partner_contact__icontains=query)
        )

    return render(request, 'contracts/contract_search.html', {'form': form, 'contracts': contracts})


User = get_user_model()
def new_contract(request):
    contract_form = NewContractForm(request.POST or None)
    client_form = ClientForm(request.POST or None)

    if request.method == 'POST':
        if client_form.is_valid() and contract_form.is_valid():
            with transaction.atomic():
                client = client_form.save(commit=False)
                primary_email = client_form.cleaned_data['primary_email']
                user, created = User.objects.get_or_create(username=primary_email, defaults={'email': primary_email})

                if created:
                    group = Group.objects.get(name='Client')
                    user.groups.add(group)
                    send_password_reset_email(primary_email)

                client.user = user
                client.save()

                contract = contract_form.save(commit=False)
                contract.client = client
                contract.save()

                # Create a schedule_a payment schedule for the contract by default
                create_schedule_a_payments(contract.contract_id)
                contract.status = 'pending'  # Optionally update contract status
                contract.save()

                # Redirect to the contract_detail page for the newly created contract
                return redirect('contracts/contract_detail', contract_id=contract.contract_id)

    context = {
        'contract_form': contract_form,
        'client_form': client_form,
    }
    return render(request, 'contracts/contract_new.html', context)

def send_password_reset_email(user_email):
    # Create a PasswordResetForm instance with the user's email
    form = PasswordResetForm({'email': user_email})

    if form.is_valid():
        # Create a dummy HttpRequest object
        request = HttpRequest()

        # Since you're using Gmail SMTP, the domain should match your email domain
        # If your Django app is hosted elsewhere, replace with your app's domain
        request.META['SERVER_NAME'] = '10.44.1.8'  # Use 'localhost' for local testing
        request.META['SERVER_PORT'] = '8000'  # Default port for Django development server

        # Save the form, which sends the password reset email
        form.save(
            request=request,
            use_https=True,  # Use HTTPS for security
            from_email='testmydjango420@gmail.com',  # Your Gmail address
            email_template_name='registration/password_reset_email.html'
        )
    else:
        # Handle the case where the form is not valid
        # You can add logging or other error handling here
        pass


def custom_login(request):
    User = get_user_model()  # Use the custom user model

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            username = User.objects.get(email=email).username
        except User.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return render(request, 'contracts/client_portal_login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Fetch the contract associated with the user
            contract = Contract.objects.filter(client=user.client).first()
            if contract:
                return redirect('contracts:client_portal', contract_id=contract.contract_id)
            else:
                messages.error(request, "No associated contract found.")
                return render(request, 'contracts/client_portal_login.html')
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, 'contracts/client_portal_login.html')

def custom_logout(request):
    logout(request)
    return redirect('contracts:client_portal_login')  # Use the view name, not the URL path

@login_required
def client_portal(request, contract_id):
    contract = get_object_or_404(Contract, contract_id=contract_id)
    content_type = ContentType.objects.get_for_model(Contract)

    # Fetch only 'contract' type notes related to this contract
    contract_notes = UnifiedCommunication.objects.filter(
        content_type=content_type,
        object_id=contract.contract_id,
        note_type=UnifiedCommunication.CONTRACT
    ).order_by('-created_at')

    if request.method == 'POST':
        form = CommunicationForm(request.POST)
        if form.is_valid():
            message = UnifiedCommunication.objects.create(
                content=form.cleaned_data['message'],
                note_type=UnifiedCommunication.CONTRACT,
                created_by=request.user,
                content_type=content_type,
                object_id=contract.contract_id
            )
            print("Message created:", message.content)  # Debugging line

            # Send an email notification to the coordinator
            if contract.coordinator:
                send_contract_message_email(request, message, contract)

            return redirect('contracts:client_portal', contract_id=contract.contract_id)
        else:
            print("Form errors:", form.errors)  # Debugging line

    form = CommunicationForm()
    context = {
        'contract': contract,
        'contract_notes': contract_notes,
        'form': form,
    }
    return render(request, 'contracts/client_portal.html', context)

def send_contract_message_email(request, message, contract):
    if contract.coordinator and contract.coordinator.email:
        subject = f'New Message Posted for Contract {contract.custom_contract_number}'
        message_body = render_to_string('communication/contract_message_email.html', {
            'user': request.user,
            'message': message,
            'contract': contract,
            'domain': get_current_site(request).domain,
        })
        send_mail(
            subject,
            message_body,
            'testmydjango420@gmail.com',  # Use a valid sender email address
            [contract.coordinator.email],
            fail_silently=False,
        )
        print("Email sent to coordinator:", contract.coordinator.email)
    else:
        print("No coordinator assigned, or missing email.")

def send_email_to_client(request, message, contract):
    client_user = contract.client.user
    if client_user and client_user.email:
        subject = f'New Message from Coordinator for Contract {contract.custom_contract_number}'
        message_body = render_to_string('communication/contract_message_email.html', {
            'user': request.user,
            'message': message,
            'contract': contract,
            'domain': get_current_site(request).domain,
        })
        send_mail(
            subject,
            message_body,
            'testmydjango420@gmail.com',
            [client_user.email],
            fail_silently=False,
        )
        print("Email sent to client:", client_user.email)
    else:
        print("Client does not have a valid email.")


def contract_detail(request, id):
    contract = get_object_or_404(Contract, pk=id)
    form = ContractForm(request.POST or None, instance=contract)
    client = contract.client  # Assuming there's a ForeignKey relationship to the Client model
    booking_form = EventStaffBookingForm()
    schedule_id = contract.payment_schedule.id if hasattr(contract, 'payment_schedule') else None
    schedule, created = PaymentSchedule.objects.get_or_create(contract=contract)
    schedule_form = PaymentScheduleForm(instance=schedule)
    schedule_payment_formset = SchedulePaymentFormSet(instance=schedule)
    discounts = contract.other_discounts.all()
    print("Other discounts total:", contract.other_discounts_total)  # Debugging statement
    service_types = ServiceType.objects.all()

    if request.method == 'POST':
        if form.is_valid():
            form.save(request.user)
            # Save prospect photographers separately if needed
            contract.prospect_photographer1 = form.cleaned_data.get('prospect_photographer1')
            contract.prospect_photographer2 = form.cleaned_data.get('prospect_photographer2')
            contract.prospect_photographer3 = form.cleaned_data.get('prospect_photographer3')
            contract.save()
            return redirect('contracts:contract_detail', id=id)

    if request.method == 'POST':
        contract_info_edit_form = ContractInfoEditForm(request.POST, instance=contract, prefix='contract_info')
        client_edit_form = ContractClientEditForm(request.POST, instance=client, prefix='client_info')
        event_edit_form = ContractEventEditForm(request.POST, instance=contract, prefix='event_details')
    else:
        contract_info_edit_form = ContractInfoEditForm(instance=contract, prefix='contract_info')
        client_edit_form = ContractClientEditForm(instance=client, prefix='client_info')
        event_edit_form = ContractEventEditForm(instance=contract, prefix='event_details')

    document_form = ContractDocumentForm(request.POST or None, request.FILES or None)
    communication_form = CommunicationForm()
    task_form = TaskForm()
    tasks = Task.objects.filter(contract=contract)

    # Handle document upload
    if request.method == 'POST' and 'upload_document' in request.POST:
        if document_form.is_valid():
            contract_document = document_form.save(commit=False)
            contract_document.contract = contract
            contract_document.save()
            return redirect('contracts:contract_detail', id=id)

    if request.method == 'POST':
        if client_edit_form.is_valid():
            client_edit_form.save()
            return redirect('contracts:contract_detail', id=id)

    # Prepare context data
    content_type = ContentType.objects.get_for_model(contract)
    all_messages = UnifiedCommunication.objects.filter(
        content_type=content_type, object_id=contract.contract_id)

    # Categorize messages by type
    messages_by_type = defaultdict(list)
    for message in all_messages:
        messages_by_type[message.note_type].append(message)

    if request.method == 'POST':
        communication_form = CommunicationForm(request.POST)
        if communication_form.is_valid():
            new_message = UnifiedCommunication.objects.create(
                content=communication_form.cleaned_data['message'],
                note_type=communication_form.cleaned_data['message_type'],
                created_by=request.user,
                content_type=content_type,
                object_id=contract.contract_id
            )

            # Check if the sender is a coordinator and send an email to the client
            if request.user.is_coordinator:
                send_email_to_client(request, new_message, contract)

            return redirect('contracts:contract_detail', id=contract.contract_id)
    else:
        communication_form = CommunicationForm()

    # Fetch related data
    photography_service_type = ServiceType.objects.get(name='Photography')
    videography_service_type = ServiceType.objects.get(name='Videography')
    dj_service_type = ServiceType.objects.get(name='Dj')
    photography_packages = Package.objects.filter(service_type__name='Photography').order_by('name')
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
    print("Engagement Session Options:", engagement_session_options)

    # Check the first object's price attribute if there are any options
    if engagement_session_options:
        print("First option price:", engagement_session_options[0].price)

    total_overtime_cost = 0

    if request.method == 'POST':
        # Handle your POST logic here, potentially processing AJAX requests
        # This could involve creating or updating ContractOvertime instances directly
        pass
    else:
        # For a GET request, prepare any data needed for displaying the form
        # Calculate the total overtime cost directly from related ContractOvertime instances
        total_overtime_cost = sum(
            overtime.hours * overtime.overtime_option.rate_per_hour
            for overtime in contract.overtimes.all()
        )

    # Calculate costs using methods defined in the Contract model
    photography_cost = contract.calculate_photography_cost()
    videography_cost = contract.calculate_videography_cost()
    dj_cost = contract.calculate_dj_cost()
    photobooth_cost = contract.calculate_photobooth_cost()

    products_formset = ContractProductFormset(instance=contract, prefix='contract_products')

    product_subtotal = contract.calculate_product_subtotal()

    # Directly access discounts from the contract if they are fields in the Contract model
    package_discount_amount = contract.calculate_package_discount()
    sunday_discount_amount = contract.calculate_sunday_discount()
    other_discounts_total = contract.other_discounts_total

    # Using model's methods to calculate total cost, tax, discounts, final total, paid amount, and balance due
    total_service_cost = contract.calculate_total_service_cost()
    total_discount = contract.calculate_discount()
    final_total = contract.final_total
    amount_paid = contract.amount_paid
    balance_due = contract.balance_due

    # Fetch the tax rate based on the contract's location
    tax_rate_object = TaxRate.objects.filter(location=contract.location, is_active=True).first()
    if tax_rate_object:
        tax_rate = tax_rate_object.tax_rate
    else:
        tax_rate = Decimal('0.00')  # Fallback value if no tax rate is found

        # Use the fetched tax rate to calculate tax
    tax_amount = contract.calculate_tax()

    # Calculating initial payment
    initial_payment = math.ceil((contract.final_total * Decimal('0.40')) / 100) * 100
    total_payments_received = sum(payment.amount for payment in contract.payments.all())

    payment_form = PaymentForm()  # For GET request

    if request.method == 'POST':
        if 'submit_payment' in request.POST:
            payment_form = PaymentForm(request.POST)
            if payment_form.is_valid():
                new_payment = payment_form.save(commit=False)
                new_payment.contract = contract
                new_payment.save()
                # Redirect or render as appropriate
                return redirect('contracts:contract_detail', id=contract.contract_id)
            else:
                # Handle form errors
                print("Payment form errors:", payment_form.errors)

                # Calculating balance due date
    balance_due_date = contract.event_date - timedelta(days=60)

    context = {
        'contract': contract,
        'form': form,
        'packages': photography_packages,
        'photography_packages': photography_packages,
        'prospect_photographer1': contract.prospect_photographer1,
        'prospect_photographer2': contract.prospect_photographer2,
        'prospect_photographer3': contract.prospect_photographer3,
        'videography_packages': videography_packages,
        'dj_packages': photography_packages,
        'booking_form' : booking_form,
        'document_form': document_form,
        'communication_form': communication_form,
        'task_form': task_form,
        'tasks': tasks,
        'contract_info_edit_form': contract_info_edit_form,
        'client_edit_form': client_edit_form,
        'event_edit_form': event_edit_form,
        'messages_by_type': dict(messages_by_type),
        'total_discount': total_discount,
        'total_service_cost': total_service_cost,
        'tax_rate': tax_rate,
        'tax_amount': tax_amount,
        'final_total': final_total,
        'payment_form': payment_form,
        'initial_payment': initial_payment,
        'total_payments_received': total_payments_received,
        'balance_due_date': balance_due_date,
        'balance_due': balance_due,
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
        'schedule_id': schedule_id,
        'schedule_form': schedule_form,
        'schedule_payment_formset': schedule_payment_formset,
        'discounts': discounts,
        'service_types': service_types
    }

    return render(request, 'contracts/contract_detail.html',  context)


# @login_required  # Optional, ensures only logged-in users can delete documents


def delete_document(request, document_id):
    document = get_object_or_404(ContractDocument, pk=document_id)

    # Check if the user has permission to delete the document
    if request.user.has_perm('contracts.delete_contractdocument') or request.user == document.contract.owner:
        document.delete()
        messages.success(request, "Document removed successfully.")
    else:
        messages.error(request, "You do not have permission to delete this document.")

    # Redirect back to the contract detail page or wherever appropriate
    return redirect('contracts:contract_detail', id=document.contract.contract_id)


def edit_contract(request, id):
    contract = get_object_or_404(Contract, pk=id)
    client = contract.client

    contract_info_edit_form = ContractInfoEditForm(request.POST or None, instance=contract, prefix='contract_info')
    client_edit_form = ContractClientEditForm(request.POST or None, instance=client, prefix='client_info')
    event_edit_form = ContractEventEditForm(request.POST or None, instance=contract, prefix='event_details')

    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if 'contract_info' in request.POST:
            contract_info_edit_form = ContractInfoEditForm(request.POST,
                                                           instance=contract)  # Ensure this form is defined
            if contract_info_edit_form.is_valid():
                original_status = contract.status  # Capture original status before saving
                contract = contract_info_edit_form.save()

                # Check for status change and log it
                if original_status != contract.status:
                    ChangeLog.objects.create(
                        user=request.user,
                        description=f"Updated contract status from {original_status} to {contract.status} for contract ID {contract.id}"
                    )

                if contract.status == 'dead':  # Check if the contract status is 'dead'
                    # Delete all bookings associated with this contract
                    EventStaffBooking.objects.filter(contract=contract).delete()
                    # Optional: Log the deletion of bookings
                    ChangeLog.objects.create(
                        user=request.user,
                        description=f"Deleted all bookings due to contract status 'dead' for contract ID {contract.id}"
                    )

                if is_ajax:
                    return JsonResponse({'status': 'success', 'message': 'Contract info updated successfully.'})
                else:
                    return redirect('contracts:contract_detail', id=contract.id)
            else:
                if is_ajax:
                    return JsonResponse({'status': 'error', 'errors': contract_info_edit_form.errors}, status=400)

        elif 'client_info' in request.POST:
            if client_edit_form.is_valid():
                client_edit_form.save()
                if is_ajax:
                    return JsonResponse({'status': 'success', 'message': 'Client info updated successfully.'})
                else:
                    return redirect('contracts/contract_detail', id=id)
            else:
                if is_ajax:
                    return JsonResponse({'status': 'error', 'errors': client_edit_form.errors}, status=400)

        elif 'event_details' in request.POST:
            if event_edit_form.is_valid():
                event_edit_form.save()
                if is_ajax:
                    return JsonResponse({'status': 'success', 'message': 'Event info updated successfully.'})
                else:
                    return redirect('contracts/contract_detail', id=id)
            else:
                if is_ajax:
                    return JsonResponse({'status': 'error', 'errors': event_edit_form.errors}, status=400)

        elif 'service_details' in request.POST:  # Check for service tab form submission
            # Handle form submission for the service tab
            # Add your logic here for processing the service tab form
            if is_ajax:
                return JsonResponse({'status': 'success', 'message': 'Service details updated successfully.'})
            else:
                return redirect('contracts/contract_detail', id=id)

        if not is_ajax:  # Only redirect if not an AJAX request
            return redirect('contracts/contract_detail', id=id)

    return render(request, 'contracts/contract_detail.html', {
        'contract_info_edit_form': contract_info_edit_form,
        'client_edit_form': client_edit_form,
        'event_edit_form': event_edit_form,
        'contract': contract
    })

def edit_services(request, id):
    contract = get_object_or_404(Contract, pk=id)

    # Initial data for all service types
    initial_data = {
        'photography_package': contract.photography_package_id,
        'photography_additional': contract.photography_additional_id,
        'engagement_session': contract.engagement_session_id,
        'prospect_photographer1': contract.prospect_photographer1_id,
        'prospect_photographer2': contract.prospect_photographer2_id,
        'prospect_photographer3': contract.prospect_photographer3_id,
        'videography_package': contract.videography_package_id,
        'videography_additional': contract.videography_additional_id,
        'dj_package': contract.dj_package_id,
        'dj_additional': contract.dj_additional_id,
        'photobooth_package': contract.photobooth_package_id
        # Add additional fields as needed
    }

    form = ContractServicesForm(request.POST or None, instance=contract, initial=initial_data)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'message': 'Services updated successfully'})
            else:
                return redirect('contracts:edit_services', id=id)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'errors': form.errors.as_json()}, status=400)

    context = {
        'contract': contract,
        'form': form,
    }

    return render(request, 'contracts/contract_detail.html', context)


def update_prospect_photographers(request, id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        contract = get_object_or_404(Contract, pk=id)
        form = ContractServicesForm(request.POST, instance=contract)

        if form.is_valid():
            # Update the prospect photographers
            contract.prospect_photographer1 = form.cleaned_data.get('prospect_photographer1')
            contract.prospect_photographer2 = form.cleaned_data.get('prospect_photographer2')
            contract.prospect_photographer3 = form.cleaned_data.get('prospect_photographer3')
            contract.save()

            return JsonResponse({'status': 'success', 'message': 'Prospect photographers updated successfully'})
        else:
            # Return form errors
            return JsonResponse({'status': 'error', 'errors': form.errors.as_json()}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)



@csrf_exempt
@require_http_methods(["POST"])
def save_overtime_entry(request, id):
    try:
        contract = Contract.objects.get(pk=id)
    except Contract.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Contract not found'}, status=404)

    # Parse JSON data from the request body
    try:
        data = json.loads(request.body.decode('utf-8'))
        option_id = data.get('optionId')
        hours = data.get('hours')
        entry_id = data.get('entryId')  # This would be used for editing an existing entry
    except (ValueError, KeyError):
        return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)

    # Validate and save the overtime entry
    try:
        overtime_option = OvertimeOption.objects.get(pk=option_id)
        if entry_id:
            # Update existing entry
            overtime_entry = ContractOvertime.objects.get(pk=entry_id, contract=contract)
            overtime_entry.overtime_option = overtime_option
            overtime_entry.hours = hours
        else:
            # Create new entry
            overtime_entry = ContractOvertime(contract=contract, overtime_option=overtime_option, hours=hours)
        overtime_entry.save()
        return JsonResponse({'status': 'success', 'message': 'Overtime entry saved successfully'})
    except (OvertimeOption.DoesNotExist, ContractOvertime.DoesNotExist, ValueError):
        return JsonResponse({'status': 'error', 'message': 'Invalid overtime option or entry'}, status=400)


def get_overtime_entry(request, entry_id):
    try:
        overtime_entry = ContractOvertime.objects.get(id=entry_id)
        # Serialize your overtime entry details here
        response_data = {
            'id': overtime_entry.id,
            'overtime_option_id': overtime_entry.overtime_option.id,  # Assuming a ForeignKey to an OvertimeOption model
            'hours': float(overtime_entry.hours),
            # Add other fields as necessary
        }
        return JsonResponse(response_data)
    except ContractOvertime.DoesNotExist:
        return JsonResponse({'error': 'Entry not found'}, status=404)


@require_POST
def edit_overtime_entry(request, entry_id):
    # Assume JSON data is sent with 'overtime_option', 'hours', and CSRF token
    data = json.loads(request.body)
    try:
        entry = ContractOvertime.objects.get(pk=entry_id)
        # Update the entry with new values
        entry.overtime_option_id = data['overtime_option']
        entry.hours = data['hours']
        entry.save()

        return JsonResponse({'status': 'success', 'message': 'Entry updated successfully'})
    except ContractOvertime.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Entry not found'}, status=404)
    except Exception as e:
        # Generic error handling, ideally log this exception
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_POST
def delete_overtime_entry(request, entry_id):
    try:
        entry = ContractOvertime.objects.get(pk=entry_id)
        entry.delete()
        return JsonResponse({'status': 'success', 'message': 'Entry deleted successfully'})
    except ContractOvertime.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Entry not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def is_ajax_request(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def get_overtime_entries(request, contract_id):
    service_type = request.GET.get('service_type')
    print(f"Service type received: {service_type}")

    try:
        entries = ContractOvertime.objects.filter(
            contract_id=contract_id,
            overtime_option__service_type__name=service_type
        ).select_related('overtime_option')

        entries_data = [{
            'id': entry.id,
            'overtime_option': entry.overtime_option.role,
            'hours': entry.hours,
            'cost': entry.overtime_option.rate_per_hour * entry.hours
        } for entry in entries]

        print(f"Entries data: {entries_data}")
        return JsonResponse({'status': 'success', 'entries': entries_data})
    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({'status': 'error', 'message': 'Error retrieving overtime entries'}, status=500)

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
    }
    return JsonResponse(data)


def contract_view(request):
    # Prepare your context data
    context = {
        'contract': {
            'event_date': '2023-01-01',
            'primary_contact': 'John Doe',
            'partner_contact': 'Jane Smith',
            'guests_qty': 100,
            'bridal_party_qty': 10,
            'primary_phone': '123-456-7890',
            'primary_email': 'john@example.com',
            'address': '123 Main St',
            'city': 'Anytown',
            'state': 'Anystate',
            'ceremony_site': 'Lovely Venue',
            'reception_site': 'Elegant Hall',
            'package': {'default_text': 'Package details here...'}
            # ... other fields as needed ...
        }
    }

    return render(request, 'contracts/contract_template.html', context)


def generate_contract_pdf(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)

    # Client information
    client_info = {
        'primary_contact': contract.client.primary_contact if contract.client else 'N/A',
        'primary_email': contract.client.primary_email if contract.client else 'N/A',
        'primary_phone': contract.client.primary_phone1 if contract.client else 'N/A',
        'partner_contact': contract.client.partner_contact if contract.client else 'N/A',
        # ... add more fields as needed
    }

    # Package default text
    package_texts = {
        'photography': contract.photography_package.default_text if contract.photography_package else 'N/A',
        'videography': contract.videography_package.default_text if contract.videography_package else 'N/A',
        'dj': contract.dj_package.default_text if contract.dj_package else 'N/A',
        'photobooth': contract.photobooth_package.default_text if contract.photobooth_package else 'N/A',
        # ... add more package types as needed
    }

    context = {
        'contract': contract,
        'client_info': client_info,
        'package_texts': package_texts,
        'logo_path': '/home/egret/django_projects/weddingbook_project/media/logo/Final_Logo.png',  # Direct path
        # ... other context variables
    }

    # Render HTML string with context
    html_string = render_to_string('contracts/contract_template.html', context)

    # Generate PDF from HTML
    pdf = HTML(string=html_string).write_pdf()

    # Send response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="contract_{contract_id}.pdf"'
    return response


def upload_contract_documents(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    if request.method == 'POST':
        form = ContractDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            contract_document = form.save(commit=False)
            contract_document.contract = contract
            contract_document.save()
            return redirect('contracts/contract_detail.html')
    else:
        form = ContractDocumentForm()


def get_package_options(request):
    # Get the service type name from request query parameters
    service_type_name = request.GET.get('service_type', None)

    # Initialize the response data
    response_data = {'packages': []}

    # Check if a service type name is provided and exists
    if service_type_name:
        service_type = ServiceType.objects.filter(name=service_type_name).first()
        if service_type:
            # Filter packages by the found service type
            packages = Package.objects.filter(service_type=service_type, is_active=True).order_by('name')
            # Prepare the package data for the response
            response_data['packages'] = [
                {
                    'id': package.id,
                    'name': package.name,
                    'price': str(package.price),
                    'hours': package.hours
                }
                for package in packages
            ]
        else:
            # Optionally, include an error message if the service type is not found
            response_data['error'] = 'Service type not found'

    return JsonResponse(response_data)



def get_additional_staff_options(request):
    # Get the service type name from request query parameters
    service_type_name = request.GET.get('service_type', None)

    # Initialize the base queryset
    queryset = AdditionalEventStaffOption.objects.filter(is_active=True)

    # If a service type name is provided, filter the queryset by that service type
    if service_type_name:
        service_type = ServiceType.objects.filter(name=service_type_name).first()
        if service_type:
            queryset = queryset.filter(service_type=service_type)

    # Fetch the filtered or unfiltered staff options
    staff_options = queryset.values('id', 'name', 'price', 'hours')

    return JsonResponse({'staff_options': list(staff_options)})

def get_engagement_session_options(request):
    # Query your EngagementSessionOption model for active sessions
    sessions = EngagementSessionOption.objects.filter(is_active=True).values('id', 'name', 'price')
    # Convert the QuerySet to a list to make it JSON serializable
    sessions_list = list(sessions)
    # Wrap the list in an object with a 'sessions' key
    return JsonResponse({'sessions': sessions_list})

def get_prospect_photographers(request):
    contract_id = request.GET.get('contract_id')
    if contract_id:
        try:
            contract = Contract.objects.get(contract_id=contract_id)
            data = {
                'prospect_photographer1': {
                    'id': contract.prospect_photographer1.id,
                    'name': f"{contract.prospect_photographer1.first_name} {contract.prospect_photographer1.last_name}"
                } if contract.prospect_photographer1 else None,
                'prospect_photographer2': {
                    'id': contract.prospect_photographer2.id,
                    'name': f"{contract.prospect_photographer2.first_name} {contract.prospect_photographer2.last_name}"
                } if contract.prospect_photographer2 else None,
                'prospect_photographer3': {
                    'id': contract.prospect_photographer3.id,
                    'name': f"{contract.prospect_photographer3.first_name} {contract.prospect_photographer3.last_name}"
                } if contract.prospect_photographer3 else None,
            }
            return JsonResponse(data)
        except Contract.DoesNotExist:
            return JsonResponse({'error': 'Contract not found'}, status=404)
    return JsonResponse({'error': 'Contract ID is required'}, status=400)


# Django view for the overtime rates API

def get_overtime_options(request):
    service_type_name = request.GET.get('service_type', None)
    options_list = []

    if service_type_name:
        try:
            # Fetch the ServiceType instance based on the name
            service_type = ServiceType.objects.get(name=service_type_name)
            # Filter OvertimeOption instances by the service_type ForeignKey
            options = OvertimeOption.objects.filter(is_active=True, service_type=service_type)
        except ServiceType.DoesNotExist:
            # Handle the case where the ServiceType does not exist
            return JsonResponse({'error': 'ServiceType not found'}, status=404)
    else:
        # Fetch all active OvertimeOption instances if service_type is not specified
        options = OvertimeOption.objects.filter(is_active=True)

    options_list = options.values('id', 'role', 'rate_per_hour', 'service_type__name', 'description')
    return JsonResponse(list(options_list), safe=False)

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


def get_additional_products(request):
    products = AdditionalProduct.objects.all().values(
        'id', 'name', 'price', 'description', 'is_taxable', 'notes'
    )
    return JsonResponse(list(products), safe=False)


def save_products(request, id):
    contract = get_object_or_404(Contract, pk=id)
    product_formset = ContractProductFormset(request.POST or None, instance=contract, prefix='contract_products')

    if request.method == 'POST':
        if product_formset.is_valid():
            product_formset.save()
            return redirect('contracts:contract_detail', id=contract.contract_id)
        else:
            # If the formset is not valid, re-render the page with the formset errors
            context = {
                'contract': contract,
                'product_formset': product_formset,
            }
            return render(request, 'contracts/contract_detail.html', context)
    else:
        # For a GET request, render the page with the formset
        context = {
            'contract': contract,
            'product_formset': product_formset,
        }
        return render(request, 'contracts/contract_detail.html', context)

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


def add_schedule_a(request, contract_id):
    contract = get_object_or_404(Contract, id=contract_id)
    if not hasattr(contract, 'payment_schedule'):
        schedule = create_schedule_a_payments(contract_id)
        contract.status = 'booked'  # Optionally update contract status
        contract.save()
    return redirect(request,'contract_detail', id=contract_id) + '#payments'

def create_schedule_a_payments(contract_id, service_fees=None):
    contract = get_object_or_404(Contract, contract_id=contract_id)
    schedule = PaymentSchedule.objects.create(contract=contract, schedule_type='schedule_a')

    # Get or create the PaymentPurpose instances for down payment and balance
    down_payment_purpose, _ = PaymentPurpose.objects.get_or_create(name='Down Payment')
    balance_payment_purpose, _ = PaymentPurpose.objects.get_or_create(name='Balance Payment')

    # Calculate the down payment (40% of the total contract cost)
    down_payment_amount = contract.calculate_total_cost() * Decimal('0.40')

    # Calculate the balance due date (60 days before the event date)
    balance_due_date = contract.event_date - timedelta(days=60)

    # Create the down payment with a note indicating it's due upon booking

    # For the down payment
    SchedulePayment.objects.create(
        schedule=schedule,
        purpose=down_payment_purpose,
        due_date=now(),  # Use the current date
        amount=down_payment_amount
    )

    # Create the balance payment
    balance_amount = contract.calculate_total_cost() - down_payment_amount
    SchedulePayment.objects.create(
        schedule=schedule,
        purpose=balance_payment_purpose,
        due_date=balance_due_date,
        amount=balance_amount
    )

    # Create payments for each service fee
    if service_fees:
        for fee in service_fees:
            fee_purpose, _ = PaymentPurpose.objects.get_or_create(name=fee['purpose'])
            SchedulePayment.objects.create(
                schedule=schedule,
                purpose=fee_purpose,
                due_date=contract.event_date,  # or another appropriate date
                amount=fee['amount']
            )

    return schedule


def check_payment_schedule_for_contract(contract_id):
    contract = get_object_or_404(Contract, id=contract_id)
    try:
        payment_schedule = contract.payment_schedule
        print(f'Payment schedule ID for contract {contract_id} is {payment_schedule.id}')
    except PaymentSchedule.DoesNotExist:
        print(f'No payment schedule exists for contract {contract_id}')

def create_or_update_schedule(request, contract_id):
    contract = get_object_or_404(Contract, contract_id=contract_id)
    schedule, created = PaymentSchedule.objects.get_or_create(contract=contract)

    if request.method == 'POST':
        schedule_form = PaymentScheduleForm(request.POST, instance=schedule)
        schedule_payment_formset = SchedulePaymentFormSet(request.POST, instance=schedule)

        if schedule_form.is_valid() and schedule_payment_formset.is_valid():
            saved_schedule = schedule_form.save(commit=False)
            saved_schedule.schedule_type = request.POST.get('schedule_type', 'schedule_a')
            saved_schedule.save()
            schedule_payment_formset.save()
            return HttpResponseRedirect(reverse('contracts:contract_detail', kwargs={'id': contract_id}) + '#payments')


    # If it's not a POST request or if the form is not valid, redirect back to the contract detail page
    return redirect(reverse('contracts:contract_detail', kwargs={'id': contract_id}))

def get_custom_schedule(request, contract_id):
    contract = get_object_or_404(Contract, contract_id=contract_id)
    schedule = contract.payment_schedule
    if schedule.schedule_type == 'custom':
        schedule_payments = schedule.schedule_payments.all()
        data = [
            {
                'purpose': payment.purpose.name if payment.purpose else '',
                'due_date': payment.due_date.strftime('%Y-%m-%d'),
                'amount': str(payment.amount),
                'paid': payment.paid
            }
            for payment in schedule_payments
        ]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)



def add_payment(request, schedule_id):
    schedule = get_object_or_404(PaymentSchedule, id=schedule_id)
    contract = schedule.contract  # Get the associated contract

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.contract = contract  # Set the contract for the payment
            payment.save()

            # Update payment status
            update_payment_status(schedule)

            return JsonResponse({'success': True, 'payment_id': payment.id})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        return JsonResponse({'success': False, 'message': 'GET request not allowed'}, status=405)

def update_payment_status(schedule):
    total_payments_made = Payment.objects.filter(contract=schedule.contract).aggregate(Sum('amount'))['amount__sum'] or 0

    for payment in schedule.schedule_payments.all():
        if total_payments_made >= payment.amount:
            payment.paid = True
            total_payments_made -= payment.amount
        else:
            payment.paid = False
        payment.save()


@login_required
def edit_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    schedule = payment.contract.payment_schedule  # Get the associated payment schedule
    original_amount = payment.amount  # Capture the original amount for logging

    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()

            # Log changes if amount is updated
            if original_amount != form.cleaned_data['amount']:
                ChangeLog.objects.create(
                    user=request.user,
                    description=f"Payment updated from {original_amount} to {form.cleaned_data['amount']} for payment ID {payment.id}",
                )

            # Update payment status after editing the payment
            update_payment_status(schedule)

            return JsonResponse({'success': True, 'payment_id': payment.id})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        return JsonResponse({'success': False, 'message': 'GET request not allowed'}, status=405)

@login_required
def delete_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    contract_id = payment.contract.contract_id
    schedule = payment.contract.payment_schedule

    # Log the payment deletion
    ChangeLog.objects.create(
        user=request.user,
        description=f"Deleted payment of {payment.amount} for payment ID {payment.id}"
    )

    payment.delete()

    # Update payment status after deletion
    update_payment_status(schedule)

    return redirect('contracts:contract_detail', id=contract_id)
def booking_detail(request, booking_id):
    # Retrieves the booking instance with the given id or raises a 404 error if it doesn't exist
    booking = get_object_or_404(EventStaffBooking, id=booking_id)

    # Retrieve the associated contract
    contract = booking.contract

    # Fetch all bookings related to the contract
    bookings = EventStaffBooking.objects.filter(contract=contract)

    # Fetch all contract notes related to the contract
    contract_notes = UnifiedCommunication.objects.filter(note_type=UnifiedCommunication.CONTRACT, object_id=contract.contract_id)

    return render(request, 'contracts/event_staff_contract_detail.html', {
        'contract': contract,
        'bookings': bookings,
        'contract_notes': contract_notes
    })

def booking_notes(request, booking_id):
    booking = get_object_or_404(EventStaffBooking, id=booking_id)
    notes = Note.objects.filter(booking=booking)
    return render(request, 'contracts/booking_notes.html', {'object': booking, 'notes': notes})


@login_required
def add_note(request):
    print("Add Note API reached")

    # Check if the request method is POST
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    # Ensure user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'User not authenticated'})

    content = request.POST.get('content')
    booking_id = request.POST.get('booking_id')  # retrieve the booking ID from the request

    # Ensure content and booking_id are present
    if not content or not booking_id:
        return JsonResponse({'success': False, 'error': 'Missing required parameters'})

    try:
        booking = EventStaffBooking.objects.get(pk=booking_id)  # get the booking instance
    except EventStaffBooking.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Booking not found'})

    # Ensure the user is a CustomUser instance before creating the note
    if not isinstance(request.user, CustomUser):
        return JsonResponse({'success': False, 'error': 'Invalid user type'})

    note = Note.objects.create(content=content, booking=booking, created_by=request.user)

    return JsonResponse({
        'success': True,
        'note_id': note.id,
        'author': note.created_by.username,  # Assuming created_by is a ForeignKey to User model
        'timestamp': note.created_at.strftime('%Y-%m-%d %H:%M:%S')  # Format the timestamp as needed
    })


def edit_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    if request.method == 'POST':
        new_content = request.POST.get('content')
        if new_content:
            note.content = new_content
            note.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'New content missing'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def delete_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    if request.method == 'POST':
        note.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@login_required
def open_task_form(request, contract_id, note_id):
    initial_data = {
        'sender': request.user.id,
        'contract': contract_id,
        'note': note_id,
    }
    form = TaskForm(initial=initial_data)
    return render(request, 'task_form.html', {'form': form})


@login_required
@require_POST
def create_task(request):
    print("Handling POST request to create a task.")  # Confirm this gets printed
    form = TaskForm(request.POST)
    if form.is_valid():
        print("Form is valid, processing task.")  # Confirm form validity
        task = form.save(commit=False)
        task.sender = request.user

        print("Task created, not yet saved to DB. Assigned to: ", task.assigned_to)  # Check assigned_to

        task.save()

        if hasattr(task.assigned_to, 'email'):
            print("Assigned to email:", task.assigned_to.email)  # Debug print
        else:
            print("No email attribute found for assigned user.")



        # Send task assignment email
        send_task_assignment_email(request, task)

        tasks = Task.objects.filter(assigned_to=request.user, is_completed=False)
        task_list_html = render_to_string('contracts/task_list_snippet.html', {'tasks': tasks}, request=request)
        return JsonResponse({'success': True, 'task_id': task.id, 'task_list_html': task_list_html})
    else:
        return JsonResponse({'success': False, 'errors': form.errors.as_json()})

def send_task_assignment_email(request, task):
    context = {
        'user': task.assigned_to,
        'task': task,
        'domain': get_current_site(request).domain,
    }
    subject = 'New Task Assigned'
    message = render_to_string('communication/task_assignment_email.html', context, request=request)
    send_mail(
        subject,
        message,
        'testmydjango420@gmail.com',  # Your sending email
        [task.assigned_to.email],
        fail_silently=False,
    )


@require_http_methods(["POST"])  # Use POST for operations that change data
def clear_booking(request, booking_id):
    booking = get_object_or_404(EventStaffBooking, id=booking_id)

    # Update the staff availability for the date if necessary
    if booking.staff:
        availability, created = Availability.objects.get_or_create(
            staff=booking.staff,
            date=booking.contract.event_date
        )
        availability.available = True
        availability.save()

    # Clear the associated role in the contract before deleting the booking
    role_field = SERVICE_ROLE_MAPPING.get(booking.role, None)
    if role_field and hasattr(booking.contract, role_field):
        setattr(booking.contract, role_field, None)
        booking.contract.save()

    # Record the username before deleting for the success message
    staff_name = booking.staff.username if booking.staff else "Unknown Staff"

    # Delete the booking
    booking.delete()

    messages.success(request, f'Booking for {staff_name} has been cleared!')
    return redirect(f'{reverse("contracts:search")}?tab=bookings')


def booking_list(request):
    bookings = EventStaffBooking.objects.all()

    # Fetch the 'q' parameter for quick search
    search_query = request.GET.get('q')
    if search_query:
        bookings = bookings.filter(
            Q(staff__username__icontains=search_query) |
            Q(staff__first_name__icontains=search_query) |
            Q(staff__last_name__icontains=search_query)
        )

    # Fetch the 'event_date' parameter from the request if provided
    date_filter = request.GET.get('event_date')
    if date_filter:
        bookings = bookings.filter(contract__event_date=date_filter)

    # Fetch the 'role_filter' parameter from the request if provided
    role_filter = request.GET.get('role_filter')
    if role_filter:
        bookings = bookings.filter(role=role_filter)

    # Fetch the 'status_filter' parameter from the request if provided
    status_filter = request.GET.get('status_filter')
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    # Sorting logic
    sort_by = request.GET.get('sort_by', '')  # No default sort_by
    order = request.GET.get('order', 'asc')  # Default to ascending if not provided

    if sort_by:
        # Modify the sort_by parameter to prefix with 'contract__' for fields in Contract
        if sort_by in ['event_date', '...other Contract fields...']:
            sort_by = 'contract__' + sort_by

        # The '-' prefix indicates descending order in Django querysets
        order_prefix = '-' if order == 'desc' else ''
        bookings = bookings.order_by(order_prefix + sort_by)
    elif status_filter:
        # If no specific sorting is selected, sort by status when filtering by status
        bookings = bookings.order_by('status')

    return render(request, 'contracts/booking_list.html', {'bookings': bookings})


def get_available_staff(request):
    event_date_str = request.GET.get('event_date')
    service_type = request.GET.get('service_type')
    print("Service Type:", service_type)  # Debug print

    try:
        event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date() if event_date_str else None
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    if not event_date:
        return JsonResponse({'error': 'Event date is required'}, status=400)

    available_staff = Availability.get_available_staff_for_date(event_date).distinct()
    combined_name = Concat(F('first_name'), Value(' '), F('last_name'), output_field=CharField())

    data = {
        'photographers': list(available_staff.filter(
            Q(role__name='PHOTOGRAPHER') | Q(additional_roles__name='PHOTOGRAPHER')
        ).annotate(name=combined_name).values('id', 'name')),
        'videographers': list(available_staff.filter(
            Q(role__name='VIDEOGRAPHER') | Q(additional_roles__name='VIDEOGRAPHER')
        ).annotate(name=combined_name).values('id', 'name')),
        'djs': list(available_staff.filter(
            Q(role__name='DJ') | Q(additional_roles__name='DJ')
        ).annotate(name=combined_name).values('id', 'name')),
        'photobooth_operators': list(available_staff.filter(
            Q(role__name='PHOTOBOOTH_OPERATOR') | Q(additional_roles__name='PHOTOBOOTH_OPERATOR')
        ).annotate(name=combined_name).values('id', 'name')),
        # Add any other event staff roles as needed...
    }

    if service_type:
        roles = Role.objects.filter(service_type__name=service_type).values_list('name', flat=True)
        staff_data = list(available_staff.filter(
            Q(role__name__in=roles) | Q(additional_roles__name__in=roles)
        ).annotate(name=combined_name).values('id', 'name'))
        data[f'{service_type.lower()}_staff'] = staff_data

    return JsonResponse(data)


def manage_staff_assignments(request, id):
    contract = get_object_or_404(Contract, contract_id=id)
    form = EventStaffBookingForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            booking_id = form.cleaned_data.get('booking_id')
            role = form.cleaned_data.get('role')
            staff = form.cleaned_data.get('staff')
            status = form.cleaned_data.get('status', 'APPROVED')  # Default to 'APPROVED' if not specified
            confirmed = form.cleaned_data.get('confirmed', True)  # Default to True if not specified
            hours_booked = form.cleaned_data.get('hours_booked', 0)  # Default to 0 if not specified

            if booking_id:
                # Update an existing booking
                booking = EventStaffBooking.objects.get(id=booking_id)
            else:
                # Prevent duplicate roles in the same contract
                if EventStaffBooking.objects.filter(contract=contract, role=role).exclude(id=booking_id).exists():
                    return JsonResponse(
                        {'success': False, 'message': 'A booking for this role already exists in this contract.'},
                        status=400)
                booking = EventStaffBooking(contract=contract)  # Ensure the contract is assigned here

            booking.role = role
            booking.staff = staff
            booking.status = status
            booking.confirmed = confirmed
            booking.hours_booked = hours_booked  # Set hours booked
            booking.save()

            # If booking is a prospect role, update the corresponding prospect field in the contract
            if 'PROSPECT' in role:
                prospect_field = f'prospect_photographer{role[-1]}'
                setattr(contract, prospect_field, booking.staff)
                contract.save()

            return JsonResponse({
                'success': True,
                'message': 'Staff booking saved successfully',
                'role': booking.role,
                'staff_name': booking.staff.get_full_name() if booking.staff else 'None',
                'hours_booked': booking.hours_booked
            })

        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    # GET request handling for initial form display
    return render(request, 'contracts/manage_staff.html', {'contract': contract, 'form': form})

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



