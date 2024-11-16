# contracts/urls.py
from django.urls import path
from django.shortcuts import redirect
from . import views
from django.contrib.auth import views as auth_views
from .views import CustomTokenObtainPairView

app_name = 'contracts'

def redirect_to_next_login(request):
    return redirect('https://www.enet2.com/client_portal')

urlpatterns = [
    path('new/', views.new_contract, name='contract_new'),

    path('api/package_options/', views.get_package_options, name='package_options'),
    path('api/engagement_session_options/', views.get_engagement_session_options, name='engagement_session_options'),
    path('api/get_package_discounts/<int:contract_id>/', views.get_package_discounts,
         name='get_package_discounts'),
    path('api/additional_staff_options/', views.get_additional_staff_options, name='additional_staff_options'),
    path('api/overtime_options/', views.get_overtime_options, name='overtime_options'),
    path('<int:id>/save_overtime_entry/', views.save_overtime_entry, name='save_overtime_entry'),
    path('<int:contract_id>/overtime_entries/', views.get_overtime_entries, name='overtime_entries'),
    path('<int:entry_id>/get_overtime_entry/', views.get_overtime_entry, name='get_overtime_entry'),
    path('<int:entry_id>/edit_overtime_entry/', views.edit_overtime_entry, name='edit_overtime_entry'),
    path('<int:entry_id>/delete_overtime_entry/', views.delete_overtime_entry, name='delete_overtime_entry'),

    # Client Portal URLs
    path('client_portal_login/', views.custom_login, name='client_portal_login'),
    path('client_portal_logout/', views.custom_logout, name='client_portal_logout'),
    path('client_portal/contract/<int:contract_id>/', views.client_portal, name='client_portal'),


    # Password Reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # JWT Authentication URLs
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),

    # Prospect Photographers API
    path('api/prospect-photographers/', views.get_prospect_photographers, name='prospect-photographers'),

    path('api/tax_rate/<int:location_id>/', views.get_tax_rate, name='get_tax_rate'),
    path('api/additional_products/', views.get_additional_products, name='get_additional_products'),
    path('<int:id>/save_products/', views.save_products, name='save_products'),
    path('success/', views.success_view, name='success'),


    path('<int:id>/', views.contract_detail, name='contract_detail'),
    path('<int:id>/edit/', views.edit_contract, name='edit_contract'),
    path('<int:id>/edit_services/', views.edit_services, name='edit_services'),
    path('<int:id>/data/', views.get_contract_data, name='get_contract_data'),


    path('search/', views.contract_search, name='contract_search'),


    path('add_service_fee/<int:contract_id>/', views.add_service_fees, name='add_service_fee'),
    path('delete_service_fee/<int:fee_id>/', views.delete_service_fee, name='delete_service_fee'),
    path('<int:contract_id>/get_service_fees/', views.get_service_fees, name='get_service_fees'),
    path('<int:contract_id>/discounts/remove/<int:discount_id>/', views.remove_discount, name='remove_discount'),
    path('<int:contract_id>/discounts/', views.discounts_view, name='discounts_view'),

    # Other URLs for this app...
]
