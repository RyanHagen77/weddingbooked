#bookings/models.py

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from bookings.constants import SERVICE_ROLE_MAPPING  # Adjust the import path as needed





class Availability(models.Model):
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    date = models.DateField(blank=True, null=True)  # Nullable for recurrent unavailability
    available = models.BooleanField(default=True)
    always_off_days = models.JSONField(default=list)  # Stores weekdays as integers, e.g., [0, 6]

    objects = models.Manager()  # Default manager

    def __str__(self):
        if self.date:
            return f"{self.staff.username} - {self.date}"
        else:
            days_off = ', '.join(str(day) for day in self.always_off_days)
            return f"{self.staff.username} - Always off on days: {days_off}"

    @classmethod
    def get_available_staff_for_date(cls, date):
        """
        Returns staff who are available for the given date.
        Staff with 'BOOKED' or 'PENDING' status are excluded from availability.
        Staff with 'PROSPECT' status remain available.
        """

        weekday = date.weekday()

        # Find staff who are unavailable on the specific date or have always-off days matching the weekday
        unavailable_staff_ids = cls.objects.filter(
            Q(date=date, available=False) | Q(always_off_days__contains=[weekday])
        ).values_list('staff_id', flat=True)

        # Find staff who are booked or pending on the specific date (PROSPECT is ignored)
        booked_or_pending_staff_ids = EventStaffBooking.objects.filter(
            contract__event_date=date,
            status__in=['BOOKED', 'PENDING']  # Only BOOKED and PENDING block availability
        ).values_list('staff_id', flat=True)

        # Combine both unavailable and booked/pending staff IDs
        all_unavailable_ids = set(unavailable_staff_ids) | set(booked_or_pending_staff_ids)

        # Use CustomUser to exclude staff who are unavailable or booked
        CustomUser = get_user_model()
        return CustomUser.objects.exclude(id__in=all_unavailable_ids)


class Service(models.Model):
    role_identifier = models.CharField(max_length=30)  # Match this with ROLE_CHOICES in EventStaffBooking
    name = models.CharField(max_length=100)
    hourly_rate = models.DecimalField(max_digits=5, decimal_places=2)
    is_taxable = models.BooleanField(default=False)

class EventStaffBookingManager(models.Manager):
    pass


class EventStaffBooking(models.Model):
    STATUS_CHOICES = (
        ('PROSPECT', 'Prospect'),
        ('PENDING', 'Pending'),
        ('BOOKED', 'Booked'),
        ('CLEARED', 'Cleared'),  # Assuming 'Cleared' status is needed as referenced in the clear method
    )

    ROLE_CHOICES = (
        ('PHOTOGRAPHER1', 'Photographer 1'),
        ('PHOTOGRAPHER2', 'Photographer 2'),
        ('ENGAGEMENT', 'Engagement'),
        ('VIDEOGRAPHER1', 'Videographer 1'),
        ('VIDEOGRAPHER2', 'Videographer 2'),
        ('DJ1', 'DJ 1'),
        ('DJ2', 'DJ 2'),
        ('PHOTOBOOTH_OP1', 'Photobooth Operator 1'),
        ('PHOTOBOOTH_OP2', 'Photobooth Operator 2'),
        ('PROSPECT1', 'Prospect Photographer 1'),
        ('PROSPECT2', 'Prospect Photographer 2'),
        ('PROSPECT3', 'Prospect Photographer 3')
        # ... add any other roles you might have ...
    )

    HOURS_CHOICES = (
        (2, '2 Hours'),
        (4, '4 Hours'),
        (6, '6 Hours'),
        (8, '8 Hours'),
    )

    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    contract = models.ForeignKey('contracts.Contract', on_delete=models.CASCADE)
    hours_booked = models.PositiveIntegerField(choices=HOURS_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    confirmed = models.BooleanField(default=False)
    booking_notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('contract', 'role')

    def save(self, *args, **kwargs):
        # Check if the request is provided and set it as an attribute
        request = kwargs.pop('request', None)
        if request:
            self._request = request

        # Get the original booking if it exists
        if not self._state.adding:
            original = EventStaffBooking.objects.get(pk=self.pk)
            # Check if the status has changed
            if original.status != self.status:
                self.handle_status_change(original.status, self.status)

        super().save(*args, **kwargs)
        self.update_contract_role()

    def handle_status_change(self, old_status, new_status):
        if old_status not in ['PENDING', 'BOOKED'] and new_status in ['PENDING', 'BOOKED']:
            # Remove staff from availability when status is set to PENDING or BOOKED
            Availability.objects.update_or_create(
                staff=self.staff,
                date=self.contract.event_date,
                defaults={'available': False}
            )
        elif old_status in ['PENDING', 'BOOKED'] and new_status not in ['PENDING', 'BOOKED']:
            # Add staff back to availability when status is changed from PENDING or BOOKED
            Availability.objects.update_or_create(
                staff=self.staff,
                date=self.contract.event_date,
                defaults={'available': True}
            )
        elif new_status == 'CLEARED':
            # Ensure availability is updated when status is cleared
            Availability.objects.update_or_create(
                staff=self.staff,
                date=self.contract.event_date,
                defaults={'available': True}
            )

        if old_status != 'BOOKED' and new_status == 'BOOKED':
            # Send email to the staff when booking is marked as 'Booked'
            self.send_booking_email(self._request, self.staff, self.contract, self.get_role_display(), is_update=False)

    def send_booking_email(self, request, staff, contract, role, is_update):
        context = {
            'user': staff,
            'contract': contract,
            'role': role,
            'domain': get_current_site(request).domain,
            'is_update': is_update,
        }
        subject = 'New Booking Assigned'
        message = render_to_string('communication/booking_assignment_email.html', context, request=request)
        from_email = 'enetadmin@enet2.com'
        to_email = [staff.email]

        send_mail(
            subject,
            message,
            from_email,
            to_email,
            fail_silently=False,
        )

    def clear(self):
        """Clears the current booking by changing its status to 'CLEARED'."""
        self.status = 'CLEARED'
        self.save()

    @classmethod
    def update_or_create_booking(cls, contract, old_staff, new_staff):
        """Updates or creates a booking for a staff member."""
        if old_staff:
            try:
                old_booking = cls.objects.get(contract=contract, staff=old_staff)
                old_booking.delete()
            except cls.DoesNotExist:
                pass

        if new_staff:
            new_booking, created = cls.objects.update_or_create(
                contract=contract, staff=new_staff,
                defaults={'status': 'PENDING', 'hours_booked': None})  # Update with appropriate defaults
            return new_booking

    def add_communication(self, content, user):
        """Adds a new communication for this booking."""
        from communication.models import UnifiedCommunication  # Lazy import

        UnifiedCommunication.objects.create(
            content=content,
            note_type='booking',
            created_by=user,
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.pk
        )

    def get_communications(self):
        """Fetches all communications for this booking."""
        from communication.models import UnifiedCommunication  # Lazy import

        return UnifiedCommunication.objects.filter(content_type=ContentType.objects.get_for_model(self),
                                                   object_id=self.pk)

    def total_cost(self):
        """Calculates the total cost for this booking."""
        service = Service.objects.get(role_identifier=self.role)
        return service.hourly_rate * self.hours_booked

    @staticmethod
    def total_service_cost(contract_id):
        """Calculates the total service cost for a given contract."""
        bookings = EventStaffBooking.objects.filter(contract_id=contract_id)
        return sum(booking.total_cost() for booking in bookings)

    def delete(self, *args, **kwargs):
        # Before deleting, clear the contract role
        self.clear_contract_role()
        super().delete(*args, **kwargs)  # Call the superclass method to delete the object

    def clear_contract_role(self):
        # Clear the role in the contract when the booking is deleted or cleared
        role_field = SERVICE_ROLE_MAPPING.get(self.role, None)
        if role_field and hasattr(self.contract, role_field):
            setattr(self.contract, role_field, None)
            self.contract.save()

    def update_contract_role(self):
        # Update the contract role when saving or clearing the booking
        role_field = SERVICE_ROLE_MAPPING.get(self.role, None)
        if role_field:
            if self.status == 'CLEARED' or not self.staff:
                setattr(self.contract, role_field, None)
            else:
                setattr(self.contract, role_field, self.staff)
            self.contract.save()