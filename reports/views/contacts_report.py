from django.shortcuts import render

from django.conf import settings
from django.contrib.auth.decorators import login_required
from contracts.models import Contract, Location


from datetime import datetime
import calendar
from django.contrib.auth import get_user_model

import logging

# Logging setup
logger = logging.getLogger(__name__)


User = get_user_model()


@login_required
def contacts_report(request):
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    # Get the current date
    today = datetime.today()
    first_day_of_month = today.replace(day=1)
    last_day_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    # Get start_date and end_date from request or default to current month
    start_date = request.GET.get('start_date', first_day_of_month.strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', last_day_of_month.strftime('%Y-%m-%d'))
    selected_location = request.GET.get('location', 'all')
    selected_status = request.GET.get('status', 'all')

    # Filter contracts by date, location, and status
    contracts = Contract.objects.all()
    if start_date:
        contracts = contracts.filter(contract_date__gte=start_date)
    if end_date:
        contracts = contracts.filter(contract_date__lte=end_date)
    if selected_location != 'all':
        contracts = contracts.filter(location_id=selected_location)
    if selected_status != 'all':
        contracts = contracts.filter(status=selected_status)

    report_data = []
    for contract in contracts:
        report_data.append({
            'primary_contact': contract.client.primary_contact,
            'primary_email': contract.client.primary_email,
            'primary_phone1': contract.client.primary_phone1,
            'contract_date': contract.contract_date,
            'event_date': contract.event_date,
            'status': contract.status,
            'location': contract.location.name if contract.location else 'N/A',
        })

    locations = Location.objects.all()

    context = {
        'logo_url': logo_url,
        'start_date': start_date,
        'end_date': end_date,
        'selected_location': selected_location,
        'selected_status': selected_status,
        'locations': locations,
        'statuses': Contract.STATUS_CHOICES,
        'report_data': report_data,
    }

    return render(request, 'reports/contacts_report.html', context)
