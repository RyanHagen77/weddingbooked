# contracts/views.py
from django.shortcuts import render, get_object_or_404, redirect
from users.models import CustomUser  # Import CustomUser
from django.db.models import Q, Sum
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.urls import reverse

from bookings.models import EventStaffBooking
from bookings.forms import EventStaffBookingForm
from communication.models import UnifiedCommunication, Task
from communication.views import send_contract_message_email, send_email_to_client
from documents.forms import ContractDocumentForm
from documents.models import ContractAgreement, RiderAgreement
from .forms import (ContractSearchForm, ClientForm, NewContractForm, ContractForm, ContractInfoEditForm,
                    ContractClientEditForm, ContractEventEditForm, ContractServicesForm,
                    ContractProductFormset, PaymentForm, PaymentScheduleForm,
                    SchedulePaymentFormSet, ServiceFeeFormSet, ServiceFeeForm)
from communication.forms import CommunicationForm, TaskForm  # Importing from the communication app
from .models import (Client, Contract, ServiceType, Payment, Package,
                     AdditionalEventStaffOption, EngagementSessionOption, Discount, ContractOvertime, AdditionalProduct,
                     OvertimeOption, PaymentPurpose, PaymentSchedule, SchedulePayment,
                     TaxRate, ChangeLog, ServiceFee)

from wedding_day_guide.models import WeddingDayGuide
from django.db import transaction
from django.views.decorators.http import require_POST
from django.contrib import messages
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, login

from .serializers import ContractSerializer
from datetime import timedelta
import json

from django.utils.timezone import now
from django.http import JsonResponse
import logging
from django.contrib.auth.forms import PasswordResetForm
from django.http import HttpRequest, HttpResponseRedirect
from django.contrib.auth import logout
from collections import defaultdict

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
        note_type=UnifiedCommunication.PORTAL
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
                note_type=UnifiedCommunication.PORTAL,
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



