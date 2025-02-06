from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from contracts.models import Location
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

import calendar

from payments.models import Payment

import logging

# Logging setup
logger = logging.getLogger(__name__)


@login_required
def sales_tax_report(request):
    """
    Generates a sales tax report based on payments received within a specified date range.
    Tax is calculated for:
    - Pre-event taxable products tied to their respective balance payments.
    - Post-event taxable products tied to their respective post-event payments.
    """
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    # Get start_date and end_date from the request
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    today = datetime.today()
    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    else:
        # Default to the current quarter
        quarter = (today.month - 1) // 3 + 1
        start_month = 3 * quarter - 2
        start_date = datetime(today.year, start_month, 1)
        end_month = start_month + 2
        end_date = datetime(today.year, end_month,
                            calendar.monthrange(today.year, end_month)[1], 23, 59, 59)

    # Filter payments within the date range
    payments = Payment.objects.filter(
        date__gte=start_date,
        date__lte=end_date,
        contract__status="booked"
    ).select_related('contract__location')

    # Initialize report data and grand totals
    report_data = []
    grand_total_taxable_revenue = Decimal('0.00')
    grand_total_tax_collected = Decimal('0.00')

    # Process payments grouped by location
    locations = Location.objects.all()
    for location in locations:
        location_taxable_revenue = Decimal('0.00')
        location_tax_collected = Decimal('0.00')

        for payment in payments.filter(contract__location=location):
            taxable_amount = Decimal('0.00')

            # Include products added on or before the payment date
            relevant_products = payment.contract.contract_products.filter(added_on__lte=payment.date)
            for cp in relevant_products:
                if cp.product.is_taxable:
                    product_revenue = Decimal(cp.quantity) * Decimal(cp.product.price)
                    taxable_amount += product_revenue

            # Calculate tax collected for this payment
            tax_rate = Decimal(location.tax_rate or 0)
            tax_collected_for_payment = (taxable_amount * tax_rate / Decimal('100.00')).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )

            location_taxable_revenue += taxable_amount
            location_tax_collected += tax_collected_for_payment

        # Append location-specific data
        report_data.append({
            'location': location.name,
            'taxable_revenue': location_taxable_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'tax_collected': location_tax_collected.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        })

        # Update grand totals
        grand_total_taxable_revenue += location_taxable_revenue
        grand_total_tax_collected += location_tax_collected

    # Append grand totals to the report
    report_data.append({
        'location': 'Grand Total',
        'taxable_revenue': grand_total_taxable_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'tax_collected': grand_total_tax_collected.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
    })

    context = {
        'logo_url': logo_url,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'report_data': report_data,
    }

    return render(request, 'reports/sales_tax_report.html', context)
