from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from contracts.models import Contract, Location
from django.db.models import Q
from datetime import datetime, timedelta
from reports.reports_helpers import get_date_range, DATE_RANGE_DISPLAY
from django.contrib.auth import get_user_model
import calendar
import logging

# Logging setup
logger = logging.getLogger(__name__)

User = get_user_model()

@login_required
def appointments_report(request):
    # Get date range, location, and period from request
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    location_id = request.GET.get('location', 'all')
    period = request.GET.get('period', 'monthly')
    date_range = request.GET.get('date_range', 'this_month')  # Added date_range for date selection

    # Use get_date_range function to get start and end dates for the selected date range
    start_date, end_date = get_date_range(date_range, start_date_str, end_date_str)

    # Handle missing custom dates
    if date_range == 'custom' and (not start_date or not end_date):
        return render(request, 'reports/error.html', {
            'message': 'Please provide both start and end dates for the custom date range.'
        })

    # Filter contracts based on location and ensure contracts have at least one service
    contracts = Contract.objects.filter(
        contract_date__range=(start_date, end_date)
    ).filter(
        Q(photography_package__isnull=False) |
        Q(videography_package__isnull=False) |
        Q(dj_package__isnull=False) |
        Q(photobooth_package__isnull=False)
    )

    if location_id != 'all':
        contracts = contracts.filter(location_id=location_id)

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

            total_appointments = month_contracts.distinct().count()

            report_data.append({
                'period': month_start.strftime('%b %Y'),
                'photo_count': month_contracts.filter(photography_package__isnull=False).count(),
                'photo_booked_count': month_contracts.filter(photography_package__isnull=False, status='booked').count(),
                'video_count': month_contracts.filter(videography_package__isnull=False).count(),
                'video_booked_count': month_contracts.filter(videography_package__isnull=False, status='booked').count(),
                'dj_count': month_contracts.filter(dj_package__isnull=False).count(),
                'dj_booked_count': month_contracts.filter(dj_package__isnull=False, status='booked').count(),
                'photobooth_count': month_contracts.filter(photobooth_package__isnull=False).count(),
                'photobooth_booked_count': month_contracts.filter(photobooth_package__isnull=False, status='booked').count(),
                'total_appointments': total_appointments,
            })

    elif period == 'weekly':
        for week_start in week_range(start_date, end_date):
            week_end = week_start + timedelta(days=6)
            week_contracts = contracts.filter(contract_date__range=(week_start, week_end))

            total_appointments = week_contracts.distinct().count()

            report_data.append({
                'period': f"{week_start.strftime('%b %d, %Y')} - {week_end.strftime('%b %d, %Y')}",
                'photo_count': week_contracts.filter(photography_package__isnull=False).count(),
                'photo_booked_count': week_contracts.filter(photography_package__isnull=False, status='booked').count(),
                'video_count': week_contracts.filter(videography_package__isnull=False).count(),
                'video_booked_count': week_contracts.filter(videography_package__isnull=False, status='booked').count(),
                'dj_count': week_contracts.filter(dj_package__isnull=False).count(),
                'dj_booked_count': week_contracts.filter(dj_package__isnull=False, status='booked').count(),
                'photobooth_count': week_contracts.filter(photobooth_package__isnull=False).count(),
                'photobooth_booked_count': week_contracts.filter(photobooth_package__isnull=False, status='booked').count(),
                'total_appointments': total_appointments,
            })

    # Gather statistics for each salesperson
    sales_data = []
    salespeople = User.objects.filter(contracts_managed__in=contracts).distinct()

    for salesperson in salespeople:
        sales_contracts = contracts.filter(csr=salesperson)

        total_appointments = sales_contracts.distinct().count()
        booked_appointments = sales_contracts.filter(
            Q(photography_package__isnull=False, status='booked') |
            Q(videography_package__isnull=False, status='booked') |
            Q(dj_package__isnull=False, status='booked') |
            Q(photobooth_package__isnull=False, status='booked')
        ).distinct().count()

        closed_percentage = (booked_appointments / total_appointments * 100) if total_appointments > 0 else 0

        sales_data.append({
            'name': salesperson.get_full_name(),
            'total_appointments': total_appointments,
            'booked_appointments': booked_appointments,
            'closed_percentage': round(closed_percentage, 2),
        })

    # Get all locations for the dropdown
    locations = Location.objects.all()

    context = {
        'report_data': report_data,
        'sales_data': sales_data,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'locations': locations,
        'selected_location': location_id,
        'selected_period': period,
        'date_range': date_range,
        'DATE_RANGE_DISPLAY': DATE_RANGE_DISPLAY,
    }

    return render(request, 'reports/appointments_report.html', context)
