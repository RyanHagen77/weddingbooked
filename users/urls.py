from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


app_name = 'users'  # replace 'users' with your actual app name

urlpatterns = [

    path('login/', views.user_login_view, name='login'),
    path('logout/', views.user_logout_view, name='logout'),
    path('office_staff/', views.OfficeStaffListView.as_view(), name='office_staff_list'),
    path('office-staff/new/', views.OfficeStaffCreateView.as_view(), name='office_staff_new'),
    path('office-staff/<int:pk>/edit/', views.OfficeStaffUpdateView.as_view(), name='office_staff_edit'),
    path('office_staff_dashboard/<int:pk>/', views.office_staff_dashboard, name='office_staff_dashboard'),
    path('event_staff_dashboard/<int:pk>/', views.event_staff_dashboard, name='event_staff_dashboard'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('profile/', views.profile_redirect, name='profile_redirect'),
    path('bookings/<int:pk>/approve/', views.approve_booking, name='approve_booking'),
    path('bookings/<int:pk>/decline/', views.decline_booking, name='decline_booking'),
    path('tasks/', views.task_list, name='tasks'),
    path('tasks/list/', views.get_tasks, name='task_list'),
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/create/contract/<int:contract_id>/', views.create_task, name='create_task_for_contract'),
    path('tasks/create/note/<int:note_id>/', views.create_task, name='create_task_for_note'),
    path('tasks/update/<int:task_id>/', views.update_task, name='update_task'),
    path('tasks/mark-complete/<int:task_id>/', views.mark_complete, name='mark_complete'),
    path('event_staff/', views.event_staff, name='event_staff'),
    path('update_event_staff_ranking/', views.update_event_staff_ranking, name='update_event_staff_ranking'),
    path('event_staff_schedule/<int:user_id>/', views.event_staff_schedule, name='event_staff_schedule'),
    path('get_event_staff_schedule/<int:user_id>/', views.get_event_staff_schedule, name='get_event_staff_schedule'),
    path('update_event_staff_schedule/<int:user_id>/', views.update_event_staff_schedule, name='update_event_staff_schedule'),
    path('financial_reports/', views.financial_reports, name='financial_reports'),


]
