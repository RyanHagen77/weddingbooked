from django import forms
from .models import UnifiedCommunication, Task  # Import your model
from users.models import CustomUser, Role
from django.core.exceptions import ValidationError



class CommunicationForm(forms.Form):
    message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'style': 'width: 100%;'}),
        label="Note Content"
    )
    message_type = forms.ChoiceField(
        choices=[
            (UnifiedCommunication.INTERNAL, 'Internal Note'),
            (UnifiedCommunication.PORTAL, 'Portal Note')
        ],
        required=True,
        label='Message Type',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class BookingCommunicationForm(forms.Form):
    message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'style': 'width: 100%;'}),
        label="Note Content"
    )
    message_type = forms.ChoiceField(
        choices=[
            (UnifiedCommunication.BOOKING, 'Booking Note')
        ],
        required=True,
        label='Message Type',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['sender', 'assigned_to', 'contract', 'note', 'due_date', 'description', 'task_type']
        widgets = {
            'contract': forms.HiddenInput(),
            'sender': forms.HiddenInput(),
            'note': forms.HiddenInput(),
            'task_type': forms.HiddenInput(),  # Update `type` to `task_type`
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'style': 'width: 100%;'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'style': 'width: 100%;'}),
        }

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        office_role_names = ['ADMIN', 'SALES PERSON', 'MANAGER', 'COORDINATOR']
        office_roles = Role.objects.filter(name__in=office_role_names)
        office_staff_queryset = CustomUser.objects.filter(role__in=office_roles, status='ACTIVE')

        # Setting the queryset for 'sender' and 'assigned_to' fields
        self.fields['sender'].queryset = office_staff_queryset
        self.fields['assigned_to'].queryset = office_staff_queryset

        # Setting the label from instance method to display full names
        self.fields['sender'].label_from_instance = lambda obj: "{} {}".format(obj.first_name, obj.last_name)
        self.fields['assigned_to'].label_from_instance = lambda obj: "{} {}".format(obj.first_name, obj.last_name)

        # Setting the queryset for 'note' field
        self.fields['note'].queryset = UnifiedCommunication.objects.filter(
            note_type__in=[UnifiedCommunication.INTERNAL, UnifiedCommunication.PORTAL]
        )
        self.fields['note'].label_from_instance = lambda obj: "{} - {}".format(obj.note_type, obj.description[:30])

        # Setting field requirements
        self.fields['contract'].required = False
        self.fields['note'].required = False

    def clean(self):
        cleaned_data = super().clean()
        task_type = cleaned_data.get('task_type')
        contract = cleaned_data.get('contract')

        if task_type == 'contract' and not contract:
            raise ValidationError("Contract-related tasks must have a contract assigned.")
