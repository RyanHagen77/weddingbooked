from django.shortcuts import render
from django.conf import settings
from contracts.models import Contract, Location
from datetime import timedelta, date
from django.utils.dateparse import parse_date
from payments.models import SchedulePayment
import calendar

import logging

# Logging setup
logger = logging.getLogger(__name__)


def payments_due_report(request):
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

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
    contract_filters = {}
    if location_id != 'all':
        contract_filters['location_id'] = location_id

    contracts = Contract.objects.filter(**contract_filters)

    # Calculate due payments
    report_data = []
    for contract in contracts:
        client = contract.client

        # Check if contract has an associated payment schedule
        if hasattr(contract, 'payment_schedule'):
            if contract.payment_schedule.schedule_type == 'schedule_a':
                due_date = contract.event_date - timedelta(days=60)
                balance_due = contract.balance_due

                # Include contracts with a balance due and due date within the selected range
                if balance_due > 0 and start_date <= due_date <= end_date:
                    report_data.append({
                        'event_date': contract.event_date,
                        'amount_due': balance_due,
                        'date_due': due_date,
                        'primary_contact': client.primary_contact,
                        'primary_phone1': client.primary_phone1,
                        'custom_contract_number': contract.custom_contract_number,
                        'contract_link': f"/contracts/{contract.contract_id}/"
                    })
            elif contract.payment_schedule.schedule_type == 'custom':
                # Get custom schedule payments within the date range that are unpaid
                schedule_payments = SchedulePayment.objects.filter(
                    schedule=contract.payment_schedule,
                    due_date__range=(start_date, end_date),
                    paid=False
                )
                for payment in schedule_payments:
                    if payment.amount > 0:
                        report_data.append({
                            'event_date': contract.event_date,
                            'amount_due': payment.amount,
                            'date_due': payment.due_date,
                            'primary_contact': client.primary_contact,
                            'primary_phone1': client.primary_phone1,
                            'custom_contract_number': contract.custom_contract_number,
                            'contract_link': f"/contracts/{contract.contract_id}/"
                        })

    locations = Location.objects.all()

    context = {
        'logo_url': logo_url,
        'report_data': report_data,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'locations': locations,
        'selected_location': location_id,
    }

    return render(request, 'reports/payments_due_report.html', context)
