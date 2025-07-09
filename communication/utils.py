from django.apps import apps
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlencode
from django.http import HttpRequest
from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError


def send_password_reset_email(user_email):
    print(f"Starting to send password reset email to: {user_email}")

    User = get_user_model()
    try:
        user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        print("User with this email does not exist.")
        return

    name = user.client.primary_contact.split()[0] if hasattr(user, 'client') and user.client.primary_contact \
        else user.get_full_name() or "Valued User"

    form = PasswordResetForm({'email': user_email})
    if form.is_valid():
        request = HttpRequest()
        request.META['SERVER_NAME'] = 'https://weddingbooked.app'  # Use domain name here
        request.META['SERVER_PORT'] = '443'  # HTTPS default port

        try:
            form.save(
                request=request,
                use_https=True,
                from_email=settings.DEFAULT_FROM_EMAIL,
                email_template_name='communication/password_reset_email.txt',
                html_email_template_name='communication/password_reset_email.html',
                extra_email_context={'name': name},
            )
            print("Password reset email sent successfully.")
        except ImproperlyConfigured as e:
            print(f"Email backend not configured properly: {e}")
        except Exception as e:
            print(f"Failed to send password reset email: {e}")
    else:
        print("PasswordResetForm is invalid. Errors:", form.errors)


def send_contract_booked_email(contract):
    salesperson = contract.csr
    if not salesperson or not salesperson.email:
        print("No salesperson assigned or missing email.")
        return

    subject = f"Contract {contract.custom_contract_number} is now BOOKED!"

    html_content = render_to_string('communication/contract_booked_email.html', {
        'first_name': salesperson.first_name,
        'contract': contract,
        'domain': 'weddingbooked.app',
    })

    text_content = (f"Your client's contract ({contract.custom_contract_number}) "
                    f"is booked. View at https://weddingbooked.app/contracts/{contract.contract_id}/")

    email = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [salesperson.email])
    email.attach_alternative(html_content, "text/html")
    try:
        email.send()
        print(f"Email successfully sent to salesperson: {salesperson.email}")
    except Exception as e:
        print(f"Failed to send email to salesperson: {e}")


def send_contract_signed_email(contract):
    Task = apps.get_model('communication', 'Task')
    logo_url = f'{settings.MEDIA_URL}logo/Final_Logo.png'
    salesperson = contract.csr  # Assuming csr is the salesperson assigned to the contract
    if not salesperson or not salesperson.email:
        print("No salesperson assigned or missing email.")
        return

    # Calculate the due date (7 days after the contract signing)
    due_date = timezone.now() + timedelta(days=7)

    # Create the task for the salesperson
    task = Task(
        sender=salesperson,  # The sender is the salesperson
        assigned_to=salesperson,  # Task is assigned to the same salesperson
        contract=contract,
        due_date=due_date,
        description=f"Signature received for contract {contract.custom_contract_number}",
        task_type='contract',
    )

    try:
        task.full_clean()  # Validate the task instance
        task.save()
        print(f"Task created successfully for salesperson: {salesperson.email}")
    except ValidationError as e:
        print(f"Error creating task: {e}")

    # Email the salesperson
    subject = f"Contract {contract.custom_contract_number} is now SIGNED!"

    html_content = render_to_string('communication/contract_signed_email.html', {
        'first_name': salesperson.first_name,
        'contract': contract,
        'logo_url': logo_url,
        'domain': 'enet2.com',
    })

    text_content = (f"Your client's contract ({contract.custom_contract_number}) "
                    f"has been signed. View at https://enet2.com/contracts/{contract.contract_id}/")

    email = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [salesperson.email])
    email.attach_alternative(html_content, "text/html")

    try:
        email.send()
        print(f"Email successfully sent to salesperson: {salesperson.email}")
    except Exception as e:
        print(f"Failed to send email to salesperson: {e}")


def send_contract_message_email_to_coordinator(request, message, contract):
    coordinator = contract.coordinator
    if not coordinator or not coordinator.email:
        print("No coordinator assigned, or missing email.")
        return

    subject = f'New Message Posted for Contract {contract.custom_contract_number}'
    context = {
        'first_name': coordinator.first_name or "Coordinator",
        'user': request.user,
        'message': message,
        'contract': contract,
        'domain': get_current_site(request).domain,
    }

    text_content = render_to_string('communication/contract_message_email_to_coordinator.txt', context)
    html_content = render_to_string('communication/contract_message_email_to_coordinator.html', context)

    email = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [coordinator.email])
    email.attach_alternative(html_content, "text/html")

    try:
        email.send()
        print(f"Email sent to coordinator: {coordinator.email}")
    except Exception as e:
        print(f"Failed to send email to coordinator: {e}")


def send_contract_message_email_to_client(request, message, contract):
    client_user = contract.client.user
    if not client_user or client_user.user_type != 'client' or not client_user.email:
        print("Client does not have a valid email or user_type is not 'client'.")
        return

    first_name = contract.client.primary_contact.split()[0] if contract.client.primary_contact else "Client"
    subject = f'New Message from Your Coordinator for Contract {contract.custom_contract_number}'

    context = {
        'first_name': first_name,
        'user': request.user,
        'message': message,
        'contract': contract,
        'domain': 'enet2.com',
    }

    text_content = render_to_string('communication/contract_message_email_to_client.txt', context)
    html_content = render_to_string('communication/contract_message_email_to_client.html', context)

    email = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [client_user.email])
    email.attach_alternative(html_content, "text/html")
    try:
        email.send()
        print(f"Email successfully sent to client: {client_user.email}")
    except Exception as e:
        print(f"Failed to send email to client: {e}")


def send_contract_and_rider_email_to_client(request, contract, rider_type=None, only_contract=False):
    client_email = contract.client.primary_email
    if not client_email:
        print("No primary email for client.")
        return

    if only_contract:
        agreement_url = reverse('documents:client_contract_agreement', args=[contract.contract_id])
        subject = 'Sign Your Contract Agreement'
        agreement_type = 'contract agreement'
    elif rider_type:
        agreement_url = reverse('documents:client_rider_agreement', args=[contract.contract_id, rider_type])
        subject = f'Sign Your {rider_type.replace("_", " ").capitalize()} Agreement'
        agreement_type = f'{rider_type.replace("_", " ").capitalize()} agreement'
    else:
        agreement_url = reverse('documents:client_contract_and_rider_agreement', args=[contract.contract_id])
        subject = 'Sign Your Contract and Rider Agreements'
        agreement_type = 'contract and rider agreements'

    login_url = f"https://{request.get_host()}{reverse('users:client_portal_login')}?{urlencode({'next': agreement_url})}"
    inline_message = f"Please sign your {agreement_type} by clicking the button below."

    context = {
        'first_name': contract.client.primary_contact.split()[0] if contract.client.primary_contact else "Client",
        'inline_message': inline_message,
        'login_url': login_url,
    }

    text_content = render_to_string('communication/contract_and_rider_email_to_client.txt', context)
    html_content = render_to_string('communication/contract_and_rider_email_to_client.html', context)

    email = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [client_email])
    email.attach_alternative(html_content, "text/html")

    try:
        email.send()
        print("Contract/rider email sent to client.")
    except Exception as e:
        print(f"Failed to send email to client: {e}")


def send_task_assignment_email(request, task):
    if task.assigned_to.role.name != 'ADMIN':
        return

    context = {
        'user': task.assigned_to,
        'task': task,
        'domain': get_current_site(request).domain,
    }
    subject = 'New Task Assigned'

    text_content = render_to_string('communication/task_assignment_email.txt', context)
    html_content = render_to_string('communication/task_assignment_email.html', context)

    email = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [task.assigned_to.email])
    email.attach_alternative(html_content, "text/html")

    try:
        email.send()
        print(f"Task assignment email sent to {task.assigned_to.email}")
    except Exception as e:
        print("Error sending task assignment email:", e)


def send_booking_assignment_email(request, staff, contract, role, is_update=False):
    subject = 'Updated Booking Assignment' if is_update else 'New Booking Assigned'

    context = {
        'user': staff,
        'contract': contract,
        'role': role,
        'domain': get_current_site(request).domain,
        'is_update': is_update,
    }

    text_content = render_to_string('communication/booking_assignment_email.txt', context)
    html_content = render_to_string('communication/booking_assignment_email.html', context)

    email = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [staff.email])
    email.attach_alternative(html_content, "text/html")

    try:
        email.send()
        print(f"Booking assignment email sent to {staff.email}")
    except Exception as e:
        print(f"Error sending booking assignment email: {e}")
