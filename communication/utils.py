from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def send_contract_booked_email(contract):
    """Send an email notification to the salesperson when a contract is booked."""

    # Ensure the contract has a salesperson
    salesperson = contract.csr
    if not salesperson or not salesperson.email:
        print("No salesperson assigned or missing email.")
        return

    subject = f"Contract {contract.custom_contract_number} is now BOOKED!"

    # Render email content
    message_body = render_to_string('communication/contract_booked_email.html', {
        'first_name': salesperson.first_name,
        'contract': contract,
        'domain': 'enet2.com',
    })

    try:
        send_mail(
            subject,
            message_body,
            settings.DEFAULT_FROM_EMAIL,  # Set this in settings.py
            [salesperson.email],  # Send to salesperson
            fail_silently=False,
        )
        print(f"Email successfully sent to salesperson: {salesperson.email}")
    except Exception as e:
        print(f"Failed to send email to salesperson: {e}")
