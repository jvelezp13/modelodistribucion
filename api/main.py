"""
FastAPI Backend para Sistema de Distribución Multimarcas

Expone endpoints REST para consumir el simulador existente.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path
import logging

# Configurar paths
root_path = Path(__file__).parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

# Importar simulador y loader
from core.simulator import Simulator
from utils.loaders_db import get_loader_db as get_loader

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear app FastAPI
app = FastAPI(
    title="Sistema DxV Multimarcas API",
    description="API REST para simulación de distribución y ventas multimarcas",
    version="2.0.0"
)

# Configurar CORS para permitir requests desde Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar el dominio de Next.js
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "DxV Multimarcas API",
        "version": "2.0.0"
    }


@app.get("/api/marcas")
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
def listar_escenarios() -> List[Dict[str, Any]]:
    """Lista todos los escenarios disponibles"""
    try:
        loader = get_loader()
        escenarios = loader.listar_escenarios()
        return escenarios
    except Exception as e:
        logger.error(f"Error listando escenarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/simulate")
def ejecutar_simulacion(
    marcas_seleccionadas: List[str],
    escenario_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Ejecuta la simulación para las marcas seleccionadas.

    Args:
        marcas_seleccionadas: Lista de IDs de marcas a simular

    Returns:
        Resultado de la simulación serializado
    """
    try:
        if not marcas_seleccionadas:
            raise HTTPException(status_code=400, detail="Debe seleccionar al menos una marca")

        logger.info(f"Ejecutando simulación para marcas: {marcas_seleccionadas}")

        # Crear simulador con loader de BD
        loader = get_loader(escenario_id=escenario_id)
        simulator = Simulator(loader=loader)
        simulator.cargar_marcas(marcas_seleccionadas)
        resultado = simulator.ejecutar_simulacion()

        # Serializar resultado a dict
        resultado_dict = serializar_resultado(resultado)

        logger.info(f"Simulación completada exitosamente")
        return resultado_dict

    except Exception as e:
        logger.error(f"Error ejecutando simulación: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/lejanias/comercial")
def obtener_detalle_lejanias_comercial(
    escenario_id: int,
    marca_id: str
) -> Dict[str, Any]:
    """
    Obtiene el detalle de lejanías comerciales por zona.

    Args:
        escenario_id: ID del escenario
        marca_id: ID de la marca

    Returns:
        Detalle de lejanías comerciales por zona
    """
    try:
        from core.models import Escenario, Marca, Zona
        from core.calculator_lejanias import CalculadoraLejanias

        # Obtener escenario y marca
        escenario = Escenario.objects.get(pk=escenario_id)
        marca = Marca.objects.get(marca_id=marca_id)

        # Inicializar calculadora
        calc = CalculadoraLejanias(escenario)

        # Debug: verificar configuración
        logger.info(f"Config lejanías: {calc.config}, Params macro: {calc.params_macro}")

        # Obtener zonas de la marca
        zonas = Zona.objects.filter(
            marca=marca,
            escenario=escenario,
            activo=True
        ).prefetch_related('municipios__municipio').select_related('vendedor', 'municipio_base_vendedor')

        logger.info(f"Zonas encontradas: {zonas.count()}")

        # Calcular para cada zona
        detalle_zonas = []
        total_combustible = 0.0
        total_pernocta = 0.0

        for zona in zonas:
            # Debug: verificar datos de la zona
            municipios_count = zona.municipios.count()
            logger.info(f"Zona: {zona.nombre}, Base vendedor: {zona.municipio_base_vendedor}, Municipios: {municipios_count}")

            resultado = calc.calcular_lejania_comercial_zona(zona)
            logger.info(f"Resultado zona {zona.nombre}: {resultado}")

            detalle_zonas.append({
                'zona_id': zona.id,
                'zona_nombre': zona.nombre,
                'vendedor': zona.vendedor.nombre if zona.vendedor else 'Sin asignar',
                'ciudad_base': zona.municipio_base_vendedor.nombre if zona.municipio_base_vendedor else 'Sin configurar',
                'tipo_vehiculo': zona.tipo_vehiculo_comercial,
                'frecuencia': zona.get_frecuencia_display(),
                'requiere_pernocta': zona.requiere_pernocta,
                'noches_pernocta': zona.noches_pernocta,
                'combustible_mensual': float(resultado['combustible_mensual']),
                'pernocta_mensual': float(resultado['pernocta_mensual']),
                'total_mensual': float(resultado['total_mensual']),
                'detalle': resultado['detalle']
            })

            total_combustible += float(resultado['combustible_mensual'])
            total_pernocta += float(resultado['pernocta_mensual'])

        return {
            'marca_id': marca_id,
            'marca_nombre': marca.nombre,
            'escenario_id': escenario_id,
            'escenario_nombre': escenario.nombre,
            'total_combustible_mensual': total_combustible,
            'total_pernocta_mensual': total_pernocta,
            'total_mensual': total_combustible + total_pernocta,
            'total_anual': (total_combustible + total_pernocta) * 12,
            'zonas': detalle_zonas
        }

    except Exception as e:
        logger.error(f"Error obteniendo detalle de lejanías comerciales: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/lejanias/logistica")
def obtener_detalle_lejanias_logistica(
    escenario_id: int,
    marca_id: str
) -> Dict[str, Any]:
    """
    Obtiene el detalle de lejanías logísticas por ruta/vehículo.

    Args:
        escenario_id: ID del escenario
        marca_id: ID de la marca

    Returns:
        Detalle de lejanías logísticas por ruta (vehículo/tercero)
    """
    try:
        from core.models import Escenario, Marca, RutaLogistica
        from core.calculator_lejanias import CalculadoraLejanias

        # Obtener escenario y marca
        escenario = Escenario.objects.get(pk=escenario_id)
        marca = Marca.objects.get(marca_id=marca_id)

        # Inicializar calculadora
        calc = CalculadoraLejanias(escenario)

        # Obtener rutas logísticas de la marca
        rutas = RutaLogistica.objects.filter(
            marca=marca,
            escenario=escenario,
            activo=True
        ).prefetch_related('municipios__municipio').select_related('vehiculo')

        # Calcular para cada ruta
        detalle_rutas = []
        total_flete_base = 0.0
        total_combustible = 0.0
        total_peaje = 0.0
        total_pernocta = 0.0

        for ruta in rutas:
            resultado = calc.calcular_lejania_logistica_ruta(ruta)

            detalle_rutas.append({
                'ruta_id': ruta.id,
                'ruta_nombre': ruta.nombre,
                'vehiculo': str(ruta.vehiculo) if ruta.vehiculo else None,
                'vehiculo_id': ruta.vehiculo.id if ruta.vehiculo else None,
                'esquema': ruta.vehiculo.esquema if ruta.vehiculo else None,
                'tipo_vehiculo': ruta.vehiculo.tipo_vehiculo if ruta.vehiculo else None,
                'frecuencia': ruta.get_frecuencia_display(),
                'flete_base_mensual': float(resultado['flete_base_mensual']),
                'combustible_mensual': float(resultado['combustible_mensual']),
                'peaje_mensual': float(resultado['peaje_mensual']),
                'pernocta_mensual': float(resultado['pernocta_mensual']),
                'total_mensual': float(resultado['total_mensual']),
                'detalle': resultado['detalle']
            })

            total_flete_base += float(resultado['flete_base_mensual'])
            total_combustible += float(resultado['combustible_mensual'])
            total_peaje += float(resultado['peaje_mensual'])
            total_pernocta += float(resultado['pernocta_mensual'])

        total_mensual = total_flete_base + total_combustible + total_peaje + total_pernocta

        return {
            'marca_id': marca_id,
            'marca_nombre': marca.nombre,
            'escenario_id': escenario_id,
            'escenario_nombre': escenario.nombre,
            'total_flete_base_mensual': total_flete_base,
            'total_combustible_mensual': total_combustible,
            'total_peaje_mensual': total_peaje,
            'total_pernocta_mensual': total_pernocta,
            'total_mensual': total_mensual,
            'total_anual': total_mensual * 12,
            'rutas': detalle_rutas
        }

    except Exception as e:
        logger.error(f"Error obteniendo detalle de lejanías logísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/marcas/{marca_id}/comercial")
def obtener_datos_comerciales(marca_id: str) -> Dict[str, Any]:
    """
    Obtiene los datos comerciales de una marca (para debug).

    Args:
        marca_id: ID de la marca

    Returns:
        Datos comerciales de la marca
    """
    try:
        loader = get_loader()
        datos = loader.cargar_marca_comercial(marca_id)
        return datos
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Marca no encontrada: {marca_id}")
    except Exception as e:
        logger.error(f"Error obteniendo datos comerciales: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/marcas/{marca_id}/ventas")
def obtener_datos_ventas(marca_id: str) -> Dict[str, Any]:
    """
    Obtiene las proyecciones de ventas de una marca.

    Args:
        marca_id: ID de la marca

    Returns:
        Datos de ventas mensuales y resumen anual
    """
    try:
        loader = get_loader()
        datos = loader.cargar_marca_ventas(marca_id)
        return datos
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Marca no encontrada: {marca_id}")
    except Exception as e:
        logger.error(f"Error obteniendo datos de ventas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def serializar_resultado(resultado) -> Dict[str, Any]:
    """
    Serializa el objeto ResultadoSimulacion a un diccionario JSON-compatible.

    Args:
        resultado: Objeto ResultadoSimulacion

    Returns:
        Diccionario con los datos de la simulación
    """
    consolidado = resultado.consolidado

    return {
        'consolidado': {
            'total_ventas_brutas_mensuales': float(consolidado.get('total_ventas_brutas_mensuales', consolidado.get('total_ventas_mensuales', 0))),
            'total_ventas_netas_mensuales': float(consolidado.get('total_ventas_netas_mensuales', consolidado.get('total_ventas_mensuales', 0))),
            'total_descuentos_mensuales': float(consolidado.get('total_descuentos_mensuales', 0)),
            'total_ventas_anuales': float(consolidado['total_ventas_anuales']),
            'total_costos_mensuales': float(consolidado['total_costos_mensuales']),
            'total_costos_anuales': float(consolidado['total_costos_anuales']),
            'margen_consolidado': float(consolidado['margen_consolidado']),
            'porcentaje_descuento_promedio': float(consolidado.get('porcentaje_descuento_promedio', 0)),
            'total_empleados': int(consolidado['total_empleados']),
            'costo_comercial_total': float(consolidado['costo_comercial_total']),
            'costo_logistico_total': float(consolidado['costo_logistico_total']),
            'costo_administrativo_total': float(consolidado['costo_administrativo_total']),
        },
        'marcas': [
            {
                'marca_id': m.marca_id,
                'nombre': m.nombre,
                'ventas_mensuales': float(m.ventas_mensuales),
                'ventas_netas_mensuales': float(m.ventas_netas_mensuales) if m.ventas_netas_mensuales > 0 else float(m.ventas_mensuales),
                'descuento_pie_factura': float(m.descuento_pie_factura),
                'rebate': float(m.rebate),
                'descuento_financiero': float(m.descuento_financiero),
                'porcentaje_descuento_total': float(m.porcentaje_descuento_total),
                'costo_total': float(m.costo_total),
                'costo_comercial': float(m.costo_comercial),
                'costo_logistico': float(m.costo_logistico),
                'costo_administrativo': float(m.costo_administrativo),
                'lejania_comercial': float(m.lejania_comercial),
                'lejania_logistica': float(m.lejania_logistica),
                'margen_porcentaje': float(m.margen_porcentaje),
                'total_empleados': int(m.total_empleados),
                'empleados_comerciales': int(m.empleados_comerciales),
                'empleados_logisticos': int(m.empleados_logisticos),
                'rubros_individuales': [
                    serializar_rubro(r) for r in m.rubros_individuales
                ],
                'rubros_compartidos_asignados': [
                    serializar_rubro(r) for r in m.rubros_compartidos_asignados
                ],
            }
            for m in resultado.marcas
        ],
        'rubros_compartidos': [
            serializar_rubro(r) for r in resultado.rubros_compartidos
        ],
        'metadata': resultado.metadata
    }


def serializar_rubro(rubro) -> Dict[str, Any]:
    """Serializa un objeto Rubro a diccionario"""
    rubro_dict = {
        'id': rubro.id,
        'nombre': rubro.nombre,
        'categoria': rubro.categoria,
        'tipo': rubro.tipo,
        'valor_total': float(rubro.valor_total),
    }

    # Agregar campos opcionales si existen
    if hasattr(rubro, 'cantidad'):
        rubro_dict['cantidad'] = rubro.cantidad
    if hasattr(rubro, 'salario_base'):
        rubro_dict['salario_base'] = float(rubro.salario_base)
    if hasattr(rubro, 'valor_unitario'):
        rubro_dict['valor_unitario'] = float(rubro.valor_unitario)
    if hasattr(rubro, 'tipo_vehiculo'):
        rubro_dict['tipo_vehiculo'] = rubro.tipo_vehiculo
    if hasattr(rubro, 'esquema'):
        rubro_dict['esquema'] = rubro.esquema
    if hasattr(rubro, 'criterio_prorrateo'):
        rubro_dict['criterio_prorrateo'] = rubro.criterio_prorrateo.value if rubro.criterio_prorrateo else None

    return rubro_dict


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
