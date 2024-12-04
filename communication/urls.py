from django.urls import path
from . import views

app_name = 'communication'


urlpatterns = [
    path('send_portal_access/<int:contract_id>/', views.send_portal_access, name='send_portal_access'),
    path('api/contract-messages/<int:contract_id>/', views.get_contract_messages, name='get_contract_messages'),
    path('api/post-contract-message/<int:contract_id>/', views.post_contract_message, name='post_contract_message'),
    path('tasks/', views.task_list, name='tasks'),
    path('tasks/get/', views.get_tasks, name='get_tasks'),
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/create/<int:contract_id>/', views.create_task, name='create_task'),
    path('tasks/update/<int:task_id>/', views.update_task, name='update_task'),
    path('tasks/mark-complete/<int:task_id>/', views.mark_complete, name='mark_complete'),
]
