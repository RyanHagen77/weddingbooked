# documents/models.py

from django.db import models
from django.conf import settings
from contracts.models import Contract


class ContractAgreement(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='contract_agreements')
    version_number = models.IntegerField()
    photographer_choice = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    signature = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Fields to store service details at the time of saving
    photography_service = models.CharField(max_length=255, blank=True, null=True)
    videography_service = models.CharField(max_length=255, blank=True, null=True)
    dj_service = models.CharField(max_length=255, blank=True, null=True)
    photobooth_service = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Agreement for {self.contract} - Version {self.version_number}"


class RiderAgreement(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='rider_agreements')
    rider_type = models.CharField(max_length=50)
    signature = models.TextField()
    client_name = models.CharField(max_length=255, blank=True, null=True)
    agreement_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    rider_text = models.TextField(blank=True, null=True)  # Add this field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('contract', 'rider_type')

    def __str__(self):
        return f"{self.contract} - {self.rider_type}"


class ContractDocument(models.Model):
    contract = models.ForeignKey('contracts.Contract', related_name='documents', on_delete=models.CASCADE)
    document = models.FileField(upload_to='contract_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_client_visible = models.BooleanField(default=True,
                                            help_text="Check if this document should be visible to clients.")
    is_event_staff_visible = models.BooleanField(default=False,
                                                 help_text="Check if this document should be visible to event staff.")

    def __str__(self):
        return f"Document for {self.contract}"
