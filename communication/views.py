# communication/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from contracts.models import Contract

from .forms import TaskForm  # Assuming you have a form for message input

from .utils import send_contract_message_email_to_coordinator, send_task_assignment_email

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import UnifiedCommunication, Task
from .serializers import UnifiedCommunicationSerializer

from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Case, When, BooleanField, Value
from django.utils import timezone



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contract_messages(request, contract_id):  # `request` parameter added here
    contract = get_object_or_404(Contract, contract_id=contract_id)
    messages = UnifiedCommunication.objects.filter(contract=contract,
                                                   note_type=UnifiedCommunication.PORTAL).order_by('-created_at')
    serializer = UnifiedCommunicationSerializer(messages, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_contract_message(request, contract_id):
    contract = get_object_or_404(Contract, contract_id=contract_id)
    content = request.data.get('content')

    if content:
        # Create the UnifiedCommunication object
        message = UnifiedCommunication.objects.create(
            content=content,
            note_type=UnifiedCommunication.PORTAL,
            created_by=request.user,
            contract=contract
        )

        # Send an email to the coordinator
        send_contract_message_email_to_coordinator(request, message, contract)

        # Automatically create a task for the coordinator
        if request.user.is_client:  # Use the is_client property
            print(f"Creating task for coordinator: {contract.coordinator}")
            create_task_for_coordinator(request.user, contract, message, content)
        else:
            print(f"User {request.user.username} is not a client. Task not created.")

        # Return the created message as a response
        serializer = UnifiedCommunicationSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response({'error': 'Content is required'}, status=status.HTTP_400_BAD_REQUEST)


@login_required
def send_portal_access(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    client = contract.client  # Accessing the client from the contract

    print(f"Processing contract {contract_id} for client {client.primary_contact}")
    print(f"User: {client.user}")
    print(f"User has usable password: {client.user.has_usable_password()}")

    # Extract the first name from primary_contact
    primary_contact = client.primary_contact
    first_name = primary_contact.split()[0] if primary_contact else "Valued Client"

    # Forcing email send regardless of has_usable_password() result
    if hasattr(client, 'user'):
        token = default_token_generator.make_token(client.user)
        uid = urlsafe_base64_encode(force_bytes(client.user.pk))
        password_reset_url = request.build_absolute_uri(
            reverse('users:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        )

        context = {
            'user': client.user,
            'first_name': first_name,
            'password_reset_url': password_reset_url,
            'domain': get_current_site(request).domain,
        }

        subject = 'Welcome to Essence Weddings!'
        message = render_to_string('communication/portal_access_email.html', context, request=request)

        try:
            send_mail(
                subject,
                message,
                'EssenceWeddings@enet2.com',  # Your sending email
                [client.user.email],
                fail_silently=False,
                html_message=message,  # Include HTML message
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



@login_required
def task_list(request):
    today = timezone.now().date()
    incomplete_tasks = Task.objects.filter(assigned_to=request.user, is_completed=False).annotate(
        is_overdue=Case(
            When(due_date__lt=today, then=Value(True)),
            default=Value(False),
            output_field=BooleanField()
        )
    ).order_by('-is_overdue', 'due_date')

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


@require_POST
@login_required
def create_task(request, contract_id=None, note_id=None):
    print(f"Received contract_id: {contract_id}, note_id: {note_id}")

    # Ensure `contract_id` and `note_id` are properly set
    contract_id = request.POST.get('contract', contract_id)
    note_id = request.POST.get('note', note_id)
    print(f"Final contract_id: {contract_id}, note_id: {note_id}")

    form = TaskForm(request.POST)
    if form.is_valid():
        task = form.save(commit=False)
        task.sender = request.user

        # Determine the task type
        task.task_type = 'contract' if contract_id else 'internal'

        # Assign contract if contract_id is provided
        if contract_id:
            task.contract = get_object_or_404(Contract, pk=contract_id)

        # Assign note if note_id is provided
        if note_id:
            task.note = get_object_or_404(UnifiedCommunication, pk=note_id)
            print(f"Assigned note: {task.note}")
        else:
            print("No note_id provided.")

        # Save the task
        task.save()

        # Optionally send email notifications
        if hasattr(task.assigned_to, 'email') and task.assigned_to.email:
            send_task_assignment_email(request, task)

        # Fetch task list
        tasks = Task.objects.filter(
            contract=task.contract if task.contract else None,
            task_type=task.task_type,
            is_completed=False
        ).distinct().order_by('due_date')

        # Render the appropriate task list HTML snippet
        task_list_template = 'contracts/partials/messages/_task_list_snippet.html' if task.task_type == 'contract' \
            else 'users/internal_task_list_snippet.html'
        task_list_html = render_to_string(task_list_template, {'tasks': tasks}, request=request)

        return JsonResponse({'success': True, 'task_id': task.id, 'task_list_html': task_list_html})
    else:
        print(f"Form errors: {form.errors}")
        return JsonResponse({'success': False, 'errors': form.errors.as_json()})


def create_task_for_coordinator(sender, contract, message, content):
    print("Creating task for coordinator automatically...")
    print(f"Sender: {sender}, Contract ID: {contract.contract_id}, Message ID: {message.id}, Content: {content}")

    if contract.coordinator:
        try:
            # Programmatically create the task
            task = Task.objects.create(
                sender=sender,
                assigned_to=contract.coordinator,
                contract=contract,
                note=message,
                due_date=now() + timedelta(days=3),  # Example: Due in 3 days
                description=f"Follow up on portal note: '{content[:50]}...'",
                # Use the first 50 characters of the content
                task_type='contract'
            )
            print(f"Task created successfully: {task}")
        except Exception as e:
            print(f"Error creating task: {e}")
    else:
        print("No coordinator assigned; task creation skipped.")


@login_required
def update_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    form = TaskForm(request.POST, instance=task)

    if form.is_valid():
        task = form.save(commit=False)
        task.sender = request.user

        # Update contract and note if provided in the form
        task.contract = form.cleaned_data.get('contract') or task.contract
        task.note = form.cleaned_data.get('note') or task.note

        task.save()

        # Specify the redirect URL to /communication/tasks/
        redirect_url = '/communication/tasks/'

        return JsonResponse({'success': True, 'redirect_url': redirect_url})
    else:
        return JsonResponse({'success': False, 'errors': form.errors.as_json()})


@login_required
def get_tasks(request, contract_id=None):
    if contract_id:
        tasks = Task.objects.filter(contract_id=contract_id, task_type='contract', is_completed=False).order_by('due_date')
    else:
        tasks = Task.objects.filter(assigned_to=request.user, task_type='internal', is_completed=False).order_by('due_date')

    task_list_html = render_to_string(
        'contracts/partials/messages/_task_list_snippet.html' if contract_id else 'users/internal_task_list_snippet.html',
        {'tasks': tasks},
        request=request
    )
    return JsonResponse({'task_list_html': task_list_html})


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
