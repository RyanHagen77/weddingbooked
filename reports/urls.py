# reports/urls.py
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
path('reports/', views.reports, name='reports'),
path('lead_source_report/', views.lead_source_report, name='lead_source_report'),
path('appointments/', views.appointments_report, name='appointments_report'),
path('reception_venue_report/', views.reception_venue_report, name='reception_venue_report'),
path('revenue_report/', views.revenue_report, name='revenue_report'),
path('revenue_by_contract/', views.revenue_by_contract, name='revenue_by_contract'),
path('deferred_revenue_report/', views.deferred_revenue_report, name='deferred_revenue_report'),
path('sales_detail_report/', views.sales_detail_report, name='sales_detail_report'),
path('sales_detail_by_contract/', views.sales_detail_by_contract, name='sales_detail_by_contract'),
path('sales_taxes_report/', views.sales_tax_report, name='sales_tax_report'),
path('event_staff_payroll/', views.event_staff_payroll_report, name='event_staff_payroll_report'),
path('payments_due_report/', views.payments_due_report, name='payments_due_report'),
path('formal_wear_deposit_report/', views.formal_wear_deposit_report, name='formal_wear_deposit_report'),
path('contacts_report/', views.contacts_report, name='contacts_report'),
]

handler403 = 'reports.views.custom_403_view'