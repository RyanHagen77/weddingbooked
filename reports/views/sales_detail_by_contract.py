from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from contracts.models import Contract, Location
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime


import logging

# Logging setup
logger = logging.getLogger(__name__)


@login_required
def sales_detail_by_contract(request):
    """
    Generates a detailed sales report grouped by contract.
    Services, products, and other charges (service fees) are included.
    Only includes booked contracts. Respects the date range passed from the detail view.
    """
    logo_url = f"https://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    # Get the date range from query parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not start_date or not end_date:
        # Fail-safe: Raise an error or provide a default (optional)
        raise ValueError("Date range is required for this report.")

    # Convert start_date and end_date to datetime objects
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')

    # Ensure end_date includes the full day
    end_date = end_date.replace(hour=23, minute=59, second=59)

    selected_location = request.GET.get('location', 'all')

    # Filter contracts by booked status and contract date
    contracts = Contract.objects.filter(contract_date__gte=start_date, contract_date__lte=end_date, status="booked")
    if selected_location != 'all':
        contracts = contracts.filter(location_id=selected_location)

    contract_data = []
    total_service_revenue = Decimal('0.00')
    total_products_revenue = Decimal('0.00')
    total_taxable_products_revenue = Decimal('0.00')
    total_tax_collected = Decimal('0.00')
    total_service_fees = Decimal('0.00')  # Other charges (service fees)
    total_revenue = Decimal('0.00')

    for contract in contracts:
        # Calculate service revenue based on contract date
        total_service_cost = Decimal(contract.calculate_total_service_cost() or 0)
        total_discount = Decimal(contract.calculate_discount() or 0)
        net_service_revenue = max(total_service_cost - total_discount, Decimal('0.00'))

        # Calculate service fees (other charges)
        service_fees = Decimal(contract.calculate_total_service_fees() or 0)

        # Initialize product revenue and taxes
        products_revenue = Decimal('0.00')
        taxable_products_revenue = Decimal('0.00')
        tax_collected = Decimal('0.00')

        # Process contract products directly (no need to use payment date)
        for cp in contract.contract_products.all():
            product_revenue = Decimal(cp.quantity) * Decimal(cp.product.price or 0)
            products_revenue += product_revenue
            if cp.product.is_taxable:
                taxable_products_revenue += product_revenue
                tax_collected += (product_revenue * Decimal(contract.location.tax_rate or 0)
                                  / Decimal('100.00')).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )

        # Calculate total revenue for the contract
        total_revenue_per_contract = net_service_revenue + products_revenue + tax_collected + service_fees

        # Append contract data
        contract_data.append({
            'contract_id': contract.contract_id,
            'custom_contract_number': contract.custom_contract_number,
            'location': contract.location.name,
            'service_revenue': net_service_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'products_revenue': products_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'taxable_products_revenue': taxable_products_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'tax_collected': tax_collected.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'service_fees': service_fees.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'total_revenue': total_revenue_per_contract.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        })

        # Update totals
        total_service_revenue += net_service_revenue
        total_products_revenue += products_revenue
        total_taxable_products_revenue += taxable_products_revenue
        total_tax_collected += tax_collected
        total_service_fees += service_fees
        total_revenue += total_revenue_per_contract

    locations = Location.objects.all()

    context = {
        'logo_url': logo_url,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'selected_location': selected_location,
        'locations': locations,
        'contract_data': contract_data,
        'total_service_revenue': total_service_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'total_products_revenue': total_products_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'total_taxable_products_revenue': total_taxable_products_revenue.quantize(Decimal('0.01'),
                                                                                  rounding=ROUND_HALF_UP),
        'total_tax_collected': total_tax_collected.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'total_service_fees': total_service_fees.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'total_revenue': total_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
    }

    return render(request, 'reports/sales_detail_by_contract.html', context)
