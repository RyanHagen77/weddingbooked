from django.urls import path
from . import views

app_name = 'communication'


urlpatterns = [
    path('send_portal_access/<int:contract_id>/', views.send_portal_access, name='send_portal_access'),
]
