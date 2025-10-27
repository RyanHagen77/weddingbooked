from datetime import datetime, timedelta, date
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required

from django.db.models import Q
from django.core.exceptions import ValidationError, FieldError

from contracts.models import Contract  # adjust import

# ---------- helpers ----------
def _parse_date(s, name):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        raise ValidationError(f"Invalid {name}: must be YYYY-MM-DD")

def _parse_int(s, name):
    try:
        v = int(s)
        if v <= 0:
            raise ValueError()
        return v
    except Exception:
        raise ValidationError(f"Invalid {name}: must be a positive integer")

def _csv_ids(s, name):
    if not s:
        return None
    try:
        return [int(x) for x in s.split(",") if x.strip()]
    except Exception:
        raise ValidationError(f"Invalid {name}: must be CSV of integers")

# ---------- search view ----------
@login_required
@require_GET
def search_contracts(request):
    """
    Query params (subset mirroring the old form):
      q
      contract_number
      primary_contact
      status
      location    (id)
      csr         (id)
      ceremony_site
      reception_site
      event_date_from, event_date_to
      contract_date_from, contract_date_to
      photographer        (id)
      videographer        (id)
      photobooth_operator (id)
      dj                  (id)
      sort: event_date|-event_date|contract_date|-contract_date|custom_contract_number|-custom_contract_number
      page (default 1), page_size (default 25, max 100)

    Response rows match the legacy table fields.
    """

    # -------- parse ----------
    try:
        q = (request.GET.get("q") or "").strip()
        contract_number = (request.GET.get("contract_number") or "").strip()
        primary_contact = (request.GET.get("primary_contact") or "").strip()
        status = (request.GET.get("status") or "").strip().lower() or None

        location_id = request.GET.get("location")
        csr_id = request.GET.get("csr")

        ceremony_site = (request.GET.get("ceremony_site") or "").strip()
        reception_site = (request.GET.get("reception_site") or "").strip()

        event_from = request.GET.get("event_date_from")
        event_to = request.GET.get("event_date_to")
        event_from = _parse_date(event_from, "event_date_from") if event_from else None
        event_to = _parse_date(event_to, "event_date_to") if event_to else None

        contract_from = request.GET.get("contract_date_from")
        contract_to = request.GET.get("contract_date_to")
        contract_from = _parse_date(contract_from, "contract_date_from") if contract_from else None
        contract_to = _parse_date(contract_to, "contract_date_to") if contract_to else None

        # staff filters (single id each)
        photographer_id = request.GET.get("photographer")
        videographer_id = request.GET.get("videographer")
        photobooth_id = request.GET.get("photobooth_operator")
        dj_id = request.GET.get("dj")

        location_id = _parse_int(location_id, "location") if location_id else None
        csr_id = _parse_int(csr_id, "csr") if csr_id else None
        photographer_id = _parse_int(photographer_id, "photographer") if photographer_id else None
        videographer_id = _parse_int(videographer_id, "videographer") if videographer_id else None
        photobooth_id = _parse_int(photobooth_id, "photobooth_operator") if photobooth_id else None
        dj_id = _parse_int(dj_id, "dj") if dj_id else None

        sort_param = request.GET.get("sort") or "event_date"  # legacy: soonest first
        allowed_sorts = {
            "event_date": "event_date",
            "-event_date": "-event_date",
            "contract_date": "contract_date",
            "-contract_date": "-contract_date",
            "custom_contract_number": "custom_contract_number",
            "-custom_contract_number": "-custom_contract_number",
        }
        if sort_param not in allowed_sorts:
            raise ValidationError(f"Invalid sort: {sort_param}")
        order_by = allowed_sorts[sort_param]

        page = int(request.GET.get("page") or 1)
        page = max(1, page)
        page_size = int(request.GET.get("page_size") or 25)
        page_size = min(100, max(1, page_size))

    except ValidationError as ve:
        return JsonResponse({"error": str(ve)}, status=400)

    # -------- base queryset ----------
    qs = Contract.objects.select_related(
        "client", "location", "csr",
        "photographer1", "photographer2",
        "videographer1", "videographer2",
        "photobooth_op1", "photobooth_op2",
        "dj1", "dj2",
    )

    # -------- apply legacy-style filters ----------
    if location_id:
        qs = qs.filter(location_id=location_id)

    if ceremony_site:
        qs = qs.filter(ceremony_site__icontains=ceremony_site)

    if reception_site:
        qs = qs.filter(reception_site__icontains=reception_site)

    if event_from and event_to:
        qs = qs.filter(event_date__range=[event_from, event_to])

    if contract_from and contract_to:
        qs = qs.filter(contract_date__range=[contract_from, contract_to])

    if contract_number:
        qs = qs.filter(
            Q(custom_contract_number__icontains=contract_number) |
            Q(old_contract_number__icontains=contract_number)
        )

    if primary_contact:
        qs = qs.filter(client__primary_contact__icontains=primary_contact)

    if status:
        qs = qs.filter(status=status)

    if csr_id:
        qs = qs.filter(csr_id=csr_id)

    if photographer_id:
        qs = qs.filter(Q(photographer1_id=photographer_id) | Q(photographer2_id=photographer_id))

    if videographer_id:
        qs = qs.filter(Q(videographer1_id=videographer_id) | Q(videographer2_id=videographer_id))

    if photobooth_id:
        qs = qs.filter(Q(photobooth_op1_id=photobooth_id) | Q(photobooth_op2_id=photobooth_id))

    if dj_id:
        qs = qs.filter(Q(dj1_id=dj_id) | Q(dj2_id=dj_id))

    # Quick search "q" (plus optional date parsing like legacy)
    if q:
        filt = (
            Q(custom_contract_number__icontains=q) |
            Q(old_contract_number__icontains=q) |
            Q(client__primary_contact__icontains=q) |
            Q(client__partner_contact__icontains=q) |
            Q(client__primary_email__icontains=q) |
            Q(client__primary_phone1__icontains=q) |
            Q(client__primary_phone2__icontains=q)
        )
        # try parse as date (mm/dd/yyyy or mm-dd-yyyy)
        date_obj = None
        for fmt in ("%m/%d/%Y", "%m-%d-%Y"):
            try:
                date_obj = datetime.strptime(q, fmt).date()
                break
            except ValueError:
                pass
        if date_obj:
            filt |= Q(event_date=date_obj)
        qs = qs.filter(filt)

    # Legacy default: if no event date supplied, show upcoming week
    today = date.today()
    if not (event_from or event_to):
        event_from = today
        event_to = today + timedelta(days=30)
        qs = qs.filter(event_date__range=[event_from, event_to])
    else:
        if event_from and event_to:
            qs = qs.filter(event_date__range=[event_from, event_to])
        elif event_from:
            qs = qs.filter(event_date__gte=event_from)
        elif event_to:
            qs = qs.filter(event_date__lte=event_to)

    # -------- order, count, slice ----------
    try:
        qs = qs.order_by(order_by, "pk")  # use pk (your model uses contract_id)
        total = qs.count()
    except FieldError as fe:
        return JsonResponse({"error": f"Field error: {fe}"}, status=400)

    start = (page - 1) * page_size
    end = start + page_size

    # -------- serialize minimal row for React (match legacy table) ----------
    rows = []
    for c in qs[start:end]:
        # resolve names safely (your related Users likely have get_full_name())
        def _full(u):
            if not u:
                return None
            # prefer get_full_name if defined, else first + last or username
            fn = getattr(u, "get_full_name", None)
            if callable(fn):
                name = fn()
                return name or None
            parts = [getattr(u, "first_name", None), getattr(u, "last_name", None)]
            name = " ".join([p for p in parts if p])
            return name or getattr(u, "username", None) or None

        rows.append({
            "id": c.pk,  # will be contract_id under the hood
            "custom_contract_number": c.custom_contract_number,
            "event_date": c.event_date.isoformat() if c.event_date else None,
            "status": c.status,
            "client": {
                "id": getattr(c.client, "id", None),
                "primary_contact": getattr(c.client, "primary_contact", None),
                "email": getattr(c.client, "primary_email", None),
            } if c.client_id else None,
            "location": {"id": c.location_id, "name": getattr(c.location, "name", None)} if c.location_id else None,
            "csr": {"id": c.csr_id, "name": _full(getattr(c, "csr", None))} if c.csr_id else None,

            # staffing + package flags (for N/A / Not Assigned rendering)
            "photography_package": bool(getattr(c, "photography_package", False)),
            "photography_additional": bool(getattr(c, "photography_additional", False)),
            "photographer1_name": _full(getattr(c, "photographer1", None)),
            "photographer2_name": _full(getattr(c, "photographer2", None)),

            "videography_package": bool(getattr(c, "videography_package", False)),
            "videography_additional": bool(getattr(c, "videography_additional", False)),
            "videographer1_name": _full(getattr(c, "videographer1", None)),
            "videographer2_name": _full(getattr(c, "videographer2", None)),

            "photobooth_package": bool(getattr(c, "photobooth_package", False)),
            "photobooth_additional": bool(getattr(c, "photobooth_additional", False)),
            "photobooth_op1_name": _full(getattr(c, "photobooth_op1", None)),
            "photobooth_op2_name": _full(getattr(c, "photobooth_op2", None)),

            "dj_package": bool(getattr(c, "dj_package", False)),
            "dj1_name": _full(getattr(c, "dj1", None)),
            "dj2_name": _full(getattr(c, "dj2", None)),
        })

    return JsonResponse({
        "results": rows,
        "page": page,
        "page_size": page_size,
        "total": total,
    }, status=200)
