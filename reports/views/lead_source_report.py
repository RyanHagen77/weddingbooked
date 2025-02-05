
from django.shortcuts import render

from django.conf import settings
from django.contrib.auth.decorators import login_required
from contracts.models import Contract, LeadSourceCategory, Location
from datetime import timedelta
import calendar
from reports.reports_helpers import get_date_range, DATE_RANGE_DISPLAY

import logging

# Logging setup
logger = logging.getLogger(__name__)


@login_required
def lead_source_report(request):
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"

    # Get date range, location, and period from request
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    location_id = request.GET.get('location', 'all')
    period = request.GET.get('period', 'monthly')
    date_range = request.GET.get('date_range', 'this_month')  # Added date_range for date selection

    # Use get_date_range function to get start and end dates for the selected date range
    start_date, end_date = get_date_range(date_range)

    # Filter contracts based on location and contract date
    if location_id == 'all':
        contracts = Contract.objects.filter(contract_date__range=(start_date, end_date))
    else:
        contracts = Contract.objects.filter(contract_date__range=(start_date, end_date), location_id=location_id)

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
            month_contracts = contracts.filter(contract_date__range=(month_start, month_end))

            for category in LeadSourceCategory.objects.all():
                total_count = month_contracts.filter(lead_source_category=category).count()
                booked_count = month_contracts.filter(lead_source_category=category, status='booked').count()
                report_data.append({
                    'period': month_start.strftime('%b %Y'),
                    'category': category.name,
                    'total_count': total_count,
                    'booked_count': booked_count,
                })
    elif period == 'weekly':
        for week_start in week_range(start_date, end_date):
            week_end = week_start + timedelta(days=6)
            week_contracts = contracts.filter(contract_date__range=(week_start, week_end))

            for category in LeadSourceCategory.objects.all():
                total_count = week_contracts.filter(lead_source_category=category).count()
                booked_count = week_contracts.filter(lead_source_category=category, status='booked').count()
                report_data.append({
                    'period': f"{week_start.strftime('%b %d, %Y')} - {week_end.strftime('%b %d, %Y')}",
                    'category': category.name,
                    'total_count': total_count,
                    'booked_count': booked_count,
                })

    # Get all locations for the dropdown
    locations = Location.objects.all()

    context = {
        'logo_url': logo_url,
        'report_data': report_data,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'locations': locations,
        'selected_location': location_id,
        'selected_period': period,
        'date_range': date_range,  # Passed to template to maintain selected range
        'DATE_RANGE_DISPLAY': DATE_RANGE_DISPLAY,  # Pass the date range options to template
    }

    return render(request, 'reports/lead_source_report.html', context)
