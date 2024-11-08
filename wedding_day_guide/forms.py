# wedding_day_guide/forms.py
from django import forms
from .models import WeddingDayGuide

class WeddingDayGuideForm(forms.ModelForm):
    class Meta:
        model = WeddingDayGuide
        fields = [
            'event_date', 'primary_contact', 'primary_email', 'primary_phone',
            'partner_contact', 'partner_email', 'partner_phone', 'dressing_location',
            'dressing_address', 'dressing_start_time', 'ceremony_site',
            'ceremony_address', 'ceremony_phone', 'ceremony_start', 'ceremony_end',
            'reception_site', 'reception_address', 'reception_phone',
            'reception_start', 'dinner_start', 'reception_end', 'staff_table', 'photo_stop1',
            'photo_stop2', 'photo_stop3', 'photo_stop4', 'photographer2_start_location',
            'photographer2_start_location_address', 'photographer2_start', 'p1_attendant_of_honor',
            'p1_attendant_qty', 'flower_attendant_qty', 'usher_qty', 'p2_attendant_of_honor',
            'p2_attendant_qty', 'ring_bearer_qty', 'p1_parent_names',
            'p1_sibling_names', 'p1_grandparent_names', 'p2_parent_names',
            'p2_sibling_names', 'p2_grandparent_names',
            'additional_photo_request1', 'additional_photo_request2',
            'additional_photo_request3', 'additional_photo_request4',
            'additional_photo_request5', 'video_client_names', 'wedding_story_song_title',
            'wedding_story_song_artist', 'dance_montage_song_title', 'dance_montage_song_artist',
            'video_special_dances', 'photo_booth_text_line1', 'photo_booth_text_line2', 'photo_booth_placement'
        ]
        widgets = {
            'event_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
            'dressing_start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm'}),
            'ceremony_start': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm'}),
            'ceremony_end': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm'}),
            'reception_start': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm'}),
            'dinner_start': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm'}),
            'reception_end': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm'}),
            'p1_parent_names': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'p1_sibling_names': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'p1_grandparent_names': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'p2_parent_names': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'p2_sibling_names': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'p2_grandparent_names': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'primary_contact': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'primary_email': forms.EmailInput(attrs={'class': 'form-control form-control-sm'}),
            'primary_phone': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'partner_contact': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'partner_email': forms.EmailInput(attrs={'class': 'form-control form-control-sm'}),
            'partner_phone': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'dressing_location': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'dressing_address': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'ceremony_site': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'ceremony_address': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'ceremony_phone': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'reception_site': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'reception_address': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'reception_phone': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'photo_stop1': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'photo_stop2': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'photo_stop3': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'photo_stop4': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'photographer2_start_location': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'photographer2_start_location_address': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'photographer2_start': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm'}),            'p1_attendant_of_honor': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'p1_attendant_qty': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'flower_attendant_qty': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'usher_qty': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'p2_attendant_of_honor': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'p2_attendant_qty': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'ring_bearer_qty': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'additional_photo_request1': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'additional_photo_request2': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'additional_photo_request3': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'additional_photo_request4': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'additional_photo_request5': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'video_client_names': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'wedding_story_song_title': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'wedding_story_song_artist': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'dance_montage_song_title': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'dance_montage_song_artist': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'video_special_dances': forms.Textarea(attrs={'class': 'form-control form-control-sm'}),
            'photo_booth_text_line1': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'photo_booth_text_line2': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'photo_booth_placement': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }

    def __init__(self, *args, **kwargs):
        self.strict_validation = kwargs.pop('strict_validation', True)
        contract = kwargs.pop('contract', None)
        super().__init__(*args, **kwargs)
        if contract:
            client = contract.client
            self.fields['event_date'].initial = contract.event_date
            self.fields['primary_contact'].initial = client.primary_contact
            self.fields['primary_email'].initial = client.primary_email
            self.fields['primary_phone'].initial = client.primary_phone1
            self.fields['partner_contact'].initial = client.partner_contact
            self.fields['partner_email'].initial = client.partner_email
            self.fields['partner_phone'].initial = client.partner_phone1
            self.fields['ceremony_site'].initial = contract.ceremony_site
            self.fields['reception_site'].initial = contract.reception_site

        # Only require specific fields
        required_fields = [
            'event_date', 'primary_contact', 'primary_email', 'primary_phone',
            'partner_contact', 'partner_email', 'partner_phone', 'dressing_location',
            'dressing_address', 'dressing_start_time', 'ceremony_site',
            'ceremony_address', 'ceremony_phone', 'ceremony_start', 'ceremony_end',
            'reception_site', 'reception_address', 'reception_phone',
            'reception_start', 'dinner_start', 'reception_end'
        ]

        for field in required_fields:
            self.fields[field].required = True

        for field in self.fields:
            if field not in required_fields:
                self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        if self.strict_validation:
            required_fields = [
                'event_date', 'primary_contact', 'primary_email', 'primary_phone',
                'partner_contact', 'partner_email', 'partner_phone', 'dressing_location',
                'dressing_address', 'dressing_start_time', 'ceremony_site',
                'ceremony_address', 'ceremony_phone', 'ceremony_start', 'ceremony_end',
                'reception_site', 'reception_address', 'reception_phone',
                'reception_start', 'dinner_start', 'reception_end'
            ]
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, f"{field.replace('_', ' ').title()} is required.")
        return cleaned_data