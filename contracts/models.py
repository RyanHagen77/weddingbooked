# contracts/models.py

from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, EmailValidator
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import re
from django.db import transaction
from bookings.constants import SERVICE_ROLE_MAPPING  # Adjust the import path as needed
from services.models import ServiceType

phone_validator = RegexValidator(
    regex=r'^\d{3}-\d{3}-\d{4}$',
    message='Phone number must be in the format XXX-XXX-XXXX.'
)

CustomUser = get_user_model()

ROLE_CHOICES = [(key, value) for key, value in SERVICE_ROLE_MAPPING.items()]


class Location(models.Model):
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True, verbose_name="Active")
    address = models.CharField(max_length=255)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.name


class TaxRate(models.Model):
    objects = None
    is_active = models.BooleanField(default=True, verbose_name="Active")
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.location.name} - {self.tax_rate}%"


class Client(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    primary_contact = models.CharField(max_length=255)
    primary_email = models.EmailField(unique=False)
    primary_phone1 = models.CharField(
        max_length=12,  # Increase max_length to accommodate dashes
        validators=[phone_validator],
        blank=True,
        null=True
    )
    primary_phone2 = models.CharField(
        max_length=12,  # Increase max_length to accommodate dashes
        validators=[phone_validator],
        blank=True,
        null=True
    )
    primary_address1 = models.CharField(max_length=255, blank=True, null=True)
    primary_address2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    partner_contact = models.CharField(max_length=255, blank=True, null=True)
    partner_email = models.EmailField(validators=[EmailValidator()], blank=True, null=True)
    partner_phone1 = models.CharField(
        max_length=12,  # Increase max_length to accommodate dashes
        validators=[phone_validator],
        blank=True,
        null=True
    )
    partner_phone2 = models.CharField(
        max_length=12,  # Increase max_length to accommodate dashes
        validators=[phone_validator],
        blank=True,
        null=True
    )
    alt_contact = models.CharField(max_length=255, blank=True, null=True)
    alt_email = models.EmailField(validators=[EmailValidator()], blank=True, null=True)
    alt_phone = models.CharField(
        max_length=12,  # Increase max_length to accommodate dashes
        validators=[phone_validator],
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['primary_contact']

    def __str__(self):
        return self.primary_contact

    def get_primary_contact_last_name(self):
        return self.primary_contact.split()[-1][:3].upper()

    def save(self, *args, **kwargs):
        updating_user_email = False
        if self.pk:
            # Check if the primary_email field is being changed
            old_client = Client.objects.get(pk=self.pk)
            if old_client.primary_email != self.primary_email:
                updating_user_email = True

        with transaction.atomic():
            super().save(*args, **kwargs)
            if updating_user_email:
                self.user.email = self.primary_email
                self.user.save()


class Discount(models.Model):
    memo = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    service_type = models.ForeignKey('services.ServiceType', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.memo} - {self.amount} - {self.service_type}"


class DiscountRule(models.Model):
    PACKAGE = 'Package'
    SUNDAY = 'Sunday'

    DISCOUNT_TYPE_CHOICES = [
        (PACKAGE, 'Package Discounts'),
        (SUNDAY, 'Sunday Discounts'),
    ]

    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    base_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    version = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('discount_type', 'version')

    def __str__(self):
        return f"{self.get_discount_type_display()} - Version {self.version} - {self.base_amount}"


class LeadSourceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Contract(models.Model):
    # Choice Constants
    ONLINE = 'ONLINE'
    REFERRAL = 'REFERRAL'
    LEAD_SOURCE_CATEGORY_CHOICES = [
        (ONLINE, 'Online'),
        (REFERRAL, 'Referral'),
    ]

    PIPELINE = 'pipeline'
    FORECAST = 'forecast'
    BOOKED = 'booked'
    COMPLETED = 'completed'
    DEAD = 'dead'
    STATUS_CHOICES = [
        (PIPELINE, 'Pipeline'),
        (FORECAST, 'Forecast'),
        (BOOKED, 'Booked'),
        (COMPLETED, 'Completed'),
        (DEAD, 'Dead'),
    ]

    # Model Fields
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PIPELINE)
    contract_id = models.AutoField(primary_key=True)
    old_contract_number = models.CharField(max_length=50, blank=True, null=True)
    custom_contract_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    contract_date = models.DateField(auto_now_add=True)
    event_date = models.DateField()
    booked_date = models.DateField(null=True, blank=True)

    # Foreign Keys
    location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True)
    csr = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                            related_name='contracts_managed')
    coordinator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='contracts_coordinated')
    lead_source_category = models.ForeignKey('LeadSourceCategory', on_delete=models.SET_NULL, null=True, blank=True)
    client = models.ForeignKey('Client', on_delete=models.CASCADE, null=True)

    # Contact Information
    is_code_92 = models.BooleanField(default=False, verbose_name="Code 92 Flag")
    lead_source_details = models.CharField(max_length=255, blank=True)
    bridal_party_qty = models.PositiveIntegerField(validators=[MinValueValidator(1)], null=True, blank=True)
    guests_qty = models.PositiveIntegerField(validators=[MinValueValidator(1)], null=True, blank=True)

    # Ceremony and Reception Information
    ceremony_site = models.CharField(max_length=255, null=True, blank=True)
    ceremony_city = models.CharField(max_length=255, null=True, blank=True)
    ceremony_state = models.CharField(max_length=255, null=True, blank=True)
    ceremony_contact = models.CharField(max_length=255, null=True, blank=True)
    ceremony_phone = models.CharField(max_length=12, validators=[phone_validator], blank=True, null=True)
    ceremony_email = models.EmailField(validators=[EmailValidator()], null=True, blank=True)
    reception_site = models.CharField(max_length=255, null=True, blank=True)
    reception_city = models.CharField(max_length=255, null=True, blank=True)
    reception_state = models.CharField(max_length=255, null=True, blank=True)
    reception_contact = models.CharField(max_length=255, null=True, blank=True)
    reception_phone = models.CharField(max_length=12, validators=[phone_validator], blank=True, null=True)
    reception_email = models.EmailField(validators=[EmailValidator()], null=True, blank=True)

    # Miscellaneous Fields
    staff_notes = models.TextField(blank=True, null=True)
    contract_document = models.FileField(upload_to='contracts/', null=True, blank=True)

    # Event Staff Linking
    photographer1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='photographer1_contracts')
    photographer2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='photographer2_contracts')
    videographer1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='videographer1_contracts')
    videographer2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='videographer2_contracts')
    dj1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                            related_name='dj1_contracts')
    dj2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                            related_name='dj2_contracts')
    photobooth_op1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='photobooth_op1_contracts')
    photobooth_op2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='photobooth_op2_contracts')

    # Additional Event Staff
    prospect_photographer1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                               related_name='prospect_photographer1_contracts')
    prospect_photographer2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                               related_name='prospect_photographer2_contracts')
    prospect_photographer3 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                               related_name='prospect_photographer3_contracts')

    # Service Packages and Options
    photography_package = models.ForeignKey('services.Package', on_delete=models.SET_NULL, null=True, blank=True,
                                            related_name='photography_packages',
                                            limit_choices_to={'service_type__name': 'Photography', 'is_active': True})
    photography_additional = models.ForeignKey('services.AdditionalEventStaffOption',
                                               on_delete=models.SET_NULL, null=True,
                                               blank=True, related_name='additional_photography_options',
                                               limit_choices_to={'service_type__name': 'Photography',
                                                                 'is_active': True})
    engagement_session = models.ForeignKey('services.EngagementSessionOption',
                                           on_delete=models.SET_NULL, null=True, blank=True,
                                           related_name='engagement_session_options',
                                           limit_choices_to={'is_active': True})
    videography_package = models.ForeignKey('services.Package', on_delete=models.SET_NULL, null=True, blank=True,
                                            related_name='videography_packages',
                                            limit_choices_to={'service_type__name': 'Videography', 'is_active': True})
    videography_additional = models.ForeignKey('services.AdditionalEventStaffOption',
                                               on_delete=models.SET_NULL, null=True,
                                               blank=True, related_name='additional_videography_options',
                                               limit_choices_to={'service_type__name': 'Videography',
                                                                 'is_active': True})
    dj_package = models.ForeignKey('services.Package', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='dj_packages',
                                   limit_choices_to={'service_type__name': 'Dj', 'is_active': True})
    dj_additional = models.ForeignKey('services.AdditionalEventStaffOption',
                                      on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='additional_dj_options',
                                      limit_choices_to={'service_type__name': 'Dj', 'is_active': True})
    photobooth_package = models.ForeignKey('services.Package', on_delete=models.SET_NULL, null=True, blank=True,
                                           related_name='photobooth_packages',
                                           limit_choices_to={'service_type__name': 'Photobooth', 'is_active': True})
    photobooth_additional = models.ForeignKey('services.AdditionalEventStaffOption',
                                              on_delete=models.SET_NULL, null=True,
                                              blank=True,
                                              related_name='additional_photobooth_options',
                                              limit_choices_to={'service_type__name': 'Photobooth', 'is_active': True})

    # Additional Fields
    overtime_options = models.ManyToManyField('services.OvertimeOption', through='services.ContractOvertime',
                                              related_name='contracts')
    custom_text = models.TextField(blank=True, null=True)
    package_discount_version = models.IntegerField(default=1)
    sunday_discount_version = models.IntegerField(default=1)
    other_discounts = models.ManyToManyField('Discount', related_name='contracts', blank=True)
    additional_products = models.ManyToManyField('products.AdditionalProduct', through='products.ContractProduct',
                                                 related_name='contracts')

    # Calculated fields
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    calculated_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid_field = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    balance_due_field = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)

    def __str__(self):
        return self.custom_contract_number or f"Contract {self.contract_id}"

    def get_lead_source_display(self):
        if self.lead_source_category and self.lead_source_details:
            return f"{self.lead_source_category.name}: {self.lead_source_details}"
        elif self.lead_source_category:
            return self.lead_source_category.name
        elif self.lead_source_details:
            return self.lead_source_details
        return 'Unknown Source'

    def calculate_photography_cost(self):
        photography_base_cost = self.photography_package.price if self.photography_package else Decimal('0.00')
        additional_photography_cost = self.photography_additional.price if self.photography_additional else Decimal(
            '0.00')
        engagement_session_cost = self.engagement_session.price if self.engagement_session else Decimal('0.00')
        photography_service_type = ServiceType.objects.get(name='Photography')
        photography_overtime_cost = sum(
            overtime.hours * overtime.overtime_option.rate_per_hour
            for overtime in self.overtimes.filter(overtime_option__service_type=photography_service_type)
        )
        total_photography_cost = (photography_base_cost + additional_photography_cost +
                                  engagement_session_cost + photography_overtime_cost)
        return total_photography_cost.quantize(Decimal('.00'), rounding=ROUND_HALF_UP)

    def calculate_videography_cost(self):
        videography_base_cost = self.videography_package.price if self.videography_package else Decimal('0.00')
        additional_videography_cost = self.videography_additional.price if self.videography_additional else Decimal(
            '0.00')
        videography_service_type = ServiceType.objects.get(name='Videography')
        videography_overtime_cost = sum(
            overtime.hours * overtime.overtime_option.rate_per_hour
            for overtime in self.overtimes.filter(overtime_option__service_type=videography_service_type)
        )
        return (videography_base_cost + additional_videography_cost + videography_overtime_cost).quantize(
            Decimal('.00'), rounding=ROUND_HALF_UP)

    def calculate_dj_cost(self):
        dj_base_cost = self.dj_package.price if self.dj_package else Decimal('0.00')
        additional_dj_cost = self.dj_additional.price if self.dj_additional else Decimal('0.00')
        dj_service_type = ServiceType.objects.get(name='Dj')
        dj_overtime_cost = sum(
            overtime.hours * overtime.overtime_option.rate_per_hour
            for overtime in self.overtimes.filter(overtime_option__service_type=dj_service_type)
        )
        return (dj_base_cost + additional_dj_cost + dj_overtime_cost).quantize(Decimal('.00'), rounding=ROUND_HALF_UP)

    def calculate_photobooth_cost(self):
        photobooth_base_cost = self.photobooth_package.price if self.photobooth_package else Decimal('0.00')
        additional_photobooth_cost = self.photobooth_additional.price if self.photobooth_additional else Decimal('0.00')
        photobooth_service_type = ServiceType.objects.get(name='Photobooth')
        photobooth_overtime_cost = sum(
            overtime.hours * overtime.overtime_option.rate_per_hour
            for overtime in self.overtimes.filter(overtime_option__service_type=photobooth_service_type)
        )
        return (photobooth_base_cost + additional_photobooth_cost +
                photobooth_overtime_cost).quantize(Decimal('.00'),
                                                   rounding=ROUND_HALF_UP)

    def is_sunday_event(self):
        return self.event_date.weekday() == 6

    def calculate_package_discount(self):
        discount_rule = DiscountRule.objects.filter(
            discount_type=DiscountRule.PACKAGE,
            version=self.package_discount_version,
            is_active=True
        ).first()

        if not discount_rule:
            return Decimal('0.00')

        selected_services = [self.photography_package, self.videography_package, self.dj_package]
        selected_services = [p for p in selected_services if p is not None]
        is_photobooth_selected = self.photobooth_package is not None

        discount = Decimal('0.00')
        base_amount = discount_rule.base_amount

        if len(selected_services) >= 2:
            discount += base_amount * len(selected_services)
            if is_photobooth_selected:
                discount += base_amount
        elif is_photobooth_selected and len(selected_services) == 1:
            discount += base_amount

        return discount.quantize(Decimal('.00'), rounding=ROUND_HALF_UP)

    def calculate_sunday_discount(self):
        if self.is_sunday_event():
            selected_services = [self.photography_package, self.videography_package, self.dj_package,
                                 self.photobooth_package]
            selected_services = [p for p in selected_services if p is not None]
            discount = Decimal('100.00') * len(selected_services)
            return discount.quantize(Decimal('.00'), rounding=ROUND_HALF_UP)
        return Decimal('0.00')

    @property
    def other_discounts_total(self):
        return self.other_discounts.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')

    def calculate_discount(self):
        total_discount = Decimal('0.00')
        total_discount += self.calculate_package_discount() + self.calculate_sunday_discount()
        total_discount += self.other_discounts_total
        return total_discount

    def calculate_total_service_cost_after_discounts(self):
        subtotal = sum([
            self.calculate_photography_cost(),
            self.calculate_videography_cost(),
            self.calculate_dj_cost(),
            self.calculate_photobooth_cost()
        ])
        total_discount = self.calculate_discount()
        total_cost_after_discounts = subtotal - total_discount
        return total_cost_after_discounts.quantize(Decimal('.00'), rounding=ROUND_HALF_UP)

    def calculate_product_subtotal(self):
        """
        Calculate the subtotal of all products associated with this contract.
        """
        return sum(
            contract_product.product.price * contract_product.quantity
            for contract_product in self.contract_products.all()
        )

    def calculate_tax(self):
        taxable_amount = sum(
            contract_product.product.price * contract_product.quantity
            for contract_product in self.contract_products.all()
            if contract_product.product.is_taxable
        )
        tax_rate = self.location.tax_rate if self.location else Decimal('0.00')
        return taxable_amount * tax_rate / 100

    def calculate_total_service_fees(self):
        return sum(fee.amount for fee in self.servicefees.all())

    def calculate_total_product_cost(self):
        product_subtotal = self.calculate_product_subtotal()
        tax_amount = self.calculate_tax()
        total_cost = product_subtotal + tax_amount
        return total_cost.quantize(Decimal('.00'), rounding=ROUND_HALF_UP)

    def calculate_total_service_cost(self):
        total_service_cost = sum([
            self.calculate_photography_cost(),
            self.calculate_videography_cost(),
            self.calculate_dj_cost(),
            self.calculate_photobooth_cost()
        ])
        return total_service_cost.quantize(Decimal('.00'), rounding=ROUND_HALF_UP)

    def calculate_total_cost(self):
        total_service_cost = self.calculate_total_service_cost()
        total_service_fees = self.calculate_total_service_fees()
        additional_products_cost = self.calculate_product_subtotal()
        subtotal = total_service_cost + additional_products_cost + total_service_fees
        tax = self.calculate_tax()
        discounts = self.calculate_discount()
        total_cost = subtotal + tax - discounts
        return total_cost.quantize(Decimal('.00'), rounding=ROUND_HALF_UP)

    @property
    def final_total(self):
        return self.calculate_total_cost()

    @property
    def amount_paid(self):
        if self.pk:
            return sum(payment.amount for payment in self.payments.all()) or Decimal('0.00')
        return Decimal('0.00')

    @property
    def balance_due(self):
        if self.pk:
            balance = self.final_total - self.amount_paid
            return max(Decimal('0.00'), balance)
        return self.final_total

    def display_calculated_tax(self):
        return self.calculate_tax()

    display_calculated_tax.short_description = "Calculated Tax"

    def display_total_service_cost(self):
        return self.calculate_total_service_cost()

    display_total_service_cost.short_description = "Total Service Cost"

    def display_product_subtotal(self):
        return self.calculate_product_subtotal()

    display_product_subtotal.short_description = "Product Subtotal"

    def display_discounts(self):
        return self.calculate_discount()

    display_discounts.short_description = "Total Discounts"

    def display_total_cost(self):
        return self.calculate_total_cost()

    display_total_cost.short_description = "Total Cost"

    def save(self, *args, **kwargs):
        """Custom save method to handle custom contract number generation and tax calculations."""
        print("Entering save method")

        # Generate custom contract number if not already set
        if not self.custom_contract_number:
            year, month = timezone.now().strftime("%y"), timezone.now().strftime("%m")

            # Extract first 3 letters of the primary contact's last name
            primary_contact_last_name = "UNK"  # Default value
            if self.client and self.client.primary_contact:
                name_parts = self.client.primary_contact.split()
                primary_contact_last_name = (
                    name_parts[-1][:3].upper() if len(name_parts) > 1 else name_parts[0][:3].upper()
                )

            # Generate custom contract number
            with transaction.atomic():
                regex_pattern = rf'^[A-Z]{{3}}-{year}-{month}-(\d+)$'
                contracts = Contract.objects.filter(custom_contract_number__regex=regex_pattern).order_by(
                    '-custom_contract_number'
                )
                new_number = max(
                    (
                        int(re.search(r'-(\d+)$', contract.custom_contract_number).group(1))
                        for contract in contracts if re.search(r'-(\d+)$', contract.custom_contract_number)
                    ),
                    default=0,
                ) + 1
                self.custom_contract_number = f"{primary_contact_last_name}-{year}-{month}-{str(new_number).zfill(2)}"

        # Set tax rate based on location
        self.tax_rate = self.location.tax_rate if self.location and self.location.tax_rate else Decimal("0.00")
        if not self.location or not self.location.tax_rate:
            print("Location or tax rate not set; defaulting to 0.")

        # Save the instance to generate a primary key if not already saved
        if not self.pk:
            super().save(*args, **kwargs)
            print("Initial save completed, primary key generated.")

        # Perform calculations requiring a saved instance
        taxable_amount = Decimal("0.00")
        for contract_product in self.contract_products.all():
            if contract_product.product.is_taxable:
                taxable_amount += contract_product.product.price * contract_product.quantity

        # Calculate tax amount
        self.tax_amount = taxable_amount * self.tax_rate / 100

        # Calculate discounts
        self.calculated_discount = self.calculate_package_discount() or Decimal("0.00")
        self.total_discount = self.calculate_discount() or Decimal("0.00")

        # Calculate total cost
        self.total_cost = self.calculate_total_cost()

        # Save all calculated fields
        super().save(*args, **kwargs)
        print("Final save completed with calculated fields.")


class ServiceFeeType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class ServiceFee(models.Model):
    contract = models.ForeignKey(Contract, related_name='servicefees', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    description = models.TextField(blank=True, default='')  # Allow blank and provide a default
    fee_type = models.ForeignKey(ServiceFeeType, on_delete=models.SET_NULL, null=True, default=None)
    applied_date = models.DateField()  # Date field for the date the fee was applied

    def __str__(self):
        return f"Service Fee - {self.amount}"


class ChangeLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    description = models.TextField()
    previous_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    contract = models.ForeignKey('Contract', on_delete=models.CASCADE, related_name='changelogs')

    def __str__(self):
        return f"{self.timestamp} - {self.user}"
