from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from contracts.models import Contract, Location
from django.db.models import Sum, F
from datetime import datetime
import calendar
import logging

logger = logging.getLogger(__name__)

@login_required
def formalwear_deposit_report_new(request):
    # Get the current date
    today = datetime.today()
    first_day_of_month = today.replace(day=1)
    last_day_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    # Get start_date and end_date from request or default to current month
    start_date = request.GET.get('start_date', first_day_of_month.strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', last_day_of_month.strftime('%Y-%m-%d'))
    selected_location = request.GET.get('location', 'all')

    filters = {}
    if start_date:
        filters['event_date__gte'] = start_date
    if end_date:
        filters['event_date__lte'] = end_date
    if selected_location != 'all':
        filters['location_id'] = selected_location

    report_data = []
    contracts = Contract.objects.filter(**filters).distinct().order_by('event_date')

    for contract in contracts:
        # Get all formalwear line items for this contract
        formalwear_qs = contract.formalwear_contracts.all()
        if formalwear_qs.exists():
            # Calculate the total deposit for the contract:
            # Multiply each line item's quantity by its formalwear product's deposit_amount.
            deposit_sum = formalwear_qs.aggregate(
                total_deposit=Sum(F('quantity') * F('formalwear_product__deposit_amount'))
            )['total_deposit'] or 0

            # Include this contract if there's a nonzero deposit amount.
            if deposit_sum > 0:
                report_data.append({
                    'event_date': contract.event_date,
                    'custom_contract_number': contract.custom_contract_number,
                    'contract_link': f"/contracts/{contract.contract_id}/",  # Link to the contract details page
                    'primary_contact': contract.client.primary_contact,
                    'primary_email': contract.client.primary_email,
                    'primary_phone1': contract.client.primary_phone1,
                    'deposit_sum': deposit_sum,  # Include the deposit total for display
                })

    locations = Location.objects.all()

    context = {
        'report_data': sorted(report_data, key=lambda x: x['event_date']),
        'start_date': start_date,
        'end_date': end_date,
        'selected_location': selected_location,
        'locations': locations,
    }

    return render(request, 'reports/formalwear_deposit_report_new.html', context)
