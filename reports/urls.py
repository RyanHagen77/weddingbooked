# reports/urls.py
from django.urls import path
from . import views
from reports.views.appointments_report import appointments_report
from reports.views.lead_source_report import lead_source_report
from reports.views.reception_venue_report import reception_venue_report
from reports.views.revenue_report import revenue_report
from reports.views.revenue_by_contract import revenue_by_contract
from reports.views.deferred_revenue_report import deferred_revenue_report
from reports.views.sales_detail_report import sales_detail_report
from reports.views.sales_detail_by_contract import sales_detail_by_contract
from reports.views.sales_tax_report import sales_tax_report
from reports.views.event_staff_payroll_report import event_staff_payroll_report
from reports.views.payments_due_report import payments_due_report
from reports.views.formalwear_deposit_report import formalwear_deposit_report
from reports.views.contacts_report import contacts_report

app_name = 'reports'

urlpatterns = [
    path('reports/', views.reports, name='reports'),
    path('lead_source_report/', lead_source_report, name='lead_source_report'),
    path('appointments/', appointments_report, name='appointments_report'),
    path('reception_venue_report/', reception_venue_report, name='reception_venue_report'),
    path('revenue_report/', revenue_report, name='revenue_report'),
    path('revenue_by_contract/', revenue_by_contract, name='revenue_by_contract'),
    path('deferred_revenue_report/', deferred_revenue_report, name='deferred_revenue_report'),
    path('sales_detail_report/', sales_detail_report, name='sales_detail_report'),
    path('sales_detail_by_contract/', sales_detail_by_contract, name='sales_detail_by_contract'),
    path('sales_taxes_report/', sales_tax_report, name='sales_tax_report'),
    path('event_staff_payroll/', event_staff_payroll_report, name='event_staff_payroll_report'),
    path('payments_due_report/', payments_due_report, name='payments_due_report'),
    path('formalwear_deposit_report/', formalwear_deposit_report, name='formalwear_deposit_report'),
    path('contacts_report/', contacts_report, name='contacts_report'),
        ]


