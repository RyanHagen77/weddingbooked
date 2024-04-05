from django.db import models
from contracts.models import Contract
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings


class UnifiedCommunication(models.Model):

    OFFICE = 'office'
    CONTRACT = 'contract'
    NOTE_TYPES = [
        (OFFICE, 'Office Note'),
        (CONTRACT, 'Contract Note'),
    ]

    content = models.TextField(verbose_name="Content")
    note_type = models.CharField(max_length=10, choices=NOTE_TYPES, verbose_name="Note Type")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Created By")

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"Note {self.id} - {self.get_note_type_display()} - {self.created_at.strftime('%Y-%m-%d')} by {self.created_by}"
    class Meta:
        verbose_name = "Unified Communication"
        verbose_name_plural = "Unified Communications"


class Task(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_tasks', verbose_name="Sender")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_tasks', verbose_name="Assigned To")
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, null=True, blank=True)
    note = models.ForeignKey(UnifiedCommunication, on_delete=models.CASCADE, verbose_name="Note", null=True, blank=True)
    due_date = models.DateTimeField(verbose_name="Due Date")
    description = models.TextField(verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    is_completed = models.BooleanField(default=False, verbose_name="Is Completed")

    def __str__(self):
        return f"Task for Contract {self.contract.id} - Due {self.due_date.strftime('%Y-%m-%d %H:%M')} - Assigned to {self.assigned_to}"

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"

