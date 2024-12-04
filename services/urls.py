# services/urls.py
from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [

    path('api/package_options/', views.get_package_options, name='package_options'),
    path('api/engagement_session_options/', views.get_engagement_session_options, name='engagement_session_options'),

    path('api/additional_staff_options/', views.get_additional_staff_options, name='additional_staff_options'),
    path('api/overtime_options/', views.get_overtime_options, name='overtime_options'),
    path('<int:id>/save_overtime_entry/', views.save_overtime_entry, name='save_overtime_entry'),
    path('<int:contract_id>/overtime_entries/', views.get_overtime_entries, name='overtime_entries'),
    path('<int:entry_id>/get_overtime_entry/', views.get_overtime_entry, name='get_overtime_entry'),
    path('<int:entry_id>/edit_overtime_entry/', views.edit_overtime_entry, name='edit_overtime_entry'),
    path('<int:entry_id>/delete_overtime_entry/', views.delete_overtime_entry, name='delete_overtime_entry'),
    # Other URLs for this app...
]
