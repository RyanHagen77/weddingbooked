

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

class ServiceType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


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
    postal_code = models.CharField(max_length=255, blank=True, null=True)
    partner_contact = models.CharField(max_length=255, blank=True, null=True)
    partner_email = models.EmailField(validators=[EmailValidator], blank=True, null=True)
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
    alt_email = models.EmailField(validators=[EmailValidator], blank=True, null=True)
    alt_phone = models.CharField(
        max_length=12,  # Increase max_length to accommodate dashes
        validators=[phone_validator],
        blank=True,
        null=True
    )
    def get_primary_contact_last_name(self):
        return self.primary_contact.split()[-1][:3].upper()

    def __str__(self):
        return self.primary_contact


class Package(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True, verbose_name="Active")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    deposit = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Deposit Amount")
    service_type = models.ForeignKey('ServiceType', on_delete=models.CASCADE, null=True, blank=True, related_name='packages')
    hours = models.IntegerField(verbose_name="Hours", default=0)
    default_text = models.TextField(blank=True, help_text="Default text for the package")
    rider_text = models.TextField(blank=True, help_text="Rider for the package")
    package_notes = models.TextField(blank=True, help_text="Additional notes for the package")

    def __str__(self):
        return f"{self.name} - {self.service_type.name if self.service_type else 'No Type'}"



class AdditionalEventStaffOption(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True, verbose_name="Active")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    deposit = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Deposit Amount")
    service_type = models.ForeignKey('ServiceType', on_delete=models.CASCADE, null=True, blank=True, related_name='event_staff_options')
    hours = models.IntegerField(verbose_name="Hours", default=0)
    default_text = models.TextField(blank=True, help_text="Default text for the staff option")
    rider_text = models.TextField(blank=True, help_text="Rider for the package")
    package_notes = models.TextField(blank=True, help_text="Additional notes for the staff option")

    def __str__(self):
        # Updated to reflect the relationship with ServiceType
        return f"{self.name} ({self.service_type.name if self.service_type else 'No Type'})"

class EngagementSessionOption(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True, verbose_name="Active")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    deposit = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Deposit Amount")
    default_text = models.TextField(blank=True, help_text="Default text for the package")
    rider_text = models.TextField(blank=True, help_text="Rider for the package")
    package_notes = models.TextField(blank=True, help_text="Additional notes for the package")
    service_type = models.ForeignKey('ServiceType', on_delete=models.CASCADE, null=True, blank=True, related_name='engagement_session_options')



    def __str__(self):
        return self.name

class AdditionalProduct(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=5, decimal_places=2)  # Price to customer
    cost = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)  # Internal cost
    is_taxable = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    default_text = models.TextField(blank=True, help_text="Default text for products")


    def __str__(self):
        return f"{self.name} - ${self.price}"


class OvertimeOption(models.Model):
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    name = models.CharField(max_length=100)  # For dropdown display
    is_active = models.BooleanField(default=True, verbose_name="Active")
    rate_per_hour = models.DecimalField(max_digits=6, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name='overtime_options')

    def __str__(self):
        return f"{self.name} - ${self.rate_per_hour}/hr"

class StaffOvertime(models.Model):
    staff_member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contract = models.ForeignKey('Contract', on_delete=models.CASCADE)
    overtime_option = models.ForeignKey(OvertimeOption, on_delete=models.SET_NULL, null=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    overtime_hours = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        return f"{self.staff_member.username} - {self.overtime_hours} hours for {self.contract}"


class Discount(models.Model):
    memo = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    service_type = models.ForeignKey(ServiceType, on_delete=models.SET_NULL, null=True, blank=True)

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

    LEAD_SOURCE_CATEGORY_CHOICES = (
        ('ONLINE', 'Online'),
        ('REFERRAL', 'Referral'),
    )

    objects = models.Manager()

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

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=PIPELINE,
    )

    contract_id = models.AutoField(primary_key=True)
    old_contract_number = models.CharField(max_length=50, unique=False, blank=True, null=True)
    custom_contract_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    contract_date = models.DateField(auto_now_add=True)
    event_date = models.DateField()
    booked_date = models.DateField(null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    csr = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='contracts_managed'
    )
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contracts_coordinated'
    )

    lead_source_category = models.ForeignKey(LeadSourceCategory, on_delete=models.SET_NULL, null=True, blank=True)
    lead_source_details = models.CharField(max_length=255, blank=True)
    # Other fields...

    def get_lead_source_display(self):
        if self.lead_source_category and self.lead_source_details:
            return f"{self.lead_source_category.name}: {self.lead_source_details}"
        elif self.lead_source_category:
            return self.lead_source_category.name
        elif self.lead_source_details:
            return self.lead_source_details
        return 'Unknown Source'

    is_code_92 = models.BooleanField(default=False, verbose_name="Code 92 Flag")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    bridal_party_qty = models.PositiveIntegerField(validators=[MinValueValidator(1)], null=True, blank=True)
    guests_qty = models.PositiveIntegerField(validators=[MinValueValidator(1)], null=True, blank=True)

    ceremony_site = models.CharField(max_length=255, null=True, blank=True)
    ceremony_city = models.CharField(max_length=255, null=True, blank=True)
    ceremony_state = models.CharField(max_length=255, null=True, blank=True)
    ceremony_contact = models.CharField(max_length=255, null=True, blank=True)
    ceremony_phone = models.CharField(
        max_length=12,  # Increase max_length to accommodate dashes
        validators=[phone_validator],
        blank=True,
        null=True
    )
    ceremony_email = models.EmailField(validators=[EmailValidator], null=True, blank=True)
    reception_site = models.CharField(max_length=255, null=True, blank=True)
    reception_city = models.CharField(max_length=255, null=True, blank=True)
    reception_state = models.CharField(max_length=255, null=True, blank=True)
    reception_contact = models.CharField(max_length=255, null=True, blank=True)
    reception_phone = models.CharField(
        max_length=12,  # Increase max_length to accommodate dashes
        validators=[phone_validator],
        blank=True,
        null=True
    )
    reception_email = models.EmailField(validators=[EmailValidator], null=True, blank=True)
    staff_notes = models.TextField(blank=True, null=True)
    contract_document = models.FileField(upload_to='contracts/', null=True, blank=True)

    # EventStaff
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




    # Other fields...


    # Prospect photographer fields
    prospect_photographer1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                               related_name='prospect_photographer1_contracts')
    prospect_photographer2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                               related_name='prospect_photographer2_contracts')
    prospect_photographer3 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                               related_name='prospect_photographer3_contracts')

    photography_package = models.ForeignKey(
        Package,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photography_packages',
        # Adjust the `limit_choices_to` to filter using the `ServiceType`'s `name` field
        limit_choices_to={'service_type__name': 'Photography', 'is_active': True}
    )

    photography_additional = models.ForeignKey(
        AdditionalEventStaffOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='additional_photography_options',
        limit_choices_to={'service_type__name': 'Photography', 'is_active': True}
    )
    
    engagement_session = models.ForeignKey(
        EngagementSessionOption,  # Assuming this is your actual model name
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='engagement_session_options',
        limit_choices_to={'is_active': True}  # Adjust this based on your model's fields
    )

    videography_package = models.ForeignKey(
        Package,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='videography_packages',
        limit_choices_to={'service_type__name': 'Videography', 'is_active': True}
    )

    videography_additional = models.ForeignKey(AdditionalEventStaffOption, on_delete=models.SET_NULL, null=True,
                                               blank=True,
                                               related_name='additional_videography_options',
                                               limit_choices_to={'service_type__name': 'Videography', 'is_active': True})
    dj_package = models.ForeignKey(
        Package,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dj_packages',
        limit_choices_to={'service_type__name': 'Dj', 'is_active': True}
    )

    dj_additional = models.ForeignKey(AdditionalEventStaffOption, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='additional_dj_options',
                                      limit_choices_to={'service_type__name': 'Dj', 'is_active': True})

    photobooth_package = models.ForeignKey(
        Package,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photobooth_packages',
        limit_choices_to={'service_type__name': 'Photobooth', 'is_active': True}
    )

    photobooth_additional = models.ForeignKey(AdditionalEventStaffOption, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='additional_photobooth_options',
                                      limit_choices_to={'service_type__name': 'Photobooth', 'is_active': True})

    overtime_options = models.ManyToManyField(
        OvertimeOption,
        through='ContractOvertime',
        related_name='contracts'
    )

    # For special terms and conditions.
    custom_text = models.TextField(blank=True, null=True)


    package_discount_version = models.IntegerField(default=1)
    sunday_discount_version = models.IntegerField(default=1)
    other_discounts = models.ManyToManyField(Discount, related_name='contracts', blank=True)

    additional_products = models.ManyToManyField(AdditionalProduct, through='ContractProduct', related_name='contracts')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return self.custom_contract_number or f"Contract {self.contract_id}"

    def calculate_photography_cost(self):
        photography_base_cost = self.photography_package.price if self.photography_package else Decimal('0.00')
        additional_photography_cost = self.photography_additional.price if self.photography_additional else Decimal(
            '0.00')
        engagement_session_cost = self.engagement_session.price if self.engagement_session else Decimal('0.00')

        # Identify the ServiceType for photography
        photography_service_type = ServiceType.objects.get(name='Photography')  # Adjust the name as needed

        # Calculate overtime cost for photography
        photography_overtime_cost = sum(
            overtime.hours * overtime.overtime_option.rate_per_hour
            for overtime in self.overtimes.filter(overtime_option__service_type=photography_service_type)
        )

        # Sum up all the components of the photography cost
        total_photography_cost = photography_base_cost + additional_photography_cost + engagement_session_cost + photography_overtime_cost

        return total_photography_cost.quantize(Decimal('.00'), rounding=ROUND_HALF_UP)

    def calculate_videography_cost(self):
        videography_base_cost = self.videography_package.price if self.videography_package else Decimal('0.00')
        additional_videography_cost = self.videography_additional.price if self.videography_additional else Decimal(
            '0.00')

        # Identify the ServiceType for videography
        videography_service_type = ServiceType.objects.get(name='Videography')  # Adjust the name as needed

        # Calculate overtime cost for videography
        videography_overtime_cost = sum(
            overtime.hours * overtime.overtime_option.rate_per_hour
            for overtime in self.overtimes.filter(overtime_option__service_type=videography_service_type)
        )

        return (videography_base_cost + additional_videography_cost + videography_overtime_cost).quantize(
            Decimal('.00'), rounding=ROUND_HALF_UP)

    def calculate_dj_cost(self):
        dj_base_cost = self.dj_package.price if self.dj_package else Decimal('0.00')
        additional_dj_cost = self.dj_additional.price if self.dj_additional else Decimal('0.00')

        # Identify the ServiceType for DJ services
        dj_service_type = ServiceType.objects.get(name='Dj')  # Adjust the name as needed

        # Calculate overtime cost for DJ services
        dj_overtime_cost = sum(
            overtime.hours * overtime.overtime_option.rate_per_hour
            for overtime in self.overtimes.filter(overtime_option__service_type=dj_service_type)
        )

        return (dj_base_cost + additional_dj_cost + dj_overtime_cost).quantize(Decimal('.00'), rounding=ROUND_HALF_UP)

    def calculate_photobooth_cost(self):
        photobooth_base_cost = self.photobooth_package.price if self.photobooth_package else Decimal('0.00')
        additional_photobooth_cost = self.photobooth_additional.price if self.photobooth_additional else Decimal('0.00')
        # Identify the ServiceType for photobooth services
        photobooth_service_type = ServiceType.objects.get(name='Photobooth')  # Adjust the name as needed

        # Calculate overtime cost for photobooth services
        photobooth_overtime_cost = sum(
            overtime.hours * overtime.overtime_option.rate_per_hour
            for overtime in self.overtimes.filter(overtime_option__service_type=photobooth_service_type)
        )

        return (photobooth_base_cost + additional_photobooth_cost + photobooth_overtime_cost).quantize(Decimal('.00'),
                                                                                                       rounding=ROUND_HALF_UP)

    def is_sunday_event(self):
        return self.event_date.weekday() == 6  # 6 is Sunday

    def calculate_package_discount(self):
        discount_rule = DiscountRule.objects.filter(
            discount_type=DiscountRule.PACKAGE,
            version=self.package_discount_version,
            is_active=True
        ).first()

        if not discount_rule:
            return Decimal('0.00')

        selected_services = [
            self.photography_package,
            self.videography_package,
            self.dj_package,
        ]

        selected_services = [p for p in selected_services if p is not None]
        is_photobooth_selected = self.photobooth_package is not None

        discount = Decimal('0.00')
        base_amount = discount_rule.base_amount

        if len(selected_services) >= 2:
            # $200 off each non-photobooth service
            discount += base_amount * len(selected_services)

            # If photobooth is also selected, additional $200 off for it
            if is_photobooth_selected:
                discount += base_amount
        elif is_photobooth_selected and len(selected_services) == 1:
            # $200 off the single other service when combined with photobooth
            discount += base_amount

        return discount.quantize(Decimal('.00'), rounding=ROUND_HALF_UP)

    def calculate_sunday_discount(self):
        if self.is_sunday_event():
            selected_services = [
                self.photography_package,
                self.videography_package,
                self.dj_package,
                self.photobooth_package
            ]
            selected_services = [p for p in selected_services if p is not None]
            discount = Decimal('100.00') * len(selected_services)
            return discount.quantize(Decimal('.00'), rounding=ROUND_HALF_UP)
        return Decimal('0.00')

    @property
    def other_discounts_total(self):
        return self.other_discounts.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')



    def calculate_discount(self):
            total_discount = Decimal('0.00')

            package_based_discount = self.calculate_package_discount()
            sunday_discount = self.calculate_sunday_discount()
            total_discount += package_based_discount + sunday_discount

            other_discounts_total = self.other_discounts.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            total_discount += other_discounts_total

            return total_discount

    def calculate_total_service_cost_after_discounts(self):
        subtotal = self.calculate_photography_cost() + self.calculate_videography_cost() + self.calculate_dj_cost() + self.calculate_photobooth_cost()
        total_discount = self.calculate_discount()
        total_cost_after_discounts = subtotal - total_discount
        return total_cost_after_discounts.quantize(Decimal('.00'), rounding=ROUND_HALF_UP)

    def calculate_product_subtotal(self):
        return sum(contract_product.product.price * contract_product.quantity for contract_product in
                   self.contract_products.all())

    def calculate_tax(self):
        """Calculate the tax amount based on the contract's tax rate and taxable products."""
        taxable_amount = Decimal('0.00')
        for contract_product in self.contract_products.all():
            if contract_product.product.is_taxable:
                taxable_amount += contract_product.product.price * contract_product.quantity

        # Get the tax rate from the location
        tax_rate = self.location.tax_rate if self.location else Decimal('0.00')
        return taxable_amount * tax_rate / 100

    def calculate_total_service_fees(self):
        """Calculate the total of all service fees."""
        return sum(fee.amount for fee in self.servicefees.all())


    def calculate_total_product_cost(self):
        """Calculate the total cost of products, including tax."""
        product_subtotal = self.calculate_product_subtotal()
        tax_amount = self.calculate_tax()
        total_cost = product_subtotal + tax_amount
        return total_cost.quantize(Decimal('.00'), rounding=ROUND_HALF_UP)
    def display_calculated_tax(self):
        """Method to display the calculated tax in the admin interface."""
        return self.calculate_tax()
    display_calculated_tax.short_description = "Calculated Tax"

    # Display methods for admin
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
        """Method to display the total cost in the admin interface or other views."""
        return self.calculate_total_cost()

    display_total_cost.short_description = "Total Cost"

    def calculate_total_service_cost(self):
        total_service_cost = Decimal('0.00')
        # Assuming methods for each service cost calculation exist
        total_service_cost += self.calculate_photography_cost()
        total_service_cost += self.calculate_videography_cost()
        total_service_cost += self.calculate_dj_cost()
        total_service_cost += self.calculate_photobooth_cost()

        # Ensure the total is rounded to two decimal places
        return total_service_cost.quantize(Decimal('.00'), rounding=ROUND_HALF_UP)


    def calculate_total_cost(self):
        """Calculate the total cost including services, products, tax, discounts, and service fees."""
        total_service_cost = self.calculate_total_service_cost()
        total_service_fees = self.calculate_total_service_fees()  # Calculate total service fees
        additional_products_cost = self.calculate_product_subtotal()

        subtotal = total_service_cost + additional_products_cost + total_service_fees  # Include service fees

        tax = self.calculate_tax()
        discounts = self.calculate_discount()

        total_cost = subtotal + tax - discounts
        return total_cost.quantize(Decimal('.00'), rounding=ROUND_HALF_UP)

    @property
    def final_total(self):
        total_cost = self.calculate_total_cost()
        return total_cost

    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def amount_paid(self):
        """Calculate the total amount paid if the contract has a primary key."""
        if self.pk:
            return sum(payment.amount for payment in self.payments.all()) or Decimal('0.00')
        return Decimal('0.00')

    @property
    def balance_due(self):
        """Calculate the balance due."""
        # Check if the contract has been saved (i.e., it has a primary key).
        if self.pk:
            # Calculate balance due by subtracting the amount paid from the final total.
            balance = self.final_total - self.amount_paid
            # Ensure that the balance due is not negative.
            return max(Decimal('0.00'), balance)
        # If the contract has not been saved, return the final total as the balance due.
        return self.final_total

    def save(self, *args, **kwargs):
        """Custom save method to handle custom contract number generation and tax calculations."""

        print("Entering save method")

        if not self.custom_contract_number:
            year, month = timezone.now().strftime("%y"), timezone.now().strftime("%m")

            # Extract first 3 letters of the primary contact's last name
            primary_contact_last_name = "UNK"  # Default value
            if self.client and self.client.primary_contact:
                name_parts = self.client.primary_contact.split()
                if len(name_parts) > 1:
                    primary_contact_last_name = name_parts[-1][:3].upper()
                else:
                    primary_contact_last_name = name_parts[0][:3].upper()  # In case only one name is provided

            # Use a transaction to ensure atomicity
            with transaction.atomic():
                # Query to retrieve all contracts for the current year and month
                regex_pattern = rf'^[A-Z]{{3}}-{year}-{month}-(\d+)$'
                contracts = Contract.objects.filter(custom_contract_number__regex=regex_pattern).order_by(
                    '-custom_contract_number')

                # Find the highest number in the retrieved contracts
                if contracts:
                    highest_number = max(int(re.search(r'-(\d+)$', contract.custom_contract_number).group(1)) for contract in contracts)
                    new_number = highest_number + 1
                else:
                    new_number = 1

                # Format the custom contract number with hyphen
                self.custom_contract_number = f"{primary_contact_last_name}-{year}-{month}-{str(new_number).zfill(2)}"
                print(f"Generated custom contract number: {self.custom_contract_number}")

                # Save the contract with the new custom contract number
                super().save(*args, **kwargs)
                print("Saved contract with custom contract number")
        else:
            print("Custom contract number already set.")
            super().save(*args, **kwargs)

        # Recalculate and store the tax amount
        taxable_amount = Decimal('0.00')
        for contract_product in self.contract_products.all():
            if contract_product.product.is_taxable:
                taxable_amount += contract_product.product.price * contract_product.quantity
        self.tax_amount = taxable_amount * self.tax_rate / 100

        # Recalculate and store the package discount
        package_based_discount = self.calculate_package_discount()
        self.calculated_discount = Decimal(package_based_discount)  # Update this field with the calculated discount

        # Recalculate the total discount considering other discounts and package discount
        self.total_discount = self.calculate_discount()

        # Recalculate the total cost and apply discounts
        self.total_cost = self.calculate_total_cost()  # Update total cost before saving
        super(Contract, self).save(*args, **kwargs)  # Save the contract with updated total




class ContractOvertime(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='overtimes')
    overtime_option = models.ForeignKey(OvertimeOption, on_delete=models.CASCADE)
    hours = models.DecimalField(max_digits=3, decimal_places=1)

    def __str__(self):
        return f"{self.contract} - {self.overtime_option} - Hours: {self.hours}"

class ContractProduct(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='contract_products')
    product = models.ForeignKey(AdditionalProduct, on_delete=models.CASCADE, related_name='product_contracts')
    quantity = models.PositiveIntegerField(default=1)
    special_notes = models.TextField(blank=True, null=True)

    def get_product_price(self):
        return self.product.price  # Access the price of the related AdditionalProduct

    def __str__(self):
        return f"{self.contract} - {self.product} - Qty: {self.quantity}"

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
    contract = models.ForeignKey('Contract', on_delete=models.CASCADE, related_name='changelogs')  # Assuming 'Contract' is the correct model name

    def __str__(self):
        return f"{self.timestamp} - {self.user}"