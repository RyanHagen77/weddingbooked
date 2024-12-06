from django.urls import path
from . import views
from .views import (
    CustomTokenObtainPairView,
    CustomPasswordResetView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetDoneView,
    CustomPasswordResetCompleteView
)

app_name = 'users'  # Replace 'users' with your actual app name

urlpatterns = [

    # JWT Authentication URLs
    path('api/token/', CustomTokenObtainPairView, name='token_obtain_pair'),

    # Client Portal URLs
    path('client_portal_login/', views.custom_login, name='client_portal_login'),
    path('client_portal_logout/', views.custom_logout, name='client_portal_logout'),
    path('client_portal/contract/<int:contract_id>/', views.client_portal, name='client_portal'),

    # Login and Logout
    path('login/', views.user_login_view, name='login'),
    path('logout/', views.user_logout_view, name='logout'),

    # Office Staff Management
    path('office_staff/', views.OfficeStaffListView, name='office_staff_list'),
    path('office-staff/new/', views.OfficeStaffCreateView, name='office_staff_new'),
    path('office-staff/<int:pk>/edit/', views.OfficeStaffUpdateView, name='office_staff_edit'),
    path('office_staff_dashboard/<int:pk>/', views.office_staff_dashboard, name='office_staff_dashboard'),

    # Event Staff Management
    path('event_staff_dashboard/<int:pk>/', views.event_staff_dashboard, name='event_staff_dashboard'),
    path('event_staff/', views.event_staff, name='event_staff'),
    path('update_event_staff_ranking/', views.update_event_staff_ranking, name='update_event_staff_ranking'),
    path('event_staff_schedule/<int:user_id>/', views.event_staff_schedule, name='event_staff_schedule'),
    path('event_staff_schedule_read_only/<int:user_id>/', views.event_staff_schedule_read_only, name='event_staff_schedule_read_only'),
    path('get_event_staff_schedule/<int:user_id>/', views.get_event_staff_schedule, name='get_event_staff_schedule'),
    path('update_always_off_days/<int:user_id>/', views.update_always_off_days, name='update_always_off_days'),
    path('update_specific_date_availability/<int:user_id>/', views.update_specific_date_availability, name='update_specific_date_availability'),

    # Password Reset Flow
    path('password_reset/', CustomPasswordResetView, name='password_reset'),
    path('password_reset/done/', CustomPasswordResetDoneView, name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView, name='password_reset_confirm'),
    path('reset/complete/', CustomPasswordResetCompleteView, name='password_reset_complete'),
]
