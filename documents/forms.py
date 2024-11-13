
from django import forms
from .models import ContractAgreement, ContractDocument, RiderAgreement

class ContractDocumentForm(forms.ModelForm):
    is_client_visible = forms.BooleanField(
        initial=False,
        required=False,
        widget=forms.CheckboxInput(attrs={'style': 'font-size: 11pt;'})
    )
    is_event_staff_visible = forms.BooleanField(
        initial=False,
        required=False,
        widget=forms.CheckboxInput(attrs={'style': 'font-size: 11pt;'})
    )

    class Meta:
        model = ContractDocument
        fields = ['document', 'is_client_visible', 'is_event_staff_visible']


class ContractAgreementForm(forms.ModelForm):
    main_signature = forms.CharField(widget=forms.HiddenInput(), required=True)

    class Meta:
        model = ContractAgreement
        fields = ['main_signature', 'photographer_choice']


class RiderAgreementForm(forms.ModelForm):
    signature = forms.CharField(widget=forms.HiddenInput(), required=True)

    class Meta:
        model = RiderAgreement
        fields = ['signature', 'client_name', 'agreement_date', 'notes']