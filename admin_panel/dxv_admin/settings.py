"""
Django settings for DxV Admin Panel
"""

import os
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

# SECRET_KEY: Clave secreta para Django
# IMPORTANTE: DEBE ser única y no compartirse en el código fuente
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-dev-key-change-in-production')

# DEBUG: Modo de depuración
# IMPORTANTE: DEBE ser False en producción para evitar exposición de información sensible
# TEMPORAL: Habilitado para diagnosticar error 500 en PersonalComercial
DEBUG = True
# DEBUG = False
# if os.environ.get('DJANGO_DEBUG', '').lower() in ('true', '1', 'yes'):
#     DEBUG = True

# 🔒 VALIDACIÓN DE SEGURIDAD
INSECURE_KEY_DETECTED = SECRET_KEY == 'django-insecure-dev-key-change-in-production'

if not DEBUG and INSECURE_KEY_DETECTED:
    raise ValueError(
        "\n"
        "=" * 70 + "\n"
        "🚨 ERROR DE CONFIGURACIÓN DE SEGURIDAD 🚨\n"
        "=" * 70 + "\n"
        "SECRET_KEY inseguro detectado en modo producción (DEBUG=False).\n"
        "\n"
        "ACCIÓN REQUERIDA:\n"
        "1. Generar una clave segura:\n"
        "   python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'\n"
        "\n"
        "2. Configurar en variables de entorno:\n"
        "   export DJANGO_SECRET_KEY='<clave-generada>'\n"
        "\n"
        "3. O agregar a .env:\n"
        "   DJANGO_SECRET_KEY=<clave-generada>\n"
        "\n"
        "NUNCA comitear la SECRET_KEY en el código fuente.\n"
        "=" * 70
    )

# Advertencia en desarrollo si se usa clave insegura
if DEBUG and INSECURE_KEY_DETECTED:
    import warnings
    warnings.warn(
        "⚠️  Usando SECRET_KEY de desarrollo. Esto es aceptable solo en entorno local.",
        stacklevel=2
    )

# Log del modo actual
import logging
logger = logging.getLogger(__name__)
if DEBUG:
    logger.warning("🟡 Servidor Django corriendo en modo DEBUG - Solo para desarrollo")
else:
    logger.info("🟢 Servidor Django corriendo en modo PRODUCCIÓN")

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0').split(',')

# CSRF trusted origins (para Easypanel y otros dominios HTTPS)
CSRF_TRUSTED_ORIGINS = os.environ.get(
    'DJANGO_CSRF_TRUSTED_ORIGINS',
    'https://*.easypanel.host,https://*.easypanel.io'
).split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'core',  # Nuestra app principal
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Para servir archivos estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dxv_admin.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.global_filters',
            ],
        },
    },
]

WSGI_APPLICATION = 'dxv_admin.wsgi.application'

# Database - PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'dxv_db'),
        'USER': os.environ.get('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'core' / 'static',
]

# WhiteNoise - Configuración para servir archivos estáticos en producción
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Admin site customization
ADMIN_SITE_HEADER = "LogiFlow - Planeación"
ADMIN_SITE_TITLE = "LogiFlow"  # Título corto para pestaña del navegador
ADMIN_INDEX_TITLE = ""
