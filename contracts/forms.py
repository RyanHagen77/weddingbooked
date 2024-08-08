from django import forms
from contracts.models import (Contract, LeadSourceCategory, Client, Payment, EventStaffBooking, Package, Discount, Location,
                              ContractDocument, PaymentSchedule, SchedulePayment,
                              AdditionalEventStaffOption, EngagementSessionOption, AdditionalProduct, ContractProduct,
                              ServiceFee, ContractAgreement, RiderAgreement, WeddingDayGuide)
from django.core.validators import RegexValidator
from users.models import Role, CustomUser
from django.forms.widgets import DateInput
from django.forms import inlineformset_factory
from django.contrib.auth import get_user_model


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
    ceremony_site = (forms.CharField(max_length=255, required=False))
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
    lead_source_category = forms.ModelChoiceField(queryset=LeadSourceCategory.objects.all(), required=False, label="Lead Source Category")
    lead_source_details = forms.CharField(max_length=255, required=False, label="Lead Source Details")

    old_contract_number = forms.CharField(max_length=255, required=False, label="Old Contract Number")

    class Meta:
        model = Contract
        fields = ['is_code_92', 'event_date', 'location', 'coordinator', 'status', 'csr', 'lead_source_category', 'lead_source_details',
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
        disabled=True,  # Disable the field to make it read-only
        widget=forms.HiddenInput()  # Optionally hide the field if it doesn't need to be visible
    )

    # ... other fields ...

    class Meta:
        model = Client
        fields = '__all__'  # or specify fields

    def __init__(self, *args, **kwargs):
        super(ContractClientEditForm, self).__init__(*args, **kwargs)
        # Disable the user field
        self.fields['user'].disabled = True
        self.fields['primary_contact'].widget.attrs.update({'id': 'client-primary-contact'})
        self.fields['primary_email'].widget.attrs.update({'id': 'client-primary-email'})
        self.fields['primary_phone1'].widget.attrs.update({'id': 'client-primary-phone1'})

        self.fields['partner_contact'].widget.attrs.update({'id': 'client-partner-contact'})
        self.fields['partner_email'].widget.attrs.update({'id': 'client-partner-email'})
        self.fields['partner_phone1'].widget.attrs.update({'id': 'client-partner-phone1'})

        self.fields['primary_address1'].widget.attrs.update({'id': 'client-primary-address1'})
        self.fields['primary_address2'].widget.attrs.update({'id': 'client-primary-address2'})
        self.fields['city'].widget.attrs.update({'id': 'client-city'})
        self.fields['state'].widget.attrs.update({'id': 'client-state'})
        self.fields['postal_code'].widget.attrs.update({'id': 'client-postal-code'})

        self.fields['alt_contact'].widget.attrs.update({'id': 'client-alt-contact'})
        self.fields['alt_email'].widget.attrs.update({'id': 'client-alt-email'})
        self.fields['alt_phone'].widget.attrs.update({'id': 'client-alt-phone'})

    def save(self, commit=True):
        client = super(ContractClientEditForm, self).save(commit=False)

        # Update the associated user email if the primary_email has changed
        if self.changed_data and 'primary_email' in self.changed_data:
            user = client.user
            if user.email != client.primary_email:
                user.email = client.primary_email
                if commit:
                    user.save()

        if commit:
            client.save()

        return client


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
        self.fields['photography_package'].queryset = Package.objects.filter(service_type__name='Photography', is_active=True)
        self.fields['photography_additional'].queryset = AdditionalEventStaffOption.objects.filter(service_type__name='Photography', is_active=True)

        # Initialize engagement session field
        self.fields['engagement_session'].queryset = EngagementSessionOption.objects.filter(is_active=True)

        # Initialize videography fields
        self.fields['videography_package'].queryset = Package.objects.filter(service_type__name='Videography', is_active=True)
        self.fields['videography_additional'].queryset = AdditionalEventStaffOption.objects.filter(service_type__name='Videography', is_active=True)

        # Initialize DJ fields
        self.fields['dj_package'].queryset = Package.objects.filter(service_type__name='Dj', is_active=True)
        self.fields['dj_additional'].queryset = AdditionalEventStaffOption.objects.filter(service_type__name='Dj', is_active=True)

        # Initialize photobooth fields
        self.fields['photobooth_package'].queryset = Package.objects.filter(service_type__name='Photobooth', is_active=True)
        self.fields['photobooth_additional'].queryset = AdditionalEventStaffOption.objects.filter(service_type__name='Photobooth', is_active=True)

        # Optionally, add an empty label for each field to show a default choice like "Select an option"
        for field_name in self.fields:
            self.fields[field_name].empty_label = "Select an option"
class ContractProductForm(forms.ModelForm):
    class Meta:
        model = ContractProduct
        fields = ['product', 'quantity', 'special_notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'special_notes': forms.Textarea(attrs={'class': 'form-control'}),
        }

ContractProductFormset = inlineformset_factory(
    Contract,
    ContractProduct,
    fields=('product', 'quantity', 'special_notes'),
    extra=0,
    can_delete=True
)


class ServiceFeeForm(forms.ModelForm):
    applied_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))  # Date input widget

    class Meta:
        model = ServiceFee
        fields = ['contract', 'amount', 'description', 'fee_type', 'applied_date']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control description-field', 'rows': 3}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'fee_type': forms.Select(attrs={'class': 'form-control'}),
            'contract': forms.HiddenInput(),  # Assuming contract is not to be edited
        }



ServiceFeeFormSet = inlineformset_factory(
    parent_model=Contract,
    model=ServiceFee,
    form=ServiceFeeForm,
    extra=0,
    can_delete=True  # Allows deletion of service fees directly from the formset
)

class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = ['memo', 'amount', 'service_type']

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'payment_purpose', 'payment_reference', 'memo']  # Adjust as per your actual model fields

        # Set required=False for fields that are not mandatory
        widgets = {
            'amount': forms.NumberInput(attrs={'required': False}),
            'payment_method': forms.Select(attrs={'required': False}),
            # Include other fields as needed
        }
class PaymentScheduleForm(forms.ModelForm):
    class Meta:
        model = PaymentSchedule
        fields = ['schedule_type']

class SchedulePaymentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SchedulePaymentForm, self).__init__(*args, **kwargs)
        # Add 'payment-form' class to each field's widget
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'payment-form'

    class Meta:
        model = SchedulePayment
        fields = ('purpose', 'due_date', 'amount')
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'payment-form'}),
        }

SchedulePaymentFormSet = inlineformset_factory(
    PaymentSchedule,
    SchedulePayment,
    form=SchedulePaymentForm,  # Use the custom form
    extra=0,
    can_delete=True
)


class ClientForm(forms.ModelForm):
    primary_phone1 = forms.CharField(
        max_length=12,
        validators=[phone_validator],
        required=True
    )
    primary_phone2 = forms.CharField(
        max_length=12,
        validators=[phone_validator],
        required=False
    )

    class Meta:
        model = Client
        fields = [
            'primary_contact', 'primary_email', 'primary_phone1', 'primary_phone2',
            'primary_address1', 'primary_address2', 'city', 'state', 'postal_code',
            'partner_contact', 'partner_email', 'partner_phone1', 'partner_phone2',
            'alt_contact', 'alt_email', 'alt_phone'
        ]

    def clean_primary_email(self):
        email = self.cleaned_data.get('primary_email')
        if not email:
            raise forms.ValidationError('This field is required.')

        User = get_user_model()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')

        return email

    def clean_primary_phone1(self):
        phone = self.cleaned_data.get('primary_phone1')
        if phone and not phone.isdigit():
            raise forms.ValidationError('Enter a valid phone number.')
        return phone


class NewContractForm(forms.ModelForm):
    is_code_92 = forms.BooleanField(required=False)
    old_contract_number = forms.CharField(max_length=255, required=False)
    location = forms.ModelChoiceField(queryset=Location.objects.all())
    primary_contact = forms.CharField(max_length=255, required=True)
    partner_contact = forms.CharField(max_length=255)
    primary_email = forms.EmailField(required=True)
    primary_phone1 = forms.CharField(
        max_length=12,  # Adjusted to accommodate dashes
        validators=[phone_validator],
        required=False  # Instead of blank=True, null=True
    )
    lead_source_category = forms.ModelChoiceField(queryset=LeadSourceCategory.objects.all(), required=False, label="Lead Source Category")
    lead_source_details = forms.CharField(max_length=255, required=False, label="Lead Source Details")

    event_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)
    csr = UserModelChoiceField(
        queryset=CustomUser.objects.filter(groups__name='Sales', is_active=True),
        required=False,
        label="Sales Person"
    )
    coordinator = UserModelChoiceField(
        queryset=CustomUser.objects.filter(role__name='COORDINATOR', groups__name='Office Staff', is_active=True),
        required=False,
        label="Coordinator"
    )

    # Optional fields
    primary_phone2 = forms.CharField(
        max_length=12,  # Adjusted to accommodate dashes
        validators=[phone_validator],
        required=False  # Instead of blank=True, null=True
    )
    primary_address1 = forms.CharField(max_length=255, required=False)
    primary_address2 = forms.CharField(max_length=255, required=False)
    city = forms.CharField(max_length=255, required=False)
    state = forms.CharField(max_length=255, required=False)
    postal_code = forms.CharField(max_length=255, required=False)
    partner_email = forms.EmailField(required=False)
    partner_phone1 = forms.CharField(
        max_length=12,  # Adjusted to accommodate dashes
        validators=[phone_validator],
        required=False  # Instead of blank=True, null=True
    )
    partner_phone2 = forms.CharField(
        max_length=12,  # Adjusted to accommodate dashes
        validators=[phone_validator],
        required=False  # Instead of blank=True, null=True
    )
    alt_contact = forms.CharField(max_length=255, required=False)
    alt_email = forms.EmailField(required=False)
    alt_phone = forms.CharField(
        max_length=12,  # Adjusted to accommodate dashes
        validators=[phone_validator],
        required=False  # Instead of blank=True, null=True
    )

    class Meta:
        model = Contract
        fields = [
            'event_date', 'csr', 'coordinator', 'old_contract_number', 'is_code_92',
            'bridal_party_qty', 'guests_qty', 'lead_source_category', 'lead_source_details',
            'ceremony_site', 'ceremony_city', 'ceremony_state', 'ceremony_contact', 'ceremony_phone', 'ceremony_email',
            'reception_site', 'reception_city', 'reception_state', 'reception_contact', 'reception_phone', 'reception_email',
            'status'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['csr'].queryset = CustomUser.objects.filter(is_active=True, groups__name='Sales')
        self.fields['coordinator'].queryset = CustomUser.objects.filter(role__name='COORDINATOR', groups__name='Office Staff')

    def save(self, commit=True):
        # Save the contract instance
        contract = super().save(commit=False)
        # Add the location to the contract
        contract.location = self.cleaned_data.get('location')

        # Set is_code_92
        contract.is_code_92 = self.cleaned_data.get('is_code_92', False)

        if commit:
            contract.save()
            self.save_m2m()

        return contract


class ContractForm(forms.ModelForm):
    # Required fields
    is_code_92 = forms.BooleanField(required=False)
    old_contract_number = forms.CharField(max_length=255, required=False)
    location = forms.ModelChoiceField(queryset=Location.objects.all())
    primary_contact = forms.CharField(max_length=255, required=True)
    primary_email = forms.EmailField(required=True)
    primary_phone1 = forms.CharField(
        max_length=12,  # Adjusted to accommodate dashes
        validators=[phone_validator],
        required=False  # Instead of blank=True, null=True
    )
    event_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)
    csr = forms.ModelChoiceField(
        queryset=CustomUser.objects.none(),
        required=True,
        label="Sales Person"
    )
    coordinator = UserModelChoiceField(
        queryset=CustomUser.objects.filter(role__name='coordinator', is_active=True),
        required=False,
        label="Coordinator"
    )

    # Additional fields for Contract set as optional
    bridal_party_qty = forms.IntegerField(min_value=1, required=False)
    guests_qty = forms.IntegerField(min_value=1, required=False)
    lead_source_category = forms.ModelChoiceField(queryset=LeadSourceCategory.objects.all(), required=False, label="Lead Source Category")
    lead_source_details = forms.CharField(max_length=255, required=False, label="Lead Source Details")
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

    photography_package = forms.ModelChoiceField(queryset=Package.objects.none(), required=False)
    photography_additional = forms.ModelChoiceField(queryset=AdditionalEventStaffOption.objects.none(), required=False)
    engagement_session = forms.ModelChoiceField(
        queryset=EngagementSessionOption.objects.filter(is_active=True),
        required=False,
        label='Engagement Session'
    )
    videography_package = forms.ModelChoiceField(queryset=Package.objects.none(), required=False)
    videography_additional = forms.ModelChoiceField(queryset=AdditionalEventStaffOption.objects.none(), required=False)
    dj_package = forms.ModelChoiceField(queryset=Package.objects.none(), required=False)
    dj_additional = forms.ModelChoiceField(queryset=AdditionalEventStaffOption.objects.none(), required=False)
    photobooth_package = forms.ModelChoiceField(queryset=Package.objects.none(), required=False)
    photobooth_additional = forms.ModelChoiceField(queryset=Package.objects.none(), required=False)

    prospect_photographer1 = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role__name='PHOTOGRAPHER'),
        required=False,
        label="Prospect Photographer 1",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    prospect_photographer2 = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role__name='PHOTOGRAPHER'),
        required=False,
        label="Prospect Photographer 2",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    prospect_photographer3 = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role__name='PHOTOGRAPHER'),
        required=False,
        label="Prospect Photographer 3",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Fields for discounts
    class Meta:
        model = Contract
        fields = [
            'event_date', 'csr', 'coordinator', 'custom_text', 'old_contract_number',# These fields are now at the top
            # Client fields
            'is_code_92', 'primary_contact', 'primary_email', 'primary_phone1', 'primary_phone2',
            'primary_address1', 'primary_address2', 'city', 'state', 'postal_code',
            'partner_contact', 'partner_email', 'partner_phone1', 'partner_phone2',
            'alt_contact', 'alt_email', 'alt_phone',

            # Contract fields
            'bridal_party_qty', 'guests_qty', 'lead_source_category', 'lead_source_details',
            'ceremony_site', 'ceremony_city', 'ceremony_state', 'ceremony_contact', 'ceremony_phone', 'ceremony_email',
            'reception_site', 'reception_city', 'reception_state', 'reception_contact', 'reception_phone', 'reception_email',
            'status',

            # Service package fields
            'photography_package', 'photography_additional', 'engagement_session',
            'videography_package', 'videography_additional',
            'dj_package', 'dj_additional', 'photobooth_package', 'photobooth_additional', 'custom_text',
            'total_cost',

            # Discount Fields

            # Prospect photographer fields
            'prospect_photographer1', 'prospect_photographer2', 'prospect_photographer3'
        ]

        widgets = {
            'custom_text': forms.Textarea(attrs={'rows': 4}),

        }

    primary_phone2 = forms.CharField(
        max_length=12,  # Adjusted to accommodate dashes
        validators=[phone_validator],
        required=False  # Instead of blank=True, null=True
    )
    primary_address1 = forms.CharField(max_length=255, required=False)
    primary_address2 = forms.CharField(max_length=255, required=False)
    city = forms.CharField(max_length=255, required=False)
    state = forms.CharField(max_length=255, required=False)
    postal_code = forms.CharField(max_length=255, required=False)
    partner_contact = forms.CharField(max_length=255, required=False)
    partner_email = forms.EmailField(required=False)
    partner_phone1 = forms.CharField(
        max_length=12,  # Adjusted to accommodate dashes
        validators=[phone_validator],
        required=False  # Instead of blank=True, null=True
    )
    partner_phone2 = forms.CharField(
        max_length=12,  # Adjusted to accommodate dashes
        validators=[phone_validator],
        required=False  # Instead of blank=True, null=True
    )
    alt_contact = forms.CharField(max_length=255, required=False)
    alt_email = forms.EmailField(required=False)
    alt_phone = forms.CharField(
        max_length=12,  # Adjusted to accommodate dashes
        validators=[phone_validator],
        required=False  # Instead of blank=True, null=True
    )

    additional_products = forms.ModelMultipleChoiceField(
        queryset=AdditionalProduct.objects.all(),
        widget=forms.SelectMultiple(attrs={'size': 5}),  # Use SelectMultiple with size attribute
        required=False,  # Adjust as needed
    )

    # Field for displaying tax rate
    current_tax_rate = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        disabled=True,
        label='Current Tax Rate (%)'
    )

    def __init__(self, *args, **kwargs):
        super(ContractForm, self).__init__(*args, **kwargs)
        contract = kwargs.get('instance')

        # Initialize the formset
        self.product_formset = ContractProductFormset(instance=self.instance if self.instance else None)

        # Set the queryset for the CSR and coordinator fields
        self.fields['csr'].queryset = CustomUser.objects.filter(role__name='SALES PERSON')
        self.fields['coordinator'].queryset = CustomUser.objects.filter(groups__name='Office Staff')

        # Fetch the photographer role object and initialize photographer dropdowns
        photographer_role = Role.objects.filter(name='PHOTOGRAPHER').first()
        photographer_queryset = CustomUser.objects.filter(
            role=photographer_role) if photographer_role else CustomUser.objects.none()
        photographer_fields = ['prospect_photographer1', 'prospect_photographer2', 'prospect_photographer3']
        for field_name in photographer_fields:
            self.fields[field_name].queryset = photographer_queryset

        # Set initial value for the current tax rate
        self.fields['current_tax_rate'].initial = 0.00  # You can set it based on your logic

    def clean_old_contract_number(self):
        old_contract_number = self.cleaned_data.get('old_contract_number')
        return old_contract_number

    def clean(self):
        cleaned_data = super().clean()  # Call the base class's clean method
        print("Cleaned data:", cleaned_data)

        print("Prospect Photographer 1:", cleaned_data.get('prospect_photographer1'))
        print("Prospect Photographer 2:", cleaned_data.get('prospect_photographer2'))
        print("Prospect Photographer 3:", cleaned_data.get('prospect_photographer3'))

        # You can inspect individual fields as well
        photography_package = cleaned_data.get('photography_package')
        print("Photography package ID:", photography_package)

        # Always return the full collection of cleaned data
        return cleaned_data

    def save(self, user, commit=True):
        # Save the contract instance
        contract = super().save(commit=False)

        # Add the location to the contract
        contract.location = self.cleaned_data.get('location')

        # Set the prospect photographers for the contract
        contract.prospect_photographer1 = self.cleaned_data.get('prospect_photographer1')
        contract.prospect_photographer2 = self.cleaned_data.get('prospect_photographer2')
        contract.prospect_photographer3 = self.cleaned_data.get('prospect_photographer3')

        print("Saving Prospect Photographer 1:", contract.prospect_photographer1)
        print("Saving Prospect Photographer 2:", contract.prospect_photographer2)
        print("Saving Prospect Photographer 3:", contract.prospect_photographer3)

        # Prepare client data
        client_data = {field: self.cleaned_data[field] for field in [
            'primary_contact', 'primary_email', 'primary_phone1', 'primary_phone2',
            'primary_address1', 'primary_address2', 'city', 'state', 'postal_code',
            'partner_contact', 'partner_email', 'partner_phone1', 'partner_phone2',
            'alt_contact', 'alt_email', 'alt_phone']}

        # Create or update the client instance
        if contract.client_id:
            # Update existing client
            Client.objects.filter(id=contract.client_id).update(**client_data)
            client = Client.objects.get(id=contract.client_id)
        else:
            # Create new client and associate with user
            client = Client.objects.create(user=user, **client_data)

        contract.client = client

        if commit:
            contract.save()  # Save the contract instance
            self.save_m2m()  # Save many-to-many data for the form

            # Handle additional products
            selected_product_ids = set(self.cleaned_data.get('additional_products', []))
            existing_product_ids = set(contract.contract_products.values_list('product_id', flat=True))

            # Create or update products
            for product_id in selected_product_ids:
                ContractProduct.objects.update_or_create(
                    contract=contract,
                    product_id=product_id,
                    defaults={'quantity': 1}  # Modify as needed
                )

            # Remove any unselected products
            for product_id in existing_product_ids - selected_product_ids:
                ContractProduct.objects.filter(contract=contract, product_id=product_id).delete()

            # Save the contract again to update related fields
            contract.save()
            self.save_m2m()  # Save many-to-many data for the form




class ContractDocumentForm(forms.ModelForm):
    is_client_visible = forms.BooleanField(
        initial=False,
        required=False,
        widget=forms.CheckboxInput(attrs={'style': 'font-size: 11pt;'})
    )
    class Meta:
        model = ContractDocument
        fields = ['document', 'is_client_visible']


class EventStaffBookingForm(forms.ModelForm):
    booking_id = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = EventStaffBooking
        fields = ['role', 'staff', 'status', 'confirmed', 'hours_booked', 'booking_id']

class ContractAgreementForm(forms.ModelForm):
    main_signature = forms.CharField(widget=forms.HiddenInput(), required=True)

    class Meta:
        model = ContractAgreement
        fields = ['main_signature', 'photographer_choice']


class RiderAgreementForm(forms.ModelForm):
    signature = forms.CharField(widget=forms.HiddenInput(), required=True)

    class Meta:
        model = RiderAgreement
        fields = ['signature', 'client_name', 'agreement_date', 'notes']

class WeddingDayGuideForm(forms.ModelForm):
    class Meta:
        model = WeddingDayGuide
        fields = [
            'event_date', 'primary_contact', 'primary_email', 'primary_phone',
            'partner_contact', 'partner_email', 'partner_phone', 'dressing_location',
            'dressing_address', 'dressing_start_time', 'ceremony_site',
            'ceremony_address', 'ceremony_phone', 'ceremony_start', 'ceremony_end',
            'reception_site', 'reception_address', 'reception_phone',
            'reception_start', 'dinner_start', 'reception_end', 'staff_table', 'photo_stop1',
            'photo_stop2', 'photo_stop3', 'photo_stop4', 'photographer2_start_location',
            'photographer2_start_location_address', 'photographer2_start', 'maid_of_honor',
            'bridesmaids_qty', 'flower_girl_qty', 'usher_qty', 'best_man',
            'groomsmen_qty', 'ring_bearer_qty', 'bride_parents_names',
            'bride_sibling_names', 'bride_grandparents_names', 'groom_parents_names',
            'groom_siblings_names', 'groom_grandparents_names',
            'additional_photo_request1', 'additional_photo_request2',
            'additional_photo_request3', 'additional_photo_request4',
            'additional_photo_request5', 'video_client_names', 'wedding_story_song_title',
            'wedding_story_song_artist', 'dance_montage_song_title', 'dance_montage_song_artist',
            'video_special_dances', 'photo_booth_text_line1', 'photo_booth_text_line2', 'photo_booth_placement'
        ]
        widgets = {
            'event_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
            'dressing_start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm'}),
            'ceremony_start': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm'}),
            'ceremony_end': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm'}),
            'reception_start': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm'}),
            'dinner_start': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm'}),
            'reception_end': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm'}),
            'bride_parents_names': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'bride_sibling_names': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'bride_grandparents_names': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'groom_parents_names': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'groom_siblings_names': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'groom_grandparents_names': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'primary_contact': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'primary_email': forms.EmailInput(attrs={'class': 'form-control form-control-sm'}),
            'primary_phone': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'partner_contact': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'partner_email': forms.EmailInput(attrs={'class': 'form-control form-control-sm'}),
            'partner_phone': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'dressing_location': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'dressing_address': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'ceremony_site': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'ceremony_address': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'ceremony_phone': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'reception_site': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'reception_address': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'reception_phone': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'photo_stop1': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'photo_stop2': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'photo_stop3': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'photo_stop4': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'photographer2_start_location': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'photographer2_start_location_address': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'photographer2_start': forms.TimeInput(attrs={'class': 'form-control form-control-sm'}),
            'maid_of_honor': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'bridesmaids_qty': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'flower_girl_qty': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'usher_qty': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'best_man': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'groomsmen_qty': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'ring_bearer_qty': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'additional_photo_request1': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'additional_photo_request2': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'additional_photo_request3': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'additional_photo_request4': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'additional_photo_request5': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'video_client_names': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'wedding_story_song_title': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'wedding_story_song_artist': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'dance_montage_song_title': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'dance_montage_song_artist': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'video_special_dances': forms.Textarea(attrs={'class': 'form-control form-control-sm'}),
            'photo_booth_text_line1': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'photo_booth_text_line2': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'photo_booth_placement': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }

    def __init__(self, *args, **kwargs):
        self.strict_validation = kwargs.pop('strict_validation', True)
        contract = kwargs.pop('contract', None)
        super().__init__(*args, **kwargs)
        if contract:
            client = contract.client
            self.fields['event_date'].initial = contract.event_date
            self.fields['primary_contact'].initial = client.primary_contact
            self.fields['primary_email'].initial = client.primary_email
            self.fields['primary_phone'].initial = client.primary_phone1
            self.fields['partner_contact'].initial = client.partner_contact
            self.fields['partner_email'].initial = client.partner_email
            self.fields['partner_phone'].initial = client.partner_phone1
            self.fields['ceremony_site'].initial = contract.ceremony_site
            self.fields['reception_site'].initial = contract.reception_site

        # Make all fields optional initially
        for field in self.fields:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        if self.strict_validation:
            for field in self.Meta.fields:
                if not cleaned_data.get(field):
                    self.add_error(field, f"{field.replace('_', ' ').title()} is required.")
        return cleaned_data
