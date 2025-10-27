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
from django.core.exceptions import ValidationError


from communication.utils import send_contract_booked_email


phone_validator = RegexValidator(
    regex=r'^(\d{3}-\d{3}-\d{4})||(\d{10})$',
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

    # ---- Prevent edits to a version once any contract references it ----
    def clean(self):
        # Only enforce when updating an existing rule
        if not self.pk:
            return

        # Local import to avoid circular import at module load
        from contracts.models import Contract

        if self.discount_type == self.PACKAGE:
            referenced = Contract.objects.filter(package_discount_version=self.version).exists()
        else:  # self.SUNDAY
            referenced = Contract.objects.filter(sunday_discount_version=self.version).exists()

        if referenced:
            # Compare with stored values to see what's changing
            old = type(self).objects.get(pk=self.pk)

            # Allow toggling is_active, but block changes to identity/amount/version
            identity_or_amount_changed = any([
                self.base_amount != old.base_amount,
                self.discount_type != old.discount_type,
                self.version != old.version,
            ])

            if identity_or_amount_changed:
                raise ValidationError(
                    "This rule version is referenced by existing contracts and cannot be modified. "
                    "Create a new version instead."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


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
    bridal_party_qty = models.PositiveIntegerField(validators=[MinValueValidator(0)], null=True, blank=True)
    guests_qty = models.PositiveIntegerField(validators=[MinValueValidator(0)], null=True, blank=True)

    # Ceremony and Reception Information
    ceremony_site = models.CharField(max_length=255, null=True, blank=True)
    ceremony_city = models.CharField(max_length=255, null=True, blank=True)
    ceremony_state = models.CharField(max_length=255, null=True, blank=True)
    ceremony_contact = models.CharField(max_length=255, null=True, blank=True)
    ceremony_phone = models.CharField(max_length=20, validators=[phone_validator], blank=True, null=True)
    ceremony_email = models.EmailField(validators=[EmailValidator()], null=True, blank=True)
    reception_site = models.CharField(max_length=255, null=True, blank=True)
    reception_city = models.CharField(max_length=255, null=True, blank=True)
    reception_state = models.CharField(max_length=255, null=True, blank=True)
    reception_contact = models.CharField(max_length=255, null=True, blank=True)
    reception_phone = models.CharField(max_length=20, validators=[phone_validator], blank=True, null=True)
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
                                               blank=True, related_name='prospect_photographer1_contracts')
    prospect_photographer2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                               blank=True, related_name='prospect_photographer2_contracts')
    prospect_photographer3 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                               blank=True, related_name='prospect_photographer3_contracts')

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

    bypass_package_discount = models.BooleanField(default=False)
    bypass_sunday_discount  = models.BooleanField(default=False)
    bypass_all_discounts    = models.BooleanField(default=False)

    # (optional) audit fields you already added:
    discount_bypass_reason = models.CharField(max_length=255, blank=True)
    discount_bypass_set_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="set_discount_bypass"
    )
    discount_bypass_set_at = models.DateTimeField(null=True, blank=True)
    other_discounts = models.ManyToManyField('Discount', related_name='contracts', blank=True)
    additional_products = models.ManyToManyField('products.AdditionalProduct', through='products.ContractProduct',
                                                 related_name='contracts')
    formalwear_products = models.ManyToManyField(
        'formalwear.FormalwearProduct',  # ✅ Correct reference to formalwear module
        through='formalwear.ContractFormalwearProduct',  # ✅ Correct reference to through model
        related_name='contracts')

    # Calculated fields
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    calculated_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid_field_legacy = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    balance_due_field_legacy = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)

    def __str__(self):
        return self.custom_contract_number or f"Contract {self.contract_id}"

    def check_and_complete(self):
        """Automatically mark contract as completed if event date has passed and status is still 'booked'."""
        if self.status == self.BOOKED and self.event_date < timezone.now().date():
            self.status = self.COMPLETED
            self.save(update_fields=['status'])

    def get_lead_source_display(self):
        if self.lead_source_category and self.lead_source_details:
            return f"{self.lead_source_category.name}: {self.lead_source_details}"
        elif self.lead_source_category:
            return self.lead_source_category.name
        elif self.lead_source_details:
            return self.lead_source_details
        return 'Unknown Source'

    def _overtime_cost_for(self, service_type_name: str) -> Decimal:
        """
        Sum hours * rate for this contract's overtimes for a given service type name.
        Uses __name filter to avoid a ServiceType lookup.
        """
        # If you often call this multiple times per request, consider
        # self._overtimes_cache = list(self.overtimes.select_related('overtime_option','overtime_option__service_type').all())
        # and sum from the cache instead of hitting DB repeatedly.
        qs = self.overtimes.select_related(
            "overtime_option", "overtime_option__service_type"
        ).filter(overtime_option__service_type__name=service_type_name)

        total = Decimal("0.00")
        for ot in qs:
            hours = getattr(ot, "hours", 0) or 0
            rate = getattr(ot.overtime_option, "rate_per_hour", Decimal("0.00")) or Decimal("0.00")
            total += Decimal(hours) * Decimal(rate)
        return total

    def _money(self, value) -> Decimal:
        """Ensure Decimal with 2dp, safe for None."""
        d = value if isinstance(value, Decimal) else Decimal(str(value or "0.00"))
        return d.quantize(Decimal(".00"), rounding=ROUND_HALF_UP)

    def _effective_tax_rate(self) -> Decimal:
        """
        Prefer the explicit field `self.tax_rate` (even before save),
        else fall back to `self.location.tax_rate`. Always return Decimal.
        """
        if self.tax_rate is not None:
            return Decimal(self.tax_rate)
        return Decimal(getattr(self.location, "tax_rate", Decimal("0.00")) or Decimal("0.00"))

    def _calc_service_cost(self, base_pkg, additional_opt, service_type_name: str,
                           extra: Decimal = Decimal("0.00")) -> Decimal:
        """
        Generic calculator for service cost = base + additional + overtime(+ extra).
        `base_pkg` and `additional_opt` are model instances (may be None) with a `.price` field.
        `extra` lets you add one more number (e.g. engagement session).
        """
        base_price = getattr(base_pkg, "price", None) or Decimal("0.00")
        additional_price = getattr(additional_opt, "price", None) or Decimal("0.00")
        overtime_cost = self._overtime_cost_for(service_type_name)
        total = Decimal(base_price) + Decimal(additional_price) + overtime_cost + Decimal(extra or "0.00")
        return self._money(total)

    def calculate_photography_cost(self) -> Decimal:
        engagement = getattr(self.engagement_session, "price", None) or Decimal("0.00")
        return self._calc_service_cost(
            base_pkg=self.photography_package,
            additional_opt=self.photography_additional,
            service_type_name="Photography",
            extra=engagement,
        )

    def calculate_videography_cost(self) -> Decimal:
        return self._calc_service_cost(
            base_pkg=self.videography_package,
            additional_opt=self.videography_additional,
            service_type_name="Videography",
        )

    def calculate_dj_cost(self) -> Decimal:
        # Your service type is spelled "Dj" elsewhere; if the service_type.name is actually "Dj",
        # keep it. If it's "DJ", change the string here to match.
        return self._calc_service_cost(
            base_pkg=self.dj_package,
            additional_opt=self.dj_additional,
            service_type_name="Dj",
        )

    def calculate_photobooth_cost(self) -> Decimal:
        return self._calc_service_cost(
            base_pkg=self.photobooth_package,
            additional_opt=self.photobooth_additional,
            service_type_name="Photobooth",
        )

    def is_sunday_event(self):
        """Return True if the contract’s event_date falls on a Sunday."""
        return self.event_date.weekday() == 6

    def calculate_package_discount(self):
        """Package discount (version-pinned, stable over time).
        - Honors: bypass_package_discount and bypass_all_discounts.
        - Uses DiscountRule(PACKAGE) for the version pinned on this contract.
        - Ignores `is_active` so historical contracts remain stable even if the rule is later deactivated.
        """
        if getattr(self, 'bypass_all_discounts', False) or getattr(self, 'bypass_package_discount', False):
            return Decimal('0.00')

        rule = DiscountRule.objects.filter(
            discount_type=DiscountRule.PACKAGE,
            version=self.package_discount_version,
        ).first()
        if not rule:
            return Decimal('0.00')

        selected_services = [self.photography_package, self.videography_package, self.dj_package]
        selected_services = [p for p in selected_services if p is not None]
        is_photobooth_selected = self.photobooth_package is not None

        discount = Decimal('0.00')
        base_amount = rule.base_amount or Decimal('0.00')

        if len(selected_services) >= 2:
            discount += base_amount * len(selected_services)
            if is_photobooth_selected:
                discount += base_amount
        elif is_photobooth_selected and len(selected_services) == 1:
            discount += base_amount

        return discount.quantize(Decimal('.00'), rounding=ROUND_HALF_UP)

    def calculate_sunday_discount(self):
        """Sunday discount (version-pinned, stable over time).
        - Uses DiscountRule(Sunday) for the version pinned on this contract.
        - FIXED amount 'base_amount' **per selected service**.
        - Honors: bypass_sunday_discount and bypass_all_discounts.
        - Ignores `is_active` so historical contracts remain stable even if the rule is later deactivated.
        """
        if getattr(self, 'bypass_all_discounts', False) or getattr(self, 'bypass_sunday_discount', False):
            return Decimal('0.00')

        if not self.is_sunday_event():
            return Decimal('0.00')

        rule = DiscountRule.objects.filter(
            discount_type=DiscountRule.SUNDAY,
            version=self.sunday_discount_version,
        ).first()
        if not rule:
            return Decimal('0.00')

        selected_services = [
            self.photography_package, self.videography_package,
            self.dj_package, self.photobooth_package
        ]
        count = sum(1 for s in selected_services if s is not None)

        discount = (rule.base_amount or Decimal('0.00')) * Decimal(count or 0)
        return Decimal(discount).quantize(Decimal('.00'), rounding=ROUND_HALF_UP)

    @property
    def other_discounts_total(self):
        """Total of manual/other discounts attached to this contract."""
        return self.other_discounts.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')

    def calculate_discount(self):
        """Total discount across all categories."""
        if getattr(self, 'bypass_all_discounts', False):
            return Decimal('0.00')

        total_discount = Decimal('0.00')
        total_discount += self.calculate_package_discount()
        total_discount += self.calculate_sunday_discount()
        # Manual/other discounts are always included; delete to remove their effect
        total_discount += self.other_discounts_total

        return total_discount.quantize(Decimal('.00'), rounding=ROUND_HALF_UP)

    def calculate_total_service_cost_after_discounts(self):
        """Subtotal of all services minus discounts (never below $0)."""
        subtotal = sum([
            self.calculate_photography_cost(),
            self.calculate_videography_cost(),
            self.calculate_dj_cost(),
            self.calculate_photobooth_cost()
        ])
        total_discount = self.calculate_discount()
        total_cost_after_discounts = subtotal - total_discount

        if total_cost_after_discounts < Decimal('0.00'):
            total_cost_after_discounts = Decimal('0.00')

        return total_cost_after_discounts.quantize(Decimal('.00'), rounding=ROUND_HALF_UP)

    def calculate_product_subtotal(self):
        """
        Calculate the subtotal of all products associated with this contract.
        """
        return sum(
            contract_product.product.price * contract_product.quantity
            for contract_product in self.contract_products.all()
        )

    def calculate_formalwear_subtotal(self):
        """
        Calculate the subtotal of all formalwear products associated with this contract.
        """
        return sum(
            contract_formalwear_product.formalwear_product.rental_price * contract_formalwear_product.quantity
            for contract_formalwear_product in self.formalwear_contracts.all()
        )

    def calculate_tax(self):
        taxable_amount = sum(
            cp.product.price * cp.quantity
            for cp in self.contract_products.all()
            if getattr(cp.product, "is_taxable", False)
        )
        tax_rate = self._effective_tax_rate()
        return self._money(taxable_amount * tax_rate / Decimal("100"))

    def calculate_total_service_fees(self):
        return sum(fee.amount for fee in self.servicefees.all())

    def calculate_total_product_cost(self):
        """
        Calculate total cost of all additional products and formalwear rentals, including tax.
        """
        product_subtotal = self.calculate_product_subtotal()
        formalwear_subtotal = self.calculate_formalwear_subtotal()
        tax_amount = self.calculate_tax()
        total_cost = product_subtotal + formalwear_subtotal + tax_amount
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
        """
        Calculate the total cost of the contract, including services, formalwear, products, tax, and discounts.
        """
        total_service_cost = self.calculate_total_service_cost()
        total_service_fees = self.calculate_total_service_fees()
        additional_products_cost = self.calculate_product_subtotal()
        formalwear_cost = self.calculate_formalwear_subtotal()

        subtotal = total_service_cost + additional_products_cost + formalwear_cost + total_service_fees
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
        return self.calculate_product_subtotal() + self.calculate_formalwear_subtotal()

    display_product_subtotal.short_description = "Product & Formalwear Subtotal"

    def display_discounts(self):
        return self.calculate_discount()

    display_discounts.short_description = "Total Discounts"

    def display_total_cost(self):
        return self.calculate_total_cost()

    display_total_cost.short_description = "Total Cost"

    class Meta:
        indexes = [
            models.Index(fields=['event_date']),
            models.Index(fields=['status']),
            models.Index(fields=['location']),
            models.Index(fields=['csr']),
            models.Index(fields=['coordinator']),
            models.Index(fields=['status', 'event_date']),
            models.Index(fields=['location', 'event_date']),
            models.Index(fields=['csr', 'event_date']),
        ]
        ordering = ['-contract_date', '-event_date']
        constraints = [
            models.CheckConstraint(
                check=models.Q(tax_rate__gte=0) & models.Q(tax_rate__lte=100),
                name="contracts_tax_rate_0_100",
            ),
        ]

    def save(self, *args, **kwargs):
        """
        Custom save with safe retry on custom_contract_number collisions.
        - Generate number BEFORE first save.
        - On duplicate, ALWAYS recompute max suffix from DB and retry.
        """

        print("Entering save method")

        # ----- side-effect flags (unchanged) -----
        user_status_update_needed = False
        send_salesperson_email = False
        if self.pk:
            old_status = Contract.objects.get(pk=self.pk).status
            if old_status != self.status:
                if self.status == self.COMPLETED:
                    user_status_update_needed = True
                elif self.status == self.BOOKED:
                    send_salesperson_email = True

        # ----- helpers -----
        def _letters3_from_client_last():
            name = (getattr(self.client, "primary_contact", "") or "").strip()
            if not name:
                return "UNK"
            last = name.split()[-1]
            letters = re.sub(r"[^A-Za-z]", "", last) or "UNK"
            return letters[:3].upper()

        def _next_suffix_for_month(yy: str, mm: str) -> int:
            """
            Look at ALL contracts that match -YY-MM-*, ignoring the AAA prefix,
            and return max(suffix) + 1.
            """
            # pattern like 'AAA-25-10-<digits>' — AAA ignored
            regex = rf'^[A-Z]{{3}}-{yy}-{mm}-(\d+)$'
            existing = (Contract.objects
                        .filter(custom_contract_number__regex=regex)
                        .values_list("custom_contract_number", flat=True))
            max_n = 0
            for num in existing:
                m = re.search(r'-(\d+)$', num or "")
                if m:
                    n = int(m.group(1))
                    if n > max_n:
                        max_n = n
            return max_n + 1

        def _format_number(prefix3: str, yy: str, mm: str, suffix_int: int) -> str:
            return f"{prefix3}-{yy}-{mm}-{str(suffix_int).zfill(2)}"

        # ----- ensure number BEFORE first save -----
        if not self.custom_contract_number:
            now = timezone.now()
            yy, mm = now.strftime("%y"), now.strftime("%m")
            prefix3 = _letters3_from_client_last()
            next_n = _next_suffix_for_month(yy, mm)
            self.custom_contract_number = _format_number(prefix3, yy, mm, next_n)

        # ----- tax rate (unchanged) -----
        self.tax_rate = (getattr(self.location, "tax_rate", None) or Decimal("0.00"))
        if not getattr(self.location, "tax_rate", None):
            print("Location or tax rate not set; defaulting to 0.")

        # ----- save with retry on duplicate number -----
        attempts = 0
        while True:
            try:
                with transaction.atomic():
                    # Recompute YY/MM and the candidate number *inside* the atomic block
                    # so each attempt is self-contained.
                    if not self.custom_contract_number:
                        now = timezone.now()
                        yy, mm = now.strftime("%y"), now.strftime("%m")
                        prefix3 = _letters3_from_client_last()
                        next_n = _next_suffix_for_month(yy, mm)
                        self.custom_contract_number = _format_number(prefix3, yy, mm, next_n)

                    super().save(*args, **kwargs)
                # success
                break

            except IntegrityError as e:
                if "custom_contract_number" not in str(e):
                    # unrelated integrity problem: bubble up
                    raise

                attempts += 1
                if attempts > 25:
                    # give up clearly — protects against an infinite loop if something’s off
                    raise

                # Collision: recompute the suffix for the current month and retry
                now = timezone.now()
                yy, mm = now.strftime("%y"), now.strftime("%m")
                prefix3 = _letters3_from_client_last()
                next_n = _next_suffix_for_month(yy, mm)
                self.custom_contract_number = _format_number(prefix3, yy, mm, next_n)
                print(f"Duplicate detected, retrying as: {self.custom_contract_number}")
                continue

        # ----- post-insert calculations (unchanged) -----
        taxable_amount = Decimal("0.00")
        for cp in self.contract_products.all():
            if getattr(cp.product, "is_taxable", False):
                taxable_amount += (cp.product.price * cp.quantity)

        self.tax_amount = taxable_amount * self.tax_rate / Decimal("100")
        self.calculated_discount = self.calculate_package_discount() or Decimal("0.00")
        self.total_discount = self.calculate_discount() or Decimal("0.00")
        self.total_cost = self.calculate_total_cost()

        super().save(update_fields=["tax_amount", "calculated_discount", "total_discount", "total_cost"])
        print("Final save completed with calculated fields.")

        # ----- side effects (unchanged) -----
        if user_status_update_needed and getattr(self.client, "user", None):
            user = self.client.user
            user.status = "INACTIVE"
            user.is_active = False
            user.save(update_fields=["status", "is_active"])
            print(f"User {user.username} marked as INACTIVE.")

        if send_salesperson_email:
            send_contract_booked_email(self)


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
