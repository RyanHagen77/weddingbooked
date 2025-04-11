from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from contracts.models import Contract, Location
from datetime import datetime
import calendar
from django.db.models import Count
from django.core.paginator import Paginator


@login_required
def all_contracts_report(request):
    today = datetime.today()
    first_day_of_month = today.replace(day=1)
    last_day_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    start_date = request.GET.get('start_date', first_day_of_month.strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', last_day_of_month.strftime('%Y-%m-%d'))
    selected_location = request.GET.get('location', 'all')
    selected_status = request.GET.get('status', 'all')

    contracts = Contract.objects.filter(contract_date__range=[start_date, end_date])
    if selected_location != 'all':
        contracts = contracts.filter(location_id=selected_location)
    if selected_status != 'all':
        contracts = contracts.filter(status=selected_status)

    paginator = Paginator(contracts, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Status count summary
    status_counts = contracts.values('status').annotate(total=Count('contract_id'))
    status_map = dict(Contract.STATUS_CHOICES)
    report_data = {status_map.get(entry['status'], entry['status']): entry['total'] for entry in status_counts}
    for key, label in Contract.STATUS_CHOICES:
        if label not in report_data:
            report_data[label] = 0

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'selected_location': selected_location,
        'selected_status': selected_status,
        'locations': Location.objects.all(),
        'statuses': Contract.STATUS_CHOICES,
        'report_data': page_obj,
        'page_obj': page_obj,
    }

    return render(request, 'reports/all_contracts_report.html', context)
