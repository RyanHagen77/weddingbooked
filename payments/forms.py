import logging
from django import forms
from django.forms import inlineformset_factory
from .models import Payment, PaymentSchedule, SchedulePayment

# Set up logging
logger = logging.getLogger(__name__)

class PaymentForm(forms.ModelForm):
    """
    Form for handling individual payments related to a contract.

    Fields:
        - amount: The payment amount.
        - payment_method: The method used for the payment (e.g., cash, credit card).
        - payment_purpose: The purpose of the payment (e.g., deposit, balance payment).
        - payment_reference: Reference details (e.g., check number or transaction ID).
        - memo: Additional notes about the payment.

    Widgets:
        - amount: NumberInput for numeric input with no 'required' validation on the form level.
        - payment_method: Select dropdown for choosing the payment method.
    """

    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'payment_purpose', 'payment_reference', 'memo']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'payment_purpose': forms.Select(attrs={'class': 'form-select'}),
            'payment_reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter reference'}),
            'memo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add any notes'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Custom initialization for the PaymentForm.
        Logs the initialization process and ensures all fields are styled consistently.
        """
        super().__init__(*args, **kwargs)
        logger.debug("Initializing PaymentForm with data: %s", self.initial)

        # Add consistent styling to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')


class PaymentScheduleForm(forms.ModelForm):
    """
    Form for handling the overall payment schedule for a contract.

    Fields:
        - schedule_type: The type of payment schedule (e.g., Schedule A, custom).
    """

    class Meta:
        model = PaymentSchedule
        fields = ['schedule_type']
        widgets = {
            'schedule_type': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Custom initialization for the PaymentScheduleForm.
        Logs the schedule type being processed.
        """
        super().__init__(*args, **kwargs)
        logger.debug("Initializing PaymentScheduleForm with data: %s", self.initial)


class SchedulePaymentForm(forms.ModelForm):
    """
    Form for handling individual scheduled payments within a payment schedule.

    Fields:
        - purpose: The purpose of the scheduled payment.
        - due_date: The date by which the payment is due.
        - amount: The amount of the scheduled payment.

    Widgets:
        - due_date: A date input styled with a custom class for better UI integration.
    """

    class Meta:
        model = SchedulePayment
        fields = ['purpose', 'due_date', 'amount']
        widgets = {
            'purpose': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Custom initialization for the SchedulePaymentForm.
        Logs the initialization process and applies a consistent style to all fields.
        """
        super().__init__(*args, **kwargs)
        logger.debug("Initializing SchedulePaymentForm with data: %s", self.initial)

        # Add consistent styling to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')


# Inline formset for managing multiple schedule payments within a payment schedule
SchedulePaymentFormSet = inlineformset_factory(
    PaymentSchedule,
    SchedulePayment,
    form=SchedulePaymentForm,  # Use the custom SchedulePaymentForm
    extra=0,  # Do not provide extra blank forms by default
    can_delete=True  # Allow deleting schedule payments
)

logger.debug("SchedulePaymentFormSet successfully initialized.")
