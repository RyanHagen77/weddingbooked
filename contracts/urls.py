# appname/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


app_name = 'contracts'

urlpatterns = [
    path('new/', views.new_contract, name='contract_new'),
    path('get_available_staff/', views.get_available_staff, name='get_available_staff'),
    path('get_prospect_photographers/', views.get_prospect_photographers, name='get_prospect_photographers'),
    path('<int:id>/update_prospect_photographers/', views.update_prospect_photographers, name='update_prospect_photographers'),
    path('api/package_options/', views.get_package_options, name='package_options'),
    path('api/engagement_session_options/', views.get_engagement_session_options, name='engagement_session_options'),
    path('api/get_package_discounts/<int:contract_id>/', views.get_package_discounts,
         name='get_package_discounts'),
    path('api/additional_staff_options/', views.get_additional_staff_options, name='additional_staff_options'),
    path('api/overtime_options/', views.get_overtime_options, name='overtime_options'),
    path('client_portal_login/', views.custom_login, name='client_portal_login'),
    path('client_portal_logout/', views.custom_logout, name='client_portal_logout'),
    path('client_portal/contract/<int:contract_id>/', views.client_portal, name='client_portal'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('api/tax_rate/<int:location_id>/', views.get_tax_rate, name='get_tax_rate'),
    path('api/additional_products/', views.get_additional_products, name='get_additional_products'),
    path('<int:id>/save_products/', views.save_products, name='save_products'),
    path('success/', views.success_view, name='success'),
    path('contract_view/', views.contract_view, name='contract_view'),
    path('contract/<int:contract_id>/pdf/', views.generate_contract_pdf, name='generate_contract_pdf'),
    path('<int:id>/', views.contract_detail, name='contract_detail'),
    path('<int:id>/edit/', views.edit_contract, name='edit_contract'),
    path('<int:id>/edit_services/', views.edit_services, name='edit_services'),
    path('<int:id>/save_overtime_entry/', views.save_overtime_entry, name='save_overtime_entry'),
    path('<int:contract_id>/overtime_entries/', views.get_overtime_entries, name='overtime_entries'),
    path('<int:entry_id>/get_overtime_entry/', views.get_overtime_entry, name='get_overtime_entry'),
    path('<int:entry_id>/edit_overtime_entry/', views.edit_overtime_entry, name='edit_overtime_entry'),
    path('<int:entry_id>/delete_overtime_entry/', views.delete_overtime_entry, name='delete_overtime_entry'),
    path('<int:id>/data/', views.get_contract_data, name='get_contract_data'),
    path('document/delete/<int:document_id>/', views.delete_document, name='delete_document'),
    path('<int:id>/manage_staff/', views.manage_staff_assignments, name='manage_staff_assignments'),
    path('get_current_booking/', views.get_current_booking, name='get_current_booking'),
    path('search/', views.search_contracts, name='contract_search'),
    path('bookings/', views.booking_list, name='booking_list'),
    path('booking/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('booking/<int:booking_id>/clear/', views.clear_booking, name='clear_booking'),  # Added this line
    path('<int:contract_id>/transactions/', views.contract_transactions, name='contract_transactions'),
    path('<int:contract_id>/schedule/', views.create_or_update_schedule, name='create_or_update_schedule'),
    path('add_payment/<int:schedule_id>/', views.add_payment, name='add_payment'),
    path('<int:contract_id>/get_custom_schedule/', views.get_custom_schedule, name='get_custom_schedule'),
    path('edit_payment/<int:payment_id>/', views.edit_payment, name='edit_payment'),
    path('delete_payment/<int:payment_id>/', views.delete_payment, name='delete_payment'),
    path('<int:contract_id>/discounts/remove/<int:discount_id>/', views.remove_discount, name='remove_discount'),
    path('<int:contract_id>/discounts/', views.discounts_view, name='discounts_view'),
    path('booking_notes/<int:booking_id>/', views.booking_notes, name='booking_notes'),
    path('add_note/', views.add_note, name='add_note'),
    path('edit_note/<int:note_id>/', views.edit_note, name='edit_note'),
    path('delete_note/<int:note_id>/', views.delete_note, name='delete_note'),
    path('tasks/create/', views.create_task, name='create_task'),

    # Other URLs for this app...
]
