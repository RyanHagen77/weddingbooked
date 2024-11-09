# wedding_day_guide/urls.py
from django.urls import path
from . import views


app_name = 'wedding_day_guide'

urlpatterns = [
path('wedding-day-guide/<int:contract_id>/', views.wedding_day_guide, name='wedding_day_guide'),
path('wedding-day-guide/view/<int:pk>/', views.wedding_day_guide_view, name='wedding_day_guide_view'),
path('wedding_day_guide/pdf/<int:pk>/', views.wedding_day_guide_pdf, name='wedding_day_guide_pdf'),
path('api/wedding_day_guide/<int:contract_id>/', views.wedding_day_guide_api, name='wedding_day_guide_api'),
    ]