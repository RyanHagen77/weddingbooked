from django import forms
from bookings.models import EventStaffBooking
from contracts.models import (Contract, LeadSourceCategory, Client, Discount, Location,
                              ServiceFee)
from services.models import AdditionalEventStaffOption, EngagementSessionOption, Package
from django.core.validators import RegexValidator
from users.models import CustomUser
from django.forms.widgets import DateInput
from django.forms import inlineformset_factory
from django.contrib.auth import get_user_model
import re

phone_validator = RegexValidator(
    regex=r'^\d{3}-\d{3}-\d{4}$',
    message='Phone number must be in the format XXX-XXX-XXXX.'
)


class UserModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.get_full_name()  # Assumes your CustomUser model has a get_full_name() method


class ContractSearchForm(forms.Form):
    STATUS_CHOICES = [
        ('', '---------'),
        ('pipeline', 'Pipeline'),
        ('forecast', 'Forecast'),
        ('pending', 'Pending'),
        ('booked', 'Booked'),
        ('completed', 'Completed'),
        ('dead', 'Dead'),
    ]

    location = forms.ModelChoiceField(queryset=Location.objects.all(), required=False)
    ceremony_site = forms.CharField(max_length=255, required=False)
    reception_site = forms.CharField(max_length=255, required=False)
    event_date_start = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date'}))
    event_date_end = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date'}))
    contract_date_start = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date'}))
    contract_date_end = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date'}))
    contract_number = forms.CharField(max_length=255, required=False, label="Custom Contract Number")
    old_contract_number = forms.CharField(max_length=255, required=False, label="Old Contract Number")
    primary_contact = forms.CharField(max_length=100, required=False)
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)

    csr = UserModelChoiceField(
        queryset=CustomUser.objects.filter(groups__name='Sales', is_active=True),
        required=False,
        label="Sales Person"
    )
    photographer = UserModelChoiceField(
        queryset=CustomUser.objects.filter(role__name='Photographer', is_active=True),
        required=False,
        label="Photographer"
    )
    videographer = UserModelChoiceField(
        queryset=CustomUser.objects.filter(role__name='Videographer', is_active=True),
        required=False,
        label="Videographer"
    )
    photobooth_operator = UserModelChoiceField(
        queryset=CustomUser.objects.filter(role__name='Photobooth Operator', is_active=True),
        required=False,
        label="Photobooth Operator"
    )

    # 🔹 **Added DJ dropdown (same as other roles)**
    dj = UserModelChoiceField(
        queryset=CustomUser.objects.filter(role__name__in=['DJ1', 'DJ2'], is_active=True),
        required=False,
        label="DJ"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set the queryset for photographers
        photographer_ids = EventStaffBooking.objects.filter(
            role__in=['PHOTOGRAPHER1', 'PHOTOGRAPHER2']
        ).values_list('staff', flat=True)
        self.fields['photographer'].queryset = CustomUser.objects.filter(id__in=photographer_ids).distinct()

        # Set the queryset for videographers
        videographer_ids = EventStaffBooking.objects.filter(
            role__in=['VIDEOGRAPHER1', 'VIDEOGRAPHER2']
        ).values_list('staff', flat=True)
        self.fields['videographer'].queryset = CustomUser.objects.filter(id__in=videographer_ids).distinct()

        # Set the queryset for photobooth operators
        photobooth_operator_ids = EventStaffBooking.objects.filter(
            role__in=['PHOTOBOOTH_OP1', 'PHOTOBOOTH_OP2']
        ).values_list('staff', flat=True)
        self.fields['photobooth_operator'].queryset = CustomUser.objects.filter(
            id__in=photobooth_operator_ids).distinct()

        # 🔹 **Set the queryset for DJs**
        dj_ids = EventStaffBooking.objects.filter(
            role__in=['DJ1', 'DJ2']
        ).values_list('staff', flat=True)
        self.fields['dj'].queryset = CustomUser.objects.filter(id__in=dj_ids).distinct()


class NewContractForm(forms.ModelForm):
    # Client Fields
    primary_contact = forms.CharField(max_length=255, required=True, label="Primary Contact")
    partner_contact = forms.CharField(max_length=255, required=True, label="Partner Contact")
    primary_email = forms.EmailField(required=True, label="Primary Email")
    primary_phone1 = forms.CharField(
        max_length=12,
        required=False,
        label="Primary Phone 1"
    )

    # Contract Fields
    is_code_92 = forms.BooleanField(required=False, label="Code 92")
    event_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True,
        label="Event Date"
    )
    location = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        required=True,
        label="Store Location"
    )
    status = forms.ChoiceField(
        choices=Contract.STATUS_CHOICES,
        required=True,
        label="Status"
    )
    csr = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(groups__name="Sales", is_active=True),
        required=True,
        label="Sales Representative"
    )
    coordinator = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role__name="COORDINATOR", groups__name="Office Staff", is_active=True),
        required=True,
        label="Coordinator"
    )
    lead_source_category = forms.ModelChoiceField(
        queryset=LeadSourceCategory.objects.all(),
        required=False,
        label="Lead Source Category"
    )
    lead_source_details = forms.CharField(
        max_length=255,
        required=False,
        label="Lead Source Details"
    )
    bridal_party_qty = forms.IntegerField(required=False, label="Bridal Party Quantity")
    guests_qty = forms.IntegerField(required=False, label="Guest Quantity")
    ceremony_site = forms.CharField(max_length=255, required=False, label="Ceremony Site")
    ceremony_city = forms.CharField(max_length=255, required=False, label="Ceremony City")
    ceremony_state = forms.CharField(max_length=255, required=False, label="Ceremony State")
    reception_site = forms.CharField(max_length=255, required=False, label="Reception Site")
    reception_city = forms.CharField(max_length=255, required=False, label="Reception City")
    reception_state = forms.CharField(max_length=255, required=False, label="Reception State")
    old_contract_number = forms.CharField(max_length=255, required=False, label="Old Contract Number")

    class Meta:
        model = Contract
        fields = [
            'is_code_92', 'event_date', 'location', 'status', 'csr', 'coordinator',
            'lead_source_category', 'lead_source_details',
            'primary_contact', 'partner_contact', 'primary_email', 'primary_phone1',
            'bridal_party_qty', 'guests_qty', 'ceremony_site', 'ceremony_city',
            'ceremony_state', 'reception_site', 'reception_city', 'reception_state',
            'old_contract_number',
        ]

    # Validation Methods
    def clean_primary_contact(self):
        """
        Validate that the primary contact contains only letters, spaces, hyphens, or apostrophes.
        """
        primary_contact = self.cleaned_data.get("primary_contact", "").strip()  # Ensure we handle None and strip spaces
        if not primary_contact:
            raise ValidationError("The primary contact name is required.")
        if not re.match(r"^[A-Za-zÀ-ÖØ-öø-ÿ\s\-']+$", primary_contact):
            raise ValidationError(
                "The primary contact name must not contain numbers or special characters (except hyphens and "
                "apostrophes).")
        return primary_contact

    def clean_partner_contact(self):
        """
        Validate that the partner contact contains only letters, spaces, hyphens, or apostrophes.
        """
        partner_contact = self.cleaned_data.get("partner_contact", "").strip()  # Ensure we handle None and strip spaces
        if partner_contact and not re.match(r"^[A-Za-zÀ-ÖØ-öø-ÿ\s\-']+$", partner_contact):
            raise ValidationError(
                "The partner contact name must not contain numbers or special characters (except hyphens and "
                "apostrophes).")
        return partner_contact

    def clean_primary_phone1(self):
        """
        Ensure the phone number format matches the required pattern.
        Only 12-character formats like 123-456-7890 or 123.456.7890 are allowed.
        """
        primary_phone1 = self.cleaned_data.get("primary_phone1")
        if primary_phone1 and not re.match(r"^\d{3}[-.]\d{3}[-.]\d{4}$", primary_phone1):
            raise ValidationError("Phone number must be in the format 123-456-7890 or 123.456.7890.")
        return primary_phone1

    def clean_primary_email(self):
        primary_email = self.cleaned_data.get("primary_email")
        if primary_email and not re.match(r"[^@]+@[^@]+\.[^@]+", primary_email):
            raise ValidationError("Enter a valid email address (e.g., example@domain.com).")
        return primary_email

    def save(self, commit=True):
        # Save or update the client instance
        client_data = {
            'primary_contact': self.cleaned_data.get('primary_contact'),
            'primary_email': self.cleaned_data.get('primary_email'),
            'primary_phone1': self.cleaned_data.get('primary_phone1'),
            'partner_contact': self.cleaned_data.get('partner_contact'),
        }

        # Check if a related client already exists
        user = get_user_model()
        primary_email = client_data['primary_email']
        user, created = user.objects.get_or_create(
            email=primary_email,
            defaults={'username': primary_email, 'user_type': 'client'}
        )
        client, created = Client.objects.update_or_create(user=user, defaults=client_data)

        # Save the contract with the associated client
        contract = super().save(commit=False)
        contract.client = client

        if commit:
            contract.save()
            self.save_m2m()

        return contract


class ContractInfoEditForm(forms.ModelForm):
    is_code_92 = forms.BooleanField(required=False)
    event_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    location = forms.ModelChoiceField(queryset=Location.objects.all(), required=False)
    coordinator = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role__name='COORDINATOR', groups__name='Office Staff', is_active=True),
        required=False,
        label="Coordinator"
    )
    csr = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(groups__name='Sales', is_active=True),
        required=False,
        label="Sales Person"
    )
    status = forms.ChoiceField(choices=Contract.STATUS_CHOICES, required=False)
    lead_source_category = forms.ModelChoiceField(queryset=LeadSourceCategory.objects.all(), required=False,
                                                  label="Lead Source Category")
    lead_source_details = forms.CharField(max_length=255, required=False, label="Lead Source Details")

    old_contract_number = forms.CharField(max_length=255, required=False, label="Old Contract Number")

    class Meta:
        model = Contract
        fields = ['is_code_92', 'event_date', 'location', 'coordinator', 'status', 'csr', 'lead_source_category',
                  'lead_source_details',
                  'old_contract_number', 'custom_text']
        widgets = {
            'custom_text': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'custom_text': 'Contract Custom Terms and Conditions',
        }

    def clean_old_contract_number(self):
        old_contract_number = self.cleaned_data.get('old_contract_number')
        return old_contract_number


class ContractClientEditForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=get_user_model().objects.all(),
        required=True,
        disabled=True,  # Keep this read-only in most cases
        widget=forms.HiddenInput()  # Optionally hide it if not necessary for standalone editing
    )

    class Meta:
        model = Client
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        contract_context = kwargs.pop('contract_context', False)  # Flag for contract context
        super().__init__(*args, **kwargs)

        # Dynamically disable the user field based on context
        if contract_context:
            self.fields['user'].disabled = True

        # Add custom attributes for client fields
        for field_name, attrs in {
            'primary_contact': {'id': 'client-primary-contact'},
            'primary_email': {'id': 'client-primary-email'},
            'primary_phone1': {'id': 'client-primary-phone1'},
            'partner_contact': {'id': 'client-partner-contact'},
            'partner_email': {'id': 'client-partner-email'},
            'partner_phone1': {'id': 'client-partner-phone1'},
            'primary_address1': {'id': 'client-primary-address1'},
            'primary_address2': {'id': 'client-primary-address2'},
            'city': {'id': 'client-city'},
            'state': {'id': 'client-state'},
            'postal_code': {'id': 'client-postal-code'},
            'alt_contact': {'id': 'client-alt-contact'},
            'alt_email': {'id': 'client-alt-email'},
            'alt_phone': {'id': 'client-alt-phone'},
        }.items():
            self.fields[field_name].widget.attrs.update(attrs)


# Django form for Event Details
class ContractEventEditForm(forms.ModelForm):
    # Define your fields here, for example:
    bridal_party_qty = forms.IntegerField(min_value=1, required=False)
    guests_qty = forms.IntegerField(min_value=1, required=False)
    ceremony_site = forms.CharField(max_length=255, required=False)
    ceremony_city = forms.CharField(max_length=255, required=False)
    ceremony_state = forms.CharField(max_length=255, required=False)
    ceremony_contact = forms.CharField(max_length=255, required=False)
    ceremony_phone = forms.CharField(
        max_length=12,  # Adjusted to accommodate dashes
        validators=[phone_validator],
        required=False  # Instead of blank=True, null=True
    )
    ceremony_email = forms.EmailField(required=False)
    reception_site = forms.CharField(max_length=255, required=False)
    reception_city = forms.CharField(max_length=255, required=False)
    reception_state = forms.CharField(max_length=255, required=False)
    reception_contact = forms.CharField(max_length=255, required=False)
    reception_phone = forms.CharField(
        max_length=12,  # Adjusted to accommodate dashes
        validators=[phone_validator],
        required=False  # Instead of blank=True, null=True
    )
    reception_email = forms.EmailField(required=False)

    class Meta:
        model = Contract  # Assuming these fields are part of the Contract model
        fields = ['bridal_party_qty', 'guests_qty', 'ceremony_site', 'ceremony_city', 'ceremony_state',
                  'ceremony_contact', 'ceremony_phone', 'ceremony_email',
                  'reception_site', 'reception_city', 'reception_state', 'reception_contact',
                  'reception_phone', 'reception_email']

    def __init__(self, *args, **kwargs):
        super(ContractEventEditForm, self).__init__(*args, **kwargs)
        self.fields['bridal_party_qty'].widget.attrs.update({'id': 'event-bridal-party-qty'})
        self.fields['guests_qty'].widget.attrs.update({'id': 'event-guests-qty'})
        self.fields['ceremony_site'].widget.attrs.update({'id': 'event-ceremony-site'})
        self.fields['ceremony_city'].widget.attrs.update({'id': 'event-ceremony-city'})
        self.fields['ceremony_state'].widget.attrs.update({'id': 'event-ceremony-state'})
        self.fields['ceremony_contact'].widget.attrs.update({'id': 'event-ceremony-contact'})
        self.fields['ceremony_phone'].widget.attrs.update({'id': 'event-ceremony-phone'})
        self.fields['ceremony_email'].widget.attrs.update({'id': 'event-ceremony-email'})
        self.fields['reception_site'].widget.attrs.update({'id': 'event-reception-site'})
        self.fields['reception_city'].widget.attrs.update({'id': 'event-reception-city'})
        self.fields['reception_state'].widget.attrs.update({'id': 'event-reception-state'})
        self.fields['reception_contact'].widget.attrs.update({'id': 'event-reception-contact'})
        self.fields['reception_phone'].widget.attrs.update({'id': 'event-reception-phone'})
        self.fields['reception_email'].widget.attrs.update({'id': 'event-reception-email'})


class ContractServicesForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = [
            'photography_package', 'photography_additional', 'engagement_session',
            'videography_package', 'videography_additional',
            'dj_package', 'dj_additional', 'photobooth_package', 'photobooth_additional'
        ]

    def __init__(self, *args, **kwargs):
        super(ContractServicesForm, self).__init__(*args, **kwargs)

        # Initialize photography fields
        self.fields['photography_package'].queryset = Package.objects.filter(service_type__name='Photography',
                                                                             is_active=True)
        self.fields['photography_additional'].queryset = AdditionalEventStaffOption.objects.filter(
            service_type__name='Photography', is_active=True)

        # Initialize engagement session field
        self.fields['engagement_session'].queryset = EngagementSessionOption.objects.filter(is_active=True)

        # Initialize videography fields
        self.fields['videography_package'].queryset = Package.objects.filter(service_type__name='Videography',
                                                                             is_active=True)
        self.fields['videography_additional'].queryset = AdditionalEventStaffOption.objects.filter(
            service_type__name='Videography', is_active=True)

        # Initialize DJ fields
        self.fields['dj_package'].queryset = Package.objects.filter(service_type__name='Dj', is_active=True)
        self.fields['dj_additional'].queryset = AdditionalEventStaffOption.objects.filter(service_type__name='Dj',
                                                                                          is_active=True)

        # Initialize photobooth fields
        self.fields['photobooth_package'].queryset = Package.objects.filter(service_type__name='Photobooth',
                                                                            is_active=True)
        self.fields['photobooth_additional'].queryset = AdditionalEventStaffOption.objects.filter(
            service_type__name='Photobooth', is_active=True)

        # Optionally, add an empty label for each field to show a default choice like "Select an option"
        for field_name in self.fields:
            self.fields[field_name].empty_label = "Select an option"


class ServiceFeeForm(forms.ModelForm):
    applied_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))  # Date input widget

    class Meta:
        model = ServiceFee
        fields = ['contract', 'amount', 'description', 'fee_type', 'applied_date']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control description-field', 'rows': 3}),
            'amount': forms.NumberInput(attrs={'class': 'key-field'}),
            'fee_type': forms.Select(attrs={'class': 'form-control'}),
            'contract': forms.HiddenInput(),  # Assuming contract is not to be edited
        }


ServiceFeeFormSet = inlineformset_factory(
    parent_model=Contract,
    model=ServiceFee,
    form=ServiceFeeForm,
    extra=1,
    can_delete=True  # Allows deletion of service fees directly from the formset
)


class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = ['memo', 'amount', 'service_type']
