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
8. [Roadmap](#-roadmap)

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

El sistema está organizado en **7 capas**:

```
📦 Sistema de Distribución Multimarcas
├── 1. CONFIGURACIÓN
│   └── Parámetros macro, factores prestacionales, catálogos base
├── 2. CATÁLOGOS
│   └── Figuras comerciales, logísticas, administrativas, vehículos
├── 3. MODELOS
│   └── Lógica de negocio (cálculos de costos, nómina, vehículos)
├── 4. DATOS
│   └── Inputs por marca + recursos compartidos
├── 5. PROCESAMIENTO
│   └── Motor de simulación, asignador de gastos, validadores
├── 6. VISUALIZACIÓN
│   └── Dashboards interactivos (general, por marca, comparativos)
└── 7. EXPORTACIÓN
    └── Excel, PDF, CSV
```

### Flujo de Funcionamiento

```
Usuario Define Marcas → Asigna Recursos Individuales/Compartidos
                            ↓
                  Motor de Simulación
                            ↓
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
 Costos Individuales  Costos Compartidos   Prorrateo
        └───────────────────┼───────────────────┘
                            ↓
                  Totalización por Marca
                            ↓
                   Cálculo de Márgenes
                            ↓
                  Dashboards + Exportación
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
│
├── config/                            # ⚙️ Configuraciones globales
│   ├── parametros_macro.yaml          # IPC, IPT, incrementos salariales
│   ├── factores_prestacionales.yaml   # Salud, pensión, ARL, etc.
│   ├── marcas.yaml                    # Lista de marcas activas
│   └── empresa.yaml                   # Datos de la razón social
│
├── catalogos/                         # 📚 Catálogos maestros
│   ├── figuras_comerciales.yaml       # Tipos de vendedores, supervisores
│   ├── figuras_logisticas.yaml        # Conductores, auxiliares, operarios
│   ├── figuras_administrativas.yaml   # Gerente, contador, aux. admin
│   ├── tipos_vehiculos.yaml           # Especificaciones de vehículos
│   └── rubros.yaml                    # Catálogo de todos los rubros
│
├── models/                            # 🧮 Lógica de negocio (Python)
│   ├── __init__.py
│   ├── marca.py                       # Clase Marca
│   ├── rama_comercial.py              # Cálculos rama comercial
│   ├── rama_logistica.py              # Cálculos rama logística
│   ├── rama_administrativa.py         # Cálculos rama administrativa
│   ├── rubro.py                       # Clase Rubro (individual/compartido)
│   ├── personal.py                    # Cálculo de nómina y prestaciones
│   ├── vehiculo.py                    # Cálculo de costos de vehículos
│   └── calculadora.py                 # Cálculos financieros generales
│
├── data/                              # 📊 Datos de entrada
│   ├── marcas/
│   │   ├── marca_a/
│   │   │   ├── comercial.yaml         # Recursos comerciales Marca A
│   │   │   ├── logistica.yaml         # Recursos logísticos Marca A
│   │   │   └── ventas.yaml            # Proyección de ventas Marca A
│   │   ├── marca_b/
│   │   │   └── ...
│   │   └── marca_c/
│   │       └── ...
│   ├── compartidos/
│   │   ├── administrativo.yaml        # Recursos admin compartidos
│   │   ├── logistica.yaml             # Recursos logísticos compartidos
│   │   └── prorrateos.yaml            # Reglas de prorrateo
│   └── referencia/
│       └── Simula DxV Nutresa 2025.xlsx  # Modelo de referencia
│
├── core/                              # ⚡ Motor de procesamiento
│   ├── __init__.py
│   ├── simulator.py                   # Motor principal de simulación
│   ├── allocator.py                   # Asignador de gastos compartidos
│   ├── calculator_nomina.py           # Calculadora de nómina
│   ├── calculator_vehiculos.py        # Calculadora de vehículos
│   └── validator.py                   # Validador de datos
│
├── panels/                            # 🎨 Dashboards (Streamlit)
│   ├── app.py                         # Aplicación principal
│   ├── dashboard_general.py           # Dashboard consolidado
│   ├── panel_marca.py                 # Panel individual por marca
│   ├── panel_comparativo.py           # Comparación entre marcas
│   ├── panel_comercial.py             # Detalle rama comercial
│   ├── panel_logistica.py             # Detalle rama logística
│   ├── panel_administrativa.py        # Detalle rama administrativa
│   └── simulador_escenarios.py        # Simulador "what-if"
│
├── output/                            # 📤 Exportación
│   ├── exportadores/
│   │   ├── excel_exporter.py          # Exportar a Excel
│   │   ├── pdf_exporter.py            # Exportar a PDF
│   │   └── csv_exporter.py            # Exportar a CSV
│   ├── templates/
│   │   ├── template_simulacion.xlsx   # Template Excel
│   │   └── template_reporte.html      # Template HTML
│   └── resultados/                    # Archivos generados
│
├── utils/                             # 🛠️ Utilidades
│   ├── loaders.py                     # Carga de archivos YAML
│   ├── formatters.py                  # Formateo de números, fechas
│   └── helpers.py                     # Funciones auxiliares
│
├── tests/                             # 🧪 Tests
│   ├── test_calculadora.py
│   ├── test_prorrateo.py
│   └── test_simulador.py
│
├── requirements.txt                   # Dependencias Python
├── .gitignore
└── LICENSE
```

---

## 🚀 Guía de Uso

### Instalación

```bash
# Clonar el repositorio
git clone https://github.com/jvelezp13/modelodistribucion.git
cd modelodistribucion

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Configuración Inicial

1. **Configurar parámetros macroeconómicos:**
   - Editar `config/parametros_macro.yaml`
   - Actualizar IPC, IPT, incrementos salariales

2. **Definir marcas:**
   - Editar `config/marcas.yaml`
   - Agregar las marcas que vas a simular

3. **Configurar recursos por marca:**
   - Crear carpeta en `data/marcas/tu_marca/`
   - Crear archivos `comercial.yaml`, `logistica.yaml`, `ventas.yaml`

4. **Configurar recursos compartidos:**
   - Editar `data/compartidos/administrativo.yaml`
   - Editar `data/compartidos/logistica.yaml`
   - Definir criterios de prorrateo en `data/compartidos/prorrateos.yaml`

### Ejecutar la Aplicación

```bash
# Iniciar el dashboard interactivo
streamlit run panels/app.py
```

La aplicación se abrirá en tu navegador en `http://localhost:8501`

### Ejemplo: Agregar una Nueva Marca

1. Crear carpeta:
```bash
mkdir -p data/marcas/nueva_marca
```

2. Crear `data/marcas/nueva_marca/comercial.yaml`:
```yaml
marca_id: nueva_marca
nombre: "Nueva Marca S.A."
proyeccion_ventas_mensual: 80000000

recursos_comerciales:
  vendedores:
    - tipo: vendedor_geografico
      cantidad: 3
      salario_base: 2150000
      asignacion: individual

  supervisores:
    - cantidad: 1
      salario_base: 3500000
      asignacion: compartido
      criterio_prorrateo: ventas
      porcentaje_dedicacion: 0.3

costos_adicionales:
  plan_datos: 35000
  uniformes: 150000
  gps: 45000
```

3. Crear `data/marcas/nueva_marca/logistica.yaml`
4. Crear `data/marcas/nueva_marca/ventas.yaml`
5. Actualizar `config/marcas.yaml` para incluir la nueva marca
6. Ejecutar la simulación

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
