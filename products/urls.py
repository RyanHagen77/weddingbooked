
from django.urls import path
from . import views


app_name = 'products'

urlpatterns = [
    path('api/additional_products/', views.get_additional_products, name='get_additional_products'),
    path('<int:id>/save_products/', views.save_products, name='save_products'),
]