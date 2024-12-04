#payments/models.py

from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from contracts.models import Contract
import logging

# Initialize logger
logger = logging.getLogger(__name__)


class PaymentPurpose(models.Model):
    """
    Represents the purpose of a payment.

    Attributes:
        name (str): The name of the payment purpose (e.g., "Deposit", "Balance Payment").
        description (str): Optional description of the payment purpose.
    """
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Payment(models.Model):
    """
    Tracks payments made towards a contract.

    Attributes:
        contract (ForeignKey): The associated contract for the payment.
        amount (DecimalField): The payment amount, must be greater than 0.01.
        payment_method (str): The method used for the payment (e.g., Cash, Check).
        date (DateTimeField): The date and time the payment was recorded.
        payment_reference (str): Optional reference information for the payment.
        memo (str): Optional memo for the payment.
        modified_by_user (ForeignKey): The user who modified or recorded the payment.
        payment_purpose (ForeignKey): The purpose of the payment (e.g., Deposit, Final Payment).
    """
    PAYMENT_CHOICES = [
        ('CASH', 'Cash'),
        ('CHECK', 'Check'),
        ('CREDIT_CARD', 'Credit Card'),
        ('ZELLE', 'Zelle'),
        ('VENMO', 'Venmo'),
    ]

    contract = models.ForeignKey('contracts.Contract', related_name='payments', on_delete=models.CASCADE)
    amount = models.DecimalField(
        max_digits=7, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    payment_method = models.CharField(max_length=12, choices=PAYMENT_CHOICES, default='CASH')
    date = models.DateTimeField(auto_now_add=True)
    payment_reference = models.TextField(blank=True, null=True)
    memo = models.CharField(max_length=255, blank=True, null=True)
    modified_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Modified by"
    )
    payment_purpose = models.ForeignKey(
        PaymentPurpose, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments'
    )

    def save(self, *args, **kwargs):
        """
        Custom save method to validate the payment amount.

        Raises:
            ValueError: If the payment amount exceeds the contract's balance due.
        """
        if self._state.adding:  # Check if the instance is being added (not updated)
            logger.debug(f"Adding new payment: {self.amount} for contract ID: {self.contract.contract_id}")
            if self.amount > self.contract.balance_due:
                logger.error(f"Payment amount {self.amount} exceeds balance due {self.contract.balance_due}")
                raise ValueError('Payment cannot exceed balance due.')
        super().save(*args, **kwargs)


class PaymentSchedule(models.Model):
    """
    Represents the payment schedule for a contract.

    Attributes:
        contract (OneToOneField): The associated contract for the schedule.
        schedule_type (str): The type of schedule (e.g., 'schedule_a', 'custom').
        created_at (DateTimeField): Timestamp when the schedule was created.
    """
    contract = models.OneToOneField(Contract, on_delete=models.CASCADE, related_name='payment_schedule')
    schedule_type = models.CharField(
        max_length=20, choices=[('schedule_a', 'Schedule A'), ('custom', 'Custom')]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def payment_summary(self):
        """
        Generates a summary of due and paid amounts for the schedule.

        Returns:
            str: A summary string in the format "Due: X, Paid: Y".
        """
        payments = self.schedule_payments.all()
        total_due = sum(payment.amount for payment in payments)
        total_paid = sum(payment.amount for payment in payments if payment.paid)
        return f"Due: {total_due}, Paid: {total_paid}"

    payment_summary.short_description = "Payment Summary"


class SchedulePayment(models.Model):
    """
    Represents an individual scheduled payment.

    Attributes:
        schedule (ForeignKey): The associated payment schedule.
        purpose (ForeignKey): The purpose of the scheduled payment.
        due_date (DateField): The date when the payment is due.
        amount (DecimalField): The amount due for the payment.
        paid (bool): Indicates if the payment has been made.
    """
    schedule = models.ForeignKey(PaymentSchedule, on_delete=models.CASCADE, related_name='schedule_payments')
    purpose = models.ForeignKey(PaymentPurpose, on_delete=models.SET_NULL, null=True, blank=True)
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.purpose} - {self.amount} due on {self.due_date}'
