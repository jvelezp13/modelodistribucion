"""
WSGI config for DxV Admin Panel
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dxv_admin.settings')

application = get_wsgi_application()
