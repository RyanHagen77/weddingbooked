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
            # Add other widgets as needed
        }

    def __init__(self, *args, **kwargs):
        self.strict_validation = kwargs.pop('strict_validation', False)  # Default to relaxed validation
        super().__init__(*args, **kwargs)

        # All fields optional by default
        for field in self.fields.values():
            field.required = False

        if self.strict_validation:
            # Enforce stricter validation only for submission
            required_fields = [
                'event_date', 'primary_contact', 'primary_email', 'primary_phone',
                'partner_contact', 'partner_email', 'partner_phone', 'dressing_location',
                'dressing_address', 'dressing_start_time', 'ceremony_site',
                'ceremony_address', 'ceremony_phone', 'ceremony_start', 'ceremony_end',
                'reception_site', 'reception_address', 'reception_phone',
                'reception_start', 'dinner_start', 'reception_end'
            ]
            for field_name in required_fields:
                if field_name in self.fields:
                    self.fields[field_name].required = True

    def clean(self):
        cleaned_data = super().clean()

        # Enforce stricter validation if strict_validation is True
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
                    self.add_error(field, f"{field.replace('_', ' ').title()} is required for submission.")

        return cleaned_data
