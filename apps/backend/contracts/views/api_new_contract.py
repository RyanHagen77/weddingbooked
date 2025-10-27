# apps/backend/contracts/views/api.py

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from django.db.models import Q, Value, CharField
from django.db.models.functions import Concat, Coalesce
from django.utils.dateparse import parse_date

from users.models import Role  # SALES_PERSON / COORDINATOR constants or names

# Your app models
from contracts.models import Contract, Location
try:
    from contracts.models import LeadSourceCategory
except Exception:
    LeadSourceCategory = None

try:
    from contracts.models import Client
except Exception:
    Client = None

User = get_user_model()


# ---------- helpers ----------

def _err(field, msg, status=400):
    return JsonResponse({"errors": {field: [msg]}}, status=status)

def _req(d, key, label=None):
    v = d.get(key)
    if v is None or str(v).strip() == "":
        raise ValueError(f"{label or key} is required.")
    return str(v).strip()

def _to_int(x):
    try:
        return int(x)
    except Exception:
        return None


# ---------- GET /api/contracts/meta/ ----------

@require_GET
def contracts_meta(request):
    """
    Returns dropdown data for the React form:
    {
      locations: [{id, name}],
      lead_source_categories: [{id, name}],
      sales: [{id, full_name}],
      coordinators: [{id, full_name}]
    }
    """
    # Locations
    locations = list(Location.objects.order_by("name").values("id", "name"))

    # Lead Source Categories (FK if present)
    if LeadSourceCategory is not None:
        lead_source_categories = list(
            LeadSourceCategory.objects.order_by("name").values("id", "name")
        )
    else:
        lead_source_categories = []

    # Employees (sales & coordinators)
    full_name_expr = Coalesce(
        Concat("first_name", Value(" "), "last_name", output_field=CharField()),
        "username",
        output_field=CharField(),
    )
    base_emp = Q(user_type="employee", status="ACTIVE", is_active=True)

    sales = list(
        User.objects.filter(
            base_emp & (
                Q(role__name=getattr(Role, "SALES_PERSON", "SALES_PERSON")) |
                Q(additional_roles__name=getattr(Role, "SALES_PERSON", "SALES_PERSON")) |
                Q(groups__name="Sales")
            )
        )
        .annotate(full_name=full_name_expr)
        .values("id", "full_name")
        .distinct()
        .order_by("first_name", "last_name", "username")
    )

    coordinators = list(
        User.objects.filter(
            base_emp &
            Q(groups__name="Office Staff") &
            (
                Q(role__name=getattr(Role, "COORDINATOR", "COORDINATOR")) |
                Q(additional_roles__name=getattr(Role, "COORDINATOR", "COORDINATOR")) |
                Q(groups__name="Coordinator")
            )
        )
        .annotate(full_name=full_name_expr)
        .values("id", "full_name")
        .distinct()
        .order_by("first_name", "last_name", "username")
    )

    return JsonResponse(
        {
            "locations": locations,
            "lead_source_categories": lead_source_categories,
            "sales": sales,
            "coordinators": coordinators,
        },
        status=200,
    )


# ---------- POST /api/contracts/new/ ----------

@require_POST
@transaction.atomic
def new_contract(request):
    """
    Accepts application/x-www-form-urlencoded from the React form.
    Creates exactly one Contract record (no second save).
    On success -> {"redirect_url": "/contracts/new/", "id": <pk>}
    """
    d = request.POST

    # required
    try:
        event_date_str  = _req(d, "event_date", "Event date")
        location_id     = _req(d, "location", "Store Location")
        csr_id          = _req(d, "csr", "Sales Representative")
        coord_id        = _req(d, "coordinator", "Coordinator")
        primary_contact = _req(d, "primary_contact", "Primary contact")
        primary_email   = _req(d, "primary_email", "Primary email")
    except ValueError as ve:
        return _err("__all__", str(ve))

    event_date = parse_date(event_date_str)
    if not event_date:
        return _err("event_date", "Invalid date. Use YYYY-MM-DD.")

    # optional
    is_code_92 = d.get("is_code_92") in ("on", "true", "1")
    lead_source_details = (d.get("lead_source_details") or "").strip()
    lsc_raw = (d.get("lead_source_category") or "").strip()

    bridal_party_qty = _to_int(d.get("bridal_party_qty")) or 0
    guests_qty       = _to_int(d.get("guests_qty")) or 0

    ceremony_site   = (d.get("ceremony_site") or "").strip()
    ceremony_city   = (d.get("ceremony_city") or "").strip()
    ceremony_state  = (d.get("ceremony_state") or "").strip()
    reception_site  = (d.get("reception_site") or "").strip()
    reception_city  = (d.get("reception_city") or "").strip()
    reception_state = (d.get("reception_state") or "").strip()

    partner_contact = (d.get("partner_contact") or "").strip() or None
    primary_phone1  = (d.get("primary_phone1")  or "").strip() or None

    # resolve FKs
    location = Location.objects.filter(pk=_to_int(location_id)).first()
    if not location:
        return _err("location", "Invalid location.")

    csr = User.objects.filter(pk=_to_int(csr_id), is_active=True).first()
    if not csr:
        return _err("csr", "Invalid sales representative.")

    coordinator = User.objects.filter(pk=_to_int(coord_id), is_active=True).first()
    if not coordinator:
        return _err("coordinator", "Invalid coordinator.")

    lsc_obj = None
    if lsc_raw:
        if not lsc_raw.isdigit() or LeadSourceCategory is None:
            return _err("lead_source_category", "Invalid lead source category.")
        lsc_obj = LeadSourceCategory.objects.filter(pk=int(lsc_raw)).first()
        if not lsc_obj:
            return _err("lead_source_category", "Invalid lead source category.")

    # upsert client (if model exists)
    client = None
    if Client is not None:
        try:
            user_model = get_user_model()
            user, _ = user_model.objects.get_or_create(
                email=primary_email,
                defaults={"username": primary_email, "user_type": "client"},
            )
            client, _ = Client.objects.update_or_create(
                user=user,
                defaults={
                    "primary_contact": primary_contact,
                    "primary_email": primary_email,
                    "primary_phone1": primary_phone1,
                    "partner_contact": partner_contact,
                },
            )
        except Exception:
            client = None  # allow the contract to save without client

    create_kwargs = dict(
        client=client,
        is_code_92=is_code_92,
        event_date=event_date,
        location=location,
        csr=csr,
        coordinator=coordinator,
        lead_source_details=lead_source_details,
        status=getattr(Contract, "PIPELINE", "pipeline"),
        bridal_party_qty=bridal_party_qty,
        guests_qty=guests_qty,
        ceremony_site=ceremony_site,
        ceremony_city=ceremony_city,
        ceremony_state=ceremony_state,
        reception_site=reception_site,
        reception_city=reception_city,
        reception_state=reception_state,
    )
    if lsc_obj is not None:
        create_kwargs["lead_source_category"] = lsc_obj

    try:
        contract = Contract.objects.create(**create_kwargs)
    except IntegrityError as ie:
        # expose the exact constraint so the FE toast is useful
        return _err("__all__", f"IntegrityError: {ie}", status=409)
    except Exception as e:
        return _err("__all__", f"{type(e).__name__}", status=400)

    # success → send the React app back to a fresh blank form
    return JsonResponse({"redirect_url": "/contracts/new/", "id": contract.pk}, status=201)
