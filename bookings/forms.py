
from django import forms
from .models import EventStaffBooking


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
        choices=[
            ("", "All Service Types"),
            ("PHOTOGRAPHER", "Photographer"),
            ("VIDEOGRAPHER", "Videographer"),
            ("DJ", "DJ"),
            ("PHOTOBOOTH", "Photobooth"),
        ],
    )
    role_filter = forms.ChoiceField(
        required=False,
        choices=[
            ("", "All Roles"),
            ("PHOTOGRAPHER1", "Photographer 1"),
            ("PHOTOGRAPHER2", "Photographer 2"),
            ("ENGAGEMENT", "Engagement"),
            ("VIDEOGRAPHER1", "Videographer 1"),
            ("VIDEOGRAPHER2", "Videographer 2"),
            ("DJ1", "DJ 1"),
            ("DJ2", "DJ 2"),
            ("PHOTOBOOTH_OP", "Photobooth Operator"),
        ],
    )
    status_filter = forms.CharField(
        required=False,
        label="Filter by Status",
        widget=forms.TextInput(attrs={"placeholder": "Comma-separated (e.g., PENDING,BOOKED)"})
    )
    sort_by = forms.ChoiceField(
        required=False,
        choices=[
            ("contract__event_date", "Event Date"),
            ("role", "Role"),
        ],
    )
    order = forms.ChoiceField(
        required=False,
        choices=[
            ("asc", "Ascending"),
            ("desc", "Descending"),
        ],
        initial="asc",
    )

class EventStaffBookingForm(forms.ModelForm):
    booking_id = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = EventStaffBooking
        fields = ['role', 'staff', 'status', 'confirmed', 'booking_id']
