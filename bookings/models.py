# bookings/models.py

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from bookings.constants import SERVICE_ROLE_MAPPING


class Availability(models.Model):
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(blank=True, null=True)
    available = models.BooleanField(default=True)
    always_off_days = models.JSONField(default=list)

    def __str__(self):
        if self.date:
            return f"{self.staff.username} - {self.date}"
        else:
            days_off = ', '.join(str(day) for day in self.always_off_days)
            return f"{self.staff.username} - Always off on days: {days_off}"

    @classmethod
    def get_available_staff_for_date(cls, date):
        weekday = date.weekday()

        unavailable_staff_ids = cls.objects.filter(
            Q(date=date, available=False) | Q(always_off_days__contains=[weekday])
        ).values_list('staff_id', flat=True)

        booked_or_pending_staff_ids = EventStaffBooking.objects.filter(
            contract__event_date=date,
            status__in=['BOOKED', 'PENDING']
        ).values_list('staff_id', flat=True)

        all_unavailable_ids = set(unavailable_staff_ids) | set(booked_or_pending_staff_ids)

        customuser = get_user_model()
        return customuser.objects.filter(
            is_active=True,
            status='ACTIVE',
            role__isnull=False
        ).exclude(id__in=all_unavailable_ids)


class Service(models.Model):
    role_identifier = models.CharField(max_length=30)
    name = models.CharField(max_length=100)
    hourly_rate = models.DecimalField(max_digits=5, decimal_places=2)
    is_taxable = models.BooleanField(default=False)


class EventStaffBooking(models.Model):
    STATUS_CHOICES = (
        ('PROSPECT', 'Prospect'),
        ('PENDING', 'Pending'),
        ('BOOKED', 'Booked'),
        ('CLEARED', 'Cleared'),
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
        ('PROSPECT3', 'Prospect Photographer 3'),
    )

    HOURS_CHOICES = (
        (2, '2 Hours'),
        (4, '4 Hours'),
        (6, '6 Hours'),
        (8, '8 Hours'),
    )

    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contract = models.ForeignKey('contracts.Contract', on_delete=models.CASCADE)
    hours_booked = models.PositiveIntegerField(choices=HOURS_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    confirmed = models.BooleanField(default=False)
    booking_notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['contract__event_date', 'role']

    def save(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        if request:
            self._request = request

        if not self._state.adding:
            original = EventStaffBooking.objects.get(pk=self.pk)
            if original.status != self.status:
                self.handle_status_change(original.status, self.status)

        super().save(*args, **kwargs)
        self.update_contract_role()

    def handle_status_change(self, old_status, new_status):
        if old_status not in ['PENDING', 'BOOKED'] and new_status in ['PENDING', 'BOOKED']:
            Availability.objects.update_or_create(
                staff=self.staff,
                date=self.contract.event_date,
                defaults={'available': False}
            )
        elif old_status in ['PENDING', 'BOOKED'] and new_status not in ['PENDING', 'BOOKED']:
            Availability.objects.update_or_create(
                staff=self.staff,
                date=self.contract.event_date,
                defaults={'available': True}
            )
        elif new_status == 'CLEARED':
            Availability.objects.update_or_create(
                staff=self.staff,
                date=self.contract.event_date,
                defaults={'available': True}
            )

        if old_status != 'BOOKED' and new_status == 'BOOKED':
            from communication.utils import send_booking_assignment_email
            if hasattr(self, '_request'):
                send_booking_assignment_email(
                    request=self._request,
                    staff=self.staff,
                    contract=self.contract,
                    role=self.get_role_display(),
                    is_update=False
                )

    def clear(self):
        self.status = 'CLEARED'
        self.save()

    @classmethod
    def update_or_create_booking(cls, contract, old_staff, new_staff):
        if old_staff:
            try:
                old_booking = cls.objects.get(contract=contract, staff=old_staff)
                old_booking.delete()
            except cls.DoesNotExist:
                pass

        if new_staff:
            new_booking, _ = cls.objects.update_or_create(
                contract=contract, staff=new_staff,
                defaults={'status': 'PENDING', 'hours_booked': None})
            return new_booking

    def add_communication(self, content, user):
        from communication.models import UnifiedCommunication
        UnifiedCommunication.objects.create(
            content=content,
            note_type='booking',
            created_by=user,
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.pk
        )

    def get_communications(self):
        from communication.models import UnifiedCommunication
        return UnifiedCommunication.objects.filter(
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.pk
        )

    def delete(self, *args, **kwargs):
        self.clear_contract_role()
        super().delete(*args, **kwargs)

    def clear_contract_role(self):
        role_field = SERVICE_ROLE_MAPPING.get(self.role)
        if role_field and hasattr(self.contract, role_field):
            setattr(self.contract, role_field, None)
            self.contract.save()

    def update_contract_role(self):
        role_field = SERVICE_ROLE_MAPPING.get(self.role)
        if role_field:
            if self.status == 'CLEARED' or not self.staff:
                setattr(self.contract, role_field, None)
            else:
                setattr(self.contract, role_field, self.staff)
            self.contract.save()
