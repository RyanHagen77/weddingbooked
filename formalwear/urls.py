from django.urls import path
from .views import save_formalwear

app_name = "formalwear"

urlpatterns = [
    path('save-formalwear/<int:contract_id>/', save_formalwear, name='save_formalwear'),  # ✅ Use `contract_id`
]
