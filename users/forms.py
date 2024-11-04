from django import forms
from .models import CustomUser, Role


class OfficeStaffForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = '__all__'  # This allows all fields to be edited

    def __init__(self, *args, **kwargs):
        super(OfficeStaffForm, self).__init__(*args, **kwargs)
        self.fields['role'].queryset = Role.objects.filter(name__in=['MANAGER', 'OFFICE_STAFF', 'SALES_PERSON'])





