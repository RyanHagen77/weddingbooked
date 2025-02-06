from django.shortcuts import render
from django.conf import settings
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
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    # Get date range and period from request
    date_range = request.GET.get('date_range', 'this_month')
    period = request.GET.get('period', 'monthly')  # Default to grouping by month
    start_date, end_date = get_date_range(date_range)

    selected_location = request.GET.get('location', 'all')

    # If the date range is 'custom', allow custom start and end date input
    if date_range == 'custom':
        custom_start = request.GET.get('start_date')
        custom_end = request.GET.get('end_date')
        if custom_start and custom_end:
            start_date = datetime.strptime(custom_start, '%Y-%m-%d')
            end_date = datetime.strptime(custom_end, '%Y-%m-%d')
            # Ensure end_date includes the entire day
            end_date = end_date.replace(hour=23, minute=59, second=59)

    # Filter contracts based on location and event date (allow future dates)
    if selected_location == 'all':
        contracts = Contract.objects.filter(event_date__range=(start_date, end_date))
    else:
        contracts = Contract.objects.filter(event_date__range=(start_date, end_date), location_id=selected_location)

    # Function to generate a list of months in the date range
    def month_range(start_date, end_date):
        start_month = start_date.replace(day=1)
        end_month = end_date.replace(day=1)
        current_month = start_month
        while current_month <= end_month:
            yield current_month
            next_month = current_month + timedelta(days=calendar.monthrange(current_month.year, current_month.month)[1])
            current_month = next_month.replace(day=1)

    # Function to generate a list of weeks in the date range
    def week_range(start_date, end_date):
        start_week = start_date - timedelta(days=start_date.weekday())
        end_week = end_date - timedelta(days=end_date.weekday())
        current_week = start_week
        while current_week <= end_week:
            yield current_week
            current_week += timedelta(days=7)

    # Gather statistics based on the selected period
    report_data = []
    if period == 'monthly':
        for month_start in month_range(start_date, end_date):
            month_end = month_start.replace(day=calendar.monthrange(month_start.year, month_start.month)[1])
            month_contracts = contracts.filter(event_date__range=(month_start, month_end))

            reception_venues = month_contracts.values('reception_site').annotate(
                event_date=F('event_date'),
                custom_contract_number=F('custom_contract_number'),
                status=F('status'),
                primary_contact=F('client__primary_contact'),
                partner_contact=F('client__partner_contact'),
            ).order_by('reception_site')

            for venue in reception_venues:
                report_data.append({
                    'reception_site': venue['reception_site'],
                    'event_date': venue['event_date'],
                    'custom_contract_number': venue['custom_contract_number'],
                    'status': venue['status'],
                    'primary_contact': venue['primary_contact'],
                    'partner_contact': venue['partner_contact'],
                })
    elif period == 'weekly':
        for week_start in week_range(start_date, end_date):
            week_end = week_start + timedelta(days=6)
            week_contracts = contracts.filter(event_date__range=(week_start, week_end))

            reception_venues = week_contracts.values('reception_site').annotate(
                event_date=F('event_date'),
                custom_contract_number=F('custom_contract_number'),
                status=F('status'),
                primary_contact=F('client__primary_contact'),
                partner_contact=F('client__partner_contact'),
            ).order_by('reception_site')

            for venue in reception_venues:
                report_data.append({
                    'reception_site': venue['reception_site'],
                    'event_date': venue['event_date'],
                    'custom_contract_number': venue['custom_contract_number'],
                    'status': venue['status'],
                    'primary_contact': venue['primary_contact'],
                    'partner_contact': venue['partner_contact'],
                })

    # Get all locations for the dropdown
    locations = Location.objects.all()

    context = {
        'logo_url': logo_url,
        'report_data': report_data,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'locations': locations,
        'selected_location': selected_location,
        'selected_period': period,
        'date_range': date_range,  # Passed to template to maintain selected range
        'DATE_RANGE_DISPLAY': DATE_RANGE_DISPLAY,  # Pass the date range options to template
    }

    return render(request, 'reports/reception_venue_report.html', context)
