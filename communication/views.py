from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.http import urlsafe_base64_encode, urlencode
from django.utils.encoding import force_bytes
from django.contrib.contenttypes.models import ContentType
from .models import UnifiedCommunication
from contracts.models import Contract
from .forms import CommunicationForm  # Assuming you have a form for message input
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Contract, UnifiedCommunication
from .serializers import UnifiedCommunicationSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contract_messages(request, contract_id):
    contract = get_object_or_404(Contract, contract_id=contract_id)
    messages = UnifiedCommunication.objects.filter(contract=contract, note_type=UnifiedCommunication.PORTAL).order_by('-created_at')
    serializer = UnifiedCommunicationSerializer(messages, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_contract_message(request, contract_id):
    contract = get_object_or_404(Contract, contract_id=contract_id)
    content = request.data.get('content')
    if content:
        message = UnifiedCommunication.objects.create(
            content=content,
            note_type=UnifiedCommunication.PORTAL,
            created_by=request.user,
            contract=contract
        )
        send_contract_message_email(request, message, contract)  # Call the email sending function
        serializer = UnifiedCommunicationSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({'error': 'Content is required'}, status=status.HTTP_400_BAD_REQUEST)

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
            'enetadmin@enet2.com',  # Use a valid sender email address
            [contract.coordinator.email],
            fail_silently=False,
        )
        print("Email sent to coordinator:", contract.coordinator.email)
    else:
        print("No coordinator assigned, or missing email.")

def send_task_assignment_email(request, task):
    # Assuming the role is stored in a related model or field called 'role'
    if task.assigned_to.role.name == 'ADMIN':  # Adjust this line based on how roles are implemented
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
            'enetadmin@enet2.com',  # Your sending email
            [task.assigned_to.email],
            fail_silently=False,
        )

@login_required
def send_portal_access(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    client = contract.client

    print(f"Processing contract {contract_id} for client {client.primary_contact}")
    print(f"User: {client.user}")
    print(f"User has usable password: {client.user.has_usable_password()}")

    # Forcing email send regardless of has_usable_password() result
    if hasattr(client, 'user'):
        token = default_token_generator.make_token(client.user)
        uid = urlsafe_base64_encode(force_bytes(client.user.pk))
        password_reset_url = request.build_absolute_uri(
            reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        )

        context = {
            'user': client.user,
            'password_reset_url': password_reset_url,
            'domain': get_current_site(request).domain,
        }

        subject = 'Portal Access'
        message = render_to_string('communication/portal_access_email.html', context, request=request)

        try:
            send_mail(
                subject,
                message,
                'enetadmin@enet2.com',  # Your sending email
                [client.user.email],
                fail_silently=False,
            )
            print("Email sent successfully")
            response_message = {'status': 'success', 'message': 'Portal access email sent successfully.'}
        except Exception as e:
            print(f"Error sending email: {e}")
            response_message = {'status': 'error', 'message': f'Error sending email: {e}'}
    else:
        response_message = {'status': 'error', 'message': 'Client user does not exist.'}
        print(response_message)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(response_message)
    else:
        print("Redirecting to contract detail page")
        return redirect('contracts:contract_detail', id=contract_id)


def send_contract_and_rider_email_to_client(request, contract, rider_type=None, only_contract=False):
    client_email = contract.client.primary_email

    if only_contract:
        agreement_url = reverse('contracts:client_contract_agreement', args=[contract.contract_id])
        subject = 'Sign Your Contract Agreement'
        message = f'Please sign your contract agreement at the following link: {agreement_url}'
    elif rider_type:
        agreement_url = reverse('contracts:client_rider_agreement', args=[contract.contract_id, rider_type])
        subject = f'Sign Your {rider_type.replace("_", " ").capitalize()} Agreement'
        message = f'Please sign your {rider_type.replace("_", " ").capitalize()} agreement at the following link: {agreement_url}'
    else:
        agreement_url = reverse('contracts:client_contract_and_rider_agreement', args=[contract.contract_id])
        subject = 'Sign Your Contract and Rider Agreements'
        message = f'Please sign your contract and rider agreements at the following link: {agreement_url}'

    login_url = f"http://{request.get_host()}{reverse('contracts:client_portal_login')}?{urlencode({'next': agreement_url})}"

    try:
        send_mail(
            subject,
            f"{message}\n\nPlease log in here to sign the documents: {login_url}",
            'enetadmin@enet2.com',  # Your sending email
            [client_email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send email to client: {e}")