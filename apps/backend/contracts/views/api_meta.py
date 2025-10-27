# apps/backend/contracts/views/api_meta.py
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_GET
from django.db.models import Q, Value, CharField
from django.db.models.functions import Concat, Coalesce

from contracts.models import Location, LeadSourceCategory  # adjust if needed
from users.models import Role  # adjust if needed

User = get_user_model()

def _has_field(model, name: str) -> bool:
    try:
        model._meta.get_field(name)
        return True
    except Exception:
        return False

def _base_employee_q():
    q = Q(is_active=True)
    if _has_field(User, "user_type"):
        q &= Q(user_type="employee")
    if _has_field(User, "status"):
        q &= Q(status="ACTIVE")
    return q

def _role_name(role_constant_fallback: str) -> str:
    # If Role.SOMETHING exists use it, else fall back to the string passed in.
    return getattr(Role, role_constant_fallback, role_constant_fallback)

def _people_q(*role_constants: str, groups: tuple[str, ...] = ()):
    roles_q = Q()
    for rc in role_constants:
        rn = _role_name(rc)
        roles_q |= Q(role__name=rn) | Q(additional_roles__name=rn)
    groups_q = Q()
    for g in groups:
        groups_q |= Q(groups__name=g)
    return _base_employee_q() & (roles_q | groups_q)

@require_GET
def contracts_meta(request):
    # Statuses for search UI
    statuses = [
        {"value": "pipeline", "label": "Pipeline"},
        {"value": "forecast", "label": "Forecast"},
        {"value": "booked", "label": "Booked"},
        {"value": "completed", "label": "Completed"},
        {"value": "dead", "label": "Dead"},
    ]

    # Locations
    locations = list(Location.objects.order_by("name").values("id", "name"))

    # Optional lead source categories
    try:
        lead_source_categories = list(
            LeadSourceCategory.objects.order_by("name").values("id", "name")
        )
    except Exception:
        lead_source_categories = []

    # Full name expr -> normalized to `name` in .values()
    full_name_expr = Coalesce(
        Concat("first_name", Value(" "), "last_name", output_field=CharField()),
        "username",
        output_field=CharField(),
    )

    # SALES / CSRs
    csrs = list(
        User.objects.filter(
            _people_q("SALES_PERSON", groups=("Sales",))
        )
        .annotate(name=full_name_expr)   # ← normalize to `name`
        .values("id", "name")
        .distinct()
        .order_by("first_name", "last_name", "username")
    )

    # COORDINATORS
    coordinators = list(
        User.objects.filter(
            _people_q("COORDINATOR", groups=("Coordinator", "Office Staff"))
        )
        .annotate(name=full_name_expr)
        .values("id", "name")
        .distinct()
        .order_by("first_name", "last_name", "username")
    )

    # Event staff lists (for search filters)
    photographers = list(
        User.objects.filter(_people_q("PHOTOGRAPHER", groups=("Photographers",)))
        .annotate(name=full_name_expr)
        .values("id", "name")
        .distinct()
        .order_by("first_name", "last_name", "username")
    )
    videographers = list(
        User.objects.filter(_people_q("VIDEOGRAPHER", groups=("Videographers",)))
        .annotate(name=full_name_expr)
        .values("id", "name")
        .distinct()
        .order_by("first_name", "last_name", "username")
    )
    photobooth_operators = list(
        User.objects.filter(_people_q("PHOTOBOOTH_OPERATOR", groups=("Photobooth", "Photo Booth")))
        .annotate(name=full_name_expr)
        .values("id", "name")
        .distinct()
        .order_by("first_name", "last_name", "username")
    )
    djs = list(
        User.objects.filter(_people_q("DJ", groups=("DJs", "DJ")))
        .annotate(name=full_name_expr)
        .values("id", "name")
        .distinct()
        .order_by("first_name", "last_name", "username")
    )

    # Response
    resp = {
        "statuses": statuses,
        "locations": locations,
        "lead_source_categories": lead_source_categories,

        # for search/new-contract UIs
        "csrs": csrs,
        "coordinators": coordinators,

        # alias for any older code expecting `sales`
        "sales": csrs,

        # event staff
        "photographers": photographers,
        "videographers": videographers,
        "photobooth_operators": photobooth_operators,
        "djs": djs,
    }

    r = JsonResponse(resp, status=200)
    r["Cache-Control"] = "public, max-age=600"
    return r
