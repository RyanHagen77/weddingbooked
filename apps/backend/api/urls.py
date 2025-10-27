from django.urls import path, include
from apps.backend.contracts.views.api_user import current_user  # ← import from contracts

urlpatterns = [
    path("contracts/", include("apps.backend.contracts.urls_api")),
    path("users/current/", current_user),   # ← lives in contracts app
]
