
import logging
from datetime import datetime


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


def serialize_photographer(photographer):
    if photographer:
        return {
            'id': photographer.id,
            'name': f"{photographer.first_name} {photographer.last_name}",
            'profile_picture': photographer.profile_picture.url if photographer.profile_picture else None,
            'website': photographer.website,
        }
    return None

