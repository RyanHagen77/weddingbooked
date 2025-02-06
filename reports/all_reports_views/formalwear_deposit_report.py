from django.shortcuts import render

from django.conf import settings
from django.contrib.auth.decorators import login_required
from contracts.models import Contract, Location, ServiceFee


from datetime import datetime
import calendar
from django.contrib.auth import get_user_model

import logging

# Logging setup
logger = logging.getLogger(__name__)


User = get_user_model()


@login_required
def formalwear_deposit_report(request):

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
    if start_date or end_date or selected_location != 'all':
        contracts = Contract.objects.filter(**filters).distinct().order_by('event_date')

        for contract in contracts:
            formal_wear_deposit_exists = ServiceFee.objects.filter(contract=contract,
                                                                   fee_type__name='Formal Wear Deposit').exists()

            if formal_wear_deposit_exists:
                report_data.append({
                    'event_date': contract.event_date,
                    'custom_contract_number': contract.custom_contract_number,
                    'contract_link': f"/contracts/{contract.contract_id}/",  # Link to the contract details page
                    'primary_contact': contract.client.primary_contact,
                    'primary_email': contract.client.primary_email,
                    'primary_phone1': contract.client.primary_phone1,
                })

    locations = Location.objects.all()

    context = {
        'report_data': sorted(report_data, key=lambda x: x['event_date']),
        'start_date': start_date,
        'end_date': end_date,
        'selected_location': selected_location,
        'locations': locations,
    }

    return render(request, 'reports/formal_wear_deposit_report.html', context)
