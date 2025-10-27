# apps/backend/users/views/api_current.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def current_user(request):
    u = request.user
    full = getattr(u, "get_full_name", None)
    full_name = full() if callable(full) else f"{getattr(u,'first_name','')} {getattr(u,'last_name','')}".strip()
    return JsonResponse({
        "id": u.pk,
        "username": u.username,
        "full_name": full_name or u.username,
        "email": u.email,
    })
