# contracts/management/commands/mark_contracts_complete.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from contracts.models import Contract


class Command(BaseCommand):
    help = 'Mark contracts as completed if their event date has passed and status is still BOOKED.'

    def handle(self, *args, **options):
        today = timezone.now().date()
        contracts_to_update = Contract.objects.filter(
            status=Contract.BOOKED,
            event_date__lt=today
        )

        count = contracts_to_update.update(status=Contract.COMPLETED)
        self.stdout.write(self.style.SUCCESS(f"{count} contract(s) marked as completed."))
