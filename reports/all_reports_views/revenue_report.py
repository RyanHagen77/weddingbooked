from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from contracts.models import Contract, Location
from payments.models import Payment

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

import calendar


import logging

# Logging setup
logger = logging.getLogger(__name__)


@login_required
def revenue_report(request):

    # Initialize variables
    today = datetime.today()
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    selected_location = request.GET.get('location', 'all')

    # Default to current quarter if no dates are provided
    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    else:
        # Calculate current quarter
        quarter = (today.month - 1) // 3 + 1
        start_month = 3 * quarter - 2
        start_date = datetime(today.year, start_month, 1)
        end_month = start_month + 2
        end_day = calendar.monthrange(today.year, end_month)[1]
        end_date = datetime(today.year, end_month, end_day, 23, 59, 59)

    # Filter contracts based on date range and location
    contracts = Contract.objects.filter(status="booked", contract_date__lte=end_date)
    if selected_location != 'all':
        contracts = contracts.filter(location_id=selected_location)

    # Fetch all payments within the selected range
    payments = Payment.objects.filter(
        date__gte=start_date,
        date__lte=end_date,
        contract__in=contracts
    ).select_related('contract__location')

    # Totals initialization
    total_deposits_received = Decimal('0.00')
    total_other_payments = Decimal('0.00')
    total_tax_collected = Decimal('0.00')

# Process payments
    for payment in payments:
        payment_taxable_amount = Decimal('0.00')

        # Include products added on or before the payment date
        relevant_products = payment.contract.contract_products.filter(added_on__lte=payment.date)
        for cp in relevant_products:
            if cp.product.is_taxable:
                product_total = Decimal(cp.quantity) * Decimal(cp.product.price)
                payment_taxable_amount += product_total

        # Tax calculation
        tax_rate = Decimal(payment.contract.location.tax_rate or 0)
        tax_collected_for_payment = (payment_taxable_amount * tax_rate / Decimal('100.00')).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        total_tax_collected += tax_collected_for_payment

        # Categorize payments
        if payment.payment_purpose and payment.payment_purpose.name == 'Deposit':
            total_deposits_received += payment.amount
        else:
            total_other_payments += payment.amount

    # Total revenue calculation
    total_revenue = total_deposits_received + total_other_payments - total_tax_collected

    # Prepare report data
    report_data = [{
        'period_start': start_date.strftime('%Y-%m-%d'),
        'period_end': end_date.strftime('%Y-%m-%d'),
        'deposits_received': total_deposits_received.quantize(Decimal('0.01')),
        'other_payments': total_other_payments.quantize(Decimal('0.01')),
        'tax_collected': total_tax_collected.quantize(Decimal('0.01')),
        'total_revenue': total_revenue.quantize(Decimal('0.01')),
    }]

    # Fetch locations for the dropdown
    locations = Location.objects.all()

    # Context for the template
    context = {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'selected_location': selected_location,
        'locations': locations,
        'report_data': report_data,
    }

    return render(request, 'reports/revenue_report.html', context)
