
import logging
from datetime import datetime
from django.contrib import messages

logger = logging.getLogger(__name__)

# Helper Functions
def parse_date_safe(date_str, field_name="date"):
    """
    Safely parses a date string into a date object.
    Returns None if parsing fails.
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None
    except ValueError:
        logger.error("Invalid %s format: %s", field_name, date_str)
        return None

def validate_date_range(start_date, end_date):
    """
    Validates and returns a date range tuple.
    Returns None if either date is invalid or the range is logically incorrect.
    """
    start = parse_date_safe(start_date, "start_date")
    end = parse_date_safe(end_date, "end_date")
    if start and end and start <= end:
        return start, end
    logger.error("Invalid date range: %s to %s", start_date, end_date)
    return None

def filter_by_date_range(request, queryset, start_date, end_date):
    """
    Filters the queryset by the given date range and handles validation.

    Args:
        request: The request object for handling messages.
        queryset: The initial queryset to filter.
        start_date: Start date as string.
        end_date: End date as string.

    Returns:
        A filtered queryset and processes messages for invalid range.
    """
    date_range = validate_date_range(start_date, end_date)
    if date_range:
        return queryset.filter(contract__event_date__range=date_range)
    elif start_date or end_date:
        messages.error(request, "Invalid date range. Please check your input.")
    return queryset


def serialize_photographer(photographer):
    if photographer:
        return {
            'id': photographer.id,
            'name': f"{photographer.first_name} {photographer.last_name}",
            'profile_picture': photographer.profile_picture.url if photographer.profile_picture else None,
            'website': photographer.website,
        }
    return None

