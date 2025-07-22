from rest_framework import serializers
from .models import WeddingDayGuide
from contracts.models import Contract


class WeddingDayGuideSerializer(serializers.ModelSerializer):
    contract = serializers.PrimaryKeyRelatedField(queryset=Contract.objects.all())

    # Optional fields explicitly marked
    dressing_location = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    dressing_address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    dressing_start_time = serializers.TimeField(required=False, allow_null=True)
    ceremony_site = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    ceremony_address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    ceremony_phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    ceremony_start = serializers.TimeField(required=False, allow_null=True)
    ceremony_end = serializers.TimeField(required=False, allow_null=True)
    reception_site = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    reception_address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    reception_phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    reception_start = serializers.TimeField(required=False, allow_null=True)
    dinner_start = serializers.TimeField(required=False, allow_null=True)
    reception_end = serializers.TimeField(required=False, allow_null=True)
    video_arrival_time = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    video_arrival_location = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    video_client_names = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    wedding_story_song_title = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    wedding_story_song_artist = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    dance_montage_song_title = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    dance_montage_song_artist = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    video_special_dances = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    photo_booth_text_line1 = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    photo_booth_text_line2 = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    photo_booth_end_time = serializers.TimeField(required=False, allow_null=True)
    photo_booth_placement = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = WeddingDayGuide
        fields = [
            'contract',
            'event_date',
            'primary_contact',
            'primary_email',
            'primary_phone',
            'partner_contact',
            'partner_email',
            'partner_phone',
            'dressing_location',
            'dressing_address',
            'dressing_start_time',
            'ceremony_site',
            'ceremony_address',
            'ceremony_phone',
            'ceremony_start',
            'ceremony_end',
            'reception_site',
            'reception_address',
            'reception_phone',
            'reception_start',
            'dinner_start',
            'reception_end',
            'video_arrival_time',
            'video_arrival_location',
            'video_client_names',
            'wedding_story_song_title',
            'wedding_story_song_artist',
            'dance_montage_song_title',
            'dance_montage_song_artist',
            'video_special_dances',
            'photo_booth_text_line1',
            'photo_booth_text_line2',
            'photo_booth_end_time',
            'photo_booth_placement',
        ]

    def validate(self, data):
        print(">>> VALIDATING DATA:", data)
        print(">>> ceremony_address present?:", "ceremony_address" in data)
        print(">>> value:", repr(data.get("ceremony_address")))

        strict_validation = self.context.get('strict_validation', False)

        if strict_validation:
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
                value = data.get(field)
                if value is None or (isinstance(value, str) and not value.strip()):
                    raise serializers.ValidationError({
                        field: f"{field.replace('_', ' ').capitalize()} is required."
                    })

        return data
