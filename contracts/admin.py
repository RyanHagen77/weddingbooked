from django.contrib import admin

from contracts.models import (Client, ServiceType, LeadSourceCategory, Contract, AdditionalProduct, TaxRate,
                     DiscountRule, Package, AdditionalEventStaffOption, EngagementSessionOption, Location, OvertimeOption,
                     ContractOvertime, ContractProduct, ServiceFeeType, ServiceFee, ChangeLog)
from bookings.models import EventStaffBooking
from documents.models import ContractAgreement, RiderAgreement
from payments.models import Payment, PaymentPurpose, PaymentSchedule, SchedulePayment
from wedding_day_guide.models import WeddingDayGuide
admin.site.register(TaxRate)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('primary_contact', 'primary_email', 'primary_phone1', 'partner_contact')

@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'price', 'service_type', 'default_text', 'rider_text', 'package_notes')
    search_fields = ('name', 'default_text', 'package_notes')
    list_filter = ('service_type',)
    list_editable = ('is_active',)

@admin.register(AdditionalEventStaffOption)
class AdditionalEventStaffOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'price', 'service_type', 'default_text', 'rider_text', 'package_notes')
    search_fields = ('name', 'default_text', 'package_notes')
    list_filter = ('service_type',)
    list_editable = ('is_active',)


@admin.register(EngagementSessionOption)
class EngagementSessionOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'price', 'default_text', 'rider_text', 'deposit')
    search_fields = ('name',)


@admin.register(EventStaffBooking)
class EventStaffBookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'staff', 'get_event_date', 'contract', 'role', 'status', 'confirmed', 'hours_booked', 'booking_notes')

    def get_event_date(self, obj):
        # Assuming the related Contract model has a field named 'event_date'
        return obj.contract.event_date if obj.contract else None
    get_event_date.short_description = 'Event Date'  # Sets the column header

@admin.register(AdditionalProduct)
class AdditionalProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_taxable', 'description', 'notes', 'cost')
    search_fields = ('name', 'description')
    list_filter = ('is_taxable',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'tax_rate')  # Columns to display in the admin list view
    search_fields = ('name', 'address')            # Fields to be included in the search
    list_filter = ('tax_rate',)                    # Filter sidebar for quick filtering by tax rate


class DiscountRuleAdmin(admin.ModelAdmin):
    list_display = ('discount_type', 'version', 'base_amount', 'is_active')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('discount_type', 'version')

admin.site.register(DiscountRule, DiscountRuleAdmin)
class ContractOvertimeInline(admin.TabularInline):
    model = ContractOvertime
    extra = 1


class ContractProductInline(admin.TabularInline):
    model = ContractProduct
    extra = 1

@admin.register(LeadSourceCategory)
class LeadSourceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):

    list_display = ('custom_contract_number', 'contract_id', 'client', 'event_date',
                    'status', 'display_total_service_cost', 'display_product_subtotal',
                    'display_discounts', 'display_calculated_tax', 'display_total_cost',
                    'calculated_package_discount', 'calculated_sunday_discount')

    list_filter = ('status', 'event_date', 'location')
    search_fields = ('client__primary_contact', 'contract_id', 'ceremony_site', 'reception_site')
    date_hierarchy = 'event_date'
    readonly_fields = ('display_calculated_tax', 'display_total_service_cost', 'tax_rate',
                       'display_product_subtotal', 'display_discounts', 'display_total_cost',
                       'amount_paid', 'balance_due', 'calculated_package_discount', 'calculated_sunday_discount')

    def calculated_package_discount(self, obj):
        return obj.calculate_package_discount()  # Assuming this method exists in your Contract model
    calculated_package_discount.short_description = 'Calculated Package Discount'

    def calculated_sunday_discount(self, obj):
        return obj.calculate_sunday_discount()
    calculated_sunday_discount.short_description = 'Calculated Sunday Discount'

    inlines = [ContractOvertimeInline, ContractProductInline]

    fieldsets = (
        (None, {
            'fields': ('client', 'location', 'event_date', 'status', 'custom_contract_number')  # Added custom_contract_number here
        }),
        ('Event Details', {
            'fields': ('bridal_party_qty', 'guests_qty', 'ceremony_site', 'ceremony_city', 'ceremony_state',
                       'reception_site', 'reception_city', 'reception_state')
        }),
        ('Packages', {
            'fields': ('photography_package', 'photography_additional', 'engagement_session', 'videography_package', 'videography_additional',
                       'dj_package', 'dj_additional', 'photobooth_package', 'photobooth_additional')
        }),
        ('Financials', {
            'fields': ('display_total_service_cost', 'display_product_subtotal', 'tax_rate', 'display_calculated_tax',
                       'display_discounts', 'display_total_cost', 'amount_paid', 'balance_due')
        }),
        ('Staff Assignments', {
            'fields': ('photographer1', 'photographer2', 'videographer1', 'videographer2', 'dj1', 'dj2',
                       'photobooth_op1', 'photobooth_op2', 'prospect_photographer1', 'prospect_photographer2', 'prospect_photographer3')
        }),
        ('Calculated Discount Fields', {
            'fields': ('calculated_package_discount', 'calculated_sunday_discount')
        }),
        ('Other Discounts', {
            'fields': ('other_discounts',)
        }),
        # Include other fieldsets as needed
    )

    def get_readonly_fields(self, request, obj=None):
        # Make sure the custom contract number is editable
        readonly_fields = super().get_readonly_fields(request, obj)
        readonly_fields = list(readonly_fields)
        if 'custom_contract_number' in readonly_fields:
            readonly_fields.remove('custom_contract_number')
        return readonly_fields

@admin.register(OvertimeOption)
class OvertimeOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'rate_per_hour', 'is_active', 'service_type')
    search_fields = ('name', 'role')
    list_filter = ('is_active', 'service_type')


@admin.register(ContractOvertime)
class ContractOvertimeAdmin(admin.ModelAdmin):
    list_display = ('contract', 'overtime_option', 'hours')
    list_filter = ('contract',)
    search_fields = ('contract__contract_id', 'overtime_option__role')

    # Add any additional configurations you need


@admin.register(PaymentPurpose)
class PaymentPurposeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

    def __str__(self):
        return self.name

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('contract', 'amount', 'payment_method', 'date', 'payment_reference', 'memo', 'modified_by_user', 'payment_purpose')
    search_fields = ('contract__id', 'payment_reference', 'memo')
    list_filter = ('payment_method', 'date', 'modified_by_user', 'payment_purpose')
    ordering = ('-date',)


@admin.register(PaymentSchedule)
class PaymentScheduleAdmin(admin.ModelAdmin):
    list_display = ('contract', 'schedule_type', 'created_at', 'payment_summary')
    list_filter = ('schedule_type',)

    readonly_fields = ('contract', 'created_at', 'payment_summary')
@admin.register(SchedulePayment)
class SchedulePaymentAdmin(admin.ModelAdmin):
    list_display = ('schedule', 'purpose', 'due_date', 'amount', 'paid')
    list_filter = ('due_date', 'paid', 'purpose')
    search_fields = ('schedule__contract__custom_contract_number', 'purpose__name')
    ordering = ('due_date',)



@admin.register(ServiceFeeType)
class FeeTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
@admin.register(ServiceFee)
class ServiceFeeAdmin(admin.ModelAdmin):
    list_display = ('contract', 'amount', 'fee_type', 'description', 'applied_date')
    search_fields = ('fee_type__name',)  # Assuming 'fee_type' is a related model
    list_filter = ('fee_type',)
    ordering = ('contract', 'applied_date')

@admin.register(ChangeLog)
class ChangeLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'description']
    readonly_fields = list_display

    @admin.register(ContractAgreement)
    class ContractAgreementAdmin(admin.ModelAdmin):
        list_display = ('contract', 'signature', 'created_at', 'updated_at')

    @admin.register(RiderAgreement)
    class RiderAgreementAdmin(admin.ModelAdmin):
        list_display = ('contract', 'rider_type', 'client_name', 'agreement_date', 'notes', 'created_at', 'updated_at')


class WeddingDayGuideAdmin(admin.ModelAdmin):
    list_display = ('contract', 'event_date', 'primary_contact', 'primary_email', 'ceremony_site', 'reception_site', 'submitted')
    search_fields = ('primary_contact', 'primary_email', 'ceremony_site', 'reception_site', 'submitted')
    list_filter = ('event_date', 'ceremony_site', 'reception_site', 'submitted')
    ordering = ('-event_date',)

    fieldsets = (
        (None, {
            'fields': ('contract', 'event_date', 'primary_contact', 'primary_email', 'submitted')
        }),
        ('Ceremony Details', {
            'fields': ('ceremony_site', 'ceremony_address', 'ceremony_start', 'ceremony_end')
        }),
        ('Reception Details', {
            'fields': ('reception_site', 'reception_address', 'reception_start', 'reception_end')
        }),
        # Add other sections as needed
    )

admin.site.register(WeddingDayGuide, WeddingDayGuideAdmin)
