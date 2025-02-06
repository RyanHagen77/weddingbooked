from django.shortcuts import render
from django.conf import settings
from contracts.models import Contract, Location
from payments.models import Payment
from decimal import Decimal
from datetime import datetime
from django.utils.timezone import make_aware

import logging

# Logging setup
logger = logging.getLogger(__name__)


def deferred_revenue_report(request):
    report_date = request.GET.get('report_date')
    selected_location = request.GET.get('location', 'all')

    # Initialize filters for contracts
    filters = {}
    if selected_location != 'all':
        filters['location_id'] = selected_location

    # Filter contracts based on the provided filters
    contracts = Contract.objects.filter(**filters).distinct()

    report_data = []

    if report_date:
        report_date_dt = make_aware(datetime.strptime(report_date, '%Y-%m-%d'))

        locations = Location.objects.all()
        total_deferred_revenue = Decimal('0.00')

        for location in locations:
            location_deferred_revenue = Decimal('0.00')

            payments = Payment.objects.filter(
                contract__in=contracts,
                date__lte=report_date_dt,
                contract__event_date__gt=report_date_dt,  # Only include payments for future events
                contract__location=location
            )

            for payment in payments:
                location_deferred_revenue += payment.amount

            total_deferred_revenue += location_deferred_revenue

            report_data.append({
                'location': location.name,
                'deferred_revenue': location_deferred_revenue.quantize(Decimal('0.00')),
            })

        # Append the total row
        report_data.append({
            'location': 'Total',
            'deferred_revenue': total_deferred_revenue.quantize(Decimal('0.00')),
        })

    locations = Location.objects.all()

    context = {
        'report_date': report_date,
        'selected_location': selected_location,
        'locations': locations,
        'report_data': report_data
    }

    return render(request, 'reports/deferred_revenue_report.html', context)
