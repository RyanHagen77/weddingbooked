# wedding_day_guide/serializers.py
from rest_framework import serializers
from .models import WeddingDayGuide
from contracts.models import Contract

class WeddingDayGuideSerializer(serializers.ModelSerializer):
    contract = serializers.PrimaryKeyRelatedField(queryset=Contract.objects.all())

    class Meta:
        model = WeddingDayGuide
        fields = '__all__'

    def validate(self, data):
        # Check if strict validation is needed
        strict_validation = self.context.get('strict_validation', False)
        print("Strict validation is:", strict_validation)
        print("Data received:", data)

        # List of fields that are required for submission
        required_fields = [
            'event_date', 'primary_contact', 'primary_email', 'primary_phone',
            'partner_contact', 'partner_email', 'partner_phone', 'dressing_location',
            'dressing_address', 'dressing_start_time', 'ceremony_site',
            'ceremony_address', 'ceremony_phone', 'ceremony_start', 'ceremony_end',
            'reception_site', 'reception_address', 'reception_phone',
            'reception_start', 'dinner_start', 'reception_end',
        ]

        if strict_validation:
            for field in required_fields:
                if not data.get(field):
                    print(f"Missing field: {field}")
                    raise serializers.ValidationError({field: f"{field.replace('_', ' ').capitalize()} is required."})

        return data