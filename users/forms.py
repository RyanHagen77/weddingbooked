from django import forms
from .models import CustomUser, Role
from contracts.models import EventStaffBooking
from communication.models import Task


class OfficeStaffForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = '__all__'  # This allows all fields to be edited

    def __init__(self, *args, **kwargs):
        super(OfficeStaffForm, self).__init__(*args, **kwargs)
        self.fields['role'].queryset = Role.objects.filter(name__in=['MANAGER', 'OFFICE_STAFF', 'SALES_PERSON'])


class EventStaffBookingForm(forms.ModelForm):
    class Meta:
        model = EventStaffBooking
        fields = '__all__'


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['assigned_to', 'sender', 'due_date', 'description']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'sender': forms.HiddenInput(),
            'assigned_to': forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        office_role_names = ['ADMIN', 'SALES_PERSON', 'MANAGER']
        office_roles = Role.objects.filter(name__in=office_role_names)
        office_staff_queryset = CustomUser.objects.filter(role__in=office_roles)
        self.fields['assigned_to'].queryset = office_staff_queryset


