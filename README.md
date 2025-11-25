# Sistema de Simulación de Distribución Multimarcas

> **Modelo de Distribución y Ventas (DxV)** - Sistema para simular, planificar y optimizar la operación de un agente distribuidor multimarcas.

---

## 📋 Tabla de Contenidos

1. [Descripción General](#-descripción-general)
2. [Arquitectura del Sistema](#-arquitectura-del-sistema)
3. [Sistema de Escenarios y Proyecciones](#-sistema-de-escenarios-y-proyecciones)
4. [Las Tres Ramas del Negocio](#-las-tres-ramas-del-negocio)
5. [Guía de Uso](#-guía-de-uso)
6. [Estructura del Proyecto](#-estructura-del-proyecto)

---

## 🎯 Descripción General

Este sistema permite **simular y optimizar** la operación de un **agente distribuidor multimarcas**, con capacidad para:

- ✅ **Gestión Multimarcas:** Administrar múltiples marcas con recursos propios y compartidos.
- ✅ **Escenarios Presupuestarios:** Crear y comparar escenarios (ej. "Plan 2025", "Real 2025", "Plan 2026").
- ✅ **Proyecciones Automáticas:** Proyectar presupuestos a años futuros aplicando índices macroeconómicos (IPC, Salario Mínimo) configurables por rubro.
- ✅ **Cálculos Precisos:** Costos de nómina, vehículos, infraestructura y márgenes netos.
- ✅ **Asignación Flexible:** Definir si un recurso (personal o gasto) es exclusivo de una marca o compartido.

---

## 🏗️ Arquitectura del Sistema

El sistema utiliza una arquitectura moderna y escalable:

```
📦 Sistema de Distribución Multimarcas
├── 1. BASE DE DATOS (PostgreSQL)
│   └── Fuente única de verdad. Almacena marcas, recursos, escenarios y parámetros.
├── 2. BACKEND (Django + FastAPI)
│   ├── Admin Panel (Django): Gestión de datos, creación de escenarios y proyecciones.
│   └── API (FastAPI): Motor de simulación y endpoints para el frontend.
├── 3. FRONTEND (Next.js)
│   └── Dashboard interactivo para visualizar y comparar resultados por escenario.
└── 4. CORE (Python)
    └── Motor de cálculo financiero y logístico.
```

---

## 🚀 Sistema de Escenarios y Proyecciones

El núcleo de la planificación financiera del sistema se basa en **Escenarios**.

### 1. Tipos de Escenarios
- **Planeado:** Presupuesto oficial aprobado para un año.
- **Sugerido por Marca:** Propuesta de presupuesto enviada por las marcas.
- **Real:** Ejecución real (para comparar vs Planeado).

### 2. Índices de Incremento
Para facilitar la proyección a años futuros, cada rubro (Salarios, Arriendos, Combustible) tiene asociado un **Índice de Incremento**:
- **IPC:** Índice de Precios al Consumidor.
- **SMLV:** Salario Mínimo Legal Vigente.
- **Personalizado:** Índices definidos por el usuario (ej. "Incremento Combustible").

### 3. Proyección Automática
Desde el Panel Administrativo, puedes tomar un escenario base (ej. "Plan 2025") y **proyectarlo** al siguiente año. El sistema:
1. Clona la estructura completa (personal, vehículos, gastos).
2. Aplica los porcentajes de incremento definidos en los Parámetros Macro a cada rubro según su tipo.
3. Genera un nuevo escenario (ej. "Plan 2026") listo para ser ajustado.

---

## 🌳 Las Tres Ramas del Negocio

El modelo estructura los costos en tres grandes áreas:

### 1️⃣ RAMA COMERCIAL
- **Personal:** Vendedores, supervisores, asesores.
- **Costos:** Salarios, prestaciones, auxilios de rodamiento.

### 2️⃣ RAMA LOGÍSTICA
- **Personal:** Conductores, auxiliares de bodega y reparto.
- **Vehículos:** Flota propia, renting o terceros.
- **Operación:** Costos variables por caja/kilo.

### 3️⃣ RAMA ADMINISTRATIVA
- **Personal:** Gerencia, analistas, auxiliares.
- **Gastos:** Arriendos, servicios, seguros, tecnología.
- **Asignación:** Estos costos suelen ser compartidos y prorrateados entre las marcas.

---

## 🛠️ Instalación y Despliegue

Para instrucciones detalladas sobre cómo instalar el proyecto localmente (Docker) o desplegarlo en producción (Easypanel), consulta la:

👉 **[Guía de Despliegue Completa (GUIA_DESPLIEGUE.md)](GUIA_DESPLIEGUE.md)**

---

## 📚 Guía de Uso

### Paso 1: Configuración (Admin Panel)
Accede a `/admin` para:
1. **Crear Marcas:** Definir las marcas que distribuyes.
2. **Definir Parámetros Macro:** Establecer IPC, SMLV y otros indicadores para el año.
3. **Cargar Recursos:** Ingresar personal, vehículos y gastos, asignándolos a un **Escenario** y definiendo su **Índice de Incremento**.

### Paso 2: Proyección (Opcional)
Si deseas crear el presupuesto del próximo año:
1. Ve a la sección **Escenarios** en el Admin.
2. Selecciona el escenario base.
3. Ejecuta la acción **"Proyectar escenario al año siguiente"**.

### Paso 3: Simulación (Dashboard)
Accede al Frontend (`/`) para:
1. **Seleccionar Escenario:** Elige qué versión del presupuesto quieres ver (ej. "Plan 2025").
2. **Seleccionar Marcas:** Filtra por una o varias marcas.
3. **Analizar Resultados:** Revisa el P&G proyectado, márgenes y costos detallados.

---

## 📂 Estructura del Proyecto

- `admin_panel/`: Backend Django (Modelos, Admin, Migraciones).
- `api/`: API FastAPI (Endpoints de simulación).
- `core/`: Lógica de negocio y calculadoras.
- `frontend/`: Interfaz de usuario Next.js.
- `models/`: Definiciones de clases base.
- `utils/`: Cargadores de datos y utilidades.
