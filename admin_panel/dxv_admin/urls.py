"""
URL configuration for DxV Admin Panel
"""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]

# Customize admin site
admin.site.site_header = "Sistema DxV - Panel de Administración"
admin.site.site_title = "DxV Admin"
admin.site.index_title = "Gestión de Distribución y Ventas"
