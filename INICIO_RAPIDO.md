# 🚀 Inicio Rápido

Esta guía te ayudará a poner en marcha el sistema de distribución multimarcas en minutos.

---

## 📋 Requisitos Previos

- Python 3.9 o superior
- pip (gestor de paquetes de Python)
- Git

---

## ⚡ Instalación Rápida

### 1. Clonar el repositorio

```bash
git clone https://github.com/jvelezp13/modelodistribucion.git
cd modelodistribucion
```

### 2. Crear entorno virtual

**En macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**En Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## 🎯 Ejecutar el Dashboard

Una vez instaladas las dependencias, ejecuta:

```bash
streamlit run panels/app.py
```

El dashboard se abrirá automáticamente en tu navegador en `http://localhost:8501`

---

## 📊 ¿Qué puedes hacer?

### En el Dashboard:

1. **Seleccionar marcas** a simular (sidebar izquierdo)
2. **Ejecutar simulación** con el botón "🚀 Ejecutar Simulación"
3. **Ver resultados**:
   - Tab "Resumen General": Consolidado de todas las marcas
   - Tab "Por Marca": Detalle de cada marca individual
   - Tab "Detalles": Información técnica y rubros compartidos

### Métricas Disponibles:

- Ventas mensuales y anuales
- Costos totales y por categoría (Comercial, Logística, Administrativa)
- Márgenes por marca y consolidado
- Comparación entre marcas
- Distribución de gastos compartidos

---

## 🔧 Configuración Básica

### Agregar una Nueva Marca

1. Crea una carpeta en `data/marcas/`:
   ```bash
   mkdir -p data/marcas/mi_nueva_marca
   ```

2. Copia los archivos de ejemplo:
   ```bash
   cp data/marcas/marca_ejemplo/*.yaml data/marcas/mi_nueva_marca/
   ```

3. Edita los archivos YAML con los datos de tu marca:
   - `comercial.yaml`: Vendedores, supervisores, costos comerciales
   - `logistica.yaml`: Vehículos, personal logístico, volumen
   - `ventas.yaml`: Proyección de ventas mensuales

4. Actualiza `config/marcas.yaml` para incluir tu marca

5. Ejecuta el dashboard - tu marca aparecerá en la lista

---

## 📝 Ejemplo de Uso

### Escenario: Quiero simular 2 marcas

1. Inicia el dashboard:
   ```bash
   streamlit run panels/app.py
   ```

2. En el sidebar, selecciona las marcas que quieres simular

3. Clic en "🚀 Ejecutar Simulación"

4. Revisa los resultados en los diferentes tabs

5. Compara márgenes y costos entre marcas

---

## 🆘 Solución de Problemas

### El dashboard no inicia

**Error: `ModuleNotFoundError: No module named 'streamlit'`**

Solución:
```bash
pip install streamlit
```

### No aparecen mis marcas

1. Verifica que la carpeta exista en `data/marcas/`
2. Verifica que tenga los 3 archivos: `comercial.yaml`, `logistica.yaml`, `ventas.yaml`
3. Revisa los logs en la terminal para ver errores específicos

### Error de simulación

1. Verifica que los archivos YAML tengan la estructura correcta
2. Asegúrate de que los valores numéricos sean números (no texto)
3. Revisa el log en la terminal para detalles del error

---

## 📚 Próximos Pasos

1. **Lee el README completo**: `README.md` tiene toda la documentación
2. **Explora la arquitectura**: `ARQUITECTURA.md` explica cómo funciona el sistema
3. **Personaliza tus marcas**: Edita los archivos YAML según tus necesidades
4. **Agrega/modifica rubros**: Sigue la guía en el README

---

## 💡 Consejos

- **Usa Git para versionar cambios**: Cada modificación a los YAML queda registrada
- **Experimenta con ramas**: Crea ramas para probar diferentes escenarios
- **Comenta tus YAML**: Agrega comentarios para documentar decisiones
- **Revisa los logs**: La terminal muestra información útil sobre la simulación

---

## 🎓 Ejemplos de Modificaciones Comunes

### Cambiar salario de vendedores

Edita `data/marcas/tu_marca/comercial.yaml`:

```yaml
vendedores:
  - tipo: vendedor_geografico
    cantidad: 5
    salario_base: 2500000  # ← Cambia aquí
```

### Agregar un vehículo

Edita `data/marcas/tu_marca/logistica.yaml`:

```yaml
vehiculos:
  renting:
    - tipo: nhr
      cantidad: 2  # ← Agrega más vehículos
```

### Cambiar criterio de prorrateo

Edita `data/compartidos/administrativo.yaml`:

```yaml
gerente_general:
  criterio_prorrateo: headcount  # ← Cambia de "ventas" a "headcount"
```

---

## 📞 Ayuda

Para más información:
- Lee el `README.md` completo
- Revisa `ARQUITECTURA.md` para detalles técnicos
- Consulta los archivos de ejemplo en `data/marcas/marca_ejemplo/`

---

**¡Listo! Ya estás preparado para usar el sistema. 🎉**
