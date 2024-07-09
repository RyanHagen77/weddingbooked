# communication/serializers.py

from rest_framework import serializers
from .models import UnifiedCommunication
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username']

class UnifiedCommunicationSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = UnifiedCommunication
        fields = ['id', 'content', 'created_at', 'created_by',]