
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings

import logging

# Logging setup
logger = logging.getLogger(__name__)


def custom_403_view(request, exception=None):
    return render(request, '403.html', status=403)


def is_report_viewer(user):
    return user.groups.filter(name__in=['EventStaffPayrollReportViewer', 'AllReportViewer']).exists()


@user_passes_test(is_report_viewer)
def reports(request):
    logo_url = f"http://{request.get_host()}{settings.MEDIA_URL}logo/Final_Logo.png"
    user_groups = list(request.user.groups.values_list('name', flat=True))

    context = {
        'logo_url': logo_url,
        'user_groups': user_groups,
        'reports': [],
    }

    # Add this line to return an HTTP response
    return render(request, 'reports/reports.html', context)
