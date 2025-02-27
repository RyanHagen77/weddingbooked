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

    # Filter contracts by location
    contract_filters = Q()
    if location_id != 'all':
        contract_filters &= Q(location_id=location_id)

    # Optimize queries using select_related
    contracts = Contract.objects.select_related('client', 'payment_schedule').filter(contract_filters)

    # Get only custom schedule payments within the date range for custom schedules
    custom_payments = SchedulePayment.objects.filter(
        due_date__range=(start_date, end_date),
        paid=False
    ).select_related('schedule', 'schedule__contract')

    report_data = []

    # Process only custom schedule payments
    for payment in custom_payments:
        contract = payment.schedule.contract
        if payment.amount > 0:
            report_data.append({
                'event_date': contract.event_date,
                'amount_due': payment.amount,
                'date_due': payment.due_date,
                'primary_contact': contract.client.primary_contact,
                'primary_phone1': contract.client.primary_phone1,
                'custom_contract_number': contract.custom_contract_number,
                'contract_link': f"/contracts/{contract.contract_id}/"
            })

    # Calculate total amount due and total number of line items
    total_due = sum(item['amount_due'] for item in report_data)
    total_items = len(report_data)

    # Fetch all locations for dropdown
    locations = Location.objects.all()

    context = {
        'report_data': report_data,
        'total_due': total_due,
        'total_items': total_items,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'locations': locations,
        'selected_location': location_id,
    }

    return render(request, 'reports/payments_due_report.html', context)
