# payments/serializers.py
from rest_framework import serializers
from .models import PaymentLink

class PaymentLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentLink
        fields = ('id', 'label', 'url', 'active', 'created_at')

class PaymentLinkWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentLink
        fields = ('label', 'url', 'active')
