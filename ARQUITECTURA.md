# Arquitectura Técnica - Sistema de Distribución Multimarcas

Este documento describe la arquitectura técnica detallada del sistema en su versión híbrida moderna.

---

## 🏗️ Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INTERFACES DE USUARIO                         │
│                                                                     │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐       │
│  │  Next.js     │      │  Streamlit   │      │ Django Admin │       │
│  │  (Frontend)  │      │  (Legacy)    │      │  (Backoffice)│       │
│  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘       │
│         │                     │                     │               │
└─────────┼─────────────────────┼─────────────────────┼───────────────┘
          │                     │                     │
          ↓ (HTTP/JSON)         ↓ (Python Import)     ↓ (ORM)
┌─────────────────────────────────────────────────────────────────────┐
│                   CAPA DE PROCESAMIENTO Y API                        │
│                                                                     │
│  ┌──────────────┐      ┌──────────────┐      ┌─────────────────┐    │
│  │   FastAPI    │      │  Simulator   │      │   Django ORM    │    │
│  │    (API)     │◄────►│    (Core)    │◄────►│    (Models)     │    │
│  └──────────────┘      └──────────────┘      └─────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                                      │
                                                      ↓ (SQL)
┌─────────────────────────────────────────────────────────────────────┐
│                       CAPA DE DATOS (PERSISTENCIA)                   │
│                                                                     │
│                      ┌──────────────────────┐                       │
│                      │      PostgreSQL      │                       │
│                      │   (Fuente de Verdad) │                       │
│                      └──────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Detalle de Componentes

### 1. CAPA DE DATOS (PostgreSQL)

**Responsabilidad:** Almacenar toda la información del sistema de forma estructurada y relacional.

**Modelos Principales:**
- `Marca`: Configuración base de cada marca.
- `PersonalComercial`: Vendedores, supervisores.
- `Vehiculo`: Flota de transporte.
- `ProyeccionVentas`: Datos mensuales de ventas.
- `ParametrosMacro`: IPC, aumentos salariales.

---

### 2. CAPA DE GESTIÓN (Django Admin)

**Ubicación:** `admin_panel/`

**Responsabilidad:** Proveer una interfaz administrativa robusta para gestionar los datos maestros.

**Características:**
- Gestión de usuarios y permisos.
- CRUD completo para todos los modelos.
- Importación/Exportación de datos (YAML support para seed data).
- Ejecución de migraciones de base de datos.

---

### 3. CAPA DE PROCESAMIENTO (Core Python)

**Ubicación:** `core/`

**Responsabilidad:** Lógica de negocio pura, agnóstica del framework web.

**Componentes:**
- **`Simulator`**: Orquestador de la simulación.
- **`Allocator`**: Lógica de prorrateo de gastos compartidos.
- **`Calculators`**: Motores de cálculo de nómina y costos vehiculares.

**Integración:**
Este núcleo es importado tanto por la API (FastAPI) como por el Dashboard Legacy (Streamlit) para garantizar consistencia en los cálculos.

---

### 4. CAPA DE API (FastAPI)

**Ubicación:** `api/`

**Responsabilidad:** Exponer la lógica del Core como servicios RESTful para el Frontend moderno.

**Endpoints:**
- `/simulate/{marca_id}`: Ejecuta simulación para una marca.
- `/marcas/`: Lista marcas disponibles.
- `/results/`: Entrega resultados en formato JSON.

---

### 5. CAPA DE VISUALIZACIÓN

#### A. Frontend Moderno (Next.js)
**Ubicación:** `frontend/`
- Interfaz reactiva y rápida.
- Gráficos interactivos con Recharts/Chart.js.
- Consumo de datos vía API.

#### B. Dashboard Legacy (Streamlit)
**Ubicación:** `panels/`
- Herramienta de prototipado rápido.
- Conexión directa a DB (vía `utils/loaders_db.py`).
- Útil para validación rápida de cambios en el Core.

---

## 🔄 Flujo de Datos

### 1. Configuración y Carga
1. El usuario administrador ingresa al **Django Admin**.
2. Crea o modifica marcas, asigna personal y vehículos.
3. Los datos se guardan en **PostgreSQL**.

### 2. Simulación
1. El usuario final accede al **Frontend (Next.js)**.
2. Selecciona una marca y solicita simulación.
3. El frontend llama a la **API (FastAPI)**.
4. La API instancia el **Simulator (Core)**.
5. El Simulator carga datos desde **PostgreSQL** (vía Django ORM).
6. Se ejecutan los cálculos en memoria.
7. La API devuelve los resultados JSON al Frontend.

---

## 🛠️ Tecnologías Utilizadas

| Componente | Tecnología | Propósito |
|------------|------------|-----------|
| **Base de Datos** | PostgreSQL 15 | Persistencia robusta |
| **Backend Admin** | Django 4.x | Gestión de datos y ORM |
| **API** | FastAPI | Servicios de alto rendimiento |
| **Frontend** | Next.js 14 | Interfaz de usuario moderna |
| **Core Logic** | Python 3.9+ | Lógica de negocio compartida |
| **Legacy UI** | Streamlit | Prototipado y validación |
| **Infraestructura** | Docker Compose | Orquestación local |

---

## 🔒 Principios de Diseño

1. **Single Source of Truth**: Todos los datos viven en PostgreSQL. Los archivos YAML son solo para carga inicial/backup.
2. **Separación de Lógica**: El directorio `core/` no depende de Django ni de Streamlit, lo que permite su reutilización.
3. **API First**: La comunicación entre Frontend y Backend es estrictamente vía API REST.

---

## 📈 Roadmap Técnico

### Fase Actual (Híbrida)
- [x] Migración de YAML a PostgreSQL
- [x] Implementación de Django Admin
- [x] Creación de API FastAPI
- [x] Inicio de Frontend Next.js

### Fase Futura
- [ ] Retiro gradual de Streamlit
- [ ] Autenticación unificada (JWT) para API y Frontend
- [ ] Sistema de escenarios "What-If" persistentes en DB
- [ ] Reportes PDF generados desde el Backend

---

**Última actualización:** Noviembre 2025

