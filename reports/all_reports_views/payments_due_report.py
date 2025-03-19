from django.core.paginator import Paginator
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from payments.models import Payment
from contracts.models import Contract, Location
from django.db.models import Sum, F
from datetime import datetime
import calendar
import logging

logger = logging.getLogger(__name__)

@login_required
def payments_due_report(request):
    today = datetime.today()
    first_day_of_month = today.replace(day=1)
    last_day_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    # Get start_date and end_date from request or default to current month
    start_date = request.GET.get('start_date', first_day_of_month.strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', last_day_of_month.strftime('%Y-%m-%d'))
    selected_location = request.GET.get('location', 'all')

    filters = {}
    if start_date:
        filters['date__gte'] = start_date  # Payments filtered by payment date
    if end_date:
        filters['date__lte'] = end_date
    if selected_location != 'all':
        filters['contract__location_id'] = selected_location

    report_data = []
    total_due = 0
    total_items = 0

    # Fetch payments sorted by due date (ascending)
    payments = Payment.objects.filter(**filters).select_related('contract__client').order_by('date')

    for payment in payments:
        contract = payment.contract
        if contract:
            report_data.append({
                'event_date': contract.event_date,
                'amount_due': payment.amount,
                'date_due': payment.date,  # Sorted by this field
                'primary_contact': contract.client.primary_contact if contract.client else '',
                'primary_phone1': contract.client.primary_phone1 if contract.client else '',
                'custom_contract_number': contract.custom_contract_number,
                'contract_link': f"/contracts/{contract.contract_id}/"
            })
            total_due += payment.amount
            total_items += 1

    # Implement pagination (50 results per page)
    paginator = Paginator(report_data, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    locations = Location.objects.all()

    context = {
        'page_obj': page_obj,  # Paginated results
        'start_date': start_date,
        'end_date': end_date,
        'selected_location': selected_location,
        'locations': locations,
        'total_due': total_due,
        'total_items': total_items,  # Pass total count
    }

    return render(request, 'reports/payments_due_report.html', context)
