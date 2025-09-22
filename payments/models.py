# payments/models.py

from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from contracts.models import Contract
import logging

logger = logging.getLogger(__name__)


class PaymentPurpose(models.Model):
    """Purpose of a payment (e.g., 'Deposit', 'Balance Payment')."""
    name = models.CharField(max_length=50, unique=True)   # ✅ prevent dupes like multiple 'Deposit'
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Payment(models.Model):
    """Actual money received against a contract."""
    PAYMENT_CHOICES = [
        ('CASH', 'Cash'),
        ('CHECK', 'Check'),
        ('ECHECK', 'ECheck'),
        ('CREDIT_CARD', 'Credit Card'),
        ('ZELLE', 'Zelle'),
        ('VENMO', 'Venmo'),
    ]

    contract = models.ForeignKey(Contract, related_name='payments', on_delete=models.CASCADE)
    # (optional) widen if your contracts can exceed 99,999.99:
    amount = models.DecimalField(max_digits=10, decimal_places=2,
                                 validators=[MinValueValidator(Decimal('0.01'))])
    payment_method = models.CharField(max_length=12, choices=PAYMENT_CHOICES, default='CASH')
    date = models.DateTimeField(auto_now_add=True)
    payment_reference = models.TextField(blank=True, null=True)
    memo = models.CharField(max_length=255, blank=True, null=True)
    modified_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                         null=True, verbose_name="Modified by")
    payment_purpose = models.ForeignKey(PaymentPurpose, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='payments')

    def save(self, *args, **kwargs):
        if self._state.adding and self.contract_id and self.amount is not None:
            # `balance_due` is a Python property; comparing in Python is fine
            if self.amount > self.contract.balance_due:
                raise ValueError('Payment cannot exceed balance due.')
        return super().save(*args, **kwargs)
    def __str__(self):
        return f'Payment {self.amount} on {self.date:%Y-%m-%d} ({self.get_payment_method_display()})'


class PaymentSchedule(models.Model):
    """Payment schedule attached to a single contract."""
    contract = models.OneToOneField(Contract, on_delete=models.CASCADE, related_name='payment_schedule')
    schedule_type = models.CharField(
        max_length=20,
        choices=[('schedule_a', 'Schedule A'), ('schedule_b', 'Schedule B'), ('custom', 'Custom')],  # ✅ include schedule_b if your views reference it
        default='schedule_a',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def payment_summary(self):
        payments = self.schedule_payments.all()
        total_due = sum(p.amount for p in payments)
        total_paid = sum(p.amount for p in payments if p.paid)
        return f"Due: {total_due}, Paid: {total_paid}"

    payment_summary.short_description = "Payment Summary"

    def __str__(self):
        return f'Schedule for {self.contract} ({self.schedule_type})'


class SchedulePayment(models.Model):
    """An individual scheduled payment (due date + amount), separate from actual receipts."""
    schedule = models.ForeignKey(PaymentSchedule, on_delete=models.CASCADE, related_name='schedule_payments')
    purpose = models.ForeignKey(PaymentPurpose, on_delete=models.SET_NULL, null=True, blank=True)
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)

    class Meta:
        ordering = ['due_date', 'id']
        indexes = [models.Index(fields=['schedule', 'paid', 'due_date'])]

    def __str__(self):
        label = self.purpose.name if self.purpose else 'Payment'
        return f'{label} - {self.amount} due on {self.due_date}'


class PaymentLink(models.Model):
    """
    Links a scheduled payment to one or more third-party checkout URLs.
    """
    payment = models.ForeignKey(SchedulePayment, on_delete=models.CASCADE, related_name='payment_links')
    label = models.CharField(max_length=120, blank=True)  # e.g., "Stripe", "Checkout 2"
    url = models.URLField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['payment', 'active', 'created_at'])]

    def __str__(self): return f'{self.label or "Link"} -> {self.url}'
