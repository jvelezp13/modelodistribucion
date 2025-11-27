"""
URL configuration for DxV Admin Panel
"""
from django.urls import path
from core.admin_site import dxv_admin_site

urlpatterns = [
    path('admin/', dxv_admin_site.urls),
]
