from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('contract/<int:contract_id>/pdf/', views.generate_contract_pdf, name='generate_contract_pdf'),
    path('contract_agreement_preview/<int:contract_id>/', views.contract_agreement_preview, name='contract_agreement_preview'),
    path('view_submitted_contract/<int:contract_id>/', views.contract_and_rider_agreement, name='view_submitted_contract'),
    path('client_contract_and_rider_agreement/<int:contract_id>/', views.contract_and_rider_agreement,
         name='client_contract_and_rider_agreement'),
    path('client_rider_agreement/<int:contract_id>/<str:rider_type>/', views.contract_and_rider_agreement,
         name='client_rider_agreement'),
    path('contract/<int:contract_id>/view/', views.view_submitted_contract, name='view_submitted_contract'),
    path('contract/<int:contract_id>/version/<int:version_number>/', views.view_submitted_contract,
         name='view_submitted_contract'),
    path('contract/<int:contract_id>/riders/', views.view_rider_agreements, name='view_rider_agreements'),
    path('document/delete/<int:document_id>/', views.delete_document, name='delete_document'),
    path('api/client-documents/<int:contract_id>/', views.client_documents, name='client_documents'),

]
