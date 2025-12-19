# 🎯 Plan de Acción - Implementación de Mejoras DxV Multimarcas

**Proyecto:** Sistema de Simulación de Distribución Multimarcas
**Basado en:** ANALISIS_CODIGO.md
**Fecha de Creación:** 19 de Diciembre, 2025
**Versión:** 1.0

---

## 📋 Índice de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Estructura de Sprints](#estructura-de-sprints)
3. [Sprint 1: Seguridad Crítica (Semana 1-2)](#sprint-1-seguridad-crítica)
4. [Sprint 2: Calidad de Código (Mes 1)](#sprint-2-calidad-de-código)
5. [Sprint 3: Testing y Performance (Mes 2-3)](#sprint-3-testing-y-performance)
6. [Sprint 4: Mejora Continua (Mes 4+)](#sprint-4-mejora-continua)
7. [Métricas de Éxito](#métricas-de-éxito)
8. [Gestión de Riesgos](#gestión-de-riesgos)

---

## 📊 Resumen Ejecutivo

### Objetivo General
Elevar la calidad, seguridad y rendimiento del sistema DxV desde **6/10** promedio hasta **8.5/10** en 4 meses, priorizando vulnerabilidades críticas de seguridad.

### Estado Actual vs. Objetivo

| Dominio | Actual | Objetivo | Δ |
|---------|--------|----------|---|
| Seguridad | 4/10 🔴 | 9/10 🟢 | +5 |
| Calidad de Código | 6/10 🟡 | 8/10 🟢 | +2 |
| Rendimiento | 6/10 🟡 | 8.5/10 🟢 | +2.5 |
| Arquitectura | 7/10 🟢 | 8.5/10 🟢 | +1.5 |
| Testing | 2/10 🔴 | 7/10 🟡 | +5 |

### Inversión Total Estimada
- **Tiempo:** 12-14 semanas (3-3.5 meses)
- **Esfuerzo:** ~280-320 horas de desarrollo
- **Equipo:** 1-2 desarrolladores

---

## 🗓️ Estructura de Sprints

```
┌─────────────────────────────────────────────────────────────┐
│                    TIMELINE DE 4 MESES                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Sprint 1        Sprint 2        Sprint 3        Sprint 4   │
│  ═══════╗        ═══════╗        ═══════╗        ═══════╗   │
│  CRÍTICO ║        CALIDAD║       TESTING ║       CONTINUA║   │
│  Sem 1-2 ║        Sem 3-6║       Sem 7-10║      Sem 11+  ║   │
│  ═══════╝        ═══════╝        ═══════╝        ═══════╝   │
│                                                              │
│  🔴 Seguridad    🟡 Refactor     🟢 Tests        🔵 Docs    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔴 Sprint 1: Seguridad Crítica (Semana 1-2)

**Duración:** 10 días laborables
**Esfuerzo:** 40 horas
**Prioridad:** CRÍTICA - Bloqueante para producción
**Responsable:** Backend Developer + DevOps

### Objetivos del Sprint
- ✅ Eliminar **TODAS** las vulnerabilidades críticas
- ✅ Preparar sistema para despliegue seguro en producción
- ✅ Establecer validaciones automáticas de seguridad

---

### 📌 Tarea 1.1: Corregir Configuración CORS

**ID:** SEC-001
**Prioridad:** 🔴 CRÍTICA
**Estimación:** 2 horas
**Dependencias:** Ninguna

#### Descripción
Reemplazar configuración CORS permisiva por política restrictiva basada en variables de entorno.

#### Archivos Afectados
- `api/main.py`
- `.env.example`
- `docker-compose.yml`

#### Implementación Paso a Paso

**Paso 1: Crear nueva configuración CORS** (30 min)

```python
# api/main.py (línea 41-48)

import os
from typing import List

# Configuración segura de CORS
def get_allowed_origins() -> List[str]:
    """Obtiene orígenes permitidos desde env vars."""
    origins_str = os.environ.get(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:3000,http://localhost:8000'  # Solo para desarrollo
    )
    return [origin.strip() for origin in origins_str.split(',')]

# Aplicar middleware con configuración segura
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    max_age=600,  # Cache preflight por 10 minutos
)
```

**Paso 2: Agregar validación de producción** (15 min)

```python
# api/main.py (después de CORSMiddleware)

# Validación: advertir si CORS está abierto
allowed_origins = get_allowed_origins()
if "*" in allowed_origins:
    logger.warning(
        "⚠️  CORS configurado con wildcard (*). "
        "Esto es INSEGURO para producción. "
        "Configure CORS_ALLOWED_ORIGINS en variables de entorno."
    )
```

**Paso 3: Documentar variables de entorno** (15 min)

```bash
# .env.example (agregar)

# === CORS Configuration ===
# Lista separada por comas de orígenes permitidos
# DESARROLLO: http://localhost:3000,http://localhost:8000
# PRODUCCIÓN: https://app.tudominio.com,https://admin.tudominio.com
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

**Paso 4: Actualizar docker-compose** (30 min)

```yaml
# docker-compose.yml (servicio api)
services:
  api:
    environment:
      - CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS:-http://localhost:3000}
```

**Paso 5: Testing** (30 min)

```bash
# Test manual
curl -H "Origin: http://malicious-site.com" http://localhost:8000/api/marcas
# Debe fallar con CORS error

curl -H "Origin: http://localhost:3000" http://localhost:8000/api/marcas
# Debe funcionar correctamente
```

#### Criterios de Aceptación
- [ ] CORS no acepta `*` como origen
- [ ] Solo dominios en whitelist pueden acceder
- [ ] Advertencia en logs si CORS está abierto
- [ ] Documentación actualizada en README
- [ ] Variables de entorno configuradas en .env.example

#### Pruebas de Validación
```python
# tests/test_security.py (NUEVO)
import pytest
from fastapi.testclient import TestClient
from api.main import app

def test_cors_rejects_unauthorized_origin():
    client = TestClient(app)
    response = client.get(
        "/api/marcas",
        headers={"Origin": "http://malicious-site.com"}
    )
    # Debería fallar o no incluir CORS headers
    assert "access-control-allow-origin" not in response.headers

def test_cors_accepts_whitelisted_origin():
    client = TestClient(app)
    response = client.get(
        "/api/marcas",
        headers={"Origin": "http://localhost:3000"}
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
```

---

### 📌 Tarea 1.2: Validar SECRET_KEY en Producción

**ID:** SEC-002
**Prioridad:** 🟠 ALTA
**Estimación:** 1 hora
**Dependencias:** Ninguna

#### Descripción
Agregar validación que previene usar SECRET_KEY inseguro en producción.

#### Archivos Afectados
- `admin_panel/dxv_admin/settings.py`

#### Implementación

```python
# admin_panel/dxv_admin/settings.py (después de línea 12)

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-dev-key-change-in-production')

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

# Advertencia en desarrollo
if DEBUG and INSECURE_KEY_DETECTED:
    import warnings
    warnings.warn(
        "Usando SECRET_KEY de desarrollo. Esto es aceptable solo en entorno local.",
        stacklevel=2
    )
```

#### Criterios de Aceptación
- [ ] Aplicación falla al iniciar en producción sin SECRET_KEY válido
- [ ] Mensaje de error claro con instrucciones
- [ ] Advertencia visible en modo desarrollo
- [ ] No rompe entorno de desarrollo local

---

### 📌 Tarea 1.3: Cambiar DEBUG Default a False

**ID:** SEC-003
**Prioridad:** 🟡 MEDIA
**Estimación:** 30 minutos
**Dependencias:** Ninguna

#### Descripción
Invertir lógica de DEBUG para que sea False por defecto (seguro por defecto).

#### Implementación

```python
# admin_panel/dxv_admin/settings.py (línea 15)

# ❌ ANTES (inseguro por defecto)
# DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

# ✅ DESPUÉS (seguro por defecto)
DEBUG = False
if os.environ.get('DJANGO_DEBUG', '').lower() in ('true', '1', 'yes'):
    DEBUG = True

# Log del modo actual
import logging
logger = logging.getLogger(__name__)
if DEBUG:
    logger.warning("🟡 Servidor corriendo en modo DEBUG - Solo para desarrollo")
else:
    logger.info("🟢 Servidor corriendo en modo PRODUCCIÓN")
```

```bash
# .env.example (documentar)

# === Django Debug Mode ===
# IMPORTANTE: Solo activar en desarrollo local
# NUNCA activar en producción
# Valores aceptados: true, 1, yes (cualquier otro = False)
DJANGO_DEBUG=true
```

#### Criterios de Aceptación
- [ ] DEBUG es False si no se configura variable
- [ ] Solo valores explícitos activan DEBUG
- [ ] Log visible del modo actual al iniciar
- [ ] Documentación clara en .env.example

---

### 📌 Tarea 1.4: Crear Checklist de Seguridad

**ID:** SEC-004
**Prioridad:** 🟢 MEDIA
**Estimación:** 2 horas
**Dependencias:** SEC-001, SEC-002, SEC-003

#### Descripción
Documentar checklist de seguridad para despliegues futuros.

#### Entregable

```markdown
# docs/SECURITY_CHECKLIST.md (NUEVO ARCHIVO)

# 🔒 Checklist de Seguridad - Sistema DxV

## Pre-Despliegue a Producción

### Variables de Entorno Críticas
- [ ] `DJANGO_SECRET_KEY` configurado con valor único y seguro
- [ ] `DJANGO_DEBUG=False` (o no configurado)
- [ ] `CORS_ALLOWED_ORIGINS` con dominios específicos (sin wildcard)
- [ ] `POSTGRES_PASSWORD` con contraseña fuerte
- [ ] Todas las passwords en variables de entorno (no en código)

### Configuración Django
- [ ] `DEBUG = False` en producción
- [ ] `ALLOWED_HOSTS` configurado correctamente
- [ ] `CSRF_TRUSTED_ORIGINS` incluye dominios HTTPS
- [ ] Secrets no presentes en repositorio Git

### Configuración FastAPI
- [ ] CORS restrictivo (dominios específicos)
- [ ] Rate limiting configurado (opcional)
- [ ] HTTPS forzado en producción
- [ ] Logs de seguridad habilitados

### Base de Datos
- [ ] Usuario de BD con permisos mínimos necesarios
- [ ] Conexión encriptada (SSL) si es remota
- [ ] Backups automáticos configurados
- [ ] Credentials rotadas periódicamente

### Testing de Seguridad
- [ ] Tests de CORS ejecutados
- [ ] Scan de dependencias sin vulnerabilidades críticas
- [ ] SECRET_KEY validation test pasa
- [ ] Endpoints sin autenticación revisados

## Comando de Validación

```bash
# Ejecutar antes de deploy
python admin_panel/manage.py check --deploy
```

## Contacto en Caso de Incidente
- Email: seguridad@tuempresa.com
- Slack: #security-incidents
```

#### Criterios de Aceptación
- [ ] Checklist completo y revisado
- [ ] Integrado en proceso de deploy
- [ ] Compartido con equipo DevOps

---

### 📊 Resumen Sprint 1

| Tarea | Estimación | Prioridad | Status |
|-------|-----------|-----------|---------|
| SEC-001: CORS | 2h | 🔴 Crítica | Pendiente |
| SEC-002: SECRET_KEY | 1h | 🟠 Alta | Pendiente |
| SEC-003: DEBUG | 30min | 🟡 Media | Pendiente |
| SEC-004: Checklist | 2h | 🟢 Media | Pendiente |
| **TOTAL** | **5.5h** | - | - |

### Métricas de Éxito Sprint 1
- ✅ **0** vulnerabilidades críticas
- ✅ **100%** de validaciones de seguridad implementadas
- ✅ **Checklist** de seguridad documentado
- ✅ **Tests** de seguridad ejecutándose en CI

---

## 🟡 Sprint 2: Calidad de Código (Mes 1)

**Duración:** 4 semanas
**Esfuerzo:** 120 horas
**Prioridad:** ALTA
**Responsable:** Backend Developer

### Objetivos del Sprint
- ✅ Refactorizar archivos monolíticos
- ✅ Mejorar manejo de errores
- ✅ Implementar caché básico
- ✅ Reducir complejidad ciclomática

---

### 📌 Tarea 2.1: Refactorizar models.py (Prioridad ALTA)

**ID:** QUALITY-001
**Prioridad:** 🔴 CRÍTICA
**Estimación:** 60 horas (1.5 semanas)
**Dependencias:** Requiere rama Git separada

#### Descripción
Dividir `admin_panel/core/models.py` (3,664 líneas) en módulos especializados por dominio.

#### Estrategia de Migración
**Enfoque:** Refactoring incremental sin romper compatibilidad

#### Plan de Ejecución

**Fase 1: Preparación** (8 horas)

```bash
# Crear estructura de carpetas
mkdir -p admin_panel/core/models
touch admin_panel/core/models/__init__.py
touch admin_panel/core/models/base.py
touch admin_panel/core/models/marca.py
touch admin_panel/core/models/personal.py
touch admin_panel/core/models/vehiculos.py
touch admin_panel/core/models/geografia.py
touch admin_panel/core/models/proyecciones.py
touch admin_panel/core/models/configuracion.py

# Crear rama de trabajo
git checkout -b refactor/split-models-module
```

**Fase 2: Extraer Modelos Base** (4 horas)

```python
# admin_panel/core/models/base.py
"""
Modelos base y utilidades compartidas.
"""
from django.db import models
from decimal import Decimal

# Choices globales (usadas por múltiples modelos)
INDICE_INCREMENTO_CHOICES = [
    ('salarios', 'Incremento Salarios General'),
    ('salario_minimo', 'Incremento Salario Mínimo'),
    ('ipc', 'IPC (Índice de Precios al Consumidor)'),
    # ... resto de choices
]

TIPO_ASIGNACION_GEO_CHOICES = [...]
TIPO_ASIGNACION_OPERACION_CHOICES = [...]
CRITERIO_PRORRATEO_OPERACION_CHOICES = [...]

# Funciones auxiliares compartidas
def _calcular_costo_nomina_compartido(...):
    """Wrapper para calcular costo de nómina."""
    from core.calculadora_prestaciones import calcular_costo_nomina
    # ... implementación
```

**Fase 3: Extraer por Dominio** (40 horas)

```python
# admin_panel/core/models/marca.py
"""Modelos relacionados con Marcas, Escenarios y Operaciones."""
from django.db import models
from .base import *

class Marca(models.Model):
    """Modelo para las marcas del sistema"""
    # ... campos

class Escenario(models.Model):
    """Representa una versión de presupuesto."""
    # ... campos

class Operacion(models.Model):
    """Operación / Centro de Costos."""
    # ... campos

class MarcaOperacion(models.Model):
    """Relación M:N entre Marca y Operación."""
    # ... campos
```

```python
# admin_panel/core/models/personal.py
"""Modelos de personal (Comercial, Logístico, Administrativo)."""
from django.db import models
from .base import *
from .marca import Escenario

class PersonalComercial(models.Model):
    """Personal de ventas."""
    # ... campos

class PersonalLogistico(models.Model):
    """Personal de logística."""
    # ... campos

class PersonalAdministrativo(models.Model):
    """Personal administrativo."""
    # ... campos

# Modelos de asignación multi-marca
class PersonalComercialMarca(models.Model):
    # ... campos

class PersonalLogisticoMarca(models.Model):
    # ... campos

class PersonalAdministrativoMarca(models.Model):
    # ... campos
```

```python
# admin_panel/core/models/vehiculos.py
"""Modelos de vehículos y rutas logísticas."""
from django.db import models
from .base import *

class Vehiculo(models.Model):
    """Vehículo de la flota."""
    # ... campos

class RutaLogistica(models.Model):
    """Ruta de distribución."""
    # ... campos

class RutaMunicipio(models.Model):
    """Municipios en una ruta."""
    # ... campos
```

```python
# admin_panel/core/models/geografia.py
"""Modelos geográficos (Municipios, Zonas, Matrices)."""
from django.db import models
from .base import *

class Municipio(models.Model):
    """Municipio colombiano."""
    # ... campos

class Zona(models.Model):
    """Zona comercial."""
    # ... campos

class ZonaMunicipio(models.Model):
    """Municipios en una zona."""
    # ... campos

class MatrizDesplazamiento(models.Model):
    """Matriz de distancias."""
    # ... campos

class ConfiguracionLejania(models.Model):
    """Configuración de lejanías."""
    # ... campos

class ZonaMarca(models.Model):
    """Asignación multi-marca de zonas."""
    # ... campos
```

```python
# admin_panel/core/models/proyecciones.py
"""Modelos de proyección de ventas."""
from django.db import models
from .base import *
from .marca import Escenario, Marca

class ProyeccionVentasConfig(models.Model):
    """Configuración de proyección de ventas."""
    # ... campos

class TipologiaProyeccion(models.Model):
    """Tipología de clientes para proyección."""
    # ... campos

class ProyeccionManual(models.Model):
    """Proyección manual mensual."""
    # ... campos

class CanalVenta(models.Model):
    """Canal de venta."""
    # ... campos

class CategoriaProducto(models.Model):
    """Categoría de producto."""
    # ... campos

class Producto(models.Model):
    """Producto comercializado."""
    # ... campos
```

```python
# admin_panel/core/models/configuracion.py
"""Modelos de configuración del sistema."""
from django.db import models
from .base import *

class ParametrosMacro(models.Model):
    """Parámetros macroeconómicos."""
    # ... campos

class FactorPrestacional(models.Model):
    """Factores prestacionales."""
    # ... campos

class PoliticaRecursosHumanos(models.Model):
    """Políticas de RRHH."""
    # ... campos

class ConfiguracionDescuentos(models.Model):
    """Configuración de descuentos."""
    # ... campos

class TramoDescuentoFactura(models.Model):
    """Tramos de descuento."""
    # ... campos

class Impuesto(models.Model):
    """Impuestos."""
    # ... campos

# Modelos de Gastos
class GastoComercial(models.Model):
    # ... campos

class GastoLogistico(models.Model):
    # ... campos

class GastoAdministrativo(models.Model):
    # ... campos

class GastoComercialMarca(models.Model):
    # ... campos

class GastoLogisticoMarca(models.Model):
    # ... campos

class GastoAdministrativoMarca(models.Model):
    # ... campos
```

**Fase 4: Retrocompatibilidad** (4 horas)

```python
# admin_panel/core/models/__init__.py
"""
Punto de entrada para modelos.
Importa todos los modelos para retrocompatibilidad.
"""

# Importar todos los modelos para que estén disponibles como antes
from .base import (
    INDICE_INCREMENTO_CHOICES,
    TIPO_ASIGNACION_GEO_CHOICES,
    TIPO_ASIGNACION_OPERACION_CHOICES,
    CRITERIO_PRORRATEO_OPERACION_CHOICES,
    _calcular_costo_nomina_compartido,
)

from .marca import (
    Marca,
    Escenario,
    Operacion,
    MarcaOperacion,
)

from .personal import (
    PersonalComercial,
    PersonalLogistico,
    PersonalAdministrativo,
    PersonalComercialMarca,
    PersonalLogisticoMarca,
    PersonalAdministrativoMarca,
)

from .vehiculos import (
    Vehiculo,
    RutaLogistica,
    RutaMunicipio,
)

from .geografia import (
    Municipio,
    Zona,
    ZonaMunicipio,
    MatrizDesplazamiento,
    ConfiguracionLejania,
    ZonaMarca,
)

from .proyecciones import (
    ProyeccionVentasConfig,
    TipologiaProyeccion,
    ProyeccionManual,
    CanalVenta,
    CategoriaProducto,
    Producto,
)

from .configuracion import (
    ParametrosMacro,
    FactorPrestacional,
    PoliticaRecursosHumanos,
    ConfiguracionDescuentos,
    TramoDescuentoFactura,
    Impuesto,
    GastoComercial,
    GastoLogistico,
    GastoAdministrativo,
    GastoComercialMarca,
    GastoLogisticoMarca,
    GastoAdministrativoMarca,
)

# Esto permite que el código existente siga funcionando:
# from admin_panel.core.models import Marca, Escenario, etc.

__all__ = [
    # Base
    'INDICE_INCREMENTO_CHOICES',
    'TIPO_ASIGNACION_GEO_CHOICES',
    'TIPO_ASIGNACION_OPERACION_CHOICES',
    'CRITERIO_PRORRATEO_OPERACION_CHOICES',
    # Marca
    'Marca',
    'Escenario',
    'Operacion',
    'MarcaOperacion',
    # Personal
    'PersonalComercial',
    'PersonalLogistico',
    'PersonalAdministrativo',
    'PersonalComercialMarca',
    'PersonalLogisticoMarca',
    'PersonalAdministrativoMarca',
    # Vehículos
    'Vehiculo',
    'RutaLogistica',
    'RutaMunicipio',
    # Geografía
    'Municipio',
    'Zona',
    'ZonaMunicipio',
    'MatrizDesplazamiento',
    'ConfiguracionLejania',
    'ZonaMarca',
    # Proyecciones
    'ProyeccionVentasConfig',
    'TipologiaProyeccion',
    'ProyeccionManual',
    'CanalVenta',
    'CategoriaProducto',
    'Producto',
    # Configuración
    'ParametrosMacro',
    'FactorPrestacional',
    'PoliticaRecursosHumanos',
    'ConfiguracionDescuentos',
    'TramoDescuentoFactura',
    'Impuesto',
    'GastoComercial',
    'GastoLogistico',
    'GastoAdministrativo',
    'GastoComercialMarca',
    'GastoLogisticoMarca',
    'GastoAdministrativoMarca',
]
```

**Fase 5: Verificación y Testing** (4 horas)

```bash
# 1. Verificar que las migraciones están al día
python admin_panel/manage.py makemigrations
# Debe mostrar: "No changes detected"

# 2. Ejecutar tests existentes
python admin_panel/manage.py test

# 3. Verificar imports en todo el proyecto
grep -r "from.*models import" admin_panel/ api/ core/

# 4. Probar que el admin sigue funcionando
python admin_panel/manage.py runserver
# Navegar a /admin y verificar todos los modelos
```

#### Criterios de Aceptación
- [ ] Todos los modelos divididos en módulos lógicos
- [ ] Ningún archivo supera 500 líneas
- [ ] Imports siguen funcionando (`from models import Marca`)
- [ ] `makemigrations` no detecta cambios
- [ ] Tests existentes pasan
- [ ] Admin panel funciona correctamente
- [ ] No hay importaciones circulares

#### Riesgos y Mitigación
| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Romper imports existentes | Media | Alto | Tests exhaustivos + __init__.py con re-exports |
| Importaciones circulares | Alta | Alto | Imports diferidos + estructura cuidadosa |
| Conflictos Git | Media | Medio | Rama separada + merge cuidadoso |

---

### 📌 Tarea 2.2: Mejorar Manejo de Excepciones

**ID:** QUALITY-002
**Prioridad:** 🟠 ALTA
**Estimación:** 16 horas (2 días)
**Dependencias:** Ninguna

#### Descripción
Reemplazar 4 bloques `except:` genéricos por manejo específico con logging.

#### Ubicaciones a Corregir

**Ubicación 1: api/main.py:1211**

```python
# ❌ ANTES
try:
    for lp in config.lista_precios.filter(activo=True).select_related('producto'):
        productos_info.append({
            'id': lp.producto.id,
            'nombre': lp.producto.nombre,
            'precio': lp.precio,
        })
except:
    pass

# ✅ DESPUÉS
try:
    for lp in config.lista_precios.filter(activo=True).select_related('producto'):
        productos_info.append({
            'id': lp.producto.id,
            'nombre': lp.producto.nombre,
            'precio': float(lp.precio),
        })
except AttributeError as e:
    logger.warning(f"Lista de precios no configurada para {config}: {e}")
    productos_info = []
except Exception as e:
    logger.exception(f"Error inesperado obteniendo productos: {e}")
    productos_info = []
```

**Ubicación 2: admin_panel/core/admin.py:2097**

```python
# ❌ ANTES
try:
    valor = obj.get_valor_display()
except:
    valor = obj.valor

# ✅ DESPUÉS
try:
    valor = obj.get_valor_display()
except AttributeError:
    # get_valor_display no existe, usar valor directo
    valor = obj.valor
except Exception as e:
    logger.error(f"Error obteniendo valor para display: {e}", exc_info=True)
    valor = "Error"
```

**Ubicación 3: admin_panel/core/admin.py:2107**

```python
# ❌ ANTES
try:
    return format_html('<span style="color: green;">✓</span>')
except:
    return '-'

# ✅ DESPUÉS
try:
    return format_html('<span style="color: green;">✓</span>')
except (ValueError, TypeError) as e:
    logger.warning(f"Error formateando HTML: {e}")
    return '-'
```

**Ubicación 4: admin_panel/core/admin.py:2196**

```python
# ❌ ANTES
try:
    related_obj = getattr(obj, field_name)
    return related_obj.nombre
except:
    return '-'

# ✅ DESPUÉS
try:
    related_obj = getattr(obj, field_name)
    if related_obj is None:
        return '-'
    return related_obj.nombre
except AttributeError as e:
    logger.debug(f"Campo {field_name} no existe en {obj}: {e}")
    return '-'
except Exception as e:
    logger.error(f"Error accediendo a {field_name}: {e}", exc_info=True)
    return 'Error'
```

#### Test de Validación

```python
# tests/test_error_handling.py (NUEVO)
import pytest
from unittest.mock import Mock, patch
from api.main import obtener_productos_info  # función refactorizada

def test_productos_info_handles_missing_config():
    """Verifica que se maneja correctamente una config sin lista_precios."""
    mock_config = Mock()
    mock_config.lista_precios.filter.side_effect = AttributeError("No lista_precios")

    result = obtener_productos_info(mock_config)

    assert result == []
    # Verificar que se loggeó la advertencia

def test_productos_info_handles_unexpected_error():
    """Verifica que errores inesperados se loggean."""
    mock_config = Mock()
    mock_config.lista_precios.filter.side_effect = RuntimeError("DB error")

    result = obtener_productos_info(mock_config)

    assert result == []
    # Verificar que se loggeó el error con traceback
```

#### Criterios de Aceptación
- [ ] 0 bloques `except:` sin tipo específico
- [ ] Todos los errores esperados loggeados apropiadamente
- [ ] Tests cubren casos de error
- [ ] No se rompe funcionalidad existente

---

### 📌 Tarea 2.3: Implementar Caché en Endpoints

**ID:** QUALITY-003
**Prioridad:** 🟡 MEDIA
**Estimación:** 8 horas (1 día)
**Dependencias:** Ninguna

#### Descripción
Agregar caché en endpoints de lectura frecuente para reducir latencia 80%.

#### Endpoints a Cachear
1. `GET /api/marcas` - Casi estático
2. `GET /api/escenarios` - Cambia raramente
3. `GET /api/operaciones` - Por escenario

#### Implementación

**Paso 1: Configurar Django Cache** (1 hora)

```python
# admin_panel/dxv_admin/settings.py (agregar)

# === CACHE CONFIGURATION ===
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'dxv-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}

# Para producción con Redis (opcional):
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
#     }
# }
```

**Paso 2: Crear utilidad de caché** (2 horas)

```python
# api/cache_utils.py (NUEVO ARCHIVO)
"""
Utilidades de caché para FastAPI endpoints.
"""
from django.core.cache import cache
from functools import wraps
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

def cache_endpoint(timeout=300, key_prefix="api"):
    """
    Decorator para cachear respuestas de endpoints.

    Args:
        timeout: Segundos de cache (default 5 minutos)
        key_prefix: Prefijo para la cache key

    Example:
        @cache_endpoint(timeout=600, key_prefix="marcas")
        def listar_marcas():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar cache key basada en función y argumentos
            key_parts = [key_prefix, func.__name__]

            # Incluir argumentos en la key
            if args:
                key_parts.append(str(args))
            if kwargs:
                key_parts.append(json.dumps(kwargs, sort_keys=True))

            cache_key = ":".join(key_parts)

            # Hash si es muy largo
            if len(cache_key) > 200:
                cache_key = f"{key_prefix}:{hashlib.md5(cache_key.encode()).hexdigest()}"

            # Intentar obtener de cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_result

            # Cache miss - ejecutar función
            logger.debug(f"Cache MISS: {cache_key}")
            result = func(*args, **kwargs)

            # Guardar en cache
            cache.set(cache_key, result, timeout)

            return result

        return wrapper
    return decorator

def invalidate_cache(key_pattern):
    """
    Invalida cache keys que coincidan con el patrón.

    Args:
        key_pattern: Patrón para invalidar (ej: "marcas:*")
    """
    # Django LocMemCache no soporta pattern matching
    # Para invalidación completa:
    cache.clear()
    logger.info(f"Cache invalidada: {key_pattern}")
```

**Paso 3: Aplicar caché a endpoints** (3 horas)

```python
# api/main.py (modificar endpoints)

from api.cache_utils import cache_endpoint

@app.get("/api/marcas")
@cache_endpoint(timeout=600, key_prefix="marcas")  # 10 minutos
def listar_marcas() -> List[str]:
    """Lista todas las marcas activas disponibles"""
    try:
        loader = get_loader()
        marcas = loader.listar_marcas()
        logger.info(f"Marcas disponibles: {marcas}")
        return marcas
    except Exception as e:
        logger.error(f"Error listando marcas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/escenarios")
@cache_endpoint(timeout=300, key_prefix="escenarios")  # 5 minutos
def listar_escenarios() -> List[Dict[str, Any]]:
    """Lista todos los escenarios disponibles"""
    try:
        loader = get_loader()
        escenarios = loader.listar_escenarios()
        return escenarios
    except Exception as e:
        logger.error(f"Error listando escenarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/operaciones")
@cache_endpoint(timeout=300, key_prefix="operaciones")
def obtener_operaciones(escenario_id: int):
    """Obtiene las operaciones de un escenario"""
    # La cache key incluirá automáticamente escenario_id
    try:
        # ... implementación
    except Exception as e:
        logger.error(f"Error obteniendo operaciones: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Paso 4: Invalidación de caché** (2 horas)

```python
# admin_panel/core/signals.py (agregar al final)

from django.core.cache import cache

@receiver(post_save, sender=Marca)
def invalidar_cache_marcas(sender, instance, **kwargs):
    """Invalida caché de marcas cuando se modifica una."""
    cache.delete_pattern("api:marcas:*")
    logger.info(f"Cache de marcas invalidada por cambio en {instance}")

@receiver(post_save, sender=Escenario)
def invalidar_cache_escenarios(sender, instance, **kwargs):
    """Invalida caché de escenarios cuando se modifica uno."""
    cache.delete_pattern("api:escenarios:*")
    cache.delete_pattern("api:operaciones:*")  # Las operaciones dependen del escenario
    logger.info(f"Cache de escenarios invalidada por cambio en {instance}")
```

#### Testing

```python
# tests/test_cache.py (NUEVO)
import pytest
from fastapi.testclient import TestClient
from api.main import app
from django.core.cache import cache

@pytest.fixture(autouse=True)
def clear_cache():
    """Limpiar cache antes de cada test."""
    cache.clear()
    yield
    cache.clear()

def test_marcas_endpoint_usa_cache():
    """Verifica que el endpoint de marcas usa caché."""
    client = TestClient(app)

    # Primera llamada - debería ir a BD
    response1 = client.get("/api/marcas")
    assert response1.status_code == 200
    marcas1 = response1.json()

    # Segunda llamada - debería venir de caché
    response2 = client.get("/api/marcas")
    assert response2.status_code == 200
    marcas2 = response2.json()

    # Resultados deben ser idénticos
    assert marcas1 == marcas2

def test_cache_expira_correctamente():
    """Verifica que el caché expira después del timeout."""
    # Implementar test con mock de tiempo
    pass
```

#### Criterios de Aceptación
- [ ] Caché configurado y funcionando
- [ ] 3+ endpoints cacheados
- [ ] Logs muestran HIT/MISS de caché
- [ ] Invalidación automática al modificar datos
- [ ] Tests de caché pasando
- [ ] Reducción >70% en latencia de endpoints cacheados

---

### 📌 Tarea 2.4: Auditar y Documentar Bloques `pass`

**ID:** QUALITY-004
**Prioridad:** 🟢 BAJA
**Estimación:** 8 horas (1 día)
**Dependencias:** Ninguna

#### Descripción
Revisar 37 bloques `pass` encontrados y documentar o implementar según corresponda.

#### Estrategia

```python
# Categorizar cada `pass` en:
# 1. PENDIENTE: Implementación futura → Agregar TODO
# 2. INTENCIONAL: Caso válido → Documentar
# 3. OBSOLETO: Ya no necesario → Eliminar
# 4. BUG: Error silenciado → Implementar manejo correcto
```

#### Ejemplo de Corrección

```python
# ❌ ANTES (api/main.py:342)
if condición_compleja:
    pass

# ✅ OPCIÓN 1: Implementación pendiente
if condición_compleja:
    # TODO(2025-12-20): Implementar validación de datos cuando se defina
    # el esquema completo en el ticket JIRA-1234
    pass

# ✅ OPCIÓN 2: Caso válido documentado
if condición_compleja:
    # Intencionalmente vacío: este caso se maneja implícitamente
    # por el comportamiento por defecto del sistema
    pass

# ✅ OPCIÓN 3: Mejor implementación
if condición_compleja:
    logger.info("Condición compleja cumplida, usando defaults")
    # No se requiere acción adicional

# ✅ OPCIÓN 4: Eliminar si es obsoleto
# (simplemente eliminar el bloque if completo)
```

#### Criterios de Aceptación
- [ ] 100% de bloques `pass` revisados
- [ ] TODOs agregados con fecha y descripción
- [ ] Casos intencionales documentados
- [ ] Código obsoleto eliminado
- [ ] Errores silenciados manejados correctamente

---

### 📊 Resumen Sprint 2

| Tarea | Estimación | Prioridad | Complejidad |
|-------|-----------|-----------|-------------|
| QUALITY-001: Refactor models.py | 60h | 🔴 Crítica | Alta |
| QUALITY-002: Excepciones | 16h | 🟠 Alta | Media |
| QUALITY-003: Caché | 8h | 🟡 Media | Media |
| QUALITY-004: Bloques pass | 8h | 🟢 Baja | Baja |
| **TOTAL** | **92h** | - | - |

### Métricas de Éxito Sprint 2
- ✅ **0** archivos >500 líneas
- ✅ **0** `except:` genéricos
- ✅ **80%** reducción latencia endpoints cacheados
- ✅ **100%** bloques `pass` documentados

---

## 🟢 Sprint 3: Testing y Performance (Mes 2-3)

**Duración:** 6 semanas
**Esfuerzo:** 140 horas
**Prioridad:** ALTA
**Responsable:** Backend Developer + QA

### Objetivos del Sprint
- ✅ Aumentar coverage de 15% a 70%+
- ✅ Optimizar queries pesadas
- ✅ Consolidar lógica duplicada
- ✅ Implementar CI/CD para tests

---

### 📌 Tarea 3.1: Implementar Tests Unitarios Core

**ID:** TEST-001
**Prioridad:** 🔴 CRÍTICA
**Estimación:** 60 horas
**Dependencias:** Ninguna

#### Descripción
Crear suite completa de tests unitarios para módulos `/core`.

#### Estructura de Tests

```
tests/
├── __init__.py
├── conftest.py                    # Fixtures compartidos
├── unit/
│   ├── __init__.py
│   ├── test_calculator_nomina.py
│   ├── test_calculator_vehiculos.py
│   ├── test_calculator_descuentos.py
│   ├── test_calculator_lejanias.py
│   ├── test_allocator.py
│   └── test_simulator.py
├── integration/
│   ├── __init__.py
│   └── test_simulacion_completa.py
└── api/
    ├── __init__.py
    ├── test_endpoints.py
    └── test_security.py
```

#### Implementación

**Paso 1: Configurar pytest** (4 horas)

```bash
# Instalar dependencias
pip install pytest pytest-cov pytest-django pytest-mock freezegun

# requirements.txt (agregar)
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-django>=4.5.0
pytest-mock>=3.11.1
freezegun>=1.2.0
```

```python
# conftest.py (NUEVO)
"""
Fixtures compartidos para tests.
"""
import pytest
from decimal import Decimal
from admin_panel.core.models import (
    Marca, Escenario, ParametrosMacro, FactorPrestacional
)

@pytest.fixture
def marca_test():
    """Marca de prueba."""
    return Marca.objects.create(
        marca_id='TEST01',
        nombre='Marca Test',
        activa=True
    )

@pytest.fixture
def escenario_test():
    """Escenario de prueba."""
    return Escenario.objects.create(
        nombre='Test 2025',
        tipo='planeado',
        anio=2025,
        activo=True
    )

@pytest.fixture
def parametros_macro_test(escenario_test):
    """Parámetros macro de prueba."""
    return ParametrosMacro.objects.create(
        escenario=escenario_test,
        salario_minimo=Decimal('1300000'),
        subsidio_transporte=Decimal('162000'),
        incremento_salarios=Decimal('10.0'),
        ipc=Decimal('5.5'),
        incremento_combustible=Decimal('8.0')
    )

@pytest.fixture
def factor_prestacional_test(escenario_test):
    """Factor prestacional de prueba."""
    return FactorPrestacional.objects.create(
        escenario=escenario_test,
        nombre='Factor Estándar',
        cesantias=Decimal('8.33'),
        intereses_cesantias=Decimal('1.00'),
        prima=Decimal('8.33'),
        vacaciones=Decimal('4.17'),
        salud=Decimal('8.50'),
        pension=Decimal('12.00'),
        arl=Decimal('0.522'),
        caja_compensacion=Decimal('4.00'),
        icbf=Decimal('3.00'),
        sena=Decimal('2.00')
    )
```

**Paso 2: Tests de Calculadora de Nómina** (12 horas)

```python
# tests/unit/test_calculator_nomina.py (NUEVO)
"""
Tests para CalculadoraNomina.
"""
import pytest
from decimal import Decimal
from core.calculator_nomina import CalculadoraNomina
from core.calculadora_prestaciones import FactoresPrestacionales

class TestCalculadoraNomina:
    """Tests para cálculos de nómina."""

    @pytest.fixture
    def calculator(self):
        """Instancia de calculadora."""
        return CalculadoraNomina()

    @pytest.fixture
    def factores_estandar(self):
        """Factores prestacionales estándar."""
        return FactoresPrestacionales(
            cesantias=Decimal('0.0833'),
            intereses_cesantias=Decimal('0.01'),
            prima=Decimal('0.0833'),
            vacaciones=Decimal('0.0417'),
            salud=Decimal('0.085'),
            pension=Decimal('0.12'),
            arl=Decimal('0.00522'),
            caja_compensacion=Decimal('0.04'),
            icbf=Decimal('0.03'),
            sena=Decimal('0.02')
        )

    def test_calculo_salario_minimo_basico(self, calculator, factores_estandar):
        """Test cálculo con salario mínimo sin auxilios."""
        resultado = calculator.calcular_costo(
            salario_base=Decimal('1300000'),
            factores=factores_estandar,
            subsidio_transporte=Decimal('162000'),
            cantidad=1
        )

        # Salario base + subsidio
        assert resultado['salario_base'] == Decimal('1300000')
        assert resultado['subsidio_transporte'] == Decimal('162000')

        # Prestaciones sociales sobre salario base
        # Cesantías: 1300000 * 0.0833 = 108,290
        assert resultado['cesantias'] == pytest.approx(Decimal('108290'), rel=Decimal('0.01'))

        # Costo total aproximado
        # Salario base + subsidio + prestaciones (~52%)
        costo_esperado = Decimal('1300000') + Decimal('162000') + (Decimal('1300000') * Decimal('0.52'))
        assert resultado['costo_total'] == pytest.approx(costo_esperado, rel=Decimal('0.05'))

    def test_calculo_con_auxilios_no_prestacionales(self, calculator, factores_estandar):
        """Test con auxilios que NO generan prestaciones."""
        resultado = calculator.calcular_costo(
            salario_base=Decimal('2000000'),
            factores=factores_estandar,
            subsidio_transporte=Decimal('0'),  # No aplica
            auxilios_no_prestacionales=Decimal('500000'),  # Arriendo, cuota carro, etc.
            cantidad=1
        )

        # Los auxilios NO prestacionales no generan factor
        assert resultado['auxilios_no_prestacionales'] == Decimal('500000')

        # Costo = salario + prestaciones_sobre_salario + auxilios
        costo_esperado = (
            Decimal('2000000') +  # Salario base
            (Decimal('2000000') * Decimal('0.52')) +  # Prestaciones sobre salario
            Decimal('500000')  # Auxilios (sin prestaciones)
        )
        assert resultado['costo_total'] == pytest.approx(costo_esperado, rel=Decimal('0.05'))

    def test_calculo_multiple_empleados(self, calculator, factores_estandar):
        """Test con múltiples empleados del mismo perfil."""
        resultado = calculator.calcular_costo(
            salario_base=Decimal('1500000'),
            factores=factores_estandar,
            subsidio_transporte=Decimal('162000'),
            cantidad=5  # 5 empleados
        )

        # El costo total debe ser 5x el individual
        assert resultado['cantidad'] == 5
        # Costo unitario * cantidad
        costo_unitario = resultado['costo_unitario']
        assert resultado['costo_total'] == costo_unitario * 5

    def test_exoneracion_parafiscales(self, calculator):
        """Test con exoneración Ley 1607 (SENA, ICBF, Salud = 0)."""
        factores_exonerados = FactoresPrestacionales(
            cesantias=Decimal('0.0833'),
            intereses_cesantias=Decimal('0.01'),
            prima=Decimal('0.0833'),
            vacaciones=Decimal('0.0417'),
            salud=Decimal('0'),  # Exonerado
            pension=Decimal('0.12'),
            arl=Decimal('0.00522'),
            caja_compensacion=Decimal('0.04'),
            icbf=Decimal('0'),  # Exonerado
            sena=Decimal('0')   # Exonerado
        )

        resultado = calculator.calcular_costo(
            salario_base=Decimal('2000000'),
            factores=factores_exonerados,
            cantidad=1
        )

        # El factor total debe ser menor (~38% vs ~52%)
        factor_total = resultado['factor_prestacional']
        assert factor_total < Decimal('0.40')

    @pytest.mark.parametrize("salario,esperado_aproximado", [
        (Decimal('1300000'), Decimal('1976000')),  # Salario mínimo
        (Decimal('2000000'), Decimal('3040000')),  # Salario medio
        (Decimal('5000000'), Decimal('7600000')),  # Salario alto
    ])
    def test_casos_multiples_salarios(self, calculator, factores_estandar, salario, esperado_aproximado):
        """Test con diferentes niveles salariales."""
        resultado = calculator.calcular_costo(
            salario_base=salario,
            factores=factores_estandar,
            subsidio_transporte=Decimal('162000') if salario <= Decimal('2600000') else Decimal('0'),
            cantidad=1
        )

        # Verificar que el costo esté en el rango esperado (±10%)
        assert resultado['costo_total'] == pytest.approx(esperado_aproximado, rel=Decimal('0.10'))
```

**Paso 3: Tests de Calculadora de Vehículos** (10 horas)

```python
# tests/unit/test_calculator_vehiculos.py
"""
Tests para CalculadoraVehiculos.
"""
import pytest
from decimal import Decimal
from core.calculator_vehiculos import CalculadoraVehiculos

class TestCalculadoraVehiculos:
    @pytest.fixture
    def calculator(self):
        return CalculadoraVehiculos()

    def test_costo_vehiculo_propio(self, calculator):
        """Test cálculo para vehículo propio."""
        # ... implementar

    def test_costo_vehiculo_renting(self, calculator):
        """Test cálculo para vehículo en renting."""
        # ... implementar

    def test_costo_vehiculo_tercero(self, calculator):
        """Test cálculo para vehículo de tercero."""
        # ... implementar
```

**Paso 4: Tests de Allocator** (12 horas)

```python
# tests/unit/test_allocator.py
"""
Tests para Allocator (asignación de costos compartidos).
"""
import pytest
from core.allocator import Allocator

class TestAllocator:
    def test_asignacion_proporcional_ventas(self):
        """Test de prorrateo proporcional por ventas."""
        # ... implementar

    def test_asignacion_equitativa(self):
        """Test de prorrateo equitativo."""
        # ... implementar

    def test_asignacion_directa(self):
        """Test de asignación directa a marca."""
        # ... implementar
```

**Paso 5: Tests de Integración** (16 horas)

```python
# tests/integration/test_simulacion_completa.py
"""
Tests de integración de simulación completa.
"""
import pytest
from core.simulator import Simulator

@pytest.mark.django_db
class TestSimulacionCompleta:
    def test_simulacion_una_marca(self, escenario_test, marca_test):
        """Test de simulación con una marca."""
        simulator = Simulator()
        simulator.cargar_marcas([marca_test.marca_id])
        resultado = simulator.ejecutar_simulacion()

        assert resultado is not None
        assert len(resultado.marcas) == 1
        assert resultado.consolidado['total_costos_mensuales'] > 0

    def test_simulacion_multimarca(self, escenario_test):
        """Test de simulación con múltiples marcas."""
        # Crear 3 marcas de prueba
        # Ejecutar simulación
        # Verificar costos compartidos se distribuyeron
        # ... implementar
```

**Paso 6: Configurar Coverage** (2 horas)

```ini
# .coveragerc (NUEVO)
[run]
source = core, api, admin_panel/core
omit =
    */tests/*
    */migrations/*
    */admin.py
    */conftest.py
    */__pycache__/*

[report]
precision = 2
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
```

```bash
# Ejecutar tests con coverage
pytest --cov=core --cov=api --cov-report=html --cov-report=term

# Ver reporte
open htmlcov/index.html
```

**Paso 7: CI/CD con GitHub Actions** (4 horas)

```yaml
# .github/workflows/tests.yml (NUEVO)
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: dxv_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-django

    - name: Run migrations
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/dxv_test
      run: |
        cd admin_panel
        python manage.py migrate

    - name: Run tests with coverage
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/dxv_test
      run: |
        pytest --cov=core --cov=api --cov-report=xml --cov-report=term

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true

    - name: Check coverage threshold
      run: |
        coverage report --fail-under=70
```

#### Criterios de Aceptación
- [ ] Coverage >70% en `/core`
- [ ] Coverage >60% en `/api`
- [ ] Tests pasan en CI/CD
- [ ] Reporte de coverage generado
- [ ] Badge de coverage en README

---

### 📌 Tarea 3.2: Optimizar Queries Pesadas

**ID:** PERF-001
**Prioridad:** 🟠 ALTA
**Estimación:** 24 horas
**Dependencias:** Ninguna

#### Descripción
Optimizar carga de personal en `pyg_service.py` para reducir consumo de memoria 50%+.

#### Problema Actual

```python
# api/pyg_service.py:530-545 (ANTES)
# ❌ Carga TODOS los registros en memoria
todo_personal_comercial = list(PersonalComercial.objects.filter(
    escenario=escenario
).distinct().prefetch_related('asignaciones_marca'))  # Podría ser 500+ registros
```

#### Solución

**Opción 1: Filtrar por marcas seleccionadas** (12 horas)

```python
# api/pyg_service.py (DESPUÉS - Opción 1)
def calcular_pyg_todos_municipios_optimizado(escenario, zona):
    """
    Versión optimizada que solo carga datos necesarios.
    """
    # Obtener solo las marcas relevantes para esta zona
    marcas_zona = zona.asignaciones_marca.values_list('marca_id', flat=True)

    # Cargar solo el personal asignado a estas marcas
    personal_comercial = PersonalComercial.objects.filter(
        escenario=escenario,
        asignaciones_marca__marca__in=marcas_zona
    ).distinct().prefetch_related(
        'asignaciones_marca__marca',
        'asignaciones_marca__zona'
    )

    # Similar para otros tipos de personal
    personal_logistico = PersonalLogistico.objects.filter(
        escenario=escenario,
        asignaciones_marca__marca__in=marcas_zona
    ).distinct().prefetch_related('asignaciones_marca__marca')

    # ... resto del procesamiento
```

**Opción 2: Usar iteradores para grandes datasets** (12 horas)

```python
# api/pyg_service.py (DESPUÉS - Opción 2)
def calcular_pyg_con_iteradores(escenario, zona):
    """
    Versión con iteradores para escenarios muy grandes.
    """
    # No cargar todo en memoria de golpe
    personal_queryset = PersonalComercial.objects.filter(
        escenario=escenario
    ).select_related('factor_prestacional').iterator(chunk_size=100)

    costos_por_marca = defaultdict(Decimal)

    for persona in personal_queryset:
        # Procesar uno a uno
        costo = calcular_costo_persona(persona)

        # Distribuir a marcas asignadas
        for asignacion in persona.asignaciones_marca.all():
            costos_por_marca[asignacion.marca_id] += costo * asignacion.porcentaje / 100

    return costos_por_marca
```

#### Testing de Performance

```python
# tests/performance/test_query_optimization.py (NUEVO)
"""
Tests de performance para optimizaciones.
"""
import pytest
from django.test import override_settings
from django.db import connection
from django.test.utils import CaptureQueriesContext

@pytest.mark.django_db
class TestQueryOptimization:
    def test_carga_personal_solo_marcas_necesarias(self, escenario_test, zona_test):
        """Verifica que solo se carguen datos necesarios."""
        with CaptureQueriesContext(connection) as context:
            resultado = calcular_pyg_todos_municipios_optimizado(escenario_test, zona_test)

        # Verificar número de queries (debe ser bajo)
        num_queries = len(context.captured_queries)
        assert num_queries < 20, f"Demasiadas queries: {num_queries}"

        # Verificar que no hay N+1 queries
        # (cada tipo de personal debe ser 1 query, no N queries)
        personal_queries = [q for q in context.captured_queries if 'personal' in q['sql'].lower()]
        assert len(personal_queries) <= 3  # comercial, logístico, administrativo

    def test_memoria_no_excede_limite(self, escenario_grande):
        """Verifica que el consumo de memoria sea razonable."""
        import tracemalloc

        tracemalloc.start()
        resultado = calcular_pyg_con_iteradores(escenario_grande, zona_test)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Peak memory no debe exceder 50MB
        assert peak < 50 * 1024 * 1024, f"Memoria pico: {peak / 1024 / 1024:.2f} MB"
```

#### Criterios de Aceptación
- [ ] Reducción 50%+ en memoria usada
- [ ] Reducción 30%+ en tiempo de respuesta
- [ ] N+1 queries eliminadas
- [ ] Tests de performance pasando
- [ ] Funcionalidad existente intacta

---

### 📌 Tarea 3.3: Consolidar Lógica Duplicada

**ID:** ARCH-001
**Prioridad:** 🟡 MEDIA
**Estimación:** 32 horas
**Dependencias:** Ninguna

#### Descripción
Extraer lógica compartida entre `admin_panel/core/services.py` y `api/pyg_service.py`.

#### Implementación

**Paso 1: Crear módulo de servicios compartidos** (8 horas)

```python
# core/services/__init__.py (NUEVO)
"""
Servicios de negocio compartidos entre admin y API.
"""

# core/services/proyeccion_service.py (NUEVO)
"""
Servicio de proyección de escenarios.
"""
from decimal import Decimal
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class ProyeccionService:
    """
    Servicio para proyectar escenarios a años futuros.
    """

    @staticmethod
    def proyectar_escenario(
        escenario_base,
        nuevo_anio: int,
        incrementos: Dict[str, Decimal]
    ):
        """
        Proyecta un escenario al año siguiente aplicando incrementos.

        Args:
            escenario_base: Escenario a proyectar
            nuevo_anio: Año destino
            incrementos: Dict con incrementos por tipo
                {
                    'salarios': 10.5,
                    'ipc': 5.2,
                    'combustible': 8.0
                }

        Returns:
            Nuevo escenario proyectado
        """
        # Lógica centralizada de proyección
        # (movida desde admin_panel/core/services.py)
        pass


# core/services/pyg_service.py (NUEVO)
"""
Servicio de cálculo de P&G.
"""
class PyGService:
    """
    Servicio para cálculos de Pérdidas y Ganancias.
    """

    @staticmethod
    def calcular_pyg_marca(marca, escenario):
        """
        Calcula P&G para una marca en un escenario.

        Args:
            marca: Instancia de Marca
            escenario: Instancia de Escenario

        Returns:
            Dict con cálculos de P&G
        """
        # Lógica centralizada
        # (movida desde api/pyg_service.py)
        pass
```

**Paso 2: Refactorizar admin para usar servicios** (12 horas)

```python
# admin_panel/core/services.py (REFACTORIZADO)
"""
Acciones del Admin - ahora usa servicios compartidos.
"""
from core.services import ProyeccionService, PyGService

def proyectar_escenario_al_siguiente_anio(escenario_base):
    """
    Action del admin - usa servicio compartido.
    """
    # Obtener incrementos del escenario
    incrementos = {
        'salarios': escenario_base.parametros_macro.incremento_salarios,
        'ipc': escenario_base.parametros_macro.ipc,
        # ...
    }

    # Delegar a servicio compartido
    nuevo_escenario = ProyeccionService.proyectar_escenario(
        escenario_base=escenario_base,
        nuevo_anio=escenario_base.anio + 1,
        incrementos=incrementos
    )

    return nuevo_escenario
```

**Paso 3: Refactorizar API para usar servicios** (12 horas)

```python
# api/main.py (REFACTORIZADO)
"""
Endpoints - usan servicios compartidos.
"""
from core.services import PyGService

@app.get("/api/pyg/zonas")
def obtener_pyg_zonas(escenario_id: int, marca_id: str):
    """
    Endpoint - usa servicio compartido.
    """
    escenario = Escenario.objects.get(pk=escenario_id)
    marca = Marca.objects.get(marca_id=marca_id)

    # Delegar a servicio compartido
    pyg_data = PyGService.calcular_pyg_marca(
        marca=marca,
        escenario=escenario
    )

    return pyg_data
```

#### Criterios de Aceptación
- [ ] Lógica duplicada eliminada
- [ ] Servicios compartidos en `/core/services`
- [ ] Admin y API usan misma lógica
- [ ] Tests cubren servicios compartidos
- [ ] No regresiones en funcionalidad

---

### 📊 Resumen Sprint 3

| Tarea | Estimación | Prioridad | Coverage Esperado |
|-------|-----------|-----------|-------------------|
| TEST-001: Tests Unitarios | 60h | 🔴 Crítica | +55% |
| PERF-001: Optimizar Queries | 24h | 🟠 Alta | - |
| ARCH-001: Consolidar Lógica | 32h | 🟡 Media | - |
| **TOTAL** | **116h** | - | **70%+** |

### Métricas de Éxito Sprint 3
- ✅ **Coverage 70%+** en core y api
- ✅ **50%** reducción en memoria
- ✅ **30%** reducción en latencia
- ✅ **CI/CD** ejecutando tests automáticamente

---

## 🔵 Sprint 4: Mejora Continua (Mes 4+)

**Duración:** Continuo
**Esfuerzo:** 40+ horas
**Prioridad:** MEDIA-BAJA
**Responsable:** Equipo completo

### Objetivos del Sprint
- ✅ Documentación completa
- ✅ Monitoreo y observabilidad
- ✅ Actualización de dependencias
- ✅ Mejoras incrementales

---

### 📌 Tarea 4.1: Documentación Completa

**ID:** DOCS-001
**Estimación:** 16 horas

#### Entregables

```markdown
docs/
├── README.md                    # Actualizado
├── ARCHITECTURE.md              # Arquitectura del sistema
├── API_REFERENCE.md             # Referencia completa de API
├── DEPLOYMENT_GUIDE.md          # Guía de despliegue
├── DEVELOPMENT_SETUP.md         # Setup para desarrollo
├── SECURITY_CHECKLIST.md        # Ya creado en Sprint 1
├── TESTING_GUIDE.md             # Guía de testing
└── CONTRIBUTING.md              # Guía para contribuir
```

---

### 📌 Tarea 4.2: Implementar Monitoreo

**ID:** OPS-001
**Estimación:** 16 horas

#### Herramientas

- **Logging:** Structured logging con Python `logging`
- **Métricas:** Prometheus + Grafana
- **Errores:** Sentry (opcional)
- **Performance:** Django Debug Toolbar (dev)

#### Implementación Básica

```python
# api/middleware.py (NUEVO)
"""
Middleware para métricas y logging.
"""
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time

        logger.info(
            "request_completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2)
            }
        )

        return response

# Agregar a app
app.add_middleware(MetricsMiddleware)
```

---

### 📌 Tarea 4.3: Actualizar Dependencias

**ID:** MAINT-001
**Estimación:** 4 horas

```bash
# Frontend
cd frontend
npm outdated
npm update
npm audit fix

# Backend
pip list --outdated
pip install --upgrade django fastapi

# Verificar que todo sigue funcionando
pytest
npm run build
```

---

### 📌 Tarea 4.4: Establecer Proceso de Mejora Continua

**ID:** PROCESS-001
**Estimación:** 4 horas

#### Checklist Mensual

- [ ] Ejecutar `npm audit` y `pip-audit`
- [ ] Revisar métricas de performance
- [ ] Actualizar dependencias no críticas
- [ ] Revisar coverage de tests (mantener >70%)
- [ ] Revisar logs de errores en producción
- [ ] Actualizar documentación según cambios

---

## 📊 Métricas de Éxito

### Métricas Cuantitativas

| Métrica | Baseline | Objetivo | Método de Medición |
|---------|----------|----------|-------------------|
| **Seguridad** | 4/10 | 9/10 | Auditoría manual + tests |
| **Vulnerabilidades Críticas** | 3 | 0 | Scan automático |
| **Test Coverage** | 15% | 70%+ | `pytest --cov` |
| **Archivos >500 LOC** | 2 | 0 | Script custom |
| **Latencia API (marcas)** | ~200ms | <40ms | Benchmark |
| **Memoria por Request** | ~80MB | <40MB | Profiling |
| **Bugs en Producción** | ? | -50% | Issue tracker |

### Métricas Cualitativas

- ✅ Código más mantenible (feedback del equipo)
- ✅ Onboarding más rápido para nuevos devs
- ✅ Menos conflictos en Git
- ✅ Deploy más confiable
- ✅ Debugging más fácil

---

## 🎯 Gestión de Riesgos

### Riesgos Técnicos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| **Romper funcionalidad en refactor** | Alta | Crítico | Tests exhaustivos + feature flags + rollback plan |
| **Migraciones de BD fallan** | Media | Alto | Backup antes de migrar + testing en staging |
| **Performance empeora** | Baja | Alto | Benchmarks antes/después + profiling |
| **Merge conflicts** | Alta | Medio | Ramas pequeñas + merges frecuentes |
| **Tests toman mucho tiempo** | Media | Bajo | Paralelizar + tests selectivos en dev |

### Riesgos de Proyecto

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| **Falta de tiempo** | Alta | Alto | Priorizar sprints 1-2 (seguridad crítica) |
| **Cambios de scope** | Media | Medio | Stick to plan + documentar cambios |
| **Falta de buy-in** | Baja | Alto | Presentar ROI + quick wins tempranos |

---

## 📅 Cronograma Visual

```
Mes 1                    Mes 2                    Mes 3                    Mes 4+
┌─────────────────────┬─────────────────────┬─────────────────────┬─────────────┐
│  SPRINT 1           │  SPRINT 2           │  SPRINT 3           │  SPRINT 4   │
│  (Sem 1-2)          │  (Sem 3-6)          │  (Sem 7-12)         │  (Continuo) │
├─────────────────────┼─────────────────────┼─────────────────────┼─────────────┤
│                     │                     │                     │             │
│ 🔴 CORS Fix         │ 🔴 Refactor Models  │ 🔴 Tests Core       │ 📚 Docs     │
│ 🔴 SECRET_KEY       │ 🟠 Excepciones      │ 🟠 Optimize Queries │ 📊 Metrics  │
│ 🔴 DEBUG Default    │ 🟡 Caché            │ 🟡 Consolidar       │ 🔄 Updates  │
│ 🟢 Checklist        │ 🟢 Pass Blocks      │                     │             │
│                     │                     │                     │             │
│ [████████████]      │ [████████████████]  │ [██████████████████]│ [██████]    │
│ 5.5h / 2 weeks      │ 92h / 4 weeks       │ 116h / 6 weeks      │ 40h+        │
│                     │                     │                     │             │
└─────────────────────┴─────────────────────┴─────────────────────┴─────────────┘

Leyenda:
🔴 Crítico  🟠 Alto  🟡 Medio  🟢 Bajo
[████] Progreso estimado
```

---

## 🚀 Próximos Pasos

### Inicio Inmediato (Esta Semana)

1. **Revisar y aprobar este plan** con el equipo
2. **Crear rama Git**: `git checkout -b sprint-1/security-fixes`
3. **Comenzar con SEC-001** (CORS Fix)
4. **Setup CI/CD pipeline** básico

### Semana 1

- [ ] Completar Sprint 1 (todas las tareas de seguridad)
- [ ] Deploy a staging para validación
- [ ] Presentar resultados al equipo

### Mes 1

- [ ] Sprint 1 completado al 100%
- [ ] Sprint 2 iniciado (refactoring)
- [ ] Primera métrica: 0 vulnerabilidades críticas

---

## 📞 Contacto y Soporte

**Responsable del Plan:** [Nombre del Tech Lead]
**Fecha de Última Actualización:** 2025-12-19
**Versión:** 1.0

**Canales de Comunicación:**
- Daily Standups: Lunes-Viernes 9:00 AM
- Sprint Reviews: Último viernes del sprint
- Slack: #dxv-mejoras-codigo
- Jira Board: [URL]

---

## 📎 Anexos

### A. Scripts Útiles

```bash
# scripts/check_file_sizes.sh
#!/bin/bash
# Encontrar archivos >500 líneas
find . -name "*.py" -exec wc -l {} \; | awk '$1 > 500 {print $0}' | sort -rn

# scripts/run_security_scan.sh
#!/bin/bash
# Scan de seguridad
pip-audit
bandit -r . -f json -o security-report.json

# scripts/check_coverage.sh
#!/bin/bash
# Verificar coverage mínimo
pytest --cov=core --cov=api --cov-report=term --cov-fail-under=70
```

### B. Plantillas

**Template de Pull Request:**

```markdown
## Descripción
[Descripción del cambio]

## Tipo de Cambio
- [ ] 🔴 Seguridad crítica
- [ ] 🐛 Bug fix
- [ ] ✨ Nueva feature
- [ ] ♻️ Refactoring
- [ ] 📝 Documentación

## Checklist
- [ ] Tests agregados/actualizados
- [ ] Coverage >70% en código nuevo
- [ ] Documentación actualizada
- [ ] No rompe funcionalidad existente
- [ ] Revisión de seguridad (si aplica)

## Testing
[Cómo se probó esto]

## Screenshots
[Si aplica]
```

---

**Fin del Plan de Acción v1.0**

*Este plan es un documento vivo. Se recomienda revisarlo y actualizarlo al final de cada sprint.*
