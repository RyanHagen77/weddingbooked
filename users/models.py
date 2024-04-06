from django.contrib.auth.models import AbstractUser, UserManager, Group, Permission
from django.db import models
from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    regex=r'^\d{3}-\d{3}-\d{4}$',
    message='Phone number must be in the format XXX-XXX-XXXX.'
)

class Role(models.Model):
    PHOTOGRAPHER = 'PHOTOGRAPHER'
    VIDEOGRAPHER = 'VIDEOGRAPHER'
    DJ = 'DJ'
    PHOTOBOOTH_OPERATOR = 'PHOTOBOOTH OPERATOR'
    ADMIN = 'ADMIN'
    SALES_PERSON = 'SALES PERSON'
    MANAGER = 'MANAGER'
    CLIENT = 'CLIENT'  # Newly added role

    ROLE_CHOICES = (
        (PHOTOGRAPHER, 'Photographer'),
        (VIDEOGRAPHER, 'Videographer'),
        (DJ, 'Dj'),
        (PHOTOBOOTH_OPERATOR, 'Photobooth Operator'),
        (ADMIN, 'Admin'),
        (SALES_PERSON, 'Sales Person'),
        (MANAGER, 'Manager'),
        (CLIENT, 'Client')  # Newly added choice
    )

    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    service_type = models.ForeignKey('contracts.ServiceType', on_delete=models.CASCADE, related_name='roles')
    objects = models.Manager()  # Explicitly added default manager

    def __str__(self):
        return self.name


class EventStaffManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role__name__in=[Role.PHOTOGRAPHER, Role.VIDEOGRAPHER, Role.DJ, Role.PHOTOBOOTH_OPERATOR])


class CustomUser(AbstractUser):
    USER_TYPES = (
        ('employee', 'Employee'),
        ('client', 'Client'),
    )

    objects = UserManager()  # Default manager
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='employee')
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    primary_phone1 = models.CharField(
        max_length=12,  # Increase max_length to accommodate dashes
        validators=[phone_validator],
        blank=True,
        null=True
    )
    primary_phone2 = models.CharField(
        max_length=12,  # Increase max_length to accommodate dashes
        validators=[phone_validator],
        blank=True,
        null=True
    )
    primary_address1 = models.CharField(max_length=255, blank=True, null=True)
    primary_address2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=255, blank=True, null=True)
    event_staff = EventStaffManager()  # Custom manager for specific queries
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)

    STATUS_CHOICES = (
        ('TRAINEE', 'Trainee'),
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    )
    status = models.CharField(choices=STATUS_CHOICES, max_length=10, default='TRAINEE')
    website = models.URLField(max_length=200, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    groups = models.ManyToManyField(Group, blank=True, related_name="customuser_set")
    user_permissions = models.ManyToManyField(Permission, blank=True, related_name="customuser_set")

    def is_event_staff(self):
        event_roles = [Role.PHOTOGRAPHER, Role.VIDEOGRAPHER, Role.DJ, Role.PHOTOBOOTH_OPERATOR]
        return self.role.name in event_roles if self.role else False

    def is_office_staff(self):
        office_roles = [Role.ADMIN, Role.SALES_PERSON, Role.MANAGER]
        return self.role.name in office_roles if self.role else False


class EventStaffProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_query_name='profile')
    # Additional fields for event staff

    def __str__(self):
        return f"Profile for {self.user.username}"


class OfficeStaffProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_query_name='office_profile')
    # Add any additional fields specific to office staff

    def __str__(self):
        return f"Office Profile for {self.user.username}"
