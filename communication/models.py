from django.db import models
from contracts.models import Contract
from django.conf import settings


class UnifiedCommunication(models.Model):
    INTERNAL = 'internal'
    PORTAL = 'portal'
    BOOKING = 'booking'

    NOTE_TYPES = [
        (INTERNAL, 'Internal Note'),
        (PORTAL, 'Portal Note'),
        (BOOKING, 'Booking Note'),
    ]

    content = models.TextField(verbose_name="Content")
    note_type = models.CharField(max_length=10, choices=NOTE_TYPES, verbose_name="Note Type", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At", db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Created By")
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='communications', null=True,
                                 blank=True, verbose_name="Contract")

    def clean(self):
        super(UnifiedCommunication, self).clean()
        # Add custom validation logic here if needed

    def __str__(self):
        return f"Note {self.id} - {self.get_note_type_display()} - {self.created_at.strftime('%Y-%m-%d')} by {self.created_by}"

    class Meta:
        verbose_name = "Unified Communication"
        verbose_name_plural = "Unified Communications"
        indexes = [
            models.Index(fields=['created_at', 'note_type']),  # Correct indexing fields
        ]



class Task(models.Model):
    TASK_TYPES = (
        ('contract', 'Contract'),
        ('internal', 'Internal'),
    )

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_tasks', verbose_name="Sender")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_tasks', verbose_name="Assigned To")
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, null=True, blank=True)
    note = models.ForeignKey(UnifiedCommunication, on_delete=models.CASCADE, verbose_name="Note", null=True, blank=True)
    due_date = models.DateTimeField(verbose_name="Due Date")
    description = models.TextField(verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    is_completed = models.BooleanField(default=False, verbose_name="Is Completed")
    type = models.CharField(max_length=10, choices=TASK_TYPES, default='internal')

    def __str__(self):
        if self.contract:
            return f"Task for Contract {self.contract.contract_id} - Due {self.due_date.strftime('%Y-%m-%d %H:%M')} - Assigned to {self.assigned_to}"
        else:
            return f"Internal Task - Due {self.due_date.strftime('%Y-%m-%d %H:%M')} - Assigned to {self.assigned_to}"

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"