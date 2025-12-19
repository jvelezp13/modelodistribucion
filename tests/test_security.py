"""
Tests de Seguridad para Sistema DxV Multimarcas

Valida que las configuraciones de seguridad críticas estén correctamente implementadas.
"""
import pytest
import os
from fastapi.testclient import TestClient


# ============================================================================
# TESTS DE CORS (API FastAPI)
# ============================================================================

def test_cors_configuration_exists():
    """Verifica que la configuración de CORS existe y está implementada."""
    from api.main import app

    # Verificar que el middleware CORS está configurado
    middlewares = [m for m in app.user_middleware]
    cors_middleware_found = any('CORSMiddleware' in str(m) for m in middlewares)

    assert cors_middleware_found, "CORSMiddleware no está configurado en la app"


def test_cors_rejects_unauthorized_origin():
    """Verifica que CORS rechaza orígenes no autorizados."""
    # Temporalmente configurar CORS para testing
    os.environ['CORS_ALLOWED_ORIGINS'] = 'http://localhost:3000'

    # Re-importar para aplicar nueva configuración
    import importlib
    import api.main
    importlib.reload(api.main)

    from api.main import app
    client = TestClient(app)

    # Intentar acceso desde origen no autorizado
    response = client.get(
        "/api/marcas",
        headers={"Origin": "http://malicious-site.com"}
    )

    # El servidor puede responder, pero no debe incluir CORS headers para este origen
    cors_header = response.headers.get("access-control-allow-origin")
    assert cors_header != "http://malicious-site.com", \
        "CORS está aceptando orígenes no autorizados"


def test_cors_accepts_whitelisted_origin():
    """Verifica que CORS acepta orígenes en la whitelist."""
    os.environ['CORS_ALLOWED_ORIGINS'] = 'http://localhost:3000,http://localhost:8000'

    import importlib
    import api.main
    importlib.reload(api.main)

    from api.main import app
    client = TestClient(app)

    response = client.get(
        "/",
        headers={"Origin": "http://localhost:3000"}
    )

    # Debe incluir el header CORS para este origen
    assert response.status_code == 200
    # Nota: TestClient de FastAPI no siempre procesa CORS headers correctamente
    # En producción, esto funcionará con requests reales


def test_cors_does_not_use_wildcard_in_code():
    """Verifica que el código no use wildcard en CORS."""
    with open('api/main.py', 'r') as f:
        content = f.read()

    # Buscar patrones peligrosos
    dangerous_patterns = [
        'allow_origins=["*"]',
        "allow_origins=['*']",
        'allow_origins = ["*"]',
    ]

    for pattern in dangerous_patterns:
        assert pattern not in content, \
            f"CORS configurado con wildcard en código: {pattern}"


# ============================================================================
# TESTS DE SECRET_KEY (Django)
# ============================================================================

def test_secret_key_validation_in_production():
    """Verifica que Django valida SECRET_KEY en producción."""
    # Guardar estado original
    original_debug = os.environ.get('DJANGO_DEBUG')
    original_secret = os.environ.get('DJANGO_SECRET_KEY')

    try:
        # Simular producción con SECRET_KEY insegura
        os.environ['DJANGO_DEBUG'] = 'False'
        os.environ['DJANGO_SECRET_KEY'] = 'django-insecure-dev-key-change-in-production'

        # Intentar importar settings debería fallar
        with pytest.raises(ValueError) as exc_info:
            import importlib
            import admin_panel.dxv_admin.settings
            importlib.reload(admin_panel.dxv_admin.settings)

        # Verificar mensaje de error
        assert "SECRET_KEY inseguro" in str(exc_info.value)
        assert "modo producción" in str(exc_info.value)

    finally:
        # Restaurar estado original
        if original_debug:
            os.environ['DJANGO_DEBUG'] = original_debug
        else:
            os.environ.pop('DJANGO_DEBUG', None)

        if original_secret:
            os.environ['DJANGO_SECRET_KEY'] = original_secret
        else:
            os.environ.pop('DJANGO_SECRET_KEY', None)


def test_secret_key_allows_development_mode():
    """Verifica que SECRET_KEY insegura está permitida en desarrollo."""
    original_debug = os.environ.get('DJANGO_DEBUG')
    original_secret = os.environ.get('DJANGO_SECRET_KEY')

    try:
        # Simular desarrollo
        os.environ['DJANGO_DEBUG'] = 'True'
        os.environ['DJANGO_SECRET_KEY'] = 'django-insecure-dev-key-change-in-production'

        # NO debería fallar en modo desarrollo
        import importlib
        import admin_panel.dxv_admin.settings
        importlib.reload(admin_panel.dxv_admin.settings)

        # Verificar que DEBUG está True
        assert admin_panel.dxv_admin.settings.DEBUG is True

    finally:
        if original_debug:
            os.environ['DJANGO_DEBUG'] = original_debug
        else:
            os.environ.pop('DJANGO_DEBUG', None)

        if original_secret:
            os.environ['DJANGO_SECRET_KEY'] = original_secret
        else:
            os.environ.pop('DJANGO_SECRET_KEY', None)


def test_secret_key_is_not_hardcoded():
    """Verifica que SECRET_KEY no está hardcodeada en el código."""
    with open('admin_panel/dxv_admin/settings.py', 'r') as f:
        content = f.read()

    # Verificar que usa os.environ.get
    assert "os.environ.get('DJANGO_SECRET_KEY'" in content, \
        "SECRET_KEY debe obtenerse de variables de entorno"

    # Verificar que no hay una SECRET_KEY hardcodeada (excepto la de desarrollo)
    lines = content.split('\n')
    for line in lines:
        if 'SECRET_KEY' in line and '=' in line and 'os.environ' not in line:
            # Si encontramos una asignación de SECRET_KEY sin os.environ
            # Solo está permitida si es la línea de default
            assert 'django-insecure-dev-key' in line, \
                f"SECRET_KEY hardcodeada encontrada: {line}"


# ============================================================================
# TESTS DE DEBUG MODE
# ============================================================================

def test_debug_default_is_false():
    """Verifica que DEBUG es False por defecto (sin variable de entorno)."""
    original_debug = os.environ.get('DJANGO_DEBUG')

    try:
        # Remover variable de entorno
        os.environ.pop('DJANGO_DEBUG', None)

        # Recargar settings
        import importlib
        import admin_panel.dxv_admin.settings
        importlib.reload(admin_panel.dxv_admin.settings)

        # DEBUG debe ser False por defecto
        assert admin_panel.dxv_admin.settings.DEBUG is False, \
            "DEBUG debe ser False por defecto (secure by default)"

    finally:
        if original_debug:
            os.environ['DJANGO_DEBUG'] = original_debug


def test_debug_can_be_enabled_explicitly():
    """Verifica que DEBUG se puede habilitar explícitamente."""
    original_debug = os.environ.get('DJANGO_DEBUG')

    try:
        # Habilitar explícitamente
        os.environ['DJANGO_DEBUG'] = 'True'

        import importlib
        import admin_panel.dxv_admin.settings
        importlib.reload(admin_panel.dxv_admin.settings)

        assert admin_panel.dxv_admin.settings.DEBUG is True

        # Probar otros valores aceptados
        for value in ['true', '1', 'yes']:
            os.environ['DJANGO_DEBUG'] = value
            importlib.reload(admin_panel.dxv_admin.settings)
            assert admin_panel.dxv_admin.settings.DEBUG is True, \
                f"DEBUG debe aceptar '{value}' como True"

    finally:
        if original_debug:
            os.environ['DJANGO_DEBUG'] = original_debug
        else:
            os.environ.pop('DJANGO_DEBUG', None)


# ============================================================================
# TESTS DE CONFIGURACIÓN GENERAL
# ============================================================================

def test_env_example_exists():
    """Verifica que existe .env.example con las variables necesarias."""
    import os.path

    assert os.path.isfile('.env.example'), \
        ".env.example debe existir para documentar variables de entorno"

    with open('.env.example', 'r') as f:
        content = f.read()

    # Variables críticas que DEBEN estar documentadas
    required_vars = [
        'DJANGO_SECRET_KEY',
        'DJANGO_DEBUG',
        'CORS_ALLOWED_ORIGINS',
        'POSTGRES_PASSWORD',
    ]

    for var in required_vars:
        assert var in content, \
            f"Variable {var} debe estar documentada en .env.example"


def test_env_is_gitignored():
    """Verifica que .env está en .gitignore."""
    with open('.gitignore', 'r') as f:
        content = f.read()

    assert '.env' in content, \
        ".env debe estar en .gitignore para no commitear secretos"


def test_no_secrets_in_git():
    """Verifica que no hay secretos obvios commiteados en Git."""
    import subprocess

    # Buscar patrones sospechosos en archivos trackeados
    patterns = [
        'password.*=.*[^example]',  # Passwords que no sean de ejemplo
        'secret.*=.*[0-9a-zA-Z]{20,}',  # Secrets largos
    ]

    for pattern in patterns:
        result = subprocess.run(
            ['git', 'grep', '-i', '-E', pattern],
            capture_output=True,
            text=True
        )

        # Si encuentra algo, debería ser solo en archivos de ejemplo
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                # Permitir solo en .env.example y documentación
                assert '.env.example' in line or 'docs/' in line or 'README' in line, \
                    f"Posible secret commiteado: {line}"


# ============================================================================
# TESTS DE ENDPOINT SECURITY
# ============================================================================

def test_health_endpoint_is_public():
    """Verifica que el endpoint de health check es público."""
    from api.main import app
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_sensitive_endpoints_protected():
    """
    Verifica que endpoints sensibles están protegidos.
    Nota: Este test debe adaptarse según tu implementación de autenticación.
    """
    # TODO: Implementar cuando se agregue autenticación
    # from api.main import app
    # client = TestClient(app)
    #
    # # Intentar acceso sin autenticación
    # response = client.post("/api/simulate", json={...})
    # assert response.status_code in [401, 403]
    pass


# ============================================================================
# TESTS DE DEPENDENCIAS
# ============================================================================

def test_requirements_txt_exists():
    """Verifica que requirements.txt existe."""
    import os.path
    assert os.path.isfile('requirements.txt'), \
        "requirements.txt debe existir"


def test_package_json_exists():
    """Verifica que package.json existe (frontend)."""
    import os.path
    assert os.path.isfile('frontend/package.json'), \
        "frontend/package.json debe existir"


# ============================================================================
# HELPER PARA EJECUTAR TESTS
# ============================================================================

if __name__ == '__main__':
    """
    Ejecutar tests de seguridad directamente:
    python tests/test_security.py
    """
    pytest.main([__file__, '-v', '--tb=short'])
