from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from .models import UnifiedCommunication
from contracts.models import Contract
from .forms import CommunicationForm  # Assuming you have a form for message input
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site


def post_contract_message(request, contract_id):
    contract = get_object_or_404(Contract, id=contract_id)

    if request.method == 'POST':
        form = CommunicationForm(request.POST)
        if form.is_valid():
            content_type = ContentType.objects.get_for_model(Contract)
            message = UnifiedCommunication.objects.create(
                content=form.cleaned_data['message'],
                note_type='contract',  # or determine type based on user role or form input
                created_by=request.user,
                content_type=content_type,
                object_id=contract.id
            )
            # Debugging: Print details about the message
            print(f"Message created: {message.content}, for contract ID: {contract.id}")

            # Call to send email to the assigned coordinator
            if send_contract_message_email(request, message, contract):
                print("Email sent successfully.")
            else:
                print("Failed to send email.")

            return redirect('client_portal', contract_id=contract.id)  # Redirect to the client portal page
        else:
            return render(request, 'post_contract_message.html', {'form': form, 'contract': contract})
    else:
        form = CommunicationForm()
        return render(request, 'post_contract_message.html', {'form': form, 'contract': contract})


def send_contract_message_email(request, message, contract):
    try:
        context = {
            'user': request.user,
            'message': message,
            'contract': contract,
            'domain': get_current_site(request).domain,
        }
        subject = f'New Message Posted for Contract {contract.id}'
        message_body = render_to_string('communication/contract_message_email.html', context, request=request)
        recipient_emails = [contract.assigned_coordinator.email] if contract.assigned_coordinator else [
            'fallback@example.com']

        send_mail(
            subject,
            message_body,
            'testmydjango420@gmail.com',  # Ensure this is a valid sender email address
            recipient_emails,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False


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
