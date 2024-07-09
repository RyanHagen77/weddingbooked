from django.urls import path
from . import views

app_name = 'communication'


urlpatterns = [
    path('send_portal_access/<int:contract_id>/', views.send_portal_access, name='send_portal_access'),
    path('api/contract-messages/<int:contract_id>/', views.get_contract_messages, name='get_contract_messages'),
    path('api/post-contract-message/<int:contract_id>/', views.post_contract_message, name='post_contract_message'),
]
