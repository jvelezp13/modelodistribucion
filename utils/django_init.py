"""
Inicializa Django para uso desde Streamlit
"""
import os
import sys
from pathlib import Path

# Agregar admin_panel al INICIO del path para que Django encuentre core.models
admin_panel_path = Path(__file__).parent.parent / 'admin_panel'
admin_panel_str = str(admin_panel_path)

# Remover si existe y agregar al inicio para asegurar prioridad
if admin_panel_str in sys.path:
    sys.path.remove(admin_panel_str)
sys.path.insert(0, admin_panel_str)

# Configurar variables de entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dxv_admin.settings')

# Inicializar Django
import django
django.setup()
