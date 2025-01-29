from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from payments.models import Payment


@receiver(post_save, sender=Payment)
def update_contract_status_on_payment(sender, instance, created, **kwargs):
    """Automatically update contract status to BOOKED if a payment is made."""

    if created:  # Ensure it only runs when a new payment is created
        contract = instance.contract  # Get the related contract

        if contract and contract.status not in [contract.BOOKED, contract.COMPLETED]:
            # Change 'amount_paid' to 'amount'
            has_payment = contract.payments.filter(amount__gt=Decimal("0.00")).exists()

            if has_payment:
                print(f"✅ Updating contract {contract.contract_id} status to BOOKED due to payment.")
                contract.status = contract.BOOKED
                contract.save(update_fields=['status'])  # Save only the status field
