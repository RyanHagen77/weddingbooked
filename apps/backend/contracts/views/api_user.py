# apps/backend/contracts/views/api_user.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def current_user(request):
    u = request.user
    return JsonResponse({
        "id": u.pk,
        "username": u.username,
        "first_name": u.first_name or u.username.split(" ")[0],
        "email": u.email,
    }, status=200)
