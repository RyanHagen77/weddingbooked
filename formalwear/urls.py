from django.urls import path
from .views import save_formalwear, get_formalwear_products

app_name = "formalwear"

urlpatterns = [
    path('<int:id>/save_formalwear/', save_formalwear, name='save_formalwear'),
    path('api/formalwear_products/', get_formalwear_products, name='get_formalwear_products'),

]
