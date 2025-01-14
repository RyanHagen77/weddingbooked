
from django import forms
from .models import EventStaffBooking

class EventStaffBookingForm(forms.ModelForm):
    booking_id = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = EventStaffBooking
        fields = ['role', 'staff', 'status', 'confirmed', 'booking_id']
