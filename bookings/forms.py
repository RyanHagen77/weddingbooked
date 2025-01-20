
from django import forms
from .models import EventStaffBooking

SERVICE_TYPE_CHOICES = [
    ("Photography", "Photography"),
    ("Videography", "Videography"),
    ("DJ", "DJ"),
    ("Photobooth", "Photobooth"),
]

class BookingSearchForm(forms.Form):
    booking_q = forms.CharField(
        required=False,
        label="Quick Search",
        widget=forms.TextInput(attrs={"placeholder": "Search by staff, client, or contract"})
    )
    event_date_start = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"})
    )
    event_date_end = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"})
    )
    service_type = forms.ChoiceField(
        required=False,
        choices=[("", "All Service Types")] + SERVICE_TYPE_CHOICES,
        label="Filter by Service Type",
    )
    role_filter = forms.ChoiceField(
        required=False,
        choices=[
            ("", "All Roles"),
            ("PHOTOGRAPHER1", "Photographer 1"),
            ("PHOTOGRAPHER2", "Photographer 2"),
            ("VIDEOGRAPHER1", "Videographer 1"),
            ("VIDEOGRAPHER2", "Videographer 2"),
            ("DJ1", "DJ 1"),
            ("DJ2", "DJ 2"),
            ("PHOTOBOOTH_OP1", "Photobooth Operator 1"),
            ("PHOTOBOOTH_OP2", "Photobooth Operator 2"),
        ],
        label="Filter by Role",
    )
    status_filter = forms.ChoiceField(
        required=False,
        choices=[
            ("", "All Statuses"),
            ("Prospect", "Prospect"),
            ("Pending", "Pending"),
            ("Booked", "Booked"),
        ],
        label="Filter by Status",
    )
    sort_by = forms.ChoiceField(
        required=False,
        choices=[
            ("contract__event_date", "Event Date"),
            ("role", "Role"),
        ],
        label="Sort by",
    )
    order = forms.ChoiceField(
        required=False,
        choices=[
            ("asc", "Ascending"),
            ("desc", "Descending"),
        ],
        initial="asc",
        label="Order",
    )


class EventStaffBookingForm(forms.ModelForm):
    booking_id = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = EventStaffBooking
        fields = ['role', 'staff', 'status', 'confirmed', 'booking_id']
