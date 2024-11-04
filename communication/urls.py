from django.urls import path
from . import views

app_name = 'communication'


urlpatterns = [
    path('send_portal_access/<int:contract_id>/', views.send_portal_access, name='send_portal_access'),

    path('booking_notes/<int:booking_id>/', views.booking_notes, name='booking_notes'),
    path('add_note/', views.add_note, name='add_note'),
    path('edit_note/<int:note_id>/', views.edit_note, name='edit_note'),
    path('delete_note/<int:note_id>/', views.delete_note, name='delete_note'),

    path('api/contract-messages/<int:contract_id>/', views.get_contract_messages, name='get_contract_messages'),
    path('api/post-contract-message/<int:contract_id>/', views.post_contract_message, name='post_contract_message'),
    path('tasks/', views.task_list, name='tasks'),
    path('tasks/create/', views.create_internal_task, name='create_internal_task'),
    path('tasks/get/', views.get_internal_tasks, name='get_internal_tasks'),
    path('tasks/create/note/<int:note_id>/', views.create_internal_task, name='create_task_for_note'),
    path('tasks/update/<int:task_id>/', views.update_task, name='update_task'),
    path('tasks/mark-complete/<int:task_id>/', views.mark_complete, name='mark_complete'),
    path('tasks/get/', views.get_internal_tasks, name='get_internal_tasks'),
    path('tasks/create/', views.create_contract_task, name='create_contract_task'),
    path('tasks/get/<int:contract_id>/', views.get_contract_tasks, name='get_contract_tasks'),
]
