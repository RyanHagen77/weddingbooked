from django import forms
from .models import UnifiedCommunication, Task  # Import your model
from users.models import CustomUser, Role


class CommunicationForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea, required=True)

    # Message type field
    message_type = forms.ChoiceField(
        choices=UnifiedCommunication.NOTE_TYPES,
        required=True,
        label='Message Type'
    )

    # Recipient field (assuming you have a way to identify recipients)
    # recipient = forms.ChoiceField(choices=[...], required=False, label='Recipient')

    # If you need to handle replies or different types of messages,
    # you can add more fields here. For example:
    # reply_to = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    # You can also add a field for the message type if needed
    # message_type = forms.ChoiceField(choices=UnifiedCommunication.NOTE_TYPES, required=True)


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['sender', 'assigned_to', 'contract', 'note', 'due_date', 'description']
        widgets = {
            'contract': forms.HiddenInput(),
            'sender': forms.HiddenInput(),
            'note': forms.HiddenInput(),
            'due_date': forms.DateInput(attrs={'type': 'date'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        office_role_names = ['ADMIN', 'SALES_PERSON', 'MANAGER']
        office_roles = Role.objects.filter(name__in=office_role_names)
        office_staff_queryset = CustomUser.objects.filter(role__in=office_roles)
        self.fields['sender'].queryset = office_staff_queryset
        self.fields['assigned_to'].queryset = office_staff_queryset
        self.fields['note'].queryset = UnifiedCommunication.objects.filter(
            note_type__in=[UnifiedCommunication.OFFICE, UnifiedCommunication.CONTRACT]
        )
        self.fields['contract'].required = True
        self.fields['note'].required = False



