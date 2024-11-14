from django import forms
from django.forms import inlineformset_factory
from .models import Payment, PaymentSchedule, SchedulePayment


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'payment_purpose', 'payment_reference', 'memo']  # Adjust as per your actual model fields

        # Set required=False for fields that are not mandatory
        widgets = {
            'amount': forms.NumberInput(attrs={'required': False}),
            'payment_method': forms.Select(attrs={'required': False}),
            # Include other fields as needed
        }
class PaymentScheduleForm(forms.ModelForm):
    class Meta:
        model = PaymentSchedule
        fields = ['schedule_type']

class SchedulePaymentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SchedulePaymentForm, self).__init__(*args, **kwargs)
        # Add 'payment-form' class to each field's widget
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'payment-form'

    class Meta:
        model = SchedulePayment
        fields = ('purpose', 'due_date', 'amount')
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'payment-form'}),
        }

SchedulePaymentFormSet = inlineformset_factory(
    PaymentSchedule,
    SchedulePayment,
    form=SchedulePaymentForm,  # Use the custom form
    extra=0,
    can_delete=True
)
