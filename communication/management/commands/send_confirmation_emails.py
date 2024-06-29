import datetime
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils.timezone import now
from contracts.models import EventStaffBooking, Contract
from django.contrib.sites.models import Site

#class Command(BaseCommand):
    help = 'Send confirmation emails to event staff for weddings 10 days from today'

    def handle(self, *args, **kwargs):
        today = now().date()
        ten_days_from_now = today + datetime.timedelta(days=10)

        # Get contracts with events 10 days from today
        contracts = Contract.objects.filter(event_date=ten_days_from_now)

        for contract in contracts:
            bookings = EventStaffBooking.objects.filter(contract=contract)

            for booking in bookings:
                staff = booking.staff

                context = {
                    'user': staff,
                    'contract': contract,
                    'domain': Site.objects.get_current().domain,
                }
                subject = 'Confirmation Request for Upcoming Wedding'
                message = render_to_string('communication/confirmation_request_email.html', context)
                from_email = 'enetadmin@enet2.com'
                to_email = [staff.email]

                send_mail(
                    subject,
                    message,
                    from_email,
                    to_email,
                    fail_silently=False,
                )

        self.stdout.write(self.style.SUCCESS('Successfully sent confirmation emails to event staff.'))


#test command (working 5/15)
class Command(BaseCommand):
    help = 'Test cron job for sending confirmation emails'

    def handle(self, *args, **kwargs):
        with open('/home/egret/django_projects/weddingbook_project/cron_test.log', 'a') as f:
            f.write(f"Cron job ran at {datetime.datetime.now()}\n")

