from django.shortcuts import render
from django.conf import settings
from contracts.models import Contract, Location
from datetime import timedelta, date
from django.utils.dateparse import parse_date
from payments.models import SchedulePayment
from django.db.models import Q
import calendar
import logging

# Logging setup
logger = logging.getLogger(__name__)


def payments_due_report(request):
    # Get date range and location from request
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    location_id = request.GET.get('location', 'all')

    # Default date range to the current month if not provided
    today = date.today()
    first_day_of_month = today.replace(day=1)
    last_day_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    # Parse start and end dates
    start_date = parse_date(start_date_str) if start_date_str else first_day_of_month
    end_date = parse_date(end_date_str) if end_date_str else last_day_of_month

    # Filter contracts by location, if specified
    contract_filters = Q()
    if location_id != 'all':
        contract_filters &= Q(location_id=location_id)

    # Fetch contracts with related client data
    contracts = Contract.objects.select_related('client').filter(contract_filters)

    # Get all unpaid scheduled payments within the date range
    schedule_payments = SchedulePayment.objects.filter(
        schedule__contract__in=contracts,
        due_date__range=(start_date, end_date),
        paid=False
    ).select_related('schedule', 'schedule__contract', 'schedule__contract__client')

    # Build report data
    report_data = []
    for payment in schedule_payments:
        contract = payment.schedule.contract
        client = contract.client

        report_data.append({
            'event_date': contract.event_date,
            'amount_due': payment.amount,
            'date_due': payment.due_date,
            'primary_contact': client.primary_contact,
            'primary_phone1': client.primary_phone1,
            'custom_contract_number': contract.custom_contract_number,
            'contract_link': f"/contracts/{contract.contract_id}/"
        })

    # Fetch all locations for dropdown
    locations = Location.objects.all()

    context = {
        'report_data': report_data,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'locations': locations,
        'selected_location': location_id,
    }

    return render(request, 'reports/payments_due_report.html', context)
