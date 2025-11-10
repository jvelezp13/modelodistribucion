# Arquitectura Técnica - Sistema de Distribución Multimarcas

Este documento describe la arquitectura técnica detallada del sistema.

---

## 🏗️ Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USUARIO / INTERFAZ                            │
│                      (Streamlit Dashboard)                           │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     CAPA DE VISUALIZACIÓN                            │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐              │
│  │  Dashboard  │  │ Panel Marca  │  │  Comparativo   │              │
│  │   General   │  │  Individual  │  │  Multimarcas   │              │
│  └─────────────┘  └──────────────┘  └────────────────┘              │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   CAPA DE PROCESAMIENTO                              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐            │
│  │  Simulator   │  │  Allocator   │  │  Calculadoras   │            │
│  │    (Core)    │  │  (Prorrateo) │  │  Especializadas │            │
│  └──────────────┘  └──────────────┘  └─────────────────┘            │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      CAPA DE MODELOS                                 │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐                  │
│  │   Marca    │  │   Rubro     │  │   Personal   │                  │
│  ├────────────┤  ├─────────────┤  ├──────────────┤                  │
│  │ Comercial  │  │  Vehículo   │  │  Calculadora │                  │
│  │ Logística  │  │             │  │   Financiera │                  │
│  │    Admin   │  │             │  │              │                  │
│  └────────────┘  └─────────────┘  └──────────────┘                  │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      CAPA DE DATOS                                   │
│  ┌──────────────────┐  ┌─────────────────┐  ┌───────────────┐       │
│  │  Configuración   │  │   Catálogos     │  │  Datos por    │       │
│  │   (YAML)         │  │   Maestros      │  │    Marca      │       │
│  └──────────────────┘  └─────────────────┘  └───────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Detalle de Componentes

### 1. CAPA DE VISUALIZACIÓN (panels/)

**Responsabilidad:** Presentar la información al usuario de forma interactiva.

#### Componentes:

**`app.py`** - Aplicación principal de Streamlit
- Punto de entrada del sistema
- Navegación entre paneles
- Gestión de sesión del usuario

**`dashboard_general.py`** - Dashboard consolidado
- Vista ejecutiva de todas las marcas
- KPIs principales
- Gráficos de alto nivel

**`panel_marca.py`** - Panel individual por marca
- Detalle completo de una marca
- Desglose por rama (Comercial, Logística, Admin)
- Comparación con objetivos

**`panel_comparativo.py`** - Comparación entre marcas
- Tablas comparativas
- Gráficos de barras y tortas
- Análisis de eficiencia

**`simulador_escenarios.py`** - Simulador "what-if"
- Cambiar parámetros en tiempo real
- Ver impacto en costos y márgenes
- Guardar escenarios

---

### 2. CAPA DE PROCESAMIENTO (core/)

**Responsabilidad:** Lógica de negocio y cálculos complejos.

#### Componentes:

**`simulator.py`** - Motor principal de simulación
```python
class Simulator:
    def __init__(self, config):
        self.config = config
        self.marcas = []
        self.recursos_compartidos = []

    def cargar_datos(self):
        """Carga configuraciones y datos de marcas"""

    def calcular_costos_individuales(self):
        """Calcula costos directos por marca"""

    def calcular_costos_compartidos(self):
        """Calcula costos compartidos y prorrateos"""

    def ejecutar_simulacion(self):
        """Ejecuta simulación completa"""
        # 1. Cargar datos
        # 2. Calcular costos individuales
        # 3. Calcular costos compartidos
        # 4. Aplicar prorrateos
        # 5. Totalizar por marca
        # 6. Calcular márgenes
        return resultados
```

**`allocator.py`** - Asignador de gastos compartidos
```python
class Allocator:
    def __init__(self, marcas, recursos_compartidos):
        self.marcas = marcas
        self.recursos_compartidos = recursos_compartidos

    def calcular_prorrateo_ventas(self, recurso):
        """Prorrateo proporcional a las ventas"""

    def calcular_prorrateo_volumen(self, recurso):
        """Prorrateo proporcional al volumen"""

    def calcular_prorrateo_headcount(self, recurso):
        """Prorrateo por cantidad de empleados"""

    def calcular_prorrateo_equitativo(self, recurso):
        """Prorrateo equitativo (partes iguales)"""

    def asignar_recursos(self):
        """Asigna todos los recursos compartidos"""
        for recurso in self.recursos_compartidos:
            criterio = recurso.criterio_prorrateo
            if criterio == 'ventas':
                self.calcular_prorrateo_ventas(recurso)
            elif criterio == 'volumen':
                self.calcular_prorrateo_volumen(recurso)
            # ... etc
```

**`calculator_nomina.py`** - Calculadora de nómina
```python
class CalculadoraNomina:
    def __init__(self, factores_prestacionales):
        self.factores = factores_prestacionales

    def calcular_costo_empleado(self, salario_base, perfil, subsidio_transporte=True):
        """
        Calcula el costo total mensual de un empleado

        Args:
            salario_base: Salario base mensual
            perfil: 'administrativo', 'comercial', 'logistico', 'aprendiz_sena'
            subsidio_transporte: Si aplica subsidio de transporte

        Returns:
            dict con desglose de costos
        """
        factor = self.factores[perfil]['factor_total']
        subsidio = 200000 if subsidio_transporte and salario_base < 2600000 else 0

        costo_prestaciones = salario_base * factor
        costo_total = salario_base + costo_prestaciones + subsidio

        return {
            'salario_base': salario_base,
            'prestaciones': costo_prestaciones,
            'subsidio_transporte': subsidio,
            'total': costo_total
        }
```

**`calculator_vehiculos.py`** - Calculadora de vehículos
```python
class CalculadoraVehiculos:
    def __init__(self, catalogo_vehiculos):
        self.catalogo = catalogo_vehiculos

    def calcular_costo_renting(self, tipo_vehiculo, km_mensuales):
        """Calcula costo mensual de vehículo en renting"""
        vehiculo = self.catalogo[tipo_vehiculo]
        costos = vehiculo['costos']['renting']

        canon = costos['canon_mensual']
        combustible = costos['combustible_promedio_mensual']
        lavada = costos['lavada_mensual']
        reposicion = costos['reposicion_mensual']

        total = canon + combustible + lavada + reposicion

        return {
            'canon': canon,
            'combustible': combustible,
            'lavada': lavada,
            'reposicion': reposicion,
            'total': total
        }

    def calcular_costo_tradicional(self, tipo_vehiculo, km_mensuales):
        """Calcula costo mensual de vehículo propio"""
        # Similar pero con depreciación, mantenimiento, seguro, etc.
```

**`validator.py`** - Validador de datos
```python
class Validator:
    def validar_marca(self, datos_marca):
        """Valida que los datos de una marca sean correctos"""
        # Verificar campos requeridos
        # Verificar rangos válidos
        # Verificar consistencia

    def validar_recursos(self, recursos):
        """Valida que los recursos sean válidos"""

    def validar_simulacion(self, resultados):
        """Valida que los resultados de la simulación sean coherentes"""
```

---

### 3. CAPA DE MODELOS (models/)

**Responsabilidad:** Representar las entidades del negocio.

#### Clases principales:

**`Marca`** - Representa una marca
```python
class Marca:
    def __init__(self, marca_id, nombre):
        self.id = marca_id
        self.nombre = nombre
        self.ventas_mensuales = 0
        self.recursos_comerciales = []
        self.recursos_logisticos = []
        self.costos_asignados = {}

    def calcular_total_costos(self):
        """Calcula el costo total de la marca"""

    def calcular_margen(self):
        """Calcula el margen de la marca"""
        return (self.ventas_mensuales - self.total_costos) / self.ventas_mensuales
```

**`Rubro`** - Representa un rubro de costo
```python
class Rubro:
    def __init__(self, nombre, tipo_asignacion, valor):
        self.nombre = nombre
        self.tipo_asignacion = tipo_asignacion  # 'individual', 'compartido'
        self.valor = valor
        self.criterio_prorrateo = None  # Si es compartido

    def calcular_asignacion(self, marca, todas_marcas):
        """Calcula cuánto de este rubro le corresponde a la marca"""
        if self.tipo_asignacion == 'individual':
            return self.valor
        else:
            # Aplicar prorrateo
            return self._prorratear(marca, todas_marcas)
```

---

### 4. CAPA DE DATOS

**Responsabilidad:** Almacenar y cargar configuraciones y datos.

#### Estructura:

```
data/
├── marcas/
│   └── [marca_id]/
│       ├── comercial.yaml    # Recursos comerciales
│       ├── logistica.yaml    # Recursos logísticos
│       └── ventas.yaml       # Proyecciones de ventas
├── compartidos/
│   ├── administrativo.yaml   # Recursos admin compartidos
│   ├── logistica.yaml        # Recursos logísticos compartidos
│   └── prorrateos.yaml       # Reglas de prorrateo
└── referencia/
    └── *.xlsx                # Archivos de referencia
```

---

## 🔄 Flujo de Datos

### 1. Carga Inicial

```
Usuario inicia app
    ↓
app.py carga configuraciones (YAML)
    ↓
Simulator.cargar_datos()
    ↓
Crea instancias de Marca, Rubro, etc.
```

### 2. Cálculo de Costos

```
Simulator.ejecutar_simulacion()
    ↓
1. Calcular costos individuales por marca
   - Vendedores dedicados
   - Vehículos exclusivos
   - etc.
    ↓
2. Calcular costos compartidos
   - Gerente
   - Bodega
   - Contador
   - etc.
    ↓
3. Allocator.asignar_recursos()
   - Aplicar prorrateos según criterio
   - Asignar proporciones a cada marca
    ↓
4. Totalizar por marca
   - Suma de costos individuales + compartidos
    ↓
5. Calcular márgenes
   - (Ventas - Costos) / Ventas
```

### 3. Visualización

```
Resultados de simulación
    ↓
Dashboard General muestra KPIs
    ↓
Usuario navega a Panel Marca
    ↓
Panel Marca muestra detalles
    ↓
Usuario exporta a Excel/PDF
```

---

## 🛠️ Tecnologías Utilizadas

| Componente | Tecnología | Propósito |
|------------|------------|-----------|
| **Backend** | Python 3.9+ | Lógica de negocio |
| **Frontend** | Streamlit | Dashboards interactivos |
| **Datos** | YAML | Configuraciones |
| **Procesamiento** | Pandas, NumPy | Manipulación de datos |
| **Visualización** | Plotly, Matplotlib | Gráficos |
| **Exportación** | openpyxl, reportlab | Excel y PDF |
| **Tests** | pytest | Testing |

---

## 🔒 Principios de Diseño

1. **Separación de Responsabilidades**
   - Cada capa tiene una responsabilidad clara
   - Los modelos no conocen la presentación
   - La presentación no conoce la lógica de negocio

2. **Configurabilidad**
   - Todo se configura mediante YAML
   - No hay valores hardcodeados
   - Fácil de adaptar a diferentes escenarios

3. **Extensibilidad**
   - Fácil agregar nuevas marcas
   - Fácil agregar nuevos tipos de rubros
   - Fácil agregar nuevos criterios de prorrateo

4. **Validación**
   - Validación temprana de datos
   - Mensajes de error claros
   - Prevención de estados inconsistentes

5. **Testabilidad**
   - Componentes pequeños y testeables
   - Mocks para datos
   - Cobertura de tests alta

---

## 📈 Roadmap Técnico

### Fase 1: MVP
- [x] Estructura de datos YAML
- [ ] Modelos básicos (Marca, Rubro)
- [ ] Calculadora de nómina
- [ ] Dashboard simple

### Fase 2: Core
- [ ] Motor de simulación completo
- [ ] Asignador de prorrateos
- [ ] Todos los paneles
- [ ] Exportación Excel

### Fase 3: Avanzado
- [ ] Base de datos (SQLAlchemy + PostgreSQL)
- [ ] API REST (FastAPI)
- [ ] Autenticación (JWT)
- [ ] Versionamiento de simulaciones

### Fase 4: Producción
- [ ] Docker + Docker Compose
- [ ] CI/CD (GitHub Actions)
- [ ] Monitoreo (Prometheus + Grafana)
- [ ] Backups automatizados

---

**Última actualización:** 2025-11-10
