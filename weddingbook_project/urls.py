"""
URL configuration for weddingbook_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path, include
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/logout/', LogoutView.as_view(next_page='/accounts/login/'), name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('bookings/', include('bookings.urls', namespace='bookings')),
    path('contracts/', include('contracts.urls', namespace='contracts')),
    path('documents/', include('documents.urls', namespace='documents')),
    path('payments/', include('payments.urls', namespace='payments')),
    path('products/', include('products.urls', namespace='products')),
    path('reports/', include('reports.urls', namespace='reports')),
    path('services/', include('services.urls', namespace='services')),
    path('users/', include('users.urls', namespace='users')),
    path('communication/', include('communication.urls', namespace='communication')),
    path('wedding_day_guide/', include('wedding_day_guide.urls', namespace='wedding_day_guide')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
