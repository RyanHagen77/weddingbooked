# contracts/urls.py
from django.urls import path
from . import views


app_name = 'payments'

urlpatterns = [
path('<int:contract_id>/schedule/', views.create_or_update_schedule, name='create_or_update_schedule'),
path('add_payment/<int:schedule_id>/', views.add_payment, name='add_payment'),
path('<int:contract_id>/schedule_payments_due/', views.get_schedule_payments_due,
     name='get_schedule_payments_due'),
path('<int:contract_id>/get_custom_schedule/', views.get_custom_schedule, name='get_custom_schedule'),
path('edit_payment/<int:payment_id>/', views.edit_payment, name='edit_payment'),
path('delete_payment/<int:payment_id>/', views.delete_payment, name='delete_payment'),
path('<int:contract_id>/get_existing_payments/', views.get_existing_payments,
     name='get_existing_payments')
    ]