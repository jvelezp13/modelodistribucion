# Arquitectura Técnica - Sistema de Distribución Multimarcas

Este documento describe la arquitectura técnica detallada del sistema, enfocada en la gestión de escenarios presupuestarios y simulación financiera.

---

## 🏗️ Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INTERFACES DE USUARIO                         │
│                                                                     │
│  ┌──────────────┐      ┌──────────────┐                             │
│  │  Next.js     │      │ Django Admin │                             │
│  │  (Dashboard) │      │ (Backoffice) │                             │
│  └──────┬───────┘      └──────┬───────┘                             │
│         │                     │                                     │
└─────────┼─────────────────────┼─────────────────────────────────────┘
          │                     │
          ↓ (HTTP/JSON)         ↓ (ORM)
┌─────────────────────────────────────────────────────────────────────┐
│                   CAPA DE PROCESAMIENTO Y API                        │
│                                                                     │
│  ┌──────────────┐      ┌──────────────┐      ┌─────────────────┐    │
│  │   FastAPI    │      │  Simulator   │      │   Django ORM    │    │
│  │    (API)     │◄────►│    (Core)    │◄────►│    (Models)     │    │
│  └──────────────┘      └──────┬───────┘      └─────────────────┘    │
│                               │                                     │
│                        ┌──────┴──────────┐                          │
│                        │ EscenarioService│                          │
│                        │ (Proyecciones)  │                          │
│                        └─────────────────┘                          │
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

**Responsabilidad:** Almacenar la configuración financiera, logística y comercial, versionada por escenarios.

**Modelos Principales:**
- **`Escenario`**: Define el contexto de la simulación (Nombre, Año, Tipo, Estado).
- **`Marca`**: Configuración base de cada marca.
- **`ParametrosMacro`**: Índices económicos (IPC, SMLV) por año.
- **Rubros (con FK a Escenario):**
    - `PersonalComercial`, `PersonalLogistico`, `PersonalAdministrativo`
    - `Vehiculo`
    - `GastoComercial`, `GastoLogistico`, `GastoAdministrativo`
    - `ProyeccionVentas`

---

### 2. CAPA DE GESTIÓN (Django Admin)

**Ubicación:** `admin_panel/`

**Responsabilidad:** Backoffice para la gestión de datos y ejecución de procesos de negocio.

**Funcionalidades Clave:**
- **Gestión de Escenarios:** Creación, edición y activación de escenarios.
- **Proyección Automática:** Acción administrativa que utiliza `EscenarioService` para clonar un escenario y proyectar sus valores al año siguiente usando los índices configurados.
- **Configuración de Índices:** Asignación de índices de incremento (IPC, SMLV, etc.) a cada rubro.

---

### 3. CAPA DE PROCESAMIENTO (Core Python)

**Ubicación:** `core/` y `admin_panel/core/services.py`

**Responsabilidad:** Lógica de negocio, cálculos financieros y proyecciones.

**Componentes:**
- **`Simulator`**: Motor principal que orquesta la carga de datos y ejecución de cálculos.
- **`EscenarioService`**: Servicio de dominio encargado de la lógica de clonación de escenarios y aplicación de fórmulas de incremento financiero.
- **`Calculators`**: Módulos especializados para nómina, prestaciones y costos vehiculares.

---

### 4. CAPA DE API (FastAPI)

**Ubicación:** `api/`

**Responsabilidad:** Exponer datos y simulaciones al Frontend.

**Endpoints Principales:**
- `GET /api/escenarios`: Lista los escenarios disponibles para simular.
- `POST /api/simulate?escenario_id={id}`: Ejecuta la simulación utilizando los datos asociados al escenario especificado.
- `GET /api/marcas`: Lista las marcas activas.

---

### 5. FRONTEND (Next.js)

**Ubicación:** `frontend/`

**Responsabilidad:** Visualización interactiva de resultados.

**Características:**
- **Selector de Escenarios:** Permite al usuario cambiar el contexto de la simulación en tiempo real.
- **Dashboard Financiero:** Muestra P&G, márgenes y costos detallados.
- **Filtros:** Selección múltiple de marcas para vistas consolidadas o individuales.
