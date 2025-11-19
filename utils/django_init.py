"""
Inicializa Django para uso desde Streamlit
"""
import os
import sys
from pathlib import Path

# Agregar admin_panel al path
admin_panel_path = Path(__file__).parent.parent / 'admin_panel'
if str(admin_panel_path) not in sys.path:
    sys.path.insert(0, str(admin_panel_path))

# Configurar variables de entorno de Django si no están configuradas
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dxv_admin.settings')

# Configurar Django
import django
django.setup()
