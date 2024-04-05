from django.contrib import admin
from .models import UnifiedCommunication, Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('sender', 'assigned_to', 'contract', 'note', 'due_date', 'description', 'is_completed')
    list_filter = ('is_completed', 'due_date')
    search_fields = ('description',)

@admin.register(UnifiedCommunication)
class UnifiedCommunicationAdmin(admin.ModelAdmin):
    list_display = ('content', 'note_type', 'created_at', 'created_by')
    list_filter = ('note_type', 'created_at')
    search_fields = ('content', 'created_by__username')
