#services/models.py

from django.db import models
from django.conf import settings
from ckeditor.fields import RichTextField

from bookings.constants import SERVICE_ROLE_MAPPING  # Adjust the import path as needed

ROLE_CHOICES = [(key, value) for key, value in SERVICE_ROLE_MAPPING.items()]

class ServiceType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Package(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True, verbose_name="Active")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    deposit = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Deposit Amount")
    service_type = models.ForeignKey('ServiceType', on_delete=models.CASCADE, null=True, blank=True, related_name='packages')
    hours = models.IntegerField(verbose_name="Hours", default=0)
    default_text = RichTextField(blank=True, help_text="Default text for the package")
    rider_text = RichTextField(blank=True, help_text="Rider text for the package")
    package_notes = models.TextField(blank=True, help_text="Additional notes for the package")

    def __str__(self):
        return f"{self.name} - {self.service_type.name if self.service_type else 'No Type'}"



class AdditionalEventStaffOption(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True, verbose_name="Active")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    deposit = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Deposit Amount")
    service_type = models.ForeignKey('ServiceType', on_delete=models.CASCADE, null=True, blank=True, related_name='event_staff_options')
    hours = models.IntegerField(verbose_name="Hours", default=0)
    default_text = RichTextField(blank=True, help_text="Default text for the additional option")
    rider_text = RichTextField(blank=True, help_text="Rider text for the additional option")
    package_notes = models.TextField(blank=True, help_text="Additional notes for the staff option")

    def __str__(self):
        # Updated to reflect the relationship with ServiceType
        return f"{self.name} ({self.service_type.name if self.service_type else 'No Type'})"

class EngagementSessionOption(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True, verbose_name="Active")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    deposit = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Deposit Amount")
    default_text = RichTextField(blank=True, help_text="Default text for the engagement session")
    rider_text = RichTextField(blank=True, help_text="Rider text for engagement session")
    package_notes = models.TextField(blank=True, help_text="Additional notes for the package")
    service_type = models.ForeignKey('ServiceType', on_delete=models.CASCADE, null=True, blank=True, related_name='engagement_session_options')


    def __str__(self):
        return self.name


class OvertimeOption(models.Model):
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    name = models.CharField(max_length=100)  # For dropdown display
    is_active = models.BooleanField(default=True, verbose_name="Active")
    rate_per_hour = models.DecimalField(max_digits=6, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name='overtime_options')

    def __str__(self):
        return f"{self.name} - ${self.rate_per_hour}/hr"

class ContractOvertime(models.Model):
    contract = models.ForeignKey("contracts.Contract", on_delete=models.CASCADE, related_name='overtimes')
    overtime_option = models.ForeignKey(OvertimeOption, on_delete=models.CASCADE)
    hours = models.DecimalField(max_digits=3, decimal_places=1)

    def __str__(self):
        return f"{self.contract} - {self.overtime_option} - Hours: {self.hours}"


class StaffOvertime(models.Model):
    staff_member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contract = models.ForeignKey('contracts.Contract', on_delete=models.CASCADE)
    overtime_option = models.ForeignKey(OvertimeOption, on_delete=models.SET_NULL, null=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    overtime_hours = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        return f"{self.staff_member.username} - {self.overtime_hours} hours for {self.contract}"
