# wedding_day_guide/forms.py
from django import forms
from .models import WeddingDayGuide

class WeddingDayGuideForm(forms.ModelForm):
    class Meta:
        model = WeddingDayGuide
        fields = '__all__'  # Include all fields

    def __init__(self, *args, **kwargs):
        self.strict_validation = kwargs.pop('strict_validation', False)
        contract = kwargs.pop('contract', None)  # Accept the `contract` argument
        super().__init__(*args, **kwargs)

        # If a contract is provided, prepopulate fields
        if contract:
            self.fields['event_date'].initial = contract.event_date
            self.fields['primary_contact'].initial = contract.client.primary_contact
            self.fields['primary_email'].initial = contract.client.primary_email
            self.fields['primary_phone'].initial = contract.client.primary_phone1
            self.fields['partner_contact'].initial = contract.client.partner_contact
            self.fields['partner_email'].initial = contract.client.partner_email
            self.fields['partner_phone'].initial = contract.client.partner_phone1
            self.fields['ceremony_site'].initial = contract.ceremony_site
            self.fields['reception_site'].initial = contract.reception_site

        # Set required fields based on strict_validation
        for field in self.fields:
            self.fields[field].required = False

        if self.strict_validation:
            required_fields = [
                'event_date', 'primary_contact', 'primary_email', 'primary_phone',
                'partner_contact', 'partner_email', 'partner_phone', 'dressing_location',
                'dressing_start_time', 'ceremony_site', 'ceremony_start', 'ceremony_end',
                'reception_site', 'reception_start', 'reception_end'
            ]
            for field in required_fields:
                self.fields[field].required = True

    def clean(self):
        cleaned_data = super().clean()
        if self.strict_validation:
            required_fields = [
                'event_date', 'primary_contact', 'primary_email', 'primary_phone',
                'partner_contact', 'partner_email', 'partner_phone', 'dressing_location',
                'dressing_start_time', 'ceremony_site', 'ceremony_start', 'ceremony_end',
                'reception_site', 'reception_start', 'reception_end'
            ]
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, f"{field.replace('_', ' ').title()} is required.")
        return cleaned_data
