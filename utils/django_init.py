"""
Inicializa Django para uso desde Streamlit
"""
import os
import sys
from pathlib import Path

# Calcular paths
root_path = Path(__file__).parent.parent
admin_panel_path = root_path / 'admin_panel'
core_simulator_path = root_path / 'core'

# IMPORTANTE: Remover /app/core (simulador) del path temporalmente
# para evitar conflicto cuando se importe core.models (Django)
core_simulator_str = str(core_simulator_path)
removed_core = False
if core_simulator_str in sys.path:
    sys.path.remove(core_simulator_str)
    removed_core = True

# Remover /app del path si existe (también tiene core/)
root_str = str(root_path)
removed_root = False
if root_str in sys.path:
    sys.path.remove(root_str)
    removed_root = True

# Agregar admin_panel al INICIO del path
admin_panel_str = str(admin_panel_path)
if admin_panel_str in sys.path:
    sys.path.remove(admin_panel_str)
sys.path.insert(0, admin_panel_str)

# CRÍTICO: Remover módulo 'core' del cache de Python si existe
# Esto es necesario porque si se importó core.simulator antes,
# Python tiene cacheado el módulo 'core' del simulador, y no podrá
# importar core.models desde admin_panel/core/
if 'core' in sys.modules:
    del sys.modules['core']
if 'core.simulator' in sys.modules:
    # Guardar referencia para restaurar después
    core_simulator_module = sys.modules['core.simulator']
    del sys.modules['core.simulator']
else:
    core_simulator_module = None

# Configurar variables de entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dxv_admin.settings')

# Inicializar Django
import django
django.setup()

# Restaurar /app al path después de configurar Django (al final, no al inicio)
if removed_root and root_str not in sys.path:
    sys.path.append(root_str)

# Restaurar core.simulator si existía
if core_simulator_module:
    sys.modules['core.simulator'] = core_simulator_module
