from django import forms
from .models import WeddingDayGuide
from django.forms import TimeInput

time_widget = TimeInput(format='%I:%M %p', attrs={'class': 'form-control'})


class WeddingDayGuideForm(forms.ModelForm):
    time_widget = TimeInput(
        format='%H:%M',  # Use 24-hour format to match what HTML expects
        attrs={'type': 'time', 'class': 'form-control'}
    )

    class Meta:
        model = WeddingDayGuide
        fields = '__all__'
        widgets = {
            'dressing_start_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'form-control'}),
            'ceremony_start': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'form-control'}),
            'ceremony_end': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'form-control'}),
            'reception_start': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'form-control'}),
            'reception_end': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'form-control'}),
            'dinner_start': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'form-control'}),
            'photographer2_start': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'form-control'}),
            'video_arrival_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'form-control'}),
            'photo_booth_end_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'form-control'}),

        }

    def __init__(self, *args, **kwargs):
        self.strict_validation = kwargs.pop('strict_validation', False)
        contract = kwargs.pop('contract', None)
        super().__init__(*args, **kwargs)

        # Ensure Django can parse 12-hour time input
        time_fields = [
            'dressing_start_time', 'ceremony_start', 'ceremony_end',
            'reception_start', 'reception_end', 'dinner_start', 'photographer2_start',
            'video_arrival_time', 'photo_booth_end_time'
        ]
        for field in time_fields:
            self.fields[field].input_formats = ['%I:%M %p']

        # Prepopulate fields from contract
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

        for field in self.fields:
            self.fields[field].required = False

        if self.strict_validation:
            required_fields = [
                'event_date',
                'primary_contact',
                'primary_email',
                'primary_phone',
                'partner_contact',
                'partner_email',
                'partner_phone',
            ]
            for field in required_fields:
                self.fields[field].required = True

    def clean(self):
        cleaned_data = super().clean()
        if self.strict_validation:
            required_fields = [
                'event_date', 'primary_contact', 'primary_email', 'primary_phone',
                'partner_contact', 'partner_email', 'partner_phone',
            ]
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, f"{field.replace('_', ' ').title()} is required.")
        return cleaned_data
