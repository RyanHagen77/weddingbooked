from django.core.paginator import Paginator
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from contracts.models import Contract, Location
from datetime import datetime, timedelta
from django.db.models import F
import calendar

from reports.reports_helpers import get_date_range, DATE_RANGE_DISPLAY

import logging

# Logging setup
logger = logging.getLogger(__name__)

@login_required
def reception_venue_report(request):
    # Get date range and period from request
    date_range = request.GET.get('date_range', 'this_month')
    period = request.GET.get('period', 'monthly')
    start_date, end_date = get_date_range(date_range)

    selected_location = request.GET.get('location', 'all')

    # Custom date range handling
    if date_range == 'custom':
        custom_start = request.GET.get('start_date')
        custom_end = request.GET.get('end_date')
        if custom_start and custom_end:
            start_date = datetime.strptime(custom_start, '%Y-%m-%d')
            end_date = datetime.strptime(custom_end, '%Y-%m-%d')
            end_date = end_date.replace(hour=23, minute=59, second=59)

    # Filter contracts based on location and event date
    contracts = Contract.objects.filter(event_date__range=(start_date, end_date))
    if selected_location != 'all':
        contracts = contracts.filter(location_id=selected_location)

    # Function to generate a list of months/weeks
    def month_range(start_date, end_date):
        start_month = start_date.replace(day=1)
        end_month = end_date.replace(day=1)
        current_month = start_month
        while current_month <= end_month:
            yield current_month
            current_month += timedelta(days=calendar.monthrange(current_month.year, current_month.month)[1])
            current_month = current_month.replace(day=1)

    def week_range(start_date, end_date):
        start_week = start_date - timedelta(days=start_date.weekday())
        end_week = end_date - timedelta(days=end_date.weekday())
        current_week = start_week
        while current_week <= end_week:
            yield current_week
            current_week += timedelta(days=7)

    # Collect data for the report
    report_data = []
    time_ranges = month_range(start_date, end_date) if period == 'monthly' else week_range(start_date, end_date)

    for time_start in time_ranges:
        time_end = time_start + timedelta(days=6 if period == 'weekly' else calendar.monthrange(time_start.year, time_start.month)[1])
        time_contracts = contracts.filter(event_date__range=(time_start, time_end))

        reception_venues = time_contracts.select_related("client").values(
            "contract_id", "reception_site", "event_date", "custom_contract_number", "status", "client__primary_contact",
            "client__partner_contact"
        ).order_by("reception_site")

        for venue in reception_venues:
            report_data.append({
                'reception_site': venue["reception_site"],
                'event_date': venue["event_date"],
                'custom_contract_number': venue["custom_contract_number"],
                'status': venue["status"],
                'primary_contact': venue["client__primary_contact"],
                'partner_contact': venue["client__partner_contact"],
                'contract_link': f"/contracts/{venue['contract_id']}/"  # Correct contract ID reference
            })


    # **Sort venues alphabetically**
    report_data = sorted(report_data, key=lambda x: (x['reception_site'] or "").lower())

    # **Paginate results (50 per page)**
    paginator = Paginator(report_data, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    locations = Location.objects.all()

    context = {
        'page_obj': page_obj,  # Paginated data
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'locations': locations,
        'selected_location': selected_location,
        'selected_period': period,
        'date_range': date_range,
        'DATE_RANGE_DISPLAY': DATE_RANGE_DISPLAY,
        'reception_venues': reception_venues,
    }

    return render(request, 'reports/reception_venue_report.html', context)
