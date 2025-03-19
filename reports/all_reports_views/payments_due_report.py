from django.core.paginator import Paginator
from django.shortcuts import render
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

    # Default to the current month if no date range is provided
    today = date.today()
    first_day_of_month = today.replace(day=1)
    last_day_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    # Parse start and end dates
    start_date = parse_date(start_date_str) if start_date_str else first_day_of_month
    end_date = parse_date(end_date_str) if end_date_str else last_day_of_month

    # Filter by location
    contract_filters = Q()
    if location_id != 'all':
        contract_filters &= Q(location_id=location_id)

    # Get only outstanding payments within the date range (paid=False)
    outstanding_payments = SchedulePayment.objects.filter(
        due_date__range=(start_date, end_date),
        paid=False  # Only unpaid payments
    ).select_related('schedule', 'schedule__contract')

    # Build report data
    report_data = []
    for payment in outstanding_payments:
        contract = payment.schedule.contract
        report_data.append({
            'event_date': contract.event_date,
            'amount_due': payment.amount,
            'date_due': payment.due_date,
            'primary_contact': contract.client.primary_contact,
            'primary_phone1': contract.client.primary_phone1,
            'custom_contract_number': contract.custom_contract_number,
            'contract_link': f"/contracts/{contract.contract_id}/"
        })

    # Sort payments by due date (ascending order)
    report_data.sort(key=lambda x: x['date_due'])

    # Calculate total amount due and total number of line items
    total_due = sum(item['amount_due'] for item in report_data)
    total_items = len(report_data)

    # Implement pagination (50 results per page)
    paginator = Paginator(report_data, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Fetch all locations for the dropdown
    locations = Location.objects.all()

    context = {
        'page_obj': page_obj,  # Paginated results
        'total_due': total_due,
        'total_items': total_items,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'locations': locations,
        'selected_location': location_id,
    }

    return render(request, 'reports/payments_due_report.html', context)
