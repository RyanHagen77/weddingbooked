from rest_framework import serializers
from .models import Contract


class ContractSerializer(serializers.ModelSerializer):
    primary_contact = serializers.CharField(source='client.primary_contact', read_only=True)
    primary_email = serializers.EmailField(source='client.primary_email', read_only=True)
    primary_phone = serializers.CharField(source='client.primary_phone1', read_only=True)
    partner_contact = serializers.CharField(source='client.partner_contact', read_only=True)
    partner_email = serializers.EmailField(source='client.partner_email', read_only=True)
    partner_phone = serializers.CharField(source='client.partner_phone1', read_only=True)

    class Meta:
        model = Contract
        fields = [
            'event_date', 'primary_contact', 'primary_email', 'primary_phone',
            'partner_contact', 'partner_email', 'partner_phone', 'ceremony_site', 'reception_site',
            # Include any other fields you need from the Contract model
        ]
