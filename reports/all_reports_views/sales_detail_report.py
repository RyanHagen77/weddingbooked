from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from contracts.models import Contract, Location
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta

from reports.reports_helpers import get_date_range, DATE_RANGE_DISPLAY


import logging

# Logging setup
logger = logging.getLogger(__name__)


@login_required
def sales_detail_report(request):
    """
    Generates a detailed sales report grouped by week or month.
    Supports predefined and custom date ranges, with a totals line.
    """

    # Get the date range and group_by from the request
    date_range = request.GET.get('date_range', 'this_month')
    group_by = request.GET.get('group_by', 'week')  # Default to grouping by week
    today = datetime.today()

    # Get start and end dates using the same logic for both presets and custom ranges
    if date_range == 'custom':
        custom_start = request.GET.get('start_date')
        custom_end = request.GET.get('end_date')
        if custom_start and custom_end:
            start_date = datetime.strptime(custom_start, '%Y-%m-%d')
            end_date = datetime.strptime(custom_end, '%Y-%m-%d')
        else:
            start_date, end_date = get_date_range('this_month', today)
    else:
        start_date, end_date = get_date_range(date_range, today)

    # Ensure end_date includes the full day
    end_date = end_date.replace(hour=23, minute=59, second=59)

    selected_location = request.GET.get('location', 'all')

    # Filter contracts with "booked" status
    contracts = Contract.objects.filter(
        contract_date__gte=start_date,
        contract_date__lte=end_date,
        status="booked"
    )

    # Apply location filter if needed
    if selected_location != 'all':
        contracts = contracts.filter(location_id=selected_location)

    report_data = []

    # Totals initialization
    total_service_revenue = Decimal('0.00')
    total_products_revenue = Decimal('0.00')
    total_taxable_products_revenue = Decimal('0.00')
    total_tax_collected = Decimal('0.00')
    total_service_fees = Decimal('0.00')
    total_revenue = Decimal('0.00')

    # Start processing grouped data
    current_date = start_date
    while current_date <= end_date:
        # Determine the period end date based on group_by
        if group_by == 'week':
            period_end_date = current_date + timedelta(days=6)
        elif group_by == 'month':
            next_month = current_date.replace(day=28) + timedelta(days=4)
            period_end_date = next_month - timedelta(days=next_month.day)
        else:
            period_end_date = end_date  # Default to single range if group_by is invalid

        if period_end_date > end_date:
            period_end_date = end_date

        # Initialize period revenue variables
        service_revenue = Decimal('0.00')
        products_revenue = Decimal('0.00')
        taxable_products_revenue = Decimal('0.00')
        tax_collected = Decimal('0.00')
        service_fees = Decimal('0.00')

        # Calculate service revenue for booked contracts
        for contract in contracts.filter(contract_date__gte=current_date, contract_date__lte=period_end_date):
            # Service revenue
            total_service_cost = Decimal(contract.calculate_total_service_cost() or 0)
            total_discount = Decimal(contract.calculate_discount() or 0)
            service_revenue += max(total_service_cost - total_discount, Decimal('0.00'))

            # Service fees (other charges)
            service_fees += Decimal(contract.calculate_total_service_fees() or 0)

            # Product revenue
            for cp in contract.contract_products.all():
                product_revenue = Decimal(cp.quantity) * Decimal(cp.product.price or 0)
                products_revenue += product_revenue
                if cp.product.is_taxable:
                    taxable_products_revenue += product_revenue
                    tax_collected += (product_revenue * Decimal(contract.location.tax_rate or 0)
                                      / Decimal('100.00')).quantize(
                        Decimal('0.01'), rounding=ROUND_HALF_UP
                    )

        # Calculate total revenue for the period
        total_revenue_period = service_revenue + products_revenue + tax_collected + service_fees

        # Append data to the report
        report_data.append({
            'period_start': current_date.strftime('%Y-%m-%d'),
            'period_end': period_end_date.strftime('%Y-%m-%d'),
            'service_revenue': service_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'products_revenue': products_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'taxable_products_revenue': taxable_products_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'tax_collected': tax_collected.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'service_fees': service_fees.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'total_revenue': total_revenue_period.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        })

        # Update totals
        total_service_revenue += service_revenue
        total_products_revenue += products_revenue
        total_taxable_products_revenue += taxable_products_revenue
        total_tax_collected += tax_collected
        total_service_fees += service_fees
        total_revenue += total_revenue_period

        # Move to the next period
        current_date = period_end_date + timedelta(days=1)

    # Append the totals row
    report_data.append({
        'period_start': 'Totals',
        'period_end': '',
        'service_revenue': total_service_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'products_revenue': total_products_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'taxable_products_revenue': total_taxable_products_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'tax_collected': total_tax_collected.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'service_fees': total_service_fees.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'total_revenue': total_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
    })

    locations = Location.objects.all()

    context = {
        'date_range': date_range,
        'group_by': group_by,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'selected_location': selected_location,
        'locations': locations,
        'report_data': report_data,
        'DATE_RANGE_DISPLAY': DATE_RANGE_DISPLAY,
    }

    return render(request, 'reports/sales_detail_report.html', context)
