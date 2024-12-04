# bookings/urls.py

from django.urls import path
from . import views

app_name = 'bookings'  # This registers the 'bookings' namespace
urlpatterns = [

    path('booking_search/', views.booking_search, name='booking_search'),
    path('get_available_staff/', views.get_available_staff, name='get_available_staff'),
    path('<int:contract_id>/manage_staff/', views.manage_staff_assignments, name='manage_staff_assignments'),
    path('get_current_booking/', views.get_current_booking, name='get_current_booking'),
    path('bookings/', views.booking_list, name='booking_list'),
    path('booking/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('booking_staff/<int:booking_id>/', views.booking_detail_staff, name='booking_detail_staff'),
    path('confirm_booking/<int:booking_id>/', views.confirm_booking, name='confirm_booking'),
    path('booking/<int:booking_id>/clear/', views.clear_booking, name='clear_booking'),  # Added this line
    # Prospect Photographers API
    path('api/prospect-photographers/', views.get_prospect_photographers, name='prospect-photographers'),

]
