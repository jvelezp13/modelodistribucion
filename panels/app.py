"""
Dashboard Principal - Sistema de Distribución Multimarcas

Aplicación Streamlit para visualizar simulaciones del modelo de distribución.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any
import sys
import logging
from pathlib import Path

# Configurar logging para debug
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)

# Configurar paths para imports
root_path = Path(__file__).parent.parent

# Agregar root path para importar el simulador (core.simulator)
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

# Importar simulador PRIMERO (antes de que Django reorganice los paths)
from core.simulator import Simulator, simular_modelo_completo

# Importar loader de DB (esto configurará Django y reorganizará paths)
from utils.loaders_db import get_loader_db as get_loader

# Configuración de la página
st.set_page_config(
    page_title="Sistema DxV Multimarcas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados modernos y profesionales
st.markdown("""
<style>
    /* Importar fuente moderna */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Variables globales */
    :root {
        --primary-color: #0066FF;
        --secondary-color: #4F46E5;
        --success-color: #10B981;
        --warning-color: #F59E0B;
        --danger-color: #EF4444;
        --text-primary: #1A1F36;
        --text-secondary: #6B7280;
        --bg-primary: #FFFFFF;
        --bg-secondary: #F7F9FC;
        --border-color: #E5E7EB;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }

    /* Tipografía mejorada */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-weight: 400;
        line-height: 1.6;
    }

    /* Header principal */
    .main-header {
        font-size: 2.25rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
        letter-spacing: -0.025em;
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* Subtítulos */
    .subtitle {
        font-size: 1rem;
        color: var(--text-secondary);
        margin-bottom: 2rem;
        font-weight: 500;
    }

    /* Mejorar métricas de Streamlit */
    [data-testid="stMetricValue"] {
        font-size: 1.875rem;
        font-weight: 700;
        color: var(--text-primary);
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    [data-testid="stMetricDelta"] {
        font-size: 0.875rem;
        font-weight: 500;
    }

    /* Cards con sombra moderna */
    .metric-card {
        background: var(--bg-primary);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid var(--border-color);
        box-shadow: var(--shadow-md);
        transition: all 0.3s ease;
    }

    .metric-card:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-2px);
    }

    /* Cards con indicador de color */
    .success-metric {
        border-left: 4px solid var(--success-color);
    }

    .warning-metric {
        border-left: 4px solid var(--warning-color);
    }

    .danger-metric {
        border-left: 4px solid var(--danger-color);
    }

    .primary-metric {
        border-left: 4px solid var(--primary-color);
    }

    /* Mejorar botones */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        padding: 0.625rem 1.25rem;
        transition: all 0.2s ease;
        border: none;
        box-shadow: var(--shadow-sm);
    }

    .stButton > button:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
    }

    /* Mejorar sidebar */
    [data-testid="stSidebar"] {
        background-color: var(--bg-secondary);
        border-right: 1px solid var(--border-color);
    }

    [data-testid="stSidebar"] h2 {
        font-size: 1.125rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 1.5rem;
    }

    /* Mejorar multiselect */
    .stMultiSelect [data-baseweb="select"] {
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }

    /* Mejorar tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        border-bottom: 2px solid var(--border-color);
    }

    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        border-radius: 8px 8px 0 0;
        padding: 0.75rem 1.5rem;
        transition: all 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: var(--bg-secondary);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(to bottom, var(--bg-secondary), transparent);
        border-bottom: 3px solid var(--primary-color);
    }

    /* Mejorar tablas */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid var(--border-color);
    }

    .dataframe thead tr {
        background-color: var(--bg-secondary);
    }

    .dataframe thead th {
        font-weight: 700;
        color: var(--text-primary);
        padding: 1rem;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
    }

    .dataframe tbody tr:hover {
        background-color: var(--bg-secondary);
    }

    /* Mejorar expanders */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: var(--text-primary);
        background-color: var(--bg-secondary);
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }

    /* Mejorar checkbox */
    .stCheckbox {
        font-weight: 500;
    }

    /* Spinner mejorado */
    .stSpinner > div {
        border-top-color: var(--primary-color) !important;
    }

    /* Alertas mejoradas */
    .stAlert {
        border-radius: 8px;
        border-left-width: 4px;
        box-shadow: var(--shadow-sm);
    }

    /* Espaciado y separadores */
    hr {
        margin: 2rem 0;
        border: none;
        border-top: 2px solid var(--border-color);
        opacity: 0.5;
    }

    /* Animaciones suaves */
    * {
        transition: background-color 0.2s ease, border-color 0.2s ease;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.75rem;
        }
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=60)  # Cache por 1 minuto
def cargar_marcas_disponibles(_force_reload=None):
    """Carga la lista de marcas disponibles.

    Args:
        _force_reload: Timestamp para forzar recarga (underscore evita que se use en hash del cache)
    """
    loader = get_loader()
    return loader.listar_marcas()


@st.cache_data(ttl=60)  # Cache por 1 minuto
def ejecutar_simulacion(marcas_seleccionadas, _force_reload=None):
    """Ejecuta la simulación para las marcas seleccionadas.

    Args:
        marcas_seleccionadas: Tupla de marcas a simular
        _force_reload: Timestamp para forzar recarga (underscore evita que se use en hash del cache)
    """
    try:
        # IMPORTANTE: Usar loader de DB en lugar de YAML
        loader = get_loader()
        simulator = Simulator(loader=loader)
        simulator.cargar_marcas(marcas_seleccionadas)
        resultado = simulator.ejecutar_simulacion()
        return resultado
    except Exception as e:
        st.error(f"Error en la simulación: {str(e)}")
        return None


def formatear_moneda(valor):
    """Formatea un valor como moneda colombiana."""
    return f"${valor:,.0f}"


def formatear_porcentaje(valor):
    """Formatea un valor como porcentaje."""
    return f"{valor:.1f}%"


def mostrar_resumen_consolidado(resultado):
    """Muestra el resumen consolidado de todas las marcas."""
    st.markdown('<p class="main-header">📊 Resumen Consolidado</p>', unsafe_allow_html=True)

    consolidado = resultado.consolidado

    # Métricas principales en columnas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Ventas Mensuales",
            formatear_moneda(consolidado['total_ventas_mensuales']),
            f"{formatear_moneda(consolidado['total_ventas_anuales'])} anuales"
        )

    with col2:
        st.metric(
            "Costos Mensuales",
            formatear_moneda(consolidado['total_costos_mensuales']),
            f"{formatear_moneda(consolidado['total_costos_anuales'])} anuales"
        )

    with col3:
        margen = consolidado['margen_consolidado'] * 100
        st.metric(
            "Margen Consolidado",
            formatear_porcentaje(margen),
            delta=None,
            delta_color="normal" if margen > 10 else "inverse"
        )

    with col4:
        st.metric(
            "Total Empleados",
            consolidado['total_empleados']
        )

    # Desglose de costos por categoría
    st.subheader("Desglose de Costos por Categoría")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Gráfico de pastel
        categorias = ['Comercial', 'Logística', 'Administrativa']
        valores = [
            consolidado['costo_comercial_total'],
            consolidado['costo_logistico_total'],
            consolidado['costo_administrativo_total']
        ]

        fig_pie = px.pie(
            values=valores,
            names=categorias,
            title="Distribución de Costos por Categoría",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Tabla de valores
        df_categorias = pd.DataFrame({
            'Categoría': categorias,
            'Costo Mensual': valores,
            '% del Total': [(v / consolidado['total_costos_mensuales'] * 100) for v in valores]
        })
        df_categorias['Costo Mensual'] = df_categorias['Costo Mensual'].apply(formatear_moneda)
        df_categorias['% del Total'] = df_categorias['% del Total'].apply(formatear_porcentaje)

        st.dataframe(df_categorias, hide_index=True, use_container_width=True)


def mostrar_comparacion_marcas(resultado):
    """Muestra la comparación entre marcas."""
    st.markdown("---")
    st.subheader("📈 Comparación entre Marcas")

    # Preparar datos
    marcas_data = []
    for marca in resultado.marcas:
        marcas_data.append({
            'Marca': marca.nombre,
            'Ventas': marca.ventas_mensuales,
            'Costos': marca.costo_total,
            'Margen %': marca.margen_porcentaje,
            'Empleados': marca.total_empleados
        })

    df_marcas = pd.DataFrame(marcas_data)

    # Gráfico de barras comparativo
    col1, col2 = st.columns(2)

    with col1:
        fig_ventas = px.bar(
            df_marcas,
            x='Marca',
            y=['Ventas', 'Costos'],
            title='Ventas vs Costos por Marca',
            barmode='group',
            color_discrete_map={'Ventas': '#28a745', 'Costos': '#dc3545'}
        )
        st.plotly_chart(fig_ventas, use_container_width=True)

    with col2:
        fig_margen = px.bar(
            df_marcas,
            x='Marca',
            y='Margen %',
            title='Margen por Marca',
            color='Margen %',
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig_margen, use_container_width=True)

    # Tabla detallada
    st.subheader("Tabla Comparativa Detallada")

    df_tabla = df_marcas.copy()
    df_tabla['Ventas'] = df_tabla['Ventas'].apply(formatear_moneda)
    df_tabla['Costos'] = df_tabla['Costos'].apply(formatear_moneda)
    df_tabla['Margen %'] = df_tabla['Margen %'].apply(formatear_porcentaje)

    st.dataframe(df_tabla, hide_index=True, use_container_width=True)


def mostrar_detalle_marca(marca):
    """Muestra el detalle de una marca específica."""
    st.markdown(f"### 🏢 {marca.nombre}")

    # Métricas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Ventas Mensuales", formatear_moneda(marca.ventas_mensuales))

    with col2:
        st.metric("Costo Total", formatear_moneda(marca.costo_total))

    with col3:
        color = "normal" if marca.margen_porcentaje > 10 else "inverse"
        st.metric("Margen", formatear_porcentaje(marca.margen_porcentaje), delta_color=color)

    with col4:
        st.metric("Empleados", marca.total_empleados)

    # Desglose de costos
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Desglose de Costos:**")
        costos_detalle = {
            'Comercial': marca.costo_comercial,
            'Logística': marca.costo_logistico,
            'Administrativa': marca.costo_administrativo
        }

        for categoria, valor in costos_detalle.items():
            porcentaje = (valor / marca.costo_total * 100) if marca.costo_total > 0 else 0
            st.write(f"- **{categoria}**: {formatear_moneda(valor)} ({formatear_porcentaje(porcentaje)})")

    with col2:
        st.markdown("**Recursos:**")
        st.write(f"- Rubros Individuales: {len(marca.rubros_individuales)}")
        st.write(f"- Rubros Compartidos: {len(marca.rubros_compartidos_asignados)}")
        st.write(f"- Empleados Comerciales: {marca.empleados_comerciales}")
        st.write(f"- Empleados Logísticos: {marca.empleados_logisticos}")

    # NUEVA SECCIÓN: Detalle de Rubros Individuales
    st.markdown("#### 📋 Detalle de Rubros Individuales")

    if marca.rubros_individuales:
        rubros_data = []
        for rubro in marca.rubros_individuales:
            rubro_info = {
                'Nombre': rubro.nombre,
                'Categoría': rubro.categoria.capitalize(),
                'Tipo': rubro.tipo
            }

            # Si es personal, mostrar detalles de nómina
            if hasattr(rubro, 'cantidad') and hasattr(rubro, 'salario_base'):
                rubro_info['Cantidad'] = rubro.cantidad
                rubro_info['Salario Base'] = formatear_moneda(rubro.salario_base)
                rubro_info['Costo Unitario'] = formatear_moneda(rubro.valor_unitario)
                rubro_info['Costo Total'] = formatear_moneda(rubro.valor_total)
            # Si es vehículo
            elif hasattr(rubro, 'tipo_vehiculo'):
                rubro_info['Cantidad'] = rubro.cantidad
                rubro_info['Tipo Vehículo'] = rubro.tipo_vehiculo.upper()
                rubro_info['Esquema'] = rubro.esquema.capitalize()
                rubro_info['Costo Unitario'] = formatear_moneda(rubro.valor_unitario)
                rubro_info['Costo Total'] = formatear_moneda(rubro.valor_total)
            else:
                rubro_info['Costo Total'] = formatear_moneda(rubro.valor_total)

            rubros_data.append(rubro_info)

        df_rubros = pd.DataFrame(rubros_data)
        st.dataframe(df_rubros, hide_index=True, use_container_width=True)

        # Subtotales por categoría
        st.markdown("**Subtotales por Categoría:**")
        col1, col2, col3 = st.columns(3)

        comercial_total = sum(r.valor_total for r in marca.rubros_individuales if r.categoria == 'comercial')
        logistico_total = sum(r.valor_total for r in marca.rubros_individuales if r.categoria == 'logistica')
        admin_total = sum(r.valor_total for r in marca.rubros_individuales if r.categoria == 'administrativa')

        with col1:
            st.metric("Comercial", formatear_moneda(comercial_total))
        with col2:
            st.metric("Logística", formatear_moneda(logistico_total))
        with col3:
            st.metric("Administrativa", formatear_moneda(admin_total))
    else:
        st.info("Esta marca no tiene rubros individuales asignados")

    st.markdown("---")


def main():
    """Función principal del dashboard."""
    # Inicializar session state para forzar recarga y mantener selección
    if 'reload_timestamp' not in st.session_state:
        st.session_state.reload_timestamp = 0
    if 'marcas_seleccionadas' not in st.session_state:
        st.session_state.marcas_seleccionadas = None

    # Header moderno
    st.markdown('<p class="main-header">Sistema de Distribución Multimarcas</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Modelo de Distribución y Ventas (DxV) - Simulación y Optimización</p>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuración")

        # Selección de marcas (con timestamp para forzar recarga)
        marcas_disponibles = cargar_marcas_disponibles(_force_reload=st.session_state.reload_timestamp)

        if not marcas_disponibles:
            st.error("No se encontraron marcas configuradas")
            st.stop()

        # Usar marcas guardadas o todas por defecto
        default_marcas = st.session_state.marcas_seleccionadas if st.session_state.marcas_seleccionadas else marcas_disponibles

        marcas_seleccionadas = st.multiselect(
            "Marcas a Simular",
            marcas_disponibles,
            default=default_marcas,
            help="Selecciona las marcas que deseas incluir en la simulación",
            key="multiselect_marcas"
        )

        # Guardar selección actual en session_state
        st.session_state.marcas_seleccionadas = marcas_seleccionadas

        # Botón para recargar datos desde PostgreSQL
        if st.button("🔄 Recargar Datos desde BD", use_container_width=True, help="Limpia el caché y recarga los datos desde PostgreSQL"):
            import time
            st.session_state.reload_timestamp = time.time()
            # Mantener las marcas seleccionadas actuales
            # (ya están guardadas en session_state.marcas_seleccionadas)
            st.cache_data.clear()
            st.success("✅ Caché limpiado. Los datos se recargarán desde la base de datos.")
            st.rerun()

        # Botón de simulación
        ejecutar = st.button("🚀 Ejecutar Simulación", type="primary", use_container_width=True)

        # DEBUG: Botón para ver datos crudos de BD
        ver_debug = st.checkbox("🔍 Mostrar Info de Debug", value=False)

        st.markdown("---")
        st.markdown("### 📖 Acerca de")
        st.markdown("""
        Este dashboard permite simular y visualizar:
        - Costos por marca y consolidados
        - Distribución de gastos compartidos
        - Márgenes y rentabilidad
        - Comparaciones entre marcas
        """)

    # Contenido principal
    if not marcas_seleccionadas:
        st.warning("⚠️ Selecciona al menos una marca para simular")
        st.stop()

    # Ejecutar simulación (con timestamp para forzar recarga)
    with st.spinner("⏳ Ejecutando simulación..."):
        resultado = ejecutar_simulacion(
            tuple(marcas_seleccionadas),
            _force_reload=st.session_state.reload_timestamp
        )

    if resultado is None:
        st.error("No se pudo ejecutar la simulación")
        st.stop()

    # DEBUG: Mostrar datos crudos de BD
    if ver_debug:
        st.markdown("---")
        st.markdown("### 🔍 DEBUG: Datos Crudos de PostgreSQL")

        loader = get_loader()
        for marca_id in marcas_seleccionadas:
            with st.expander(f"📊 Datos de {marca_id.upper()}", expanded=True):
                try:
                    # Cargar datos comerciales
                    datos_comerciales = loader.cargar_marca_comercial(marca_id)

                    st.markdown("**Personal Comercial:**")
                    for tipo, lista_personal in datos_comerciales['recursos_comerciales'].items():
                        total_cantidad = sum(p['cantidad'] for p in lista_personal)
                        st.write(f"- **{tipo}**: {len(lista_personal)} registros, Total: {total_cantidad} personas")
                        for idx, p in enumerate(lista_personal, 1):
                            st.write(f"  Registro {idx}: Cantidad={p['cantidad']}, Salario=${p['salario_base']:,.0f}")
                except Exception as e:
                    st.error(f"Error cargando datos: {str(e)}")
        st.markdown("---")

    # Tabs principales
    tab1, tab2, tab3 = st.tabs(["📊 Resumen General", "📈 Por Marca", "🔍 Detalles"])

    with tab1:
        mostrar_resumen_consolidado(resultado)
        st.markdown("---")
        mostrar_comparacion_marcas(resultado)

    with tab2:
        for marca in resultado.marcas:
            mostrar_detalle_marca(marca)

    with tab3:
        st.subheader("🔍 Información Detallada")

        # Nueva sección: Proyecciones de Ventas
        st.markdown("### 📈 Proyección de Ventas Mensuales")

        # Cargar datos de ventas desde YAML para cada marca
        loader = get_loader()

        for marca in resultado.marcas:
            try:
                datos_ventas = loader.cargar_marca_ventas(marca.marca_id)

                if 'ventas_mensuales' in datos_ventas:
                    st.markdown(f"#### {marca.nombre}")

                    # Crear DataFrame con las ventas mensuales
                    ventas_mensuales = datos_ventas['ventas_mensuales']
                    meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                            'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

                    df_ventas = pd.DataFrame({
                        'Mes': [m.capitalize() for m in meses],
                        'Ventas': [ventas_mensuales.get(m, 0) for m in meses]
                    })

                    # Gráfico de línea
                    fig_ventas = px.line(
                        df_ventas,
                        x='Mes',
                        y='Ventas',
                        title=f'Proyección Mensual - {marca.nombre}',
                        markers=True
                    )
                    fig_ventas.update_layout(yaxis_title="Ventas (COP)")
                    st.plotly_chart(fig_ventas, use_container_width=True)

                    # Tabla con valores
                    df_ventas_display = df_ventas.copy()
                    df_ventas_display['Ventas'] = df_ventas_display['Ventas'].apply(formatear_moneda)

                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.dataframe(df_ventas_display, hide_index=True, use_container_width=True)

                    with col2:
                        # Resumen
                        total_anual = df_ventas['Ventas'].sum()
                        promedio = df_ventas['Ventas'].mean()
                        mes_max = df_ventas.loc[df_ventas['Ventas'].idxmax(), 'Mes']
                        mes_min = df_ventas.loc[df_ventas['Ventas'].idxmin(), 'Mes']

                        st.metric("Total Anual", formatear_moneda(total_anual))
                        st.metric("Promedio Mensual", formatear_moneda(promedio))
                        st.write(f"**Mes Mayor:** {mes_max}")
                        st.write(f"**Mes Menor:** {mes_min}")

                    st.markdown("---")

            except Exception as e:
                st.warning(f"No se pudieron cargar datos de ventas para {marca.nombre}")

        # Rubros Compartidos
        st.markdown("### 🔄 Rubros Compartidos")
        st.write(f"Total de rubros compartidos: {len(resultado.rubros_compartidos)}")

        if resultado.rubros_compartidos:
            rubros_df = pd.DataFrame([
                {
                    'ID': r.id,
                    'Nombre': r.nombre,
                    'Categoría': r.categoria,
                    'Criterio Prorrateo': r.criterio_prorrateo.value if r.criterio_prorrateo else 'N/A',
                    'Valor Total': formatear_moneda(r.valor_total)
                }
                for r in resultado.rubros_compartidos
            ])
            st.dataframe(rubros_df, hide_index=True, use_container_width=True)

        st.markdown("### ⚙️ Metadata")
        st.json(resultado.metadata)


if __name__ == "__main__":
    main()
