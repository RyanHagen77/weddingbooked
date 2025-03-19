from django.core.paginator import Paginator
from django.shortcuts import render
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
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    location_id = request.GET.get('location', 'all')
    period = request.GET.get('period', 'monthly')
    date_range = request.GET.get('date_range', 'this_month')  # Default selection

    # Get the start and end dates
    start_date, end_date = get_date_range(date_range, start_date_str, end_date_str)

    if date_range == 'custom' and (not start_date or not end_date):
        return render(request, 'reports/error.html', {'message': 'Please provide both start and end dates for the custom date range.'})

    # Filter contracts
    contracts = Contract.objects.filter(contract_date__range=(start_date, end_date))
    if location_id != 'all':
        contracts = contracts.filter(location_id=location_id)

    # Define period range functions
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

    # Collect statistics
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

    # **Sort venues alphabetically**
    report_data = sorted(report_data, key=lambda x: x['category'])

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
        'selected_location': location_id,
        'selected_period': period,
        'date_range': date_range,
        'DATE_RANGE_DISPLAY': DATE_RANGE_DISPLAY,
    }

    return render(request, 'reports/lead_source_report.html', context)
