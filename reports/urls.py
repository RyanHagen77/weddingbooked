# reports/urls.py
from django.urls import path
from . import views
from reports.all_reports_views.appointments_report import appointments_report
from reports.all_reports_views.lead_source_report import lead_source_report
from reports.all_reports_views.reception_venue_report import reception_venue_report
from reports.all_reports_views.revenue_report import revenue_report
from reports.all_reports_views.revenue_by_contract import revenue_by_contract
from reports.all_reports_views.deferred_revenue_report import deferred_revenue_report
from reports.all_reports_views.sales_detail_report import sales_detail_report
from reports.all_reports_views.sales_detail_by_contract import sales_detail_by_contract
from reports.all_reports_views.sales_tax_report import sales_tax_report
from reports.all_reports_views.event_staff_payroll_report import event_staff_payroll_report
from reports.all_reports_views.services_report import services_report
from reports.all_reports_views.payments_due_report import payments_due_report
from reports.all_reports_views.contacts_report import contacts_report
from reports.all_reports_views.formalwear_deposit_report_new import formalwear_deposit_report_new
from reports.all_reports_views.all_contracts_report import all_contracts_report


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
    path('services_report/', services_report, name='services_report'),
    path('payments_due_report/', payments_due_report, name='payments_due_report'),
    path('formalwear_deposit_report_new/', formalwear_deposit_report_new, name='formalwear_deposit_report_new'),
    path('contacts_report/', contacts_report, name='contacts_report'),
    path('all_contracts_report/', all_contracts_report, name='all_contracts_report')
        ]


