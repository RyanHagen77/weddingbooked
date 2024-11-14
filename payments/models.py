
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from contracts.models import Contract


class PaymentPurpose(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Payment(models.Model):
    PAYMENT_CHOICES = [
        ('CASH', 'Cash'),
        ('CHECK', 'Check'),
        ('CREDIT_CARD', 'Credit Card'),
        ('ZELLE', 'Zelle'),
        ('VENMO', 'Venmo'),
    ]

    contract = models.ForeignKey('contracts.Contract', related_name='payments', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=7, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    payment_method = models.CharField(max_length=12, choices=PAYMENT_CHOICES, default='CASH')
    date = models.DateTimeField(auto_now_add=True)
    payment_reference = models.TextField(blank=True, null=True)
    memo = models.CharField(max_length=255, blank=True, null=True)
    modified_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Modified by")
    payment_purpose = models.ForeignKey(PaymentPurpose, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')

    def save(self, *args, **kwargs):
        if self._state.adding:  # Check if the instance is being added (not updated)
            total_cost = self.contract.total_cost
            amount_paid = self.contract.amount_paid
            if self.amount > (total_cost - amount_paid):
                raise ValueError('Payment cannot exceed balance due.')

        super().save(*args, **kwargs)


class PaymentSchedule(models.Model):
    contract = models.OneToOneField(Contract, on_delete=models.CASCADE, related_name='payment_schedule')
    schedule_type = models.CharField(max_length=20, choices=[('schedule_a', 'Schedule A'), ('custom', 'Custom')])
    created_at = models.DateTimeField(auto_now_add=True)

    def payment_summary(self):
        payments = self.schedule_payments.all()
        total_due = sum(payment.amount for payment in payments)
        total_paid = sum(payment.amount for payment in payments if payment.paid)
        return f"Due: {total_due}, Paid: {total_paid}"

    payment_summary.short_description = "Payment Summary"


class SchedulePayment(models.Model):
    schedule = models.ForeignKey(PaymentSchedule, on_delete=models.CASCADE, related_name='schedule_payments')
    purpose = models.ForeignKey(PaymentPurpose, on_delete=models.SET_NULL, null=True, blank=True)
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.purpose} - {self.amount} due on {self.due_date}'


