
from datetime import datetime, timedelta
import calendar


DATE_RANGE_DISPLAY = {
    'current_quarter': 'Current Quarter',
    'last_quarter': 'Last Quarter',
    'this_month': 'This Month',
    'last_month': 'Last Month',
    'this_year': 'This Year',
    'last_year': 'Last Year',
}


def get_date_range(date_range, today=None):
    if today is None:
        today = datetime.today()

    if date_range == 'custom':
        return None, None  # Let the view handle custom inputs

    if date_range == 'current_quarter':
        quarter = (today.month - 1) // 3 + 1
        start_month = 3 * quarter - 2
        start_date = datetime(today.year, start_month, 1)
        end_month = start_month + 2
        end_date = datetime(today.year, end_month, calendar.monthrange(today.year, end_month)[1])
    elif date_range == 'last_quarter':
        quarter = (today.month - 1) // 3
        if quarter == 0:
            start_date = datetime(today.year - 1, 10, 1)
            end_date = datetime(today.year - 1, 12, 31)
        else:
            start_month = 3 * quarter - 2
            start_date = datetime(today.year, start_month, 1)
            end_month = start_month + 2
            end_date = datetime(today.year, end_month, calendar.monthrange(today.year, end_month)[1])
    elif date_range == 'this_month':
        start_date = today.replace(day=1)
        end_date = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    elif date_range == 'last_month':
        first_day_of_this_month = today.replace(day=1)
        last_day_of_last_month = first_day_of_this_month - timedelta(days=1)
        start_date = last_day_of_last_month.replace(day=1)
        end_date = last_day_of_last_month
    elif date_range == 'this_year':
        start_date = datetime(today.year, 1, 1)
        end_date = datetime(today.year, 12, 31)
    elif date_range == 'last_year':
        start_date = datetime(today.year - 1, 1, 1)
        end_date = datetime(today.year - 1, 12, 31)
    else:
        # Default to the current month
        start_date = today.replace(day=1)
        end_date = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    return start_date, end_date
