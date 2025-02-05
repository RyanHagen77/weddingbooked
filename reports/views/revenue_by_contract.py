from django.shortcuts import render

from django.conf import settings
from django.contrib.auth.decorators import login_required
from contracts.models import Contract, Location


from payments.models import Payment

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from django.utils.timezone import localtime
import calendar
from django.contrib.auth import get_user_model

import logging

# Logging setup
logger = logging.getLogger(__name__)


User = get_user_model()


@login_required
def revenue_by_contract(request):
    """
    Generates a revenue report grouped by contract, detailing payments and tax collected.
    """
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    # Default to current quarter if no dates are provided
    today = datetime.today()
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    else:
        quarter = (today.month - 1) // 3 + 1
        start_month = 3 * quarter - 2
        start_date = datetime(today.year, start_month, 1)
        end_month = start_month + 2
        end_day = calendar.monthrange(today.year, end_month)[1]
        end_date = datetime(today.year, end_month, end_day, 23, 59, 59)

    selected_location = request.GET.get('location', 'all')

    # Initialize filters
    filters = {
        'payments__date__gte': start_date,
        'payments__date__lte': end_date,
    }
    if selected_location != 'all':
        filters['location_id'] = selected_location

    # Fetch contracts
    contracts = Contract.objects.filter(**filters).distinct()

    contracts_data = []
    grand_total_payments = Decimal('0.00')
    grand_total_tax_collected = Decimal('0.00')
    grand_total_revenue = Decimal('0.00')

    # Process each contract
    for contract in contracts:
        total_payments = Decimal('0.00')
        total_tax_collected = Decimal('0.00')
        payments_data = []

        # Fetch payments for the contract within date range
        contract_payments = Payment.objects.filter(
            contract=contract,
            date__gte=start_date,
            date__lte=end_date
        )

        for payment in contract_payments:
            payment_taxable_amount = Decimal('0.00')

            # Include products added on or before the payment date
            relevant_products = contract.contract_products.filter(added_on__lte=payment.date)
            for cp in relevant_products:
                if cp.product.is_taxable:
                    product_total = Decimal(cp.quantity) * Decimal(cp.product.price)
                    payment_taxable_amount += product_total

            # Tax calculation
            tax_rate = Decimal(contract.location.tax_rate or 0)
            tax_collected = (payment_taxable_amount * tax_rate / Decimal('100.00')).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )

            total_payments += payment.amount
            total_tax_collected += tax_collected

            payments_data.append({
                'date': localtime(payment.date).strftime('%B %d, %Y'),
                'amount': payment.amount.quantize(Decimal('0.01')),
                'purpose': payment.payment_purpose.name if payment.payment_purpose else 'Unknown',
                'tax_collected': tax_collected.quantize(Decimal('0.01')),
            })

        # Calculate net revenue (payments minus tax collected)
        total_revenue = total_payments - total_tax_collected

        contracts_data.append({
            'contract_id': contract.contract_id,
            'custom_contract_number': contract.custom_contract_number,
            'location': contract.location.name if contract.location else 'N/A',
            'payments': payments_data,
            'total_payments': total_payments.quantize(Decimal('0.01')),
            'total_tax_collected': total_tax_collected.quantize(Decimal('0.01')),
            'total_revenue': total_revenue.quantize(Decimal('0.01')),
        })

        # Update grand totals
        grand_total_payments += total_payments
        grand_total_tax_collected += total_tax_collected
        grand_total_revenue += total_revenue

    locations = Location.objects.all()

    context = {
        'logo_url': logo_url,
        'contracts_data': contracts_data,
        'grand_total_payments': grand_total_payments.quantize(Decimal('0.01')),
        'grand_total_tax_collected': grand_total_tax_collected.quantize(Decimal('0.01')),
        'grand_total_revenue': grand_total_revenue.quantize(Decimal('0.01')),
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'selected_location': selected_location,
        'locations': locations,
    }

    return render(request, 'reports/revenue_by_contract.html', context)
