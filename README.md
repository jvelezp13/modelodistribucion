# Sistema de Simulación de Distribución Multimarcas

> **Modelo de Distribución y Ventas (DxV)** - Sistema para simular, planificar y optimizar la operación de un agente distribuidor multimarcas.

---

## 📋 Tabla de Contenidos

1. [Descripción General](#-descripción-general)
2. [Arquitectura del Sistema](#-arquitectura-del-sistema)
3. [Las Tres Ramas del Negocio](#-las-tres-ramas-del-negocio)
4. [Modelo Multimarcas](#-modelo-multimarcas)
5. [Rubros y Relaciones](#-rubros-y-relaciones)
6. [Estructura del Proyecto](#-estructura-del-proyecto)
7. [Guía de Uso](#-guía-de-uso)
8. [Gestión de Rubros y Flexibilidad](#-gestión-de-rubros-y-flexibilidad)
9. [Roadmap](#-roadmap)

---

## 🎯 Descripción General

Este sistema permite **simular y optimizar** la operación de un **agente distribuidor multimarcas**, con capacidad para:

- ✅ Gestionar múltiples marcas simultáneamente
- ✅ Asignar recursos **individuales** por marca o **compartidos** entre marcas
- ✅ Calcular automáticamente costos de nómina, vehículos, infraestructura
- ✅ Prorratear gastos compartidos según criterios configurables (ventas, volumen, headcount, etc.)
- ✅ Simular escenarios "what-if" para evaluar viabilidad financiera
- ✅ Generar dashboards interactivos y exportar resultados

### Origen del Modelo

El modelo se basa en la experiencia de distribución con Nutresa (archivo `Simula DxV Nutresa 2025.xlsx`), pero ha sido **rediseñado desde cero** para:
- Ser más intuitivo y profesional
- Soportar múltiples marcas y razones sociales
- Facilitar la adición, modificación y simulación de recursos
- Optimizar gastos mediante recursos compartidos

---

## 🏗️ Arquitectura del Sistema

El sistema ha evolucionado a una arquitectura híbrida moderna para soportar escalabilidad y una mejor experiencia de usuario:

```
📦 Sistema de Distribución Multimarcas
├── 1. BASE DE DATOS (PostgreSQL)
│   └── Fuente única de verdad para configuraciones, marcas y simulaciones
├── 2. BACKEND (Django + FastAPI)
│   ├── Admin Panel (Django): Gestión de datos maestros y usuarios
│   └── API (FastAPI): Lógica de simulación y servicios para el frontend
├── 3. FRONTEND (Next.js)
│   └── Nueva interfaz de usuario moderna y reactiva
├── 4. LEGACY DASHBOARD (Streamlit)
│   └── Dashboard original para visualización rápida (conectado a DB)
└── 5. CORE (Python)
    └── Motor de cálculo compartido entre todos los componentes
```

### Flujo de Funcionamiento

```
Usuario (Admin) → Django Admin Panel → PostgreSQL
                                        ↑
Usuario (Simulador) → Next.js Frontend → API (FastAPI) → Motor de Simulación
                                        ↓
                                   Resultados
```

---

## 🌳 Las Tres Ramas del Negocio

El modelo está estructurado en **3 ramas principales**, cada una con sus rubros específicos:

### 1️⃣ RAMA COMERCIAL

**Objetivo:** Gestionar la fuerza de ventas y estructura comercial.

**Componentes:**

#### Personal Comercial
- **Vendedores** (varios tipos):
  - Vendedor Geográfico
  - Vendedor Consumo Local
  - Vendedor Minimercado
  - Vendedor Especializado (droguerías, snacker)
  - Vendedor Televenta
  - Desarrollador Comercial
  - Asesor Técnico
- **Supervisores Comerciales**
- **Auxiliar de Información Comercial**
- **Supernumerarios de Ventas**

#### Costos Asociados
- Salarios base
- Prestaciones sociales (salud, pensión, ARL, cesantías, prima, vacaciones)
- Subsidio de transporte
- Auxilio adicional (para minimercados, droguerías)
- Plan de datos/voz (celulares)
- Uniformes
- Gastos de viaje (lejanía)
- Subsidio lejanía supervisor
- GPS comercial
- Control horario

**Fórmula General:**
```
TOTAL COSTO VENTA = Σ (Salarios + Prestaciones + Subsidios + Auxilios + Gastos Extra)
```

---

### 2️⃣ RAMA LOGÍSTICA

**Objetivo:** Gestionar la distribución, transporte e infraestructura.

**Componentes:**

#### Vehículos
Dos esquemas posibles:

**A. Esquema Renting** (arriendo)
- Tipos de vehículos:
  - Bicicleta Eléctrica
  - Motocarro (0.5 Ton)
  - Minitruck (0.77 Ton - 6.45 m³)
  - Pick up (0.57 Ton - 7.77 m³)
  - NHR (1.37 Ton - 13.6 m³)
  - NKR (1.99 Ton - 18.8 m³)
  - NPR (3.48 Ton - 23.3 m³)
- Costos:
  - Cánon mensual (fijo)
  - Combustible (variable)
  - Lavada
  - Reposición

**B. Esquema Tradicional** (propio)
- Depreciación
- Mantenimiento
- Seguro
- Combustible
- Impuestos

#### Personal Logístico
- **Conductores**
- **Auxiliares de Entrega**
- **Operarios de Bodega**
- **Líder Logístico**
- **Supernumerarios Logística**

#### Infraestructura
- Arriendo de bodega
- Servicios públicos (bodega)
- Seguridad
- Mantenimiento
- Equipos (montacargas, estibas)

**Fórmula General:**
```
TOTAL COSTO LOGÍSTICA = Costo Vehículos + Costo Personal Logístico + Costo Infraestructura
```

---

### 3️⃣ RAMA ADMINISTRATIVA

**Objetivo:** Gestionar la administración, contabilidad y servicios generales.

**Componentes:**

#### Personal Administrativo
- **Gerente General**
- **Auxiliar Administrativo**
- **Contador** (honorarios)
- **Servicios Generales** (aseo, oficios varios)
- **Desarrollador de Talentos** (RRHH)
- **Practicante SENA**

#### Costos Asociados
- Salarios + prestaciones
- Subsidio de transporte
- Uniformes

#### Infraestructura y Servicios
- Arriendo de oficina
- Servicios públicos (oficina)
- Internet y telefonía
- Papelería
- Software/Tecnología (ERP, CRM, licencias)
- Seguridad
- Aseo

**Fórmula General:**
```
TOTAL COSTO ADMINISTRATIVO = Costo Personal Admin + Costo Infraestructura + Costo Servicios
```

---

## 🏢 Modelo Multimarcas

El sistema permite gestionar múltiples marcas con **recursos individuales y compartidos**.

### Tipos de Asignación

#### 🔴 Recursos INDIVIDUALES
Asignados 100% a una marca específica.

**Ejemplos:**
- Vendedor dedicado exclusivamente a Marca A
- Vehículo que solo distribuye productos de Marca B
- Comisiones por ventas de Marca C

**En el sistema:**
```yaml
asignacion: individual
marca: marca_a
```

---

#### 🟢 Recursos COMPARTIDOS
Utilizados por múltiples marcas, con prorrateo automático.

**Ejemplos:**
- Gerente General (trabaja para todas las marcas)
- Bodega compartida
- Contador (lleva la contabilidad de todas las marcas)

**En el sistema:**
```yaml
asignacion: compartido
criterio_prorrateo: ventas  # o 'volumen', 'headcount', 'equitativo'
```

---

### Criterios de Prorrateo

El sistema soporta **5 criterios de prorrateo** para gastos compartidos:

| Criterio | Descripción | Ejemplo de Uso |
|----------|-------------|----------------|
| **ventas** | Proporcional a las ventas de cada marca | Gerente, contador, servicios generales |
| **volumen** | Proporcional al volumen manejado (m³, pallets) | Bodega, equipos de almacenamiento |
| **headcount** | Proporcional a la cantidad de empleados | Sistemas RRHH, software de nómina |
| **uso_real** | Según uso medido real | Licencias de software por usuario |
| **equitativo** | Todas las marcas pagan por igual | Ciertos servicios fijos |

**Ejemplo de Prorrateo por Ventas:**

Si tenemos 3 marcas con las siguientes ventas mensuales:
- Marca A: $150M (50%)
- Marca B: $90M (30%)
- Marca C: $60M (20%)

Y el Gerente cuesta $8M/mes (compartido), entonces:
- Marca A asume: $8M × 50% = **$4M**
- Marca B asume: $8M × 30% = **$2.4M**
- Marca C asume: $8M × 20% = **$1.6M**

---

### Clasificación de Rubros (Compartidos vs Individuales)

#### 🟢 Típicamente COMPARTIDOS

**Rama Administrativa:**
- ✅ Gerente General
- ✅ Contador
- ✅ Auxiliar Administrativo
- ✅ Servicios Generales
- ✅ Arriendo oficina/bodega compartida
- ✅ Servicios públicos
- ✅ Software/Tecnología
- ✅ Papelería

**Rama Logística (si aplica):**
- ✅ Líder Logístico (gestiona varias marcas)
- ✅ Bodega compartida
- ✅ Operarios de bodega multimarca
- ✅ Equipos de bodega

---

#### 🔴 Típicamente INDIVIDUALES

**Rama Comercial:**
- ❌ Vendedores dedicados
- ❌ Comisiones por ventas
- ❌ Material POP de marca específica

**Rama Logística:**
- ❌ Vehículos exclusivos de una marca
- ❌ Conductores asignados a marca específica
- ❌ Combustible de vehículos dedicados

---

#### 🟡 MIXTOS (depende de la configuración)

Pueden ser compartidos O individuales según el caso:
- Vendedores (si venden varias marcas → compartido)
- Vehículos (si distribuyen varias marcas → compartido)
- Supervisores (si supervisan equipos multimarca → compartido)
- Auxiliares de bodega

---

## 📊 Rubros y Relaciones

### Catálogo Completo de Rubros

El sistema maneja **más de 150 rubros** clasificados en:

<details>
<summary><b>Rubros Comerciales (34 rubros)</b></summary>

1. Ventas mensuales
2. Vendedores geográficos
3. Vendedores Consumo Local
4. Vendedores Minimercado
5. Desarrollador Comercial
6. Asesor Técnico
7. Vendedor Especializado de droguerías
8. Vendedor Snacker
9. Vendedores Televenta
10. Vendedores totales
11. Supernumerarios Ventas
12. Total Vendedores + Supern.
13. Supervisores
14. Salario Vendedores
15. Salario Supervisores
16. Auxiliar de Información Comercial
17. Prestaciones Sociales Comerciales
18. Subsidio Transporte
19. Costo auxilio adicional (minimercados, droguerías)
20. Plan de datos/voz
21. Uniformes comerciales
22. Gastos de viaje (lejanía)
23. Subsidio lejanía supervisor
24. GPS comercial
25. Control horario comercial
26. **TOTAL COSTO VENTA**
27. ...

</details>

<details>
<summary><b>Rubros Logísticos (96 rubros)</b></summary>

**Vehículos:**
- Tipos: Bicicleta Eléctrica, Motocarro, Minitruck, Pick up, NHR, NKR, NPR
- Por cada tipo: Cantidad, Cánon, Combustible, Lavada, Reposición, Mantenimiento

**Personal Logístico:**
- Conductores (salario + prestaciones)
- Auxiliares de Entrega
- Operarios de Bodega
- Líder Logístico
- Supernumerarios Logística

**Infraestructura:**
- Arriendo bodega
- Servicios públicos bodega
- Seguridad
- **TOTAL COSTO LOGÍSTICA**
- ...

</details>

<details>
<summary><b>Rubros Administrativos (20 rubros)</b></summary>

1. Gerente General (salario)
2. Prestaciones Gerente
3. Auxiliar Administrativo (salario)
4. Prestaciones Aux. Admin
5. Contador (honorarios)
6. Servicios Generales (salario)
7. Prestaciones Servicios Generales
8. Subsidio transporte figuras admin
9. Uniformes admin
10. Arriendo oficina
11. Servicios públicos oficina
12. Internet/Telefonía
13. Papelería
14. Software/Tecnología
15. Seguridad oficina
16. Aseo
17. **TOTAL COSTO ADMINISTRATIVO**
18. ...

</details>

---

### Parámetros Macroeconómicos

El sistema utiliza **drivers** para proyectar costos:

| Parámetro | Valor 2025 | Uso |
|-----------|------------|-----|
| **IPC** | 5.2% | Incremento de costos generales |
| **IPT** | 6.5% | Incremento precios de transporte |
| **Incremento Salario Mínimo** | 9.53% | Ajuste salario mínimo legal |
| **Incremento Subsidio Transporte** | 23.46% | Ajuste subsidio |
| **Incremento Salarios (No mínimo)** | 5.2% | Salarios por encima del mínimo |

---

### Factores Prestacionales

Cálculo de prestaciones sociales:

| Concepto | Administrativos | Comerciales | Aprendiz SENA |
|----------|----------------|-------------|---------------|
| **Salud** | 0% (empresa) | 0% | 12.5% |
| **Pensión** | 12% | 12% | 0% |
| **ARL** | 0.522% | 4.35% | 0.522% |
| **Cesantías** | 9.37% | 9.37% | 0% |
| **Intereses Cesantías** | 1.12% | 1.12% | 0% |
| **Prima** | 9.37% | 9.37% | 0% |
| **Vacaciones** | 4.17% | 4.17% | 0% |
| **TOTAL** | ~37.8% | ~40.2% | ~12.5% |

**Factor Prestacional** = % sobre el salario base que se suma para calcular el costo total de nómina.

---

### Relaciones de Cálculo

#### Ejemplo: Cálculo de Costo de un Vendedor

```
Salario Base: $2,150,000
Factor Prestacional Comercial: 40.2%
Subsidio de Transporte: $200,000
Plan de Datos: $35,000

Costo Mensual:
= Salario Base × (1 + Factor Prestacional) + Subsidio + Plan Datos
= $2,150,000 × 1.402 + $200,000 + $35,000
= $3,014,300 + $200,000 + $35,000
= $3,249,300
```

#### Ejemplo: Cálculo de Costo de Vehículo en Renting

```
Vehículo: NHR (1.37 Ton)
Cánon Mensual: $2,800,000
Combustible Promedio: $1,200,000
Lavada: $80,000
Reposición: $150,000

Costo Mensual:
= Cánon + Combustible + Lavada + Reposición
= $2,800,000 + $1,200,000 + $80,000 + $150,000
= $4,230,000
```

#### Ejemplo: Margen / Fee

```
Marca A:
Ventas Mensuales: $150,000,000
Costo Total (Comercial + Logística + Admin): $18,500,000

Margen / Fee:
= (Ventas - Costo Total) / Ventas × 100
= ($150M - $18.5M) / $150M × 100
= 87.67%

Costo como % de Ventas:
= $18.5M / $150M × 100
= 12.33%
```

---

## 📁 Estructura del Proyecto

```
modelodistribucion/
│
├── README.md                          # Este archivo
├── ARQUITECTURA.md                    # Documentación técnica detallada
├── docker-compose.yml                 # 🐳 Orquestación de contenedores
│
├── admin_panel/                       # ⚙️ Backend Django (Admin)
│   ├── core/                          # Modelos y lógica de negocio
│   ├── dxv_admin/                     # Configuración del proyecto
│   └── manage.py
│
├── frontend/                          # 💻 Frontend Next.js
│   ├── src/app/                       # Páginas y componentes
│   └── public/
│
├── api/                               # 🔌 API FastAPI
│   └── main.py
│
├── panels/                            # 📊 Legacy Dashboard (Streamlit)
│   ├── app.py
│   └── ...
│
├── core/                              # 🧠 Motor de cálculo (Python puro)
│   ├── simulator.py
│   ├── allocator.py
│   └── ...
│
├── config/                            # 📝 Configuración YAML (Seed data)
│   └── ...
│
└── data/                              # 💾 Datos YAML (Seed data)
    └── ...
```

---

## 🚀 Guía de Uso

### Requisitos
- Docker y Docker Compose

### Instalación y Ejecución

La forma más sencilla de iniciar todo el sistema es usando Docker Compose:

```bash
# Clonar el repositorio
git clone https://github.com/jvelezp13/modelodistribucion.git
cd modelodistribucion

# Iniciar todos los servicios
docker-compose up --build
```

Esto levantará:
1. **Base de Datos** (PostgreSQL): `localhost:5432`
2. **Admin Panel** (Django): `http://localhost:8000/admin`
3. **Frontend** (Next.js): `http://localhost:3000`
4. **API** (FastAPI): `http://localhost:8001`
5. **Legacy Dashboard** (Streamlit): `http://localhost:8501`

### Carga Inicial de Datos

La primera vez que inicies el sistema, la base de datos estará vacía. El contenedor de Django ejecutará automáticamente las migraciones. Para cargar los datos iniciales desde los archivos YAML:

```bash
# Ejecutar comando de importación dentro del contenedor de Django
docker-compose exec django_admin python manage.py import_from_yaml
```

### Desarrollo Local (Sin Docker)

Si deseas ejecutar componentes individualmente para desarrollo, consulta `INICIO_RAPIDO.md` para instrucciones detalladas de configuración de entorno virtual y conexión a base de datos.

---

## 🔧 Gestión de Rubros y Flexibilidad

Uno de los pilares fundamentales del sistema es la **flexibilidad total** para agregar, modificar y eliminar rubros sin tocar código.

### Filosofía de Diseño: YAML + Git (Fase 1)

**¿Por qué YAML en lugar de Base de Datos al inicio?**

El sistema usa archivos YAML por estas ventajas clave:

✅ **Súper fácil de editar** - Cualquier editor de texto
✅ **Versionamiento completo** - Git rastrea todos los cambios
✅ **Sin infraestructura** - No necesitas servidor de BD
✅ **Flexible y humano** - Comentarios, visual, entendible
✅ **Perfecto para iterar** - Cambios inmediatos, sin migraciones

### ¿Cómo Agregar/Modificar/Eliminar Rubros?

#### Agregar un Nuevo Rubro

**Opción 1: Editar directamente el YAML**

```yaml
# data/marcas/mi_marca/comercial.yaml

vendedores:
  # Rubro existente
  - tipo: vendedor_geografico
    cantidad: 5
    salario_base: 2150000
    asignacion: individual

  # NUEVO RUBRO - Solo agrégalo aquí!
  - tipo: vendedor_ecommerce
    cantidad: 2
    salario_base: 2400000
    asignacion: individual
    bono_ventas_online: 300000  # Campo personalizado
```

**Opción 2: Usar el Panel de Gestión (próximamente)**

El sistema incluirá un panel web donde podrás:
- Ver todos los rubros activos
- Agregar nuevos rubros con formulario
- Modificar valores existentes
- Desactivar rubros obsoletos
- Ver historial de cambios

#### Modificar un Rubro Existente

Simplemente edita el archivo YAML:

```yaml
# Cambiar salario de vendedores
vendedores:
  - tipo: vendedor_geografico
    cantidad: 5
    salario_base: 2300000  # ← Cambié de 2150000 a 2300000
    asignacion: individual
```

Guarda, haz commit en Git, y listo.

#### Eliminar/Desactivar un Rubro

**Opción 1: Comentar (mantiene histórico)**
```yaml
vendedores:
  # - tipo: vendedor_minimercado  # ← Ya no lo usamos
  #   cantidad: 1
  #   salario_base: 2150000
```

**Opción 2: Eliminar completamente**
```yaml
vendedores:
  # Eliminado: vendedor_minimercado
  - tipo: vendedor_geografico
    cantidad: 5
```

### Catálogo Central de Rubros

El sistema mantiene un **catálogo maestro** de todos los tipos de rubros disponibles:

**`catalogos/rubros.yaml`** - Define qué rubros puedes usar

```yaml
rubros_disponibles:
  - id: vendedor_geografico
    nombre: "Vendedor Geográfico"
    categoria: comercial
    tipo: personal
    campos_requeridos:
      - cantidad
      - salario_base
    campos_opcionales:
      - comision_porcentaje
      - auxilio_adicional
    asignacion_permitida: [individual, compartido]
    activo: true

  - id: vehiculo_nhr
    nombre: "Vehículo NHR"
    categoria: logistica
    tipo: vehiculo
    esquemas: [renting, tradicional]
    activo: true
```

**Ventajas del catálogo:**
- Validación automática de datos
- Autocompletado en interfaces
- Documentación incluida
- Control de qué rubros están activos

### Sistema de Validación Flexible

El `RubroManager` valida que:
- Los rubros usados existan en el catálogo
- Los campos requeridos estén presentes
- Los valores sean del tipo correcto
- La asignación (individual/compartido) sea válida

Pero NO te limita - puedes agregar campos personalizados cuando lo necesites.

### Versionamiento y Auditoría

**Cada cambio queda registrado en Git:**

```bash
# Ver historial de cambios en una marca
git log --oneline data/marcas/marca_a/comercial.yaml

# Ver qué cambió exactamente
git diff HEAD~1 data/marcas/marca_a/comercial.yaml

# Revertir un cambio
git checkout HEAD~1 data/marcas/marca_a/comercial.yaml
```

**Ventajas:**
- Sabes quién cambió qué y cuándo
- Puedes revertir errores
- Comparas versiones fácilmente
- Auditoría completa sin BD

### Migración Futura a Base de Datos

**¿Cuándo migrar a BD?**

Cuando necesites:
- ✅ Interfaz web para usuarios no técnicos
- ✅ Más de 10 usuarios editando simultáneamente
- ✅ Guardar miles de simulaciones históricas
- ✅ Integración automática con ERP/sistemas contables
- ✅ APIs para terceros

**Estrategia de migración:**

```
Fase 1 (Hoy - 6 meses): YAML + Git
  ↓ Migración gradual
Fase 2 (6-12 meses): Híbrido (YAML + BD)
  ↓ Migración completa
Fase 3 (>12 meses): BD + API + Multi-usuario
```

**Lo mejor: La migración NO rompe nada**

El código usa una capa de abstracción (`DataLoader`) que puede leer de YAML o BD:

```python
# El mismo código funciona con YAML o BD
marca = data_loader.cargar_marca("marca_a")

# Internamente puede leer de:
# - YAML: data/marcas/marca_a/comercial.yaml
# - BD: SELECT * FROM marcas WHERE id = 'marca_a'
```

Cambias la fuente de datos sin cambiar la lógica del sistema.

### Ejemplos Prácticos de Flexibilidad

**Ejemplo 1: Agregar nuevo tipo de vendedor**

```yaml
# En 30 segundos agregas un nuevo perfil:
vendedores:
  - tipo: vendedor_farmacia
    cantidad: 3
    salario_base: 2500000
    comision_porcentaje: 0.02
    certificacion_requerida: true
    bono_certificacion: 200000
```

**Ejemplo 2: Crear rubro completamente personalizado**

```yaml
# Quieres trackear influencers digitales?
marketing_digital:
  - tipo: influencer_instagram
    cantidad: 2
    pago_mensual: 1500000
    alcance_promedio: 50000
    engagement_rate: 0.08
    asignacion: individual
```

El sistema lo procesa automáticamente.

**Ejemplo 3: Cambiar criterio de prorrateo**

```yaml
# Cambiar cómo se distribuye el gerente entre marcas
gerente_general:
  salario_base: 8000000
  criterio_prorrateo: headcount  # ← Cambié de "ventas" a "headcount"
```

Un cambio, impacto inmediato en todos los cálculos.

### Mejores Prácticas

**1. Usa nombres descriptivos**
```yaml
# ❌ Malo
- tipo: v1
  cantidad: 5

# ✅ Bueno
- tipo: vendedor_tradicional
  cantidad: 5
```

**2. Comenta tus cambios**
```yaml
# 2025-11-10: Incremento salarial por inflación
vendedores:
  - tipo: vendedor_geografico
    salario_base: 2300000  # Antes: 2150000
```

**3. Haz commits frecuentes**
```bash
git commit -m "Incrementar salarios vendedores 7% por inflación"
```

**4. Usa ramas para experimentos**
```bash
git checkout -b experimento/salarios-competitivos
# Haz cambios experimentales
# Si funciona: merge
# Si no: descarta la rama
```

### Resumen

🎯 **El sistema es flexible por diseño:**
- Agrega rubros → Edita YAML
- Modifica valores → Edita YAML
- Elimina rubros → Comenta o borra en YAML
- Todo versionado → Git automático
- Migración futura → Sin romper nada

No hay límites artificiales. Si necesitas trackear algo nuevo, simplemente agrégalo.

---

## 📈 Roadmap

### Fase 1: MVP (Actual)
- [x] Análisis del modelo de referencia (Nutresa)
- [x] Diseño de arquitectura multimarcas
- [x] Documentación comprehensiva (README)
- [ ] Crear estructura de carpetas y archivos base
- [ ] Implementar modelos de cálculo básicos
- [ ] Dashboard simple con Streamlit

### Fase 2: Core Features
- [ ] Motor de simulación completo
- [ ] Asignador de gastos compartidos
- [ ] Calculadoras de nómina y vehículos
- [ ] Panel por marca individual
- [ ] Panel comparativo entre marcas
- [ ] Exportación a Excel

### Fase 3: Optimización
- [ ] Simulador de escenarios "what-if"
- [ ] Optimizador de recursos (sugerir asignaciones óptimas)
- [ ] Validación de datos robusta
- [ ] Exportación a PDF con reportes
- [ ] Tests automatizados

### Fase 4: Avanzado
- [ ] Base de datos (PostgreSQL)
- [ ] API REST
- [ ] Autenticación y múltiples usuarios
- [ ] Versionamiento de simulaciones
- [ ] Integración con sistemas contables
- [ ] Machine Learning para proyecciones

---

## 👥 Contribución

Este proyecto está en desarrollo activo. Si deseas contribuir:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto es privado y de uso interno.

---

## 📞 Contacto

**Desarrollado por:** Julian Velez
**Email:** jvelez.nexo@gmail.com
**Proyecto:** Nexo Distribuciones S.A.S

---

## 🙏 Agradecimientos

- Modelo de referencia basado en la experiencia de distribución con Nutresa
- Inspirado en las mejores prácticas de distribución en Colombia

---

**Última actualización:** 2025-11-10
