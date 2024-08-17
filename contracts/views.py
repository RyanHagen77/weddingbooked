# contracts/views.py
from django.shortcuts import render, get_object_or_404, redirect
from users.models import CustomUser  # Import CustomUser
from django.db.models import Q, F, Value, CharField, Sum
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_GET
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.urls import reverse
from users.models import Role
from django.conf import settings
from communication.models import UnifiedCommunication, Task
from communication.views import send_task_assignment_email, send_contract_and_rider_email_to_client, send_contract_message_email
from .forms import (ContractSearchForm, ClientForm, NewContractForm, ContractForm, ContractInfoEditForm,
                    ContractClientEditForm, ContractAgreementForm,
                    ContractEventEditForm, ContractServicesForm, ContractDocumentForm,
                    EventStaffBookingForm, ContractProductFormset, PaymentForm, PaymentScheduleForm,
                    SchedulePaymentFormSet, ServiceFeeFormSet, ServiceFeeForm, WeddingDayGuideForm)
from communication.forms import CommunicationForm, BookingCommunicationForm, TaskForm  # Importing from the communication app
from .models import (Client, Contract, ServiceType, Availability, Payment, Package,
                     AdditionalEventStaffOption, EngagementSessionOption, Discount, EventStaffBooking, ContractOvertime, AdditionalProduct,
                     OvertimeOption, PaymentPurpose, PaymentSchedule, SchedulePayment,
                     TaxRate, ContractDocument, ChangeLog, ServiceFee, ContractAgreement, RiderAgreement, WeddingDayGuide)
from django.db import transaction
from django.core.mail import send_mail
from django.db.models.functions import Concat
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, login
from django.contrib.sites.shortcuts import get_current_site
from django.core.files.storage import default_storage
from django.core.mail import EmailMessage
from django.core.files.base import ContentFile
from .serializers import ContractSerializer, WeddingDayGuideSerializer
from datetime import datetime, timedelta
import json
import os
from django.utils.timezone import now
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from weasyprint import HTML
import logging
from django.contrib.auth.forms import PasswordResetForm
from django.http import HttpRequest, HttpResponseRedirect
from django.contrib.auth import logout
from .constants import SERVICE_ROLE_MAPPING  # Adjust the import path as needed
from django.template.defaultfilters import linebreaks
from collections import defaultdict

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
    form = ContractSearchForm(request.GET)
    contracts = Contract.objects.all().order_by('-event_date')

    order = request.GET.get('order', 'desc')
    if order == 'asc':
        contracts = contracts.order_by('event_date')
    else:
        contracts = contracts.order_by('-event_date')

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
            contracts = contracts.filter(custom_contract_number__icontains=form.cleaned_data['contract_number'])
        if form.cleaned_data.get('primary_contact'):
            contracts = contracts.filter(client__primary_contact__icontains=form.cleaned_data['primary_contact'])
        if form.cleaned_data.get('status'):
            contracts = contracts.filter(status=form.cleaned_data['status'])
        if form.cleaned_data.get('csr'):
            contracts = contracts.filter(csr=form.cleaned_data['csr'])

        service_type = form.cleaned_data.get('service_type')
        if service_type:
            staff_roles = {
                "PHOTOGRAPHER": ['PHOTOGRAPHER1', 'PHOTOGRAPHER2'],
                "VIDEOGRAPHER": ['VIDEOGRAPHER1', 'VIDEOGRAPHER2'],
                "DJ": ['DJ1', 'DJ2'],
                "PHOTOBOOTH": ['PHOTOBOOTH_OP1', 'PHOTOBOOTH_OP2']
            }
            roles = staff_roles.get(service_type, [])
            service_contracts = EventStaffBooking.objects.filter(role__in=roles).values_list('contract_id', flat=True)
            contracts = contracts.filter(contract_id__in=service_contracts)

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
                role__in=['PHOTOBOOTH_OP1', 'PHOTOBOOTH_OP2']
            ).values_list('contract_id', flat=True)
            contracts = contracts.filter(contract_id__in=photobooth_operator_contracts)

    query = request.GET.get('q')
    if query:
        contracts = contracts.filter(
            Q(custom_contract_number__icontains=query) |
            Q(client__primary_contact__icontains=query) |
            Q(client__partner_contact__icontains=query) |
            Q(old_contract_number__icontains=query) |
            Q(client__primary_email__icontains=query) |
            Q(client__primary_phone1__icontains=query)
        )

    return render(request, 'contracts/contract_search.html', {
        'form': form,
        'contracts': contracts,
    })

@login_required
def booking_search(request):
    booking_search_query = request.GET.get('booking_q')
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

    if request.GET.get('event_date_start') and request.GET.get('event_date_end'):
        bookings = bookings.filter(contract__event_date__range=[
            request.GET.get('event_date_start'), request.GET.get('event_date_end')
        ])

    if request.GET.get('service_type'):
        service_type = request.GET.get('service_type')
        if service_type == "PHOTOGRAPHER":
            roles = ['PHOTOGRAPHER1', 'PHOTOGRAPHER2']
        elif service_type == "VIDEOGRAPHER":
            roles = ['VIDEOGRAPHER1', 'VIDEOGRAPHER2']
        elif service_type == "DJ":
            roles = ['DJ1', 'DJ2']
        elif service_type == "PHOTOBOOTH":
            roles = ['PHOTOBOOTH_OP1', 'PHOTOBOOTH_OP2']
        else:
            roles = []
        bookings = bookings.filter(role__in=roles)

    if request.GET.get('role_filter'):
        bookings = bookings.filter(role=request.GET.get('role_filter'))

    if request.GET.get('status_filter'):
        status_filter = request.GET.get('status_filter').lower() == 'true'
        bookings = bookings.filter(confirmed=status_filter)

    if request.GET.get('sort_by') and request.GET.get('order'):
        sort_by = request.GET.get('sort_by')
        order = request.GET.get('order')
        if order == 'asc':
            bookings = bookings.order_by(sort_by)
        else:
            bookings = bookings.order_by('-' + sort_by)

    return render(request, 'contracts/booking_search.html', {
        'bookings': bookings,
    })


@login_required
def new_contract(request):
    contract_form = NewContractForm(request.POST or None)
    client_form = ClientForm(request.POST or None)

    if request.method == 'POST':
        if client_form.is_valid() and contract_form.is_valid():  # Ensure both forms are validated
            with transaction.atomic():
                primary_email = client_form.cleaned_data.get('primary_email')
                User = get_user_model()

                try:
                    # Check if the user already exists
                    user = User.objects.get(email=primary_email)
                    # Check if the client associated with the user exists
                    client = Client.objects.get(user=user)
                except User.DoesNotExist:
                    # If the user does not exist, create a new user
                    user = User.objects.create(username=primary_email, email=primary_email, user_type='client')
                    client = client_form.save(commit=False)
                    client.user = user
                    client.save()
                except Client.DoesNotExist:
                    # If the user exists but the client does not, create a new client
                    client = client_form.save(commit=False)
                    client.user = user
                    client.save()

                # Create and save the contract
                contract = contract_form.save(commit=False)
                contract.client = client
                contract.save()

                # Automatically create a WeddingDayGuide for the contract
                WeddingDayGuide.objects.create(
                    contract=contract,
                )

                create_schedule_a_payments(contract.contract_id)
                contract.status = 'pipeline'
                contract.save()

                return JsonResponse({'redirect_url': reverse('contracts:contract_detail', kwargs={'id': contract.contract_id})})

        else:
            # Combine errors from both forms and return them in a JSON response
            errors = {**client_form.errors, **contract_form.errors}
            return JsonResponse({'errors': errors}, status=400)

    return render(request, 'contracts/contract_new.html', {
        'contract_form': contract_form,
        'client_form': client_form,
    })


def send_password_reset_email(user_email):
    print(f"Starting to send password reset email to: {user_email}")
    form = PasswordResetForm({'email': user_email})
    if form.is_valid():
        request = HttpRequest()
        request.META['SERVER_NAME'] = '127.0.0.1'
        request.META['SERVER_PORT'] = '8000'


        try:
            form.save(
                request=request,
                use_https=True,
                from_email='enetadmin@enet2.com',
                email_template_name='registration/password_reset_email.html'
            )
            print("Password reset email sent successfully.")
        except Exception as e:
            print(f"Failed to send password reset email due to: {e}")
    else:
        print("PasswordResetForm is invalid. Errors:", form.errors)

def custom_login(request):
    User = get_user_model()  # Use the custom user model

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return render(request, 'contracts/client_portal_login.html', {'next': request.POST.get('next')})
        except User.MultipleObjectsReturned:
            users = User.objects.filter(email=email)
            user = None
            for u in users:
                if u.check_password(password):
                    user = u
                    break
            if user is None:
                messages.error(request, "Invalid email or password.")
                return render(request, 'contracts/client_portal_login.html', {'next': request.POST.get('next')})

        if user is not None and user.check_password(password):
            login(request, user)
            next_url = request.POST.get('next')
            print(f"Next URL after login: {next_url}")  # Debugging
            if next_url:
                return redirect(next_url)
            else:
                contract = Contract.objects.filter(client=user.client).first()
                if contract:
                    return redirect('contracts:client_portal', contract_id=contract.contract_id)
                else:
                    messages.error(request, "No associated contract found.")
                    return render(request, 'contracts/client_portal_login.html', {'next': next_url})
        else:
            messages.error(request, "Invalid email or password.")

    next_url = request.GET.get('next', '')
    print(f"Next URL on GET: {next_url}")  # Debugging
    return render(request, 'contracts/client_portal_login.html', {'next': next_url})

def custom_logout(request):
    logout(request)
    response = redirect('contracts:client_portal_login')  # Redirect to the login page or any other page
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        try:
            client = Client.objects.get(user=user)
            contract = Contract.objects.get(client=client)
            token['contract_id'] = contract.contract_id
        except (Client.DoesNotExist, Contract.DoesNotExist):
            token['contract_id'] = None
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        data['contract_id'] = refresh['contract_id']
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

@login_required
def client_portal(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)

    # Fetch 'contract' type notes related to this contract
    contract_notes = UnifiedCommunication.objects.filter(
        contract=contract,
        note_type=UnifiedCommunication.CONTRACT
    ).order_by('-created_at')

    # Fetch documents visible to the client
    client_documents = contract.documents.filter(is_client_visible=True)

    # Fetch contract agreements and rider agreements
    contract_agreements = ContractAgreement.objects.filter(contract=contract).order_by('-version_number')
    rider_agreements = RiderAgreement.objects.filter(contract=contract)

    if request.method == 'POST':
        form = CommunicationForm(request.POST)
        if form.is_valid():
            message = UnifiedCommunication.objects.create(
                content=form.cleaned_data['message'],
                note_type=UnifiedCommunication.CONTRACT,
                created_by=request.user,
                contract=contract
            )

            # Send an email notification to the coordinator
            if contract.coordinator:
                send_contract_message_email(request, message, contract)

            return redirect('contracts:client_portal', contract_id=contract.contract_id)

    form = CommunicationForm()

    context = {
        'contract': contract,
        'contract_notes': contract_notes,
        'client_documents': client_documents,
        'contract_agreements': contract_agreements,
        'rider_agreements': rider_agreements,
        'form': form,
    }

    return render(request, 'contracts/client_portal.html', context)



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
            'enetadmin@enet2.com',
            [client_user.email],
            fail_silently=False,
        )
        print("Email sent to client:", client_user.email)
    else:
        print("Client does not have a valid email.")



@login_required
def contract_detail(request, id):
    contract = get_object_or_404(Contract, pk=id)

    # Check if the user is in the "Office Staff" group
    is_office_staff = request.user.groups.filter(name='Office Staff').exists()

    form = ContractForm(request.POST or None, instance=contract)
    client = contract.client  # Assuming there's a ForeignKey relationship to the Client model
    booking_form = EventStaffBookingForm()
    schedule, created = PaymentSchedule.objects.get_or_create(contract=contract, defaults={'schedule_type': 'schedule_a'})
    schedule_id = schedule.id
    schedule_form = PaymentScheduleForm(instance=schedule)
    schedule_payment_formset = SchedulePaymentFormSet(instance=schedule)
    service_fee_formset = ServiceFeeForm(instance=contract)
    payment_purposes = PaymentPurpose.objects.all()
    discounts = contract.other_discounts.all()
    service_types = ServiceType.objects.all()
    changelogs = ChangeLog.objects.filter(contract=contract).order_by('-timestamp')

    if request.method == 'POST':
        contract_info_edit_form = ContractInfoEditForm(request.POST, instance=contract, prefix='contract_info')
        client_edit_form = ContractClientEditForm(request.POST, instance=client, prefix='client_info')
        event_edit_form = ContractEventEditForm(request.POST, instance=contract, prefix='event_details')
    else:
        contract_info_edit_form = ContractInfoEditForm(instance=contract, prefix='contract_info')
        client_edit_form = ContractClientEditForm(instance=client, prefix='client_info')
        event_edit_form = ContractEventEditForm(instance=contract, prefix='event_details')

    if request.method == 'POST':
        if client_edit_form.is_valid():
            client_edit_form.save()
            return redirect('contracts:contract_detail', id=id)

    communication_form = CommunicationForm()
    task_form = TaskForm()
    tasks = Task.objects.filter(contract=contract)

    documents = contract.documents.all()
    for document in documents:
        document.badge_class = 'badge-success' if document.is_client_visible else 'badge-secondary'
        document.badge_label = 'Visible to Client' if document.is_client_visible else 'Internal Use'

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
            new_message = UnifiedCommunication.objects.create(
                content=communication_form.cleaned_data['message'],
                note_type=communication_form.cleaned_data['message_type'],
                created_by=request.user,
                contract=contract,
            )
            if request.user.is_coordinator:
                send_email_to_client(request, new_message, contract)
            return redirect('contracts:contract_detail', id=contract.contract_id)
    else:
        communication_form = CommunicationForm()

    photography_service_type = ServiceType.objects.get(name='Photography')
    videography_service_type = ServiceType.objects.get(name='Videography')
    dj_service_type = ServiceType.objects.get(name='Dj')
    photography_packages = Package.objects.filter(service_type__name='Photography').order_by('name')
    videography_packages = Package.objects.filter(service_type__name='Videography').order_by('name')
    products_for_contract = contract.contract_products.all()
    payments_made = Payment.objects.filter(contract=contract)
    additional_photography_options = AdditionalEventStaffOption.objects.filter(service_type=photography_service_type, is_active=True)
    additional_videography_options = AdditionalEventStaffOption.objects.filter(service_type=videography_service_type, is_active=True)
    additional_dj_options = AdditionalEventStaffOption.objects.filter(service_type=dj_service_type, is_active=True)
    overtime_options = OvertimeOption.objects.all().values('id', 'role', 'rate_per_hour')
    engagement_session_options = EngagementSessionOption.objects.filter(is_active=True)

    total_overtime_cost = sum(
        overtime.hours * overtime.overtime_option.rate_per_hour
        for overtime in contract.overtimes.all()
    )

    photography_cost = contract.calculate_photography_cost()
    videography_cost = contract.calculate_videography_cost()
    dj_cost = contract.calculate_dj_cost()
    photobooth_cost = contract.calculate_photobooth_cost()

    products_formset = ContractProductFormset(instance=contract, prefix='contract_products')
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
    if tax_rate_object:
        tax_rate = tax_rate_object.tax_rate
    else:
        tax_rate = Decimal('0.00')

    tax_amount = contract.calculate_tax()
    total_payments_received = sum(payment.amount for payment in contract.payments.all())

    if request.method == 'POST':
        service_fee_formset = ServiceFeeFormSet(request.POST, instance=contract)
        if service_fee_formset.is_valid():
            service_fee_formset.save()
            create_schedule_a_payments(contract.id)  # Recalculate payments
            return redirect('contracts:contract_detail', id=contract.contract_id)
    else:
        service_fee_formset = ServiceFeeFormSet(instance=contract)

    payment_form = PaymentForm()
    if request.method == 'POST' and 'submit_payment' in request.POST:
        payment_form = PaymentForm(request.POST)
        if payment_form.is_valid():
            new_payment = payment_form.save(commit=False)
            new_payment.contract = contract
            new_payment.save()
            create_schedule_a_payments(contract.contract_id)  # Recalculate payments
            return redirect('contracts:contract_detail', id=contract.contract_id)
        else:
            print("Payment form errors:", payment_form.errors)

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
        'booking_form': booking_form,
        'documents': documents,
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
        'payment_purposes': payment_purposes,
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
        'service_fee_formset': service_fee_formset,
        'discounts': discounts,
        'service_types': service_types,
        'changelogs': changelogs,
        'is_office_staff': is_office_staff,  # Pass to the template
    }

    return render(request, 'contracts/contract_detail.html', context)


@login_required
def edit_contract(request, id):
    contract = get_object_or_404(Contract, pk=id)
    original_status = contract.status
    client = contract.client

    contract_info_edit_form = ContractInfoEditForm(request.POST or None, instance=contract, prefix='contract_info')
    client_edit_form = ContractClientEditForm(request.POST or None, instance=client, prefix='client_info')
    event_edit_form = ContractEventEditForm(request.POST or None, instance=contract, prefix='event_details')

    response_message = {'status': 'error', 'message': 'Invalid form submission.'}

    if request.method == 'POST':
        if 'contract_info' in request.POST:
            if contract_info_edit_form.is_valid():
                contract = contract_info_edit_form.save()

                if original_status != contract.status:
                    ChangeLog.objects.create(
                        user=request.user,
                        description=f"Contract status changed from {original_status} to {contract.status}",
                        contract=contract
                    )
                    if contract.status == 'forecast' and hasattr(client,
                                                                 'user') and not client.user.has_usable_password():
                        send_password_reset_email(client.user.email)

                # Check if the user is allowed to mark the contract as "dead"
                if contract.status == 'dead':
                    allowed_user = CustomUser.objects.get(username='MikeG')
                    if request.user == allowed_user:
                        EventStaffBooking.objects.filter(contract=contract).delete()
                    else:
                        contract.status = original_status  # Revert status change
                        contract.save()
                        response_message = {'status': 'unauthorized',
                                            'message': 'You do not have permission to mark this contract as dead.'}
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse(response_message)
                        else:
                            return redirect(
                                f'{request.path}?unauthorized=true&message=You do not have permission to mark this contract as dead.')

                response_message = {'status': 'success', 'message': 'Contract info updated successfully.'}
            else:
                response_message = {'status': 'error', 'message': contract_info_edit_form.errors}

        elif 'client_info' in request.POST:
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

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(response_message)
        else:
            return redirect('contracts:contract_detail', id=id)

    return render(request, 'contracts/manage_staff.html', {
        'contract_info_edit_form': contract_info_edit_form,
        'client_edit_form': client_edit_form,
        'event_edit_form': event_edit_form,
        'contract': contract
    })


@login_required
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
                url = reverse('contracts:contract_detail', args=[id]) + '#services'
                return redirect(url)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'errors': form.errors.as_json()}, status=400)

    context = {
        'contract': contract,
        'form': form,
    }

    return render(request, 'contracts/contract_detail.html', context)



@login_required
@csrf_exempt
@require_http_methods(["POST"])
def save_overtime_entry(request, id):
    try:
        contract = Contract.objects.get(pk=id)
    except Contract.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Contract not found'}, status=404)

    try:
        data = json.loads(request.body.decode('utf-8'))
        option_id = data.get('optionId')
        hours = data.get('hours')
        entry_id = data.get('entryId')
    except (ValueError, KeyError):
        return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)

    try:
        overtime_option = OvertimeOption.objects.get(pk=option_id)
        if entry_id:
            overtime_entry = ContractOvertime.objects.get(pk=entry_id, contract=contract)
            overtime_entry.overtime_option = overtime_option
            overtime_entry.hours = hours
        else:
            overtime_entry = ContractOvertime(contract=contract, overtime_option=overtime_option, hours=hours)
        overtime_entry.save()
        return JsonResponse({'status': 'success', 'message': 'Overtime entry saved successfully'})
    except (OvertimeOption.DoesNotExist, ContractOvertime.DoesNotExist, ValueError) as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def get_overtime_entry(request, entry_id):
    try:
        overtime_entry = ContractOvertime.objects.get(id=entry_id)
        response_data = {
            'id': overtime_entry.id,
            'overtime_option_id': overtime_entry.overtime_option.id,
            'hours': float(overtime_entry.hours),
        }
        return JsonResponse(response_data)
    except ContractOvertime.DoesNotExist:
        return JsonResponse({'error': 'Entry not found'}, status=404)

@require_POST
def edit_overtime_entry(request, entry_id):
    data = json.loads(request.body)
    try:
        entry = ContractOvertime.objects.get(pk=entry_id)
        entry.overtime_option_id = data['overtime_option']
        entry.hours = data['hours']
        entry.save()

        return JsonResponse({'status': 'success', 'message': 'Entry updated successfully'})
    except ContractOvertime.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Entry not found'}, status=404)
    except Exception as e:
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

def get_overtime_entries(request, contract_id):
    service_type = request.GET.get('service_type')
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

        return JsonResponse({'status': 'success', 'entries': entries_data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': 'Error retrieving overtime entries'}, status=500)

def get_overtime_options(request):
    service_type_name = request.GET.get('service_type', None)
    options_list = []

    if service_type_name:
        try:
            service_type = ServiceType.objects.get(name=service_type_name)
            options = OvertimeOption.objects.filter(is_active=True, service_type=service_type)
        except ServiceType.DoesNotExist:
            return JsonResponse({'error': 'ServiceType not found'}, status=404)
    else:
        options = OvertimeOption.objects.filter(is_active=True)

    options_list = options.values('id', 'role', 'rate_per_hour', 'service_type__name', 'description')
    return JsonResponse(list(options_list), safe=False)

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

@require_GET
def client_documents(request, contract_id):
    try:
        contract = Contract.objects.get(contract_id=contract_id)
        documents = contract.documents.filter(is_client_visible=True)
        document_list = [
            {
                'id': doc.id,
                'url': doc.document.url,
                'name': os.path.basename(doc.document.name),  # Extract the file name
                'badge_class': 'badge-success' if doc.is_client_visible else 'badge-secondary',
                'badge_label': 'Visible to Client' if doc.is_client_visible else 'Internal Use'
            } for doc in documents
        ]
        return JsonResponse(document_list, safe=False)
    except Contract.DoesNotExist:
        return JsonResponse({'error': 'Contract not found'}, status=404)

@login_required
def generate_contract_pdf(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)

    # Constructing full URL for the logo and company signature
    domain = '127.0.0.1:8000'
    logo_url = f'http://{domain}{settings.MEDIA_URL}logo/Final_Logo.png'
    company_signature_url = f'http://{domain}{settings.MEDIA_URL}signatures/company_signature.png'

    # Package texts
    package_texts = {
        'photography': linebreaks(contract.photography_package.default_text) if contract.photography_package else None,
        'videography': linebreaks(contract.videography_package.default_text) if contract.videography_package else None,
        'dj': linebreaks(contract.dj_package.default_text) if contract.dj_package else None,
        'photobooth': linebreaks(contract.photobooth_package.default_text) if contract.photobooth_package else None,
    }

    # Additional services text processing
    additional_services_texts = {
        'photography_additional': linebreaks(
            contract.photography_additional.default_text) if contract.photography_additional else None,
        'videography_additional': linebreaks(
            contract.videography_additional.default_text) if contract.videography_additional else None,
        'dj_additional': linebreaks(contract.dj_additional.default_text) if contract.dj_additional else None,
        'photobooth_additional': linebreaks(
            contract.photobooth_additional.default_text) if contract.photobooth_additional else None,
    }

    # Additional staff
    additional_staff = defaultdict(list)
    for staff_option in [contract.photography_additional, contract.videography_additional, contract.dj_additional,
                         contract.photobooth_additional]:
        if staff_option:
            additional_staff[staff_option.service_type.name].append({
                'name': staff_option.name,
                'service_type': staff_option.service_type.name,
                'price': staff_option.price,
                'hours': staff_option.hours,
                'default_text': staff_option.default_text,
            })

    # Initialize an empty dictionary to store overtime options grouped by service type
    overtime_options_by_service_type = {}

    # Initialize total overtime cost
    total_overtime_cost = 0

    # Iterate over each overtime option
    for contract_overtime in contract.overtimes.all():
        service_type = contract_overtime.overtime_option.service_type.name
        if service_type in overtime_options_by_service_type:
            overtime_options_by_service_type[service_type].append({
                'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role,
                                               contract_overtime.overtime_option.role),
                'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                'hours': contract_overtime.hours,
            })
        else:
            overtime_options_by_service_type[service_type] = [{
                'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role,
                                               contract_overtime.overtime_option.role),
                'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                'hours': contract_overtime.hours,
            }]

    # Calculate total cost for each overtime option
    for service_type, options in overtime_options_by_service_type.items():
        for option in options:
            option['total_cost'] = option['hours'] * option['rate_per_hour']
            total_overtime_cost += option['total_cost']

    total_service_cost = contract.calculate_total_service_cost()
    total_discount = contract.calculate_discount()
    total_cost_after_discounts = contract.calculate_total_service_cost_after_discounts()

    # Get the first contract agreement for the contract
    first_agreement = ContractAgreement.objects.filter(contract=contract).order_by('version_number').first()

    # Get the latest contract agreement for the contract
    latest_agreement = ContractAgreement.objects.filter(contract=contract).order_by('-version_number').first()

    # Get the rider agreements for the contract
    rider_agreements = RiderAgreement.objects.filter(contract=contract)

    context = {
        'contract': contract,
        'client_info': {
            'primary_contact': contract.client.primary_contact if contract.client else 'N/A',
            'primary_email': contract.client.primary_email if contract.client else 'N/A',
            'primary_phone': contract.client.primary_phone1 if contract.client else 'N/A',
            'partner_contact': contract.client.partner_contact if contract.client else 'N/A',
        },
        'logo_url': logo_url,
        'company_signature_url': company_signature_url,
        'package_texts': package_texts,
        'additional_staff': additional_staff,
        'total_overtime_cost': total_overtime_cost,
        'overtime_options_by_service_type': overtime_options_by_service_type,
        'ROLE_DISPLAY_NAMES': ROLE_DISPLAY_NAMES,
        'total_service_cost': total_service_cost,
        'total_discount': total_discount,
        'total_cost_after_discounts': total_cost_after_discounts,
        'rider_agreements': rider_agreements,
        'first_agreement': first_agreement,  # Add first agreement to context
        'latest_agreement': latest_agreement,  # Add latest agreement to context
    }

    # Render HTML to string
    html_string = render_to_string('contracts/contract_template.html', context)

    # Generate PDF from HTML
    pdf = HTML(string=html_string).write_pdf()

    # Send response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="contract_{contract_id}.pdf"'
    return response


@login_required
def contract_agreement(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    if request.method == 'POST':
        rider_type = request.POST.get('rider_type')
        if rider_type:
            # Handle sending a specific rider email
            send_contract_and_rider_email_to_client(request, contract, rider_type=rider_type)
            return JsonResponse({'status': 'success', 'message': f'{rider_type.replace("_", " ").capitalize()} agreement email sent successfully.'})
        elif 'contract_agreement' in request.POST:
            # Handle sending just the contract agreement email
            send_contract_and_rider_email_to_client(request, contract, only_contract=True)
            return JsonResponse({'status': 'success', 'message': 'Contract agreement email sent successfully.'})
        else:
            # Handle sending the combined contract and rider agreements email
            send_contract_and_rider_email_to_client(request, contract)
            return JsonResponse({'status': 'success', 'message': 'Contract and rider agreements email sent successfully.'})

    form = ContractAgreementForm()

    # Initialize an empty dictionary to store overtime options grouped by service type
    overtime_options_by_service_type = {}

    # Initialize total overtime cost
    total_overtime_cost = 0

    # Iterate over each overtime option
    for contract_overtime in contract.overtimes.all():
        # Get the service type of the overtime option
        service_type = contract_overtime.overtime_option.service_type.name

        # Check if the service type already exists in the dictionary
        if service_type in overtime_options_by_service_type:
            # If the service type exists, append the overtime option to its list
            overtime_options_by_service_type[service_type].append({
                'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role, contract_overtime.overtime_option.role),
                'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                'hours': contract_overtime.hours,
            })
        else:
            # If the service type does not exist, create a new list with the overtime option
            overtime_options_by_service_type[service_type] = [{
                'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role, contract_overtime.overtime_option.role),
                'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                'hours': contract_overtime.hours,
            }]

    # Calculate total cost for each overtime option
    for service_type, options in overtime_options_by_service_type.items():
        for option in options:
            option['total_cost'] = option['hours'] * option['rate_per_hour']
            total_overtime_cost += option['total_cost']

    context = {
        'contract': contract,
        'logo_url': logo_url,
        'form': form,
        'package_texts': {
            'photography': linebreaks(contract.photography_package.default_text) if contract.photography_package else '',
            'videography': linebreaks(contract.videography_package.default_text) if contract.videography_package else '',
            'dj': linebreaks(contract.dj_package.default_text) if contract.dj_package else '',
            'photobooth': linebreaks(contract.photobooth_package.default_text) if contract.photobooth_package else '',
        },
        'additional_services_texts': {
            'photography_additional': linebreaks(contract.photography_additional.default_text) if contract.photography_additional else '',
            'videography_additional': linebreaks(contract.videography_additional.default_text) if contract.videography_additional else '',
            'dj_additional': linebreaks(contract.dj_additional.default_text) if contract.dj_additional else '',
            'photobooth_additional': linebreaks(contract.photobooth_additional.default_text) if contract.photobooth_additional else '',
        },
        'rider_texts': {
            'photography': linebreaks(contract.photography_package.rider_text) if contract.photography_package else '',
            'videography': linebreaks(contract.videography_package.rider_text) if contract.videography_package else '',
            'dj': linebreaks(contract.dj_package.rider_text) if contract.dj_package else '',
            'photobooth': linebreaks(contract.photobooth_package.rider_text) if contract.photobooth_package else '',
        },
        'total_service_cost': contract.calculate_total_service_cost(),
        'total_discount': contract.calculate_discount(),
        'total_cost_after_discounts': contract.calculate_total_service_cost_after_discounts(),
        'photographer_choices': [
            contract.prospect_photographer1,
            contract.prospect_photographer2,
            contract.prospect_photographer3
        ],
        'overtime_options_by_service_type': overtime_options_by_service_type,
        'total_overtime_cost': total_overtime_cost,
        'ROLE_DISPLAY_NAMES': ROLE_DISPLAY_NAMES,  # Add role display names to context
    }

    return render(request, 'contracts/contract_agreement_form.html', context)




@login_required
def client_contract_agreement(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    if request.method == 'POST':
        form = ContractAgreementForm(request.POST)
        if form.is_valid():
            agreement = form.save(commit=False)
            agreement.contract = contract
            agreement.signature = form.cleaned_data['main_signature']

            latest_agreement = ContractAgreement.objects.filter(contract=contract).order_by('-version_number').first()
            agreement.version_number = latest_agreement.version_number + 1 if latest_agreement else 1

            # Save the state of services
            agreement.photography_service = contract.photography_package.service_type if contract.photography_package else None
            agreement.videography_service = contract.videography_package.service_type if contract.videography_package else None
            agreement.dj_service = contract.dj_package.service_type if contract.dj_package else None
            agreement.photobooth_service = contract.photobooth_package.service_type if contract.photobooth_package else None

            agreement.save()

            portal_url = reverse('contracts:client_portal', args=[contract_id])

            # Render the status page upon successful form submission
            return render(request, 'contracts/status_page.html', {
                'message': 'You\'re all set, thank you!',
                'portal_url': portal_url
            })
        else:
            portal_url = reverse('contracts:client_portal', args=[contract_id])

            return render(request, 'contracts/status_page.html', {
                'message': 'There was an error submitting the contract agreement.',
                'portal_url': portal_url
            })

    else:
        form = ContractAgreementForm()

    # Initialize an empty dictionary to store overtime options grouped by service type
    overtime_options_by_service_type = {}

    # Initialize total overtime cost
    total_overtime_cost = 0

    # Iterate over each overtime option
    for contract_overtime in contract.overtimes.all():
        # Get the service type of the overtime option
        service_type = contract_overtime.overtime_option.service_type.name

        # Check if the service type already exists in the dictionary
        if service_type in overtime_options_by_service_type:
            # If the service type exists, append the overtime option to its list
            overtime_options_by_service_type[service_type].append({
                'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role, contract_overtime.overtime_option.role),
                'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                'hours': contract_overtime.hours,
            })
        else:
            # If the service type does not exist, create a new list with the overtime option
            overtime_options_by_service_type[service_type] = [{
                'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role, contract_overtime.overtime_option.role),
                'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                'hours': contract_overtime.hours,
            }]

    # Calculate total cost for each overtime option
    for service_type, options in overtime_options_by_service_type.items():
        for option in options:
            option['total_cost'] = option['hours'] * option['rate_per_hour']
            total_overtime_cost += option['total_cost']

    package_texts = {
        'photography': linebreaks(contract.photography_package.default_text) if contract.photography_package else None,
        'videography': linebreaks(contract.videography_package.default_text) if contract.videography_package else None,
        'dj': linebreaks(contract.dj_package.default_text) if contract.dj_package else None,
        'photobooth': linebreaks(contract.photobooth_package.default_text) if contract.photobooth_package else None,
    }

    context = {
        'contract': contract,
        'logo_url': logo_url,
        'package_texts': package_texts,
        'total_service_cost': contract.calculate_total_service_cost(),
        'total_discount': contract.calculate_discount(),
        'total_cost_after_discounts': contract.calculate_total_service_cost_after_discounts(),
        'photographer_choices': [
            contract.prospect_photographer1,
            contract.prospect_photographer2,
            contract.prospect_photographer3
        ],
        'overtime_options_by_service_type': overtime_options_by_service_type,
        'total_overtime_cost': total_overtime_cost,
        'ROLE_DISPLAY_NAMES': ROLE_DISPLAY_NAMES,  # Add role display names to context
        'form': form,
    }

    return render(request, 'contracts/client_contract_agreement.html', context)

@login_required
def view_submitted_contract(request, contract_id, version_number):
    contract = get_object_or_404(Contract, pk=contract_id)
    contract_agreement = get_object_or_404(ContractAgreement, contract=contract, version_number=version_number)
    rider_agreements = RiderAgreement.objects.filter(contract=contract)
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    # Initialize an empty dictionary to store overtime options grouped by service type
    overtime_options_by_service_type = {}

    # Initialize total overtime cost
    total_overtime_cost = 0

    # Iterate over each overtime option
    for contract_overtime in contract.overtimes.all():
        # Get the service type of the overtime option
        service_type = contract_overtime.overtime_option.service_type.name

        # Check if the service type already exists in the dictionary
        if service_type in overtime_options_by_service_type:
            # If the service type exists, append the overtime option to its list
            overtime_options_by_service_type[service_type].append({
                'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role, contract_overtime.overtime_option.role),
                'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                'hours': contract_overtime.hours,
            })
        else:
            # If the service type does not exist, create a new list with the overtime option
            overtime_options_by_service_type[service_type] = [{
                'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role, contract_overtime.overtime_option.role),
                'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                'hours': contract_overtime.hours,
            }]

    # Calculate total cost for each overtime option
    for service_type, options in overtime_options_by_service_type.items():
        for option in options:
            option['total_cost'] = option['hours'] * option['rate_per_hour']
            total_overtime_cost += option['total_cost']

    package_texts = {
        'photography': linebreaks(contract.photography_package.default_text) if contract.photography_package else None,
        'videography': linebreaks(contract.videography_package.default_text) if contract.videography_package else None,
        'dj': linebreaks(contract.dj_package.default_text) if contract.dj_package else None,
        'photobooth': linebreaks(contract.photobooth_package.default_text) if contract.photobooth_package else None,
    }

    additional_services_texts = {
        'photography_additional': linebreaks(contract.photography_additional.default_text) if contract.photography_additional else None,
        'videography_additional': linebreaks(contract.videography_additional.default_text) if contract.videography_additional else None,
        'dj_additional': linebreaks(contract.dj_additional.default_text) if contract.dj_additional else None,
        'photobooth_additional': linebreaks(contract.photobooth_additional.default_text) if contract.photobooth_additional else None,
    }

    total_service_cost = contract.calculate_total_service_cost()
    total_discount = contract.calculate_discount()
    total_cost_after_discounts = contract.calculate_total_service_cost_after_discounts()

    context = {
        'contract': contract,
        'contract_agreement': contract_agreement,
        'rider_agreements': rider_agreements,
        'logo_url': logo_url,
        'package_texts': package_texts,
        'additional_services_texts': additional_services_texts,
        'total_service_cost': total_service_cost,
        'total_discount': total_discount,
        'total_cost_after_discounts': total_cost_after_discounts,
        'overtime_options_by_service_type': overtime_options_by_service_type,
        'total_overtime_cost': total_overtime_cost,
        'ROLE_DISPLAY_NAMES': ROLE_DISPLAY_NAMES,  # Add role display names to context
    }

    return render(request, 'contracts/view_submitted_contract.html', context)

@login_required
def client_contract_and_rider_agreement(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"
    company_signature_url = f"http://{request.get_host()}{settings.MEDIA_URL}signatures/company_signature.png"

    if request.method == 'POST':
        form = ContractAgreementForm(request.POST)
        if form.is_valid():
            agreement = form.save(commit=False)
            agreement.contract = contract
            agreement.signature = form.cleaned_data['main_signature']
            agreement.photographer_choice = form.cleaned_data['photographer_choice']  # Save photographer choice

            latest_agreement = ContractAgreement.objects.filter(contract=contract).order_by('-version_number').first()
            agreement.version_number = latest_agreement.version_number + 1 if latest_agreement else 1

            agreement.save()

            rider_agreements = []
            for rider in ['photography', 'photography_additional', 'videography', 'videography_additional', 'dj',
                          'dj_additional', 'photobooth', 'photobooth_additional']:
                signature = request.POST.get(f'signature_{rider}')
                client_name = request.POST.get(f'client_name_{rider}')
                agreement_date = request.POST.get(f'agreement_date_{rider}')
                notes = request.POST.get(f'notes_{rider}')
                rider_text = request.POST.get(f'rider_text_{rider}')

                if signature:
                    rider_agreement = RiderAgreement.objects.create(
                        contract=contract,
                        rider_type=rider,
                        signature=signature,
                        client_name=client_name,
                        agreement_date=agreement_date,
                        notes=notes,
                        rider_text=rider_text
                    )
                    rider_agreements.append(rider_agreement)
                else:
                    print(f"Missing signature for {rider}")

            # Initialize an empty dictionary to store overtime options grouped by service type
            overtime_options_by_service_type = {}

            # Initialize total overtime cost
            total_overtime_cost = 0

            # Iterate over each overtime option
            for contract_overtime in contract.overtimes.all():
                service_type = contract_overtime.overtime_option.service_type.name
                if service_type in overtime_options_by_service_type:
                    overtime_options_by_service_type[service_type].append({
                        'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role,
                                                       contract_overtime.overtime_option.role),
                        'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                        'hours': contract_overtime.hours,
                    })
                else:
                    overtime_options_by_service_type[service_type] = [{
                        'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role,
                                                       contract_overtime.overtime_option.role),
                        'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                        'hours': contract_overtime.hours,
                    }]

            for service_type, options in overtime_options_by_service_type.items():
                for option in options:
                    option['total_cost'] = option['hours'] * option['rate_per_hour']
                    total_overtime_cost += option['total_cost']

            package_texts = {
                'photography': linebreaks(contract.photography_package.default_text) if contract.photography_package else None,
                'videography': linebreaks(contract.videography_package.default_text) if contract.videography_package else None,
                'dj': linebreaks(contract.dj_package.default_text) if contract.dj_package else None,
                'photobooth': linebreaks(contract.photobooth_package.default_text) if contract.photobooth_package else None,
            }

            additional_services_texts = {
                'photography_additional': linebreaks(contract.photography_additional.default_text) if contract.photography_additional else None,
                'videography_additional': linebreaks(contract.videography_additional.default_text) if contract.videography_additional else None,
                'dj_additional': linebreaks(contract.dj_additional.default_text) if contract.dj_additional else None,
                'photobooth_additional': linebreaks(contract.photobooth_additional.default_text) if contract.photobooth_additional else None,
            }

            rider_texts = {
                'photography': linebreaks(contract.photography_package.rider_text) if contract.photography_package else None,
                'photography_additional': linebreaks(contract.photography_additional.rider_text) if contract.photography_additional else None,
                'engagement_session': linebreaks(contract.engagement_session.rider_text) if contract.engagement_session else None,
                'videography': linebreaks(contract.videography_package.rider_text) if contract.videography_package else None,
                'videography_additional': linebreaks(contract.videography_additional.rider_text) if contract.videography_additional else None,
                'dj': linebreaks(contract.dj_package.rider_text) if contract.dj_package else None,
                'dj_additional': linebreaks(contract.dj_additional.rider_text) if contract.dj_additional else None,
                'photobooth': linebreaks(contract.photobooth_package.rider_text) if contract.photobooth_package else None,
                'photobooth_additional': linebreaks(contract.photobooth_additional.rider_text) if contract.photobooth_additional else None,
            }

            total_service_cost = contract.calculate_total_service_cost()
            total_discount = contract.calculate_discount()
            total_cost_after_discounts = contract.calculate_total_service_cost_after_discounts()

            context = {
                'contract': contract,
                'logo_url': logo_url,
                'company_signature_url': company_signature_url,
                'latest_agreement': agreement,
                'rider_agreements': rider_agreements,
                'package_texts': package_texts,
                'additional_services_texts': additional_services_texts,
                'rider_texts': rider_texts,
                'total_service_cost': total_service_cost,
                'total_discount': total_discount,
                'total_cost_after_discounts': total_cost_after_discounts,
                'overtime_options_by_service_type': overtime_options_by_service_type,
                'total_overtime_cost': total_overtime_cost,
                'ROLE_DISPLAY_NAMES': ROLE_DISPLAY_NAMES,
            }

            # Generate PDF
            html_string = render_to_string('contracts/client_contract_and_rider_agreement_pdf.html', context)
            pdf_file = HTML(string=html_string).write_pdf()

            # Save PDF to the documents section of the contract
            pdf_name = f"contract_{contract_id}_agreement.pdf"
            path = default_storage.save(f"contract_documents/{pdf_name}", ContentFile(pdf_file))

            ContractDocument.objects.create(
                contract=contract,
                document=path,
                is_client_visible=True,
            )

            # Email the PDF to the client
            client_email = contract.client.primary_email
            email = EmailMessage(
                subject="Your Contract Agreement",
                body="Please find attached your signed contract agreement.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[client_email],
            )
            email.attach(pdf_name, pdf_file, 'application/pdf')
            email.send()

            portal_url = reverse('contracts:client_portal', args=[contract_id])
            return render(request, 'contracts/status_page.html', {
                'message': 'You\'re all set, thank you!',
                'portal_url': portal_url
            })
        else:
            portal_url = reverse('client_portal', args=[contract_id])

            return render(request, 'contracts/status_page.html', {
                'message': 'There was an error submitting the agreements.',
                'portal_url': portal_url
            })

    else:
        form = ContractAgreementForm()

        # Initialize an empty dictionary to store overtime options grouped by service type
        overtime_options_by_service_type = {}

        # Initialize total overtime cost
        total_overtime_cost = 0

        # Iterate over each overtime option
        for contract_overtime in contract.overtimes.all():
            service_type = contract_overtime.overtime_option.service_type.name
            if service_type in overtime_options_by_service_type:
                overtime_options_by_service_type[service_type].append({
                    'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role,
                                                   contract_overtime.overtime_option.role),
                    'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                    'hours': contract_overtime.hours,
                })
            else:
                overtime_options_by_service_type[service_type] = [{
                    'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role,
                                                   contract_overtime.overtime_option.role),
                    'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                    'hours': contract_overtime.hours,
                }]

        for service_type, options in overtime_options_by_service_type.items():
            for option in options:
                option['total_cost'] = option['hours'] * option['rate_per_hour']
                total_overtime_cost += option['total_cost']

        package_texts = {
            'photography': linebreaks(contract.photography_package.default_text) if contract.photography_package else None,
            'videography': linebreaks(contract.videography_package.default_text) if contract.videography_package else None,
            'dj': linebreaks(contract.dj_package.default_text) if contract.dj_package else None,
            'photobooth': linebreaks(contract.photobooth_package.default_text) if contract.photobooth_package else None,
        }

        additional_services_texts = {
            'photography_additional': linebreaks(contract.photography_additional.default_text) if contract.photography_additional else None,
            'videography_additional': linebreaks(contract.videography_additional.default_text) if contract.videography_additional else None,
            'dj_additional': linebreaks(contract.dj_additional.default_text) if contract.dj_additional else None,
            'photobooth_additional': linebreaks(contract.photobooth_additional.default_text) if contract.photobooth_additional else None,
        }

        rider_texts = {
            'photography': linebreaks(contract.photography_package.rider_text) if contract.photography_package else None,
            'photography_additional': linebreaks(contract.photography_additional.rider_text) if contract.photography_additional else None,
            'engagement_session': linebreaks(contract.engagement_session.rider_text) if contract.engagement_session else None,
            'videography': linebreaks(contract.videography_package.rider_text) if contract.videography_package else None,
            'videography_additional': linebreaks(contract.videography_additional.rider_text) if contract.videography_additional else None,
            'dj': linebreaks(contract.dj_package.rider_text) if contract.dj_package else None,
            'dj_additional': linebreaks(contract.dj_additional.rider_text) if contract.dj_additional else None,
            'photobooth': linebreaks(contract.photobooth_package.rider_text) if contract.photobooth_package else None,
            'photobooth_additional': linebreaks(contract.photobooth_additional.rider_text) if contract.photobooth_additional else None,
        }

        total_service_cost = contract.calculate_total_service_cost()
        total_discount = contract.calculate_discount()
        total_cost_after_discounts = contract.calculate_total_service_cost_after_discounts()

        photographer_choices = [
            contract.prospect_photographer1,
            contract.prospect_photographer2,
            contract.prospect_photographer3
        ]

        context = {
            'contract': contract,
            'logo_url': logo_url,
            'package_texts': package_texts,
            'additional_services_texts': additional_services_texts,
            'rider_texts': rider_texts,
            'total_service_cost': total_service_cost,
            'total_discount': total_discount,
            'total_cost_after_discounts': total_cost_after_discounts,
            'photographer_choices': photographer_choices,
            'overtime_options_by_service_type': overtime_options_by_service_type,
            'total_overtime_cost': total_overtime_cost,
            'ROLE_DISPLAY_NAMES': ROLE_DISPLAY_NAMES,
            'form': form,
        }

        return render(request, 'contracts/client_contract_and_rider_agreement.html', context)


@login_required
def client_rider_agreement(request, contract_id, rider_type):
    contract = get_object_or_404(Contract, pk=contract_id)
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"
    company_signature_url = f"http://{request.get_host()}{settings.MEDIA_URL}signatures/company_signature.png"

    if request.method == 'POST':
        form = ContractAgreementForm(request.POST)
        if form.is_valid():
            agreement = form.save(commit=False)
            agreement.contract = contract
            agreement.signature = form.cleaned_data['main_signature']

            latest_agreement = ContractAgreement.objects.filter(contract=contract).order_by('-version_number').first()
            agreement.version_number = latest_agreement.version_number + 1 if latest_agreement else 1

            agreement.save()

            signature = request.POST.get(f'signature_{rider_type}')
            client_name = request.POST.get(f'client_name_{rider_type}')
            agreement_date = request.POST.get(f'agreement_date_{rider_type}')
            notes = request.POST.get(f'notes_{rider_type}')
            rider_text = request.POST.get(f'rider_text_{rider_type}')

            rider_agreement = None
            if signature:
                try:
                    rider_agreement = RiderAgreement.objects.create(
                        contract=contract,
                        rider_type=rider_type,
                        signature=signature,
                        client_name=client_name,
                        agreement_date=agreement_date,
                        notes=notes,
                        rider_text=rider_text
                    )
                except Exception as e:
                    pass

            # Generate PDF
            rider_agreements = RiderAgreement.objects.filter(contract=contract)
            first_agreement = ContractAgreement.objects.filter(contract=contract).order_by('version_number').first()

            context = {
                'contract': contract,
                'logo_url': logo_url,
                'company_signature_url': company_signature_url,
                'latest_agreement': agreement,
                'rider_agreements': rider_agreements,
                'first_agreement': first_agreement,
            }

            # Initialize an empty dictionary to store overtime options grouped by service type
            overtime_options_by_service_type = {}

            # Initialize total overtime cost
            total_overtime_cost = 0

            # Iterate over each overtime option
            for contract_overtime in contract.overtimes.all():
                service_type = contract_overtime.overtime_option.service_type.name
                if service_type in overtime_options_by_service_type:
                    overtime_options_by_service_type[service_type].append({
                        'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role,
                                                       contract_overtime.overtime_option.role),
                        'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                        'hours': contract_overtime.hours,
                    })
                else:
                    overtime_options_by_service_type[service_type] = [{
                        'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role,
                                                       contract_overtime.overtime_option.role),
                        'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                        'hours': contract_overtime.hours,
                    }]

            for service_type, options in overtime_options_by_service_type.items():
                for option in options:
                    option['total_cost'] = option['hours'] * option['rate_per_hour']
                    total_overtime_cost += option['total_cost']

            package_texts = {
                'photography': linebreaks(contract.photography_package.default_text) if contract.photography_package else None,
                'videography': linebreaks(contract.videography_package.default_text) if contract.videography_package else None,
                'dj': linebreaks(contract.dj_package.default_text) if contract.dj_package else None,
                'photobooth': linebreaks(contract.photobooth_package.default_text) if contract.photobooth_package else None,
            }

            additional_services_texts = {
                'photography_additional': linebreaks(contract.photography_additional.default_text) if contract.photography_additional else None,
                'videography_additional': linebreaks(contract.videography_additional.default_text) if contract.videography_additional else None,
                'dj_additional': linebreaks(contract.dj_additional.default_text) if contract.dj_additional else None,
                'photobooth_additional': linebreaks(contract.photobooth_additional.default_text) if contract.photobooth_additional else None,
            }

            rider_texts = {
                'photography': linebreaks(contract.photography_package.rider_text) if contract.photography_package else None,
                'photography_additional': linebreaks(contract.photography_additional.rider_text) if contract.photography_additional else None,
                'engagement_session': linebreaks(contract.engagement_session.rider_text) if contract.engagement_session else None,
                'videography': linebreaks(contract.videography_package.rider_text) if contract.videography_package else None,
                'videography_additional': linebreaks(contract.videography_additional.rider_text) if contract.videography_additional else None,
                'dj': linebreaks(contract.dj_package.rider_text) if contract.dj_package else None,
                'dj_additional': linebreaks(contract.dj_additional.rider_text) if contract.dj_additional else None,
                'photobooth': linebreaks(contract.photobooth_package.rider_text) if contract.photobooth_package else None,
                'photobooth_additional': linebreaks(contract.photobooth_additional.rider_text) if contract.photobooth_additional else None,
            }

            total_service_cost = contract.calculate_total_service_cost()
            total_discount = contract.calculate_discount()
            total_cost_after_discounts = contract.calculate_total_service_cost_after_discounts()

            context.update({
                'overtime_options_by_service_type': overtime_options_by_service_type,
                'total_overtime_cost': total_overtime_cost,
                'package_texts': package_texts,
                'additional_services_texts': additional_services_texts,
                'rider_texts': rider_texts,
                'total_service_cost': total_service_cost,
                'total_discount': total_discount,
                'total_cost_after_discounts': total_cost_after_discounts,
            })

            html_string = render_to_string('contracts/client_contract_and_rider_agreement_pdf.html', context)
            pdf_file = HTML(string=html_string).write_pdf()

            # Save PDF to the documents section of the contract
            pdf_name = f"contract_{contract_id}_rider_{rider_type}.pdf"
            path = default_storage.save(f"contract_documents/{pdf_name}", ContentFile(pdf_file))

            ContractDocument.objects.create(
                contract=contract,
                document=path,
                is_client_visible=True,
            )

            # Email the PDF to the client
            client_email = contract.client.primary_email
            email = EmailMessage(
                subject=f"Your {rider_type.replace('_', ' ').capitalize()} Rider Agreement",
                body="Please find attached your signed rider agreement.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[client_email],
            )
            email.attach(pdf_name, pdf_file, 'application/pdf')
            email.send()

            portal_url = reverse('contracts:client_portal', args=[contract_id])
            return render(request, 'contracts/status_page.html', {
                'message': 'You\'re all set, thank you!',
                'portal_url': portal_url
            })
        else:
            portal_url = reverse('contracts:client_portal', args=[contract_id])

            return render(request, 'contracts/status_page.html', {
                'message': 'There was an error submitting the agreements.',
                'portal_url': portal_url
            })
    else:
        form = ContractAgreementForm()

    # Initialize an empty dictionary to store overtime options grouped by service type
    overtime_options_by_service_type = {}

    # Initialize total overtime cost
    total_overtime_cost = 0

    # Iterate over each overtime option
    for contract_overtime in contract.overtimes.all():
        # Get the service type of the overtime option
        service_type = contract_overtime.overtime_option.service_type.name

        # Check if the service type already exists in the dictionary
        if service_type in overtime_options_by_service_type:
            # If the service type exists, append the overtime option to its list
            overtime_options_by_service_type[service_type].append({
                'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role, contract_overtime.overtime_option.role),
                'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                'hours': contract_overtime.hours,
            })
        else:
            # If the service type does not exist, create a new list with the overtime option
            overtime_options_by_service_type[service_type] = [{
                'role': ROLE_DISPLAY_NAMES.get(contract_overtime.overtime_option.role, contract_overtime.overtime_option.role),
                'rate_per_hour': contract_overtime.overtime_option.rate_per_hour,
                'hours': contract_overtime.hours,
            }]

    for service_type, options in overtime_options_by_service_type.items():
        for option in options:
            option['total_cost'] = option['hours'] * option['rate_per_hour']
            total_overtime_cost += option['total_cost']

    package_texts = {
        'photography': linebreaks(contract.photography_package.default_text) if contract.photography_package else None,
        'videography': linebreaks(contract.videography_package.default_text) if contract.videography_package else None,
        'dj': linebreaks(contract.dj_package.default_text) if contract.dj_package else None,
        'photobooth': linebreaks(contract.photobooth_package.default_text) if contract.photobooth_package else None,
    }

    additional_services_texts = {
        'photography_additional': linebreaks(contract.photography_additional.default_text) if contract.photography_additional else None,
        'videography_additional': linebreaks(contract.videography_additional.default_text) if contract.videography_additional else None,
        'dj_additional': linebreaks(contract.dj_additional.default_text) if contract.dj_additional else None,
        'photobooth_additional': linebreaks(contract.photobooth_additional.default_text) if contract.photobooth_additional else None,
    }

    rider_texts = {
        'photography': linebreaks(contract.photography_package.rider_text) if contract.photography_package else None,
        'photography_additional': linebreaks(contract.photography_additional.rider_text) if contract.photography_additional else None,
        'engagement_session': linebreaks(contract.engagement_session.rider_text) if contract.engagement_session else None,
        'videography': linebreaks(contract.videography_package.rider_text) if contract.videography_package else None,
        'videography_additional': linebreaks(contract.videography_additional.rider_text) if contract.videography_additional else None,
        'dj': linebreaks(contract.dj_package.rider_text) if contract.dj_package else None,
        'dj_additional': linebreaks(contract.dj_additional.rider_text) if contract.dj_additional else None,
        'photobooth': linebreaks(contract.photobooth_package.rider_text) if contract.photobooth_package else None,
        'photobooth_additional': linebreaks(contract.photobooth_additional.rider_text) if contract.photobooth_additional else None,
    }

    total_service_cost = contract.calculate_total_service_cost()
    total_discount = contract.calculate_discount()
    total_cost_after_discounts = contract.calculate_total_service_cost_after_discounts()

    photographer_choices = [
        contract.prospect_photographer1,
        contract.prospect_photographer2,
        contract.prospect_photographer3
    ]

    context = {
        'contract': contract,
        'logo_url': logo_url,
        'package_texts': package_texts,
        'additional_services_texts': additional_services_texts,
        'rider_texts': rider_texts,
        'total_service_cost': total_service_cost,
        'total_discount': total_discount,
        'total_cost_after_discounts': total_cost_after_discounts,
        'photographer_choices': photographer_choices,
        'overtime_options_by_service_type': overtime_options_by_service_type,
        'total_overtime_cost': total_overtime_cost,
        'ROLE_DISPLAY_NAMES': ROLE_DISPLAY_NAMES,
        'form': form,
        'rider_text': rider_texts.get(rider_type, ""),
        'rider_type': rider_type,
    }

    return render(request, 'contracts/client_rider_agreement.html', context)


def view_rider_agreements(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    rider_agreements = RiderAgreement.objects.filter(contract=contract)
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    package_texts = {
        'photography': linebreaks(contract.photography_package.default_text) if contract.photography_package else None,
        'videography': linebreaks(contract.videography_package.default_text) if contract.videography_package else None,
        'dj': linebreaks(contract.dj_package.default_text) if contract.dj_package else None,
        'photobooth': linebreaks(contract.photobooth_package.default_text) if contract.photobooth_package else None,
    }

    additional_services_texts = {
        'photography_additional': linebreaks(contract.photography_additional.default_text) if contract.photography_additional else None,
        'videography_additional': linebreaks(contract.videography_additional.default_text) if contract.videography_additional else None,
        'dj_additional': linebreaks(contract.dj_additional.default_text) if contract.dj_additional else None,
        'photobooth_additional': linebreaks(contract.photobooth_additional.default_text) if contract.photobooth_additional else None,
    }

    total_service_cost = contract.calculate_total_service_cost()
    total_discount = contract.calculate_discount()
    total_cost_after_discounts = contract.calculate_total_service_cost_after_discounts()

    context = {
        'contract': contract,
        'rider_agreements': rider_agreements,
        'logo_url': logo_url,
        'package_texts': package_texts,
        'additional_services_texts': additional_services_texts,
        'total_service_cost': total_service_cost,
        'total_discount': total_discount,
        'total_cost_after_discounts': total_cost_after_discounts,
    }

    return render(request, 'contracts/view_rider_agreement.html', context)



@login_required
def upload_contract_documents(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    if request.method == 'POST':
        form = ContractDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            contract_document = form.save(commit=False)
            contract_document.contract = contract
            contract_document.save()
            return redirect('contracts:contract_detail', pk=contract_id)
    else:
        form = ContractDocumentForm()

    return render(request, 'contracts/upload_contract_documents.html', {'form': form})

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
                    'hours': package.hours,
                    'default_text': package.default_text  # Make sure this attribute exists in your model
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

@csrf_exempt
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


@login_required
def save_products(request, id):
    contract = get_object_or_404(Contract, pk=id)

    if request.method == 'POST':
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                products = data.get('products', [])

                # Log incoming data for debugging
                print('Incoming products data:', products)

                # Clear existing products
                contract.contract_products.all().delete()

                # Add updated products
                for product_data in products:
                    product_id = product_data['product_id']
                    quantity = product_data['quantity']
                    product = Product.objects.get(id=product_id)
                    contract.contract_products.create(product=product, quantity=quantity)

                # Recalculate the tax
                tax_amount = contract.calculate_tax()
                contract.tax_amount = tax_amount
                contract.save()

                print('Tax calculated and saved:', tax_amount)  # Log calculated tax

                return JsonResponse({'status': 'success', 'tax_amount': tax_amount})
            except json.JSONDecodeError as e:
                return JsonResponse({'status': 'fail', 'error': 'Invalid JSON data', 'details': str(e)}, status=400)
            except Product.DoesNotExist as e:
                return JsonResponse({'status': 'fail', 'error': 'Product not found', 'details': str(e)}, status=400)
            except Exception as e:
                return JsonResponse({'status': 'fail', 'error': 'An unexpected error occurred', 'details': str(e)}, status=500)
        else:
            product_formset = ContractProductFormset(request.POST, instance=contract, prefix='contract_products')
            if product_formset.is_valid():
                product_formset.save()
                return redirect(reverse('contracts:contract_detail', kwargs={'id': contract.contract_id}) + '#products')
            else:
                # If the formset is not valid, re-render the page with the formset errors
                context = {
                    'contract': contract,
                    'product_formset': product_formset,
                }
                return render(request, 'contracts/contract_detail.html', context)
    else:
        # For a GET request, render the page with the formset
        product_formset = ContractProductFormset(instance=contract, prefix='contract_products')
        context = {
            'contract': contract,
            'product_formset': product_formset,
        }
        return render(request, 'contracts/contract_detail.html', context)

def add_service_fees(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    if request.method == 'POST':
        service_fee_formset = ServiceFeeFormSet(request.POST, instance=contract)
        if service_fee_formset.is_valid():
            service_fee_formset.save()
            # Optional: Update contract totals if necessary
            contract.total_cost = sum([fee.amount for fee in contract.servicefees.all()])
            contract.save()
            return redirect(reverse('contracts:contract_detail', kwargs={'id': contract_id}) + '#financial')
    else:
        service_fee_formset = ServiceFeeFormSet(instance=contract)

    return render(request, 'contracts/contract_detail.html', {'service_fee_formset': service_fee_formset, 'contract': contract})


@login_required
def delete_service_fee(request, fee_id):
    if request.method == 'POST':
        fee = get_object_or_404(ServiceFee, id=fee_id)
        contract_id = fee.contract.contract_id
        fee.delete()
        return redirect(f'/contracts/{contract_id}/#payments')  # Redirect back to the payments tab
    else:
        return redirect('contracts:contract_detail')

def get_service_fees(request, contract_id):
    service_fees = ServiceFee.objects.filter(contract_id=contract_id)
    fees_data = [
        {
            'description': fee.description,
            'fee_type': fee.fee_type.name if fee.fee_type else '',
            'amount': str(fee.amount),
            'applied_date': fee.applied_date.strftime('%Y-%m-%d')  # Format the date for JSON response
        }
        for fee in service_fees
    ]
    return JsonResponse(fees_data, safe=False)

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
    contract = get_object_or_404(Contract, contract_id=contract_id)
    if not hasattr(contract, 'payment_schedule'):
        schedule = create_schedule_a_payments(contract_id)
        contract.status = 'booked'  # Optionally update contract status
        contract.save()
    return redirect(request,'contract_detail', id=contract_id) + '#payments'

def create_schedule_a_payments(contract_id):
    contract = get_object_or_404(Contract, contract_id=contract_id)
    schedule, created = PaymentSchedule.objects.get_or_create(contract=contract, defaults={'schedule_type': 'schedule_a'})

    # Clear existing Schedule A payments
    SchedulePayment.objects.filter(schedule=schedule).delete()

    # Change the purpose name from 'Down Payment' to 'Deposit'
    deposit_purpose, _ = PaymentPurpose.objects.get_or_create(name='Deposit')
    balance_payment_purpose, _ = PaymentPurpose.objects.get_or_create(name='Balance Payment')

    # Calculate the deposit amount (50% of the total contract cost, rounded up to the nearest 100)
    raw_deposit_amount = contract.final_total * Decimal('0.50')
    deposit_amount = (raw_deposit_amount / Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * Decimal('100')

    # Calculate the balance due date (60 days before the event date)
    balance_due_date = contract.event_date - timedelta(days=60)

    # Create the deposit payment with a note indicating it's due upon booking
    SchedulePayment.objects.create(
        schedule=schedule,
        purpose=deposit_purpose,
        due_date=now(),  # Use the current date
        amount=deposit_amount,
        paid=contract.amount_paid >= deposit_amount
    )

    # Create the balance payment
    balance_amount = contract.final_total - deposit_amount
    SchedulePayment.objects.create(
        schedule=schedule,
        purpose=balance_payment_purpose,
        due_date=balance_due_date,
        amount=balance_amount,
        paid=contract.amount_paid >= contract.final_total
    )

    return schedule

def check_payment_schedule_for_contract(contract_id):
    contract = get_object_or_404(Contract, contract_id=contract_id)
    try:
        payment_schedule = contract.payment_schedule
        print(f'Payment schedule ID for contract {contract_id} is {payment_schedule.id}')
    except PaymentSchedule.DoesNotExist:
        print(f'No payment schedule exists for contract {contract_id}')

@login_required
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

            # Create or update service fees in the custom schedule
            service_fees = request.POST.getlist('service_fees')
            if service_fees:
                for fee in service_fees:
                    fee_data = fee.split(',')
                    fee_purpose, _ = PaymentPurpose.objects.get_or_create(name=fee_data[0])
                    SchedulePayment.objects.create(
                        schedule=schedule,
                        purpose=fee_purpose,
                        due_date=contract.event_date,
                        amount=Decimal(fee_data[1])
                    )

            return HttpResponseRedirect(reverse('contracts:contract_detail', kwargs={'id': contract_id}) + '#financial')

    else:
        schedule_form = PaymentScheduleForm(instance=schedule)
        schedule_payment_formset = SchedulePaymentFormSet(instance=schedule)

    return render(request, 'contracts/schedule_form.html', {
        'contract': contract,
        'schedule_form': schedule_form,
        'schedule_payment_formset': schedule_payment_formset,
    })



def get_schedule_payments_due(request, contract_id):
    contract = get_object_or_404(Contract, contract_id=contract_id)
    schedule = contract.payment_schedule

    if not schedule:
        return JsonResponse({'next_payment_amount': '0.00', 'next_payment_due_date': 'N/A'})

    if schedule.schedule_type == 'schedule_a':
        next_payment_due_date = contract.event_date - timedelta(days=60)
        next_payment_amount = contract.balance_due
    else:
        schedule_payments = schedule.schedule_payments.filter(paid=False).order_by('due_date')
        if schedule_payments.exists():
            next_payment = schedule_payments.first()
            next_payment_due_date = next_payment.due_date
            next_payment_amount = next_payment.amount
        else:
            next_payment_due_date = 'N/A'
            next_payment_amount = '0.00'

    payment_details = {
        'next_payment_amount': str(next_payment_amount),
        'next_payment_due_date': next_payment_due_date.strftime('%Y-%m-%d') if next_payment_due_date != 'N/A' else 'N/A'
    }

    return JsonResponse(payment_details)


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


@login_required
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
    original_amount = payment.amount  # Capture the original amount for logging

    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.modified_by_user = request.user
            payment.save()  # Save the payment

            # Log changes if the amount is updated
            if original_amount != payment.amount:
                ChangeLog.objects.create(
                    user=request.user,
                    description=f"Payment updated from {original_amount} to {payment.amount} for payment ID {payment.id}",
                    contract=payment.contract  # Pass the associated contract
                )

            # Update payment status after editing the payment
            update_payment_status(payment.contract.payment_schedule)

            return JsonResponse({'success': True, 'payment_id': payment.id})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        return JsonResponse({'success': False, 'message': 'GET request not allowed'}, status=405)


@login_required
def delete_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    contract = payment.contract  # Get the contract directly

    # Log the payment deletion
    ChangeLog.objects.create(
        user=request.user,
        description=f"Deleted payment of {payment.amount} for payment ID {payment.id}",
        contract=contract  # Ensure the contract is associated with the log
    )

    payment.delete()

    # Update payment status after deletion
    if contract.payment_schedule:
        update_payment_status(contract.payment_schedule)

    return redirect('contracts:contract_detail', id=contract.contract_id)  # Make sure to use `id` or `pk`

@login_required
def get_existing_payments(request, contract_id):
    contract = get_object_or_404(Contract, contract_id=contract_id)
    payments = contract.payments.all()  # Related name 'payments'
    data = [
        {
            'id': payment.id,
            'date': payment.date.isoformat(),  # Ensure the date is in ISO format
            'amount': float(payment.amount),  # Convert amount to float
            'method': payment.payment_method,  # Correct field name
            'purpose': payment.payment_purpose.name if payment.payment_purpose else '',  # Get purpose name
            'reference': payment.payment_reference if payment.payment_reference else '',
            'memo': payment.memo if payment.memo else '',
        }
        for payment in payments
    ]
    return JsonResponse(data, safe=False)


@login_required
def booking_detail(request, booking_id):
    # Retrieve the booking instance
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"
    booking = get_object_or_404(EventStaffBooking, id=booking_id)
    contract = booking.contract

    # Fetch all booking notes related to this booking
    booking_notes = UnifiedCommunication.objects.filter(note_type='BOOKING', contract=contract)

    # Fetch contract messages related to this contract
    contract_messages = UnifiedCommunication.objects.filter(note_type='CONTRACT', contract=contract)

    # Categorize notes by type
    notes_by_type = defaultdict(list)
    for note in booking_notes:
        notes_by_type[note.note_type].append(note)
    for message in contract_messages:
        notes_by_type[message.note_type].append(message)

    # Handle form submission for new notes
    if request.method == 'POST':
        communication_form = BookingCommunicationForm(request.POST)
        if communication_form.is_valid():
            new_note = UnifiedCommunication.objects.create(
                content=communication_form.cleaned_data['message'],
                note_type='BOOKING',  # Explicitly set note type to booking
                created_by=request.user,
                contract=contract,
            )

            return redirect('contracts:booking_detail', booking_id=booking_id)
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

    return render(request, 'contracts/booking_detail_office.html', {
        'logo_url': logo_url,
        'contract': contract,
        'booking': booking,
        'bookings': EventStaffBooking.objects.filter(contract=contract),
        'booking_notes': notes_by_type['BOOKING'],  # Render only booking notes
        'contract_notes': notes_by_type['CONTRACT'],  # Render contract notes
        'communication_form': communication_form,
        'overtime_entries': overtime_entries,  # Pass overtime entries to the template
    })


@login_required
def booking_detail_staff(request, booking_id):
    booking = get_object_or_404(EventStaffBooking, id=booking_id)
    contract = booking.contract
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    # Fetch all booking notes related to this booking
    booking_notes = UnifiedCommunication.objects.filter(note_type='BOOKING', contract=contract)

    # Fetch contract messages related to this contract
    contract_messages = UnifiedCommunication.objects.filter(note_type=UnifiedCommunication.CONTRACT, contract_id=contract.contract_id)

    # Categorize notes by type
    notes_by_type = defaultdict(list)
    for note in booking_notes:
        notes_by_type[note.note_type].append(note)
    for message in contract_messages:
        notes_by_type[message.note_type].append(message)

    # Handle form submission for new notes
    if request.method == 'POST':
        communication_form = BookingCommunicationForm(request.POST)
        if communication_form.is_valid():
            new_note = UnifiedCommunication.objects.create(
                content=communication_form.cleaned_data['message'],
                note_type='BOOKING',  # Explicitly set note type to booking
                created_by=request.user,
                contract=contract,
            )
            return redirect('contracts:booking_detail_staff', booking_id=booking_id)
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

    return render(request, 'contracts/booking_detail_staff.html', {
        'contract': contract,
        'booking': booking,
        'bookings': EventStaffBooking.objects.filter(contract=contract),
        'booking_notes': notes_by_type[UnifiedCommunication.BOOKING],
        'contract_notes': notes_by_type[UnifiedCommunication.CONTRACT],
        'communication_form': communication_form,
        'staff_member': request.user,
        'logo_url': logo_url,
        'overtime_entries': overtime_entries,
    })


def booking_notes(request, booking_id):
    booking = get_object_or_404(EventStaffBooking, id=booking_id)
    notes = Note.objects.filter(booking=booking)
    print("Notes for booking:", booking_id, "->", notes)  # Debug output to check notes
    return render(request, 'contracts/booking_notes.html', {'object': booking, 'notes': notes})


@login_required
def add_note(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    content = request.POST.get('content')
    booking_id = request.POST.get('booking_id')
    note_type = request.POST.get('note_type')

    if not content or not booking_id or not note_type:
        return JsonResponse({'success': False, 'error': 'Missing required parameters'})

    try:
        booking = EventStaffBooking.objects.get(pk=booking_id)
    except EventStaffBooking.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Booking not found'})

    # Create a new communication directly
    UnifiedCommunication.objects.create(
        content=content,
        note_type=note_type,
        created_by=request.user,
        content_type=ContentType.objects.get_for_model(booking),
        object_id=booking_id
    )

    return JsonResponse({
        'success': True,
        'content': content
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

@require_POST
@login_required
def create_contract_task(request, contract_id=None, note_id=None):
    form = TaskForm(request.POST)
    if form.is_valid():
        task = form.save(commit=False)
        task.sender = request.user
        task.type = 'contract'

        if contract_id:
            task.contract = get_object_or_404(Contract, id=contract_id)
        if note_id:
            task.note = get_object_or_404(UnifiedCommunication, id=note_id)

        task.save()

        if hasattr(task.assigned_to, 'email') and task.assigned_to.email:
            send_task_assignment_email(request, task)

        tasks = Task.objects.filter(
            contract=task.contract, type='contract', is_completed=False
        ).distinct().order_by('due_date')

        task_list_html = render_to_string('contracts/task_list_snippet.html', {'tasks': tasks}, request=request)
        return JsonResponse({'success': True, 'task_id': task.id, 'task_list_html': task_list_html})
    else:
        return JsonResponse({'success': False, 'errors': form.errors.as_json()})

@login_required
def get_contract_tasks(request, contract_id):
    tasks = Task.objects.filter(
        assigned_to=request.user, contract_id=contract_id, type='contract', is_completed=False
    ).order_by('due_date')
    task_list_html = render_to_string('contracts/internal_task_list_snippet.html', {'tasks': tasks}, request=request)
    return JsonResponse({'task_list_html': task_list_html})



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

    return render(request, 'contracts/booking_search_results.html', {'bookings': bookings})


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

    available_staff = Availability.get_available_staff_for_date(event_date).distinct().order_by('rank')
    combined_name = Concat(F('first_name'), Value(' '), F('last_name'), output_field=CharField())

    data = {
        'photographers': list(available_staff.filter(
            Q(role__name='PHOTOGRAPHER') | Q(additional_roles__name='PHOTOGRAPHER')
        ).annotate(name=combined_name).values('id', 'name', 'rank').order_by('rank')),
        'videographers': list(available_staff.filter(
            Q(role__name='VIDEOGRAPHER') | Q(additional_roles__name='VIDEOGRAPHER')
        ).annotate(name=combined_name).values('id', 'name', 'rank').order_by('rank')),
        'djs': list(available_staff.filter(
            Q(role__name='DJ') | Q(additional_roles__name='DJ')
        ).annotate(name=combined_name).values('id', 'name', 'rank').order_by('rank')),
        'photobooth_operators': list(available_staff.filter(
            Q(role__name='PHOTOBOOTH_OPERATOR') | Q(additional_roles__name='PHOTOBOOTH_OPERATOR')
        ).annotate(name=combined_name).values('id', 'name', 'rank').order_by('rank')),
        # Add any other event staff roles as needed...
    }

    if service_type:
        roles = Role.objects.filter(service_type__name=service_type).values_list('name', flat=True)
        staff_data = list(available_staff.filter(
            Q(role__name__in=roles) | Q(additional_roles__name__in=roles)
        ).annotate(name=combined_name).values('id', 'name', 'rank').order_by('rank'))
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

    return render(request, 'contracts/manage_staff.html', {'contract': contract, 'form': form})

def send_booking_email(request, staff, contract, role, is_update):
    context = {
        'user': staff,
        'contract': contract,
        'role': role,
        'domain': get_current_site(request).domain,
        'is_update': is_update,
    }
    subject = 'Booking Updated' if is_update else 'New Booking Assigned'
    message = render_to_string('communication/booking_assignment_email.html', context, request=request)
    from_email = 'enetadmin@enet2.com'
    to_email = [staff.email]

    send_mail(
        subject,
        message,
        from_email,
        to_email,
        fail_silently=False,
    )

@login_required
def confirm_booking(request, booking_id):
    booking = get_object_or_404(EventStaffBooking, id=booking_id)
    if request.method == 'POST':
        booking.confirmed = True
        booking.save()
        messages.success(request, 'Your attendance has been confirmed.')
    return redirect('contracts:booking_detail_staff', booking_id=booking_id)


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


@login_required
def wedding_day_guide(request, contract_id):
    # Check if the user is part of the "Office Staff" group
    is_office_staff = request.user.groups.filter(name='Office Staff').exists()

    if is_office_staff:
        # Office Staff can access any contract
        contract = get_object_or_404(Contract, contract_id=contract_id)
    else:
        # Clients can only access their own contracts
        contract = get_object_or_404(Contract, contract_id=contract_id, client__user=request.user)

    try:
        guide = WeddingDayGuide.objects.get(contract=contract)
    except WeddingDayGuide.DoesNotExist:
        guide = None

    if guide and guide.submitted and not is_office_staff:
        # If the guide has been submitted and the user is not Office Staff, show a message
        return render(request, 'contracts/wedding_day_guide_submitted.html', {
            'message': 'This Wedding Day Guide has already been submitted and cannot be edited.',
        })

    if request.method == 'POST':
        strict_validation = 'submit' in request.POST
        form = WeddingDayGuideForm(request.POST, instance=guide, strict_validation=strict_validation, contract=contract)
        if form.is_valid() or not strict_validation:
            guide = form.save(commit=False)
            guide.contract = contract
            if 'submit' in request.POST:
                guide.submitted = True
            guide.save()

            # Generate PDF if submitted
            if 'submit' in request.POST:
                # Determine the version number
                existing_versions = ContractDocument.objects.filter(contract=contract, document__icontains=f"wedding_day_guide_{guide.pk}_v").count()
                version_number = existing_versions + 1

                # Generate the PDF
                context = {
                    'guide': guide,
                    'logo_url': logo_url,
                }
                html_string = render_to_string('contracts/wedding_day_guide_pdf.html', context)
                pdf_file = HTML(string=html_string).write_pdf()

                # Save PDF with versioned filename
                pdf_name = f"wedding_day_guide_{guide.pk}_v{version_number}.pdf"
                path = default_storage.save(f"contract_documents/{pdf_name}", ContentFile(pdf_file))

                ContractDocument.objects.create(
                    contract=contract,
                    document=path,
                    is_client_visible=True,
                )

                # Redirect to the contract page with the documents section
                return redirect(f'/contracts/{contract.contract_id}/#docs')

            return redirect('contracts:wedding_day_guide', contract_id=contract.contract_id)
    else:
        form = WeddingDayGuideForm(instance=guide, strict_validation=False, contract=contract)

    return render(request, 'contracts/wedding_day_guide.html', {
        'form': form,
        'submitted': guide.submitted if guide else False,
    })


@login_required
def wedding_day_guide_view(request, pk):
    guide = get_object_or_404(WeddingDayGuide, pk=pk, contract__client__user=request.user)
    return render(request, 'wedding_day_guide_view.html', {'guide': guide})


@login_required
def wedding_day_guide_pdf(request, pk):
    guide = get_object_or_404(WeddingDayGuide, pk=pk, contract__client__user=request.user)
    html_string = render_to_string('wedding_day_guide_pdf.html', {'guide': guide})
    html = HTML(string=html_string)

    try:
        pdf = html.write_pdf()
    except Exception as e:
        return HttpResponse(f'Error generating PDF: {e}', status=500)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="wedding_day_guide_{guide.pk}.pdf"'
    return response


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def wedding_day_guide_api(request, contract_id):
    try:
        contract = Contract.objects.get(contract_id=contract_id)

        if request.method == 'GET':
            try:
                guide = WeddingDayGuide.objects.get(contract_id=contract_id)
            except WeddingDayGuide.DoesNotExist:
                return Response({"error": "Guide not found."}, status=status.HTTP_404_NOT_FOUND)

            serializer = WeddingDayGuideSerializer(guide)
            return Response(serializer.data)

        elif request.method == 'POST':
            data = request.data.copy()
            data['contract'] = contract.contract_id  # Ensure the contract is correctly set

            # Determine if this is a submit action (strict validation)
            strict_validation = request.data.get('strict_validation', False)

            serializer = WeddingDayGuideSerializer(data=data, context={'strict_validation': strict_validation})
            if serializer.is_valid():
                guide, created = WeddingDayGuide.objects.update_or_create(
                    contract=contract,
                    defaults=serializer.validated_data
                )

                # Mark the guide as submitted if strict_validation is True (i.e., the form was submitted)
                if strict_validation:
                    guide.submitted = True
                    guide.save()

                return Response(WeddingDayGuideSerializer(guide).data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Contract.DoesNotExist:
        return Response({"error": "Contract not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)