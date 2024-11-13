# communication/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.http import urlsafe_base64_encode, urlencode
from django.utils.encoding import force_bytes
from contracts.models import Contract
from .forms import TaskForm  # Assuming you have a form for message input
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import UnifiedCommunication, Task
from bookings.models import EventStaffBooking
from .serializers import UnifiedCommunicationSerializer
from django.contrib.contenttypes.models import ContentType


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contract_messages(request, contract_id):  # `request` parameter added here
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




def booking_notes(request, booking_id):
    booking = get_object_or_404(EventStaffBooking, id=booking_id)
    notes = Note.objects.filter(booking=booking)
    print("Notes for booking:", booking_id, "->", notes)  # Debug output to check notes
    return render(request, 'communication/booking_notes.html', {'object': booking, 'notes': notes})


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
        agreement_url = reverse('documents:client_contract_agreement', args=[contract.contract_id])
        subject = 'Sign Your Contract Agreement'
        message = f'Please sign your contract agreement at the following link: {agreement_url}'
    elif rider_type:
        agreement_url = reverse('documents:client_rider_agreement', args=[contract.contract_id, rider_type])
        subject = f'Sign Your {rider_type.replace("_", " ").capitalize()} Agreement'
        message = f'Please sign your {rider_type.replace("_", " ").capitalize()} agreement at the following link: {agreement_url}'
    else:
        agreement_url = reverse('documents:client_contract_and_rider_agreement', args=[contract.contract_id])
        subject = 'Sign Your Contract and Rider Agreements'
        message = f'Please sign your contract and rider agreements at the following link: {agreement_url}'

    login_url = f"https://{request.get_host()}{reverse('contracts:client_portal_login')}?{urlencode({'next': agreement_url})}"

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


@login_required
def task_list(request):
    # Fetch both completed and incomplete tasks
    incomplete_tasks = Task.objects.filter(assigned_to=request.user, is_completed=False).order_by('due_date')
    completed_tasks = Task.objects.filter(assigned_to=request.user, is_completed=True).order_by('due_date')

    task_form = TaskForm()
    logo_url = f"https://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    return render(request, 'users/task_list.html', {
        'incomplete_tasks': incomplete_tasks,
        'completed_tasks': completed_tasks,
        'task_form': task_form,
        'logo_url': logo_url
    })

@login_required
def open_task_form(request, contract_id=None, note_id=None):
    initial_data = {
        'sender': request.user.id,
        'contract': contract_id,
        'note': note_id,
    }
    form = TaskForm(initial=initial_data)
    return render(request, 'task_form.html', {'form': form})

@login_required
@require_POST
def create_internal_task(request):
    form = TaskForm(request.POST)
    if form.is_valid():
        task = form.save(commit=False)
        task.sender = request.user
        task.task_type = 'internal'
        task.save()

        if hasattr(task.assigned_to, 'email') and task.assigned_to.email:
            send_task_assignment_email(request, task)

        incomplete_tasks = Task.objects.filter(
            assigned_to=request.user, task_type='internal', is_completed=False
        ).order_by('due_date')

        completed_tasks = Task.objects.filter(
            assigned_to=request.user, task_type='internal', is_completed=True
        ).order_by('due_date')

        task_list_html = render_to_string(
            'users/internal_task_list_snippet.html',
            {'incomplete_tasks': incomplete_tasks, 'completed_tasks': completed_tasks},
            request=request
        )
        return JsonResponse({'success': True, 'task_id': task.id, 'task_list_html': task_list_html})
    else:
        return JsonResponse({'success': False, 'errors': form.errors.as_json()})

@login_required
def get_internal_tasks(request):
    tasks = Task.objects.filter(
        assigned_to=request.user, type='internal', is_completed=False
    ).order_by('due_date')
    task_list_html = render_to_string('users/internal_task_list_snippet.html', {'tasks': tasks}, request=request)
    return JsonResponse({'task_list_html': task_list_html})

@require_POST
@login_required
def create_contract_task(request, contract_id=None, note_id=None):
    form = TaskForm(request.POST)
    if form.is_valid():
        task = form.save(commit=False)
        task.sender = request.user
        task.task_type = 'contract'

        if contract_id:
            task.contract = get_object_or_404(Contract, id=contract_id)
        if note_id:
            task.note = get_object_or_404(UnifiedCommunication, id=note_id)

        task.save()

        if hasattr(task.assigned_to, 'email') and task.assigned_to.email:
            send_task_assignment_email(request, task)

        tasks = Task.objects.filter(
            contract=task.contract, task_type='contract', is_completed=False
        ).distinct().order_by('due_date')

        task_list_html = render_to_string('contracts/task_list_snippet.html', {'tasks': tasks}, request=request)
        return JsonResponse({'success': True, 'task_id': task.id, 'task_list_html': task_list_html})
    else:
        return JsonResponse({'success': False, 'errors': form.errors.as_json()})

@login_required
def get_contract_tasks(request, contract_id):
    tasks = Task.objects.filter(
        assigned_to=request.user, contract_id=contract_id, task_type='contract', is_completed=False
    ).order_by('due_date')
    task_list_html = render_to_string('contracts/internal_task_list_snippet.html', {'tasks': tasks}, request=request)
    return JsonResponse({'task_list_html': task_list_html})

@login_required
@require_POST
def update_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    form = TaskForm(request.POST, instance=task)

    if form.is_valid():
        task = form.save(commit=False)
        task.sender = request.user  # Set the sender explicitly

        # Ensure contract and note fields are set if they exist in the form data
        task.contract = form.cleaned_data.get('contract') or task.contract
        task.note = form.cleaned_data.get('note') or task.note
        task.task_type = form.cleaned_data.get('task_type') or task.task_type

        task.save()

        # Return the updated task list HTML if needed
        task_list_html = render_to_string('users/internal_task_list_snippet.html', {
            'incomplete_tasks': Task.objects.filter(assigned_to=request.user, is_completed=False).order_by('due_date'),
            'completed_tasks': Task.objects.filter(assigned_to=request.user, is_completed=True).order_by('due_date'),
        }, request=request)

        return JsonResponse({'success': True, 'task_list_html': task_list_html})
    else:
        return JsonResponse({'success': False, 'errors': form.errors.as_json()})


@login_required
@require_POST
def mark_complete(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    task.is_completed = not task.is_completed
    task.save()

    incomplete_tasks = Task.objects.filter(assigned_to=request.user, is_completed=False).order_by('due_date')
    completed_tasks = Task.objects.filter(assigned_to=request.user, is_completed=True).order_by('due_date')
    task_list_html = render_to_string('users/internal_task_list_snippet.html', {
        'incomplete_tasks': incomplete_tasks,
        'completed_tasks': completed_tasks
    }, request=request)

    return JsonResponse({'success': True, 'task_list_html': task_list_html})