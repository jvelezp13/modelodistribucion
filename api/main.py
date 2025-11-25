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
