from django.contrib.auth.models import AbstractUser, UserManager, Group, Permission
from django.db import models
from django.core.validators import RegexValidator
from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone


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
    COORDINATOR = 'COORDINATOR'
    CLIENT = 'CLIENT'  # Existing role
    PROSPECT1 = 'PROSPECT1'
    PROSPECT2 = 'PROSPECT2'
    PROSPECT3 = 'PROSPECT3'

    ROLE_CHOICES = (
        (PHOTOGRAPHER, 'Photographer'),
        (VIDEOGRAPHER, 'Videographer'),
        (DJ, 'Dj'),
        (PHOTOBOOTH_OPERATOR, 'Photobooth Operator'),
        (ADMIN, 'Admin'),
        (SALES_PERSON, 'Sales Person'),
        (MANAGER, 'Manager'),
        (COORDINATOR, 'Coordinator'),
        (CLIENT, 'Client'),  # Existing choice
        (PROSPECT1, 'Prospect Photographer 1'),
        (PROSPECT2, 'Prospect Photographer 2'),
        (PROSPECT3, 'Prospect Photographer 3')
    )

    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    service_type = models.ForeignKey('contracts.ServiceType', on_delete=models.CASCADE, related_name='roles')
    objects = models.Manager()  # Explicitly added default manager

    def __str__(self):
        return self.name


class EventStaffManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role__name__in=[Role.PHOTOGRAPHER, Role.VIDEOGRAPHER, Role.DJ,
                                                             Role.PHOTOBOOTH_OPERATOR])


class CustomUser(AbstractUser):
    USER_TYPES = (
        ('employee', 'Employee'),
        ('client', 'Client'),
    )

    objects = UserManager()  # Default manager
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='client')
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
    rank = models.IntegerField(default=0, help_text="Determines the order of photographers.")
    additional_roles = models.ManyToManyField(Role, related_name='additional_users', blank=True)


    STATUS_CHOICES = (
        ('TRAINEE', 'Trainee'),
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    )
    status = models.CharField(choices=STATUS_CHOICES, max_length=10, default='ACTIVE')
    website = models.URLField(max_length=200, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    groups = models.ManyToManyField(Group, blank=True, related_name="customuser_set")
    user_permissions = models.ManyToManyField(Permission, blank=True, related_name="customuser_set")

    @property
    def is_coordinator(self):
        """Check if the user is a coordinator."""
        return self.groups.filter(name='Coordinator').exists()

    @property
    def is_client(self):
        """Check if the user is a client based on user_type."""
        return self.user_type == 'client'

    def is_event_staff(self):
        event_roles = [Role.PHOTOGRAPHER, Role.VIDEOGRAPHER, Role.DJ, Role.PHOTOBOOTH_OPERATOR]
        return self.role.name in event_roles if self.role else False

    def is_office_staff(self):
        office_roles = [Role.ADMIN, Role.SALES_PERSON, Role.MANAGER]
        return self.role.name in office_roles if self.role else False

    # Method to calculate booking totals dynamically
    def current_year_bookings(self):
        from contracts.models import EventStaffBooking  # Adjust the import path based on your project structure

        current_year = timezone.now().year
        return EventStaffBooking.objects.filter(
            staff=self,
            contract__event_date__year=current_year
        ).count()

    def next_year_bookings(self):
        from contracts.models import EventStaffBooking  # Adjust the import path based on your project structure

        next_year = timezone.now().year + 1
        return EventStaffBooking.objects.filter(
            staff=self,
            contract__event_date__year=next_year
        ).count()


class UserModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.get_full_name()  # Assumes your CustomUser model has a get_full_name() method
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
