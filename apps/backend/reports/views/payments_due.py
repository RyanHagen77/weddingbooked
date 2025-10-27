# apps/backend/contracts/views/api_reports.py
from datetime import date
import calendar
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from payments.models import SchedulePayment
from contracts.models import Location

@login_required
def payments_due_api(request):
    # Inputs
    start_date_str = request.GET.get("start_date")
    end_date_str   = request.GET.get("end_date")
    location_id    = request.GET.get("location", "all")
    page           = int(request.GET.get("page", 1))
    page_size      = int(request.GET.get("page_size", 50))

    # Defaults to current month
    today = date.today()
    first_day = today.replace(day=1)
    last_day  = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    start_date = parse_date(start_date_str) if start_date_str else first_day
    end_date   = parse_date(end_date_str)   if end_date_str   else last_day

    # Base queryset: unpaid payments in date range
    qs = (
        SchedulePayment.objects
        .filter(due_date__range=(start_date, end_date), paid=False)
        .select_related("schedule", "schedule__contract", "schedule__contract__client")
    )

    if location_id != "all":
        qs = qs.filter(schedule__contract__location_id=location_id)

    # Build flat dicts (avoids N+1; we already selected related)
    rows = []
    for p in qs:
        c = p.schedule.contract
        rows.append({
            "event_date": c.event_date.isoformat(),
            "amount_due": float(p.amount),
            "date_due": p.due_date.isoformat(),
            "primary_contact": getattr(c.client, "primary_contact", "") if c.client_id else "",
            "primary_phone1": getattr(c.client, "primary_phone1", "") if c.client_id else "",
            "custom_contract_number": c.custom_contract_number,
            "contract_id": c.contract_id,
        })

    # Sort by due date asc (like your template)
    rows.sort(key=lambda r: r["date_due"])

    # Totals and pagination
    total_due = round(sum(r["amount_due"] for r in rows), 2)
    paginator = Paginator(rows, page_size)
    page_obj = paginator.get_page(page)

    # Locations for filter dropdown
    locations = list(Location.objects.order_by("name").values("id", "name"))

    return JsonResponse({
        "filters": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "location": location_id,
            "page": page_obj.number,
            "page_size": page_size,
        },
        "summary": {
            "total_due": total_due,
            "total_items": len(rows),
            "total_pages": paginator.num_pages,
        },
        "locations": locations,
        "results": list(page_obj.object_list),
    }, status=200)
