"""
FastAPI Backend para Sistema de Distribución Multimarcas

Expone endpoints REST para consumir el simulador existente.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
import os
from pathlib import Path
import logging


# Modelos Pydantic para request bodies
class SimulacionRequest(BaseModel):
    marcas_seleccionadas: List[str]
    escenario_id: Optional[int] = None
    operacion_ids: Optional[List[int]] = None

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

# ============================================================================
# CONFIGURACIÓN SEGURA DE CORS
# ============================================================================
def get_allowed_origins() -> List[str]:
    """
    Obtiene orígenes permitidos desde variables de entorno.

    En desarrollo: localhost:3000, localhost:8000
    En producción: dominios específicos configurados en CORS_ALLOWED_ORIGINS

    Returns:
        Lista de orígenes permitidos
    """
    origins_str = os.environ.get(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:3000,http://localhost:8000'  # Solo para desarrollo
    )
    origins = [origin.strip() for origin in origins_str.split(',')]

    # Advertencia si CORS está abierto
    if "*" in origins:
        logger.warning(
            "⚠️  CORS configurado con wildcard (*). "
            "Esto es INSEGURO para producción. "
            "Configure CORS_ALLOWED_ORIGINS en variables de entorno."
        )

    logger.info(f"🔒 CORS configurado con orígenes: {origins}")
    return origins


# Aplicar middleware con configuración segura
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    max_age=600,  # Cache preflight por 10 minutos
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
def ejecutar_simulacion(request: SimulacionRequest) -> Dict[str, Any]:
    """
    Ejecuta la simulación para las marcas seleccionadas.

    Request body:
        - marcas_seleccionadas: Lista de IDs de marcas a simular
        - escenario_id: ID del escenario (opcional)
        - operacion_ids: Lista de IDs de operaciones para filtrar (opcional)

    Returns:
        Resultado de la simulación serializado con desglose mensual de ventas
        y cálculo de ICA por operación
    """
    try:
        marcas_seleccionadas = request.marcas_seleccionadas
        escenario_id = request.escenario_id
        operacion_ids = request.operacion_ids

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

        # Agregar desglose mensual de ventas desde ProyeccionVentasConfig
        # Si hay operacion_ids, aplicar las participaciones de esas operaciones
        if escenario_id:
            ventas_mensuales_por_marca = obtener_ventas_mensuales_por_marca(
                escenario_id, marcas_seleccionadas, operacion_ids
            )
            # Agregar a cada marca su desglose mensual
            for marca_data in resultado_dict['marcas']:
                marca_id = marca_data['marca_id']
                if marca_id in ventas_mensuales_por_marca:
                    marca_data['ventas_mensuales_desglose'] = ventas_mensuales_por_marca[marca_id]
                else:
                    marca_data['ventas_mensuales_desglose'] = {}

        # Agregar configuración de descuentos por marca
        config_descuentos = obtener_configuracion_descuentos_por_marca(marcas_seleccionadas)
        for marca_data in resultado_dict['marcas']:
            marca_id = marca_data['marca_id']
            if marca_id in config_descuentos:
                marca_data['configuracion_descuentos'] = config_descuentos[marca_id]
            else:
                marca_data['configuracion_descuentos'] = {
                    'tiene_configuracion': False,
                    'descuento_pie_factura_ponderado': 0,
                    'tramos': [],
                    'porcentaje_rebate': 0,
                    'aplica_descuento_financiero': False,
                    'porcentaje_descuento_financiero': 0,
                    'aplica_cesantia_comercial': False,
                }

        # Agregar tasa ICA y desglose por operación
        ica_resultado = calcular_ica_por_operaciones(
            marcas_seleccionadas, escenario_id, operacion_ids
        )
        for marca_data in resultado_dict['marcas']:
            marca_id = marca_data['marca_id']
            marca_ica = ica_resultado.get(marca_id, {})
            marca_data['tasa_ica'] = marca_ica.get('tasa_ponderada', 0.0)
            marca_data['ica_por_operacion'] = marca_ica.get('por_operacion', [])
            marca_data['ica_total'] = marca_ica.get('ica_total', 0.0)

        # Agregar operaciones filtradas al resultado
        resultado_dict['operaciones_filtradas'] = operacion_ids or []

        logger.info(f"Simulación completada exitosamente")
        return resultado_dict

    except Exception as e:
        logger.error(f"Error ejecutando simulación: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def obtener_ventas_mensuales_por_marca(
    escenario_id: int,
    marcas_ids: List[str],
    operacion_ids: Optional[List[int]] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Obtiene el desglose mensual de ventas, CMV y margen para cada marca.

    Si se especifican operacion_ids, aplica las participaciones de esas operaciones
    para obtener las ventas filtradas. Si no, devuelve las ventas totales de la marca.

    Args:
        escenario_id: ID del escenario
        marcas_ids: Lista de marca_id
        operacion_ids: Lista opcional de IDs de operaciones para filtrar

    Returns:
        Dict con marca_id como key y dict con ventas, cmv, margen_lista y tipo como value
    """
    try:
        from core.models import Escenario, Marca, ProyeccionVentasConfig, MarcaOperacion
        from decimal import Decimal

        escenario = Escenario.objects.get(pk=escenario_id)
        resultado = {}

        for marca_id in marcas_ids:
            try:
                marca = Marca.objects.get(marca_id=marca_id)
                config = ProyeccionVentasConfig.objects.get(
                    marca=marca,
                    escenario=escenario,
                    anio=escenario.anio
                )
                ventas_totales = config.calcular_ventas_mensuales()

                if operacion_ids:
                    # Calcular ventas aplicando participación de las operaciones seleccionadas
                    marcas_op = MarcaOperacion.objects.filter(
                        marca=marca,
                        operacion__escenario=escenario,
                        operacion_id__in=operacion_ids,
                        activo=True
                    )

                    # Sumar participaciones (cada operación tiene su % de la marca)
                    participacion_total = sum(
                        mo.participacion_ventas for mo in marcas_op
                    ) / Decimal('100')  # Convertir de % a decimal

                    # Aplicar participación a cada mes
                    ventas_filtradas = {}
                    for mes, venta in ventas_totales.items():
                        ventas_filtradas[mes] = float(Decimal(str(venta)) * participacion_total)

                    resultado[marca_id] = {
                        'ventas': ventas_filtradas,
                    }
                else:
                    # Sin filtro de operaciones, devolver ventas totales
                    resultado[marca_id] = {
                        'ventas': {k: float(v) for k, v in ventas_totales.items()},
                    }

            except (Marca.DoesNotExist, ProyeccionVentasConfig.DoesNotExist):
                resultado[marca_id] = {
                    'ventas': {},
                }

        return resultado

    except Exception as e:
        logger.warning(f"Error obteniendo ventas mensuales: {e}")
        return {}


def obtener_configuracion_descuentos_por_marca(
    marcas_ids: List[str]
) -> Dict[str, Dict[str, Any]]:
    """
    Obtiene la configuración de descuentos para cada marca desde ConfiguracionDescuentos.

    Returns:
        Dict con marca_id como key y configuración de descuentos como value
    """
    try:
        from core.models import Marca, ConfiguracionDescuentos

        resultado = {}

        for marca_id in marcas_ids:
            try:
                marca = Marca.objects.get(marca_id=marca_id)
                config = ConfiguracionDescuentos.objects.prefetch_related('tramos').get(
                    marca=marca,
                    activa=True
                )

                # Calcular descuento ponderado de los tramos
                tramos_data = []
                descuento_ponderado = 0.0

                for tramo in config.tramos.all().order_by('orden'):
                    peso = float(tramo.porcentaje_ventas) / 100
                    descuento = float(tramo.porcentaje_descuento) / 100
                    descuento_ponderado += peso * descuento

                    tramos_data.append({
                        'orden': tramo.orden,
                        'porcentaje_ventas': float(tramo.porcentaje_ventas),
                        'porcentaje_descuento': float(tramo.porcentaje_descuento),
                    })

                resultado[marca_id] = {
                    'tiene_configuracion': True,
                    'descuento_pie_factura_ponderado': descuento_ponderado * 100,  # En porcentaje
                    'tramos': tramos_data,
                    'porcentaje_rebate': float(config.porcentaje_rebate),
                    'aplica_descuento_financiero': config.aplica_descuento_financiero,
                    'porcentaje_descuento_financiero': float(config.porcentaje_descuento_financiero),
                    'aplica_cesantia_comercial': config.aplica_cesantia_comercial,
                }

            except (Marca.DoesNotExist, ConfiguracionDescuentos.DoesNotExist):
                resultado[marca_id] = {
                    'tiene_configuracion': False,
                    'descuento_pie_factura_ponderado': 0,
                    'tramos': [],
                    'porcentaje_rebate': 0,
                    'aplica_descuento_financiero': False,
                    'porcentaje_descuento_financiero': 0,
                    'aplica_cesantia_comercial': False,
                }

        return resultado

    except Exception as e:
        logger.warning(f"Error obteniendo configuración de descuentos: {e}")
        return {}


def calcular_ica_por_operaciones(
    marcas_ids: List[str],
    escenario_id: Optional[int] = None,
    operacion_ids: Optional[List[int]] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Calcula el ICA para cada marca basado en las operaciones (filtradas o todas).

    Usa MarcaOperacion.venta_proyectada como fuente de ventas por operación.

    Returns:
        Dict con marca_id como key y:
        - tasa_ponderada: Tasa ICA ponderada (decimal 0-1)
        - por_operacion: Lista de {operacion_id, operacion_nombre, venta, tasa_ica, ica_calculado}
        - ica_total: Suma total de ICA
        - venta_total: Suma total de ventas
    """
    try:
        from core.models import Marca, MarcaOperacion, Operacion, Escenario
        from decimal import Decimal

        resultado = {}

        # Obtener escenario si se especificó
        escenario = None
        if escenario_id:
            try:
                escenario = Escenario.objects.get(pk=escenario_id)
            except Escenario.DoesNotExist:
                pass

        for marca_id in marcas_ids:
            try:
                marca = Marca.objects.get(marca_id=marca_id)

                # Filtro base por marca
                mo_qs = MarcaOperacion.objects.filter(
                    marca=marca,
                    activo=True
                ).select_related('operacion')

                # Filtrar por escenario si se especificó
                if escenario:
                    mo_qs = mo_qs.filter(operacion__escenario=escenario)

                # Filtrar por operaciones si se especificaron
                if operacion_ids:
                    mo_qs = mo_qs.filter(operacion_id__in=operacion_ids)

                if not mo_qs.exists():
                    resultado[marca_id] = {
                        'tasa_ponderada': 0.0,
                        'por_operacion': [],
                        'ica_total': 0.0,
                        'venta_total': 0.0,
                    }
                    continue

                # Calcular ICA por operación
                por_operacion = []
                ica_total = Decimal('0')
                venta_total = Decimal('0')

                for mo in mo_qs:
                    venta = mo.venta_proyectada or Decimal('0')
                    tasa_ica = mo.operacion.tasa_ica or Decimal('0')  # Ya en porcentaje 0-100
                    ica = venta * (tasa_ica / Decimal('100'))

                    por_operacion.append({
                        'operacion_id': mo.operacion.id,
                        'operacion_nombre': mo.operacion.nombre,
                        'operacion_codigo': mo.operacion.codigo,
                        'venta_proyectada': float(venta),
                        'tasa_ica': float(tasa_ica),  # Porcentaje 0-100
                        'ica_calculado': float(ica),
                    })

                    ica_total += ica
                    venta_total += venta

                # Calcular tasa ponderada (como decimal 0-1 para compatibilidad)
                tasa_ponderada = Decimal('0')
                if venta_total > 0:
                    tasa_ponderada = ica_total / venta_total

                resultado[marca_id] = {
                    'tasa_ponderada': float(tasa_ponderada),
                    'por_operacion': por_operacion,
                    'ica_total': float(ica_total),
                    'venta_total': float(venta_total),
                }

            except Marca.DoesNotExist:
                resultado[marca_id] = {
                    'tasa_ponderada': 0.0,
                    'por_operacion': [],
                    'ica_total': 0.0,
                    'venta_total': 0.0,
                }

        return resultado

    except Exception as e:
        logger.warning(f"Error calculando ICA por operaciones: {e}")
        return {}


def obtener_tasa_ica_ponderada_por_marca(
    marcas_ids: List[str],
    escenario_id: Optional[int] = None
) -> Dict[str, float]:
    """
    DEPRECATED: Usar calcular_ica_por_operaciones() que usa MarcaOperacion.venta_proyectada.

    Calcula la tasa ICA ponderada para cada marca basada en las zonas.
    Mantenida para compatibilidad.
    """
    resultado = calcular_ica_por_operaciones(marcas_ids, escenario_id)
    return {marca_id: data.get('tasa_ponderada', 0.0) for marca_id, data in resultado.items()}


@app.get("/api/lejanias/comercial")
def obtener_detalle_lejanias_comercial(
    escenario_id: int,
    marca_id: str,
    operacion_ids: Optional[str] = None
) -> Dict[str, Any]:
    """
    Obtiene el detalle de lejanías comerciales por zona.

    Lee los totales desde GastoComercial (calculados por signals de Django)
    y genera el detalle por zona para visualización en frontend.

    Args:
        escenario_id: ID del escenario
        marca_id: ID de la marca
        operacion_ids: IDs de operaciones separados por coma (opcional, ej: '1,2,3')

    Returns:
        Detalle de lejanías comerciales por zona
    """
    try:
        from core.models import (
            Escenario, Marca, Zona, GastoComercial,
            ConfiguracionLejania, MatrizDesplazamiento
        )
        from decimal import Decimal

        # Obtener escenario y marca
        escenario = Escenario.objects.get(pk=escenario_id)
        marca = Marca.objects.get(marca_id=marca_id)

        # Obtener configuración de lejanías
        try:
            config = ConfiguracionLejania.objects.get(escenario=escenario)
        except ConfiguracionLejania.DoesNotExist:
            config = None

        # Leer totales desde GastoComercial (ya calculados por signals)
        gastos_combustible = GastoComercial.objects.filter(
            escenario=escenario,
            marca=marca,
            tipo='transporte_vendedores',
            nombre__startswith='Combustible Lejanía'
        )
        gastos_pernocta = GastoComercial.objects.filter(
            escenario=escenario,
            marca=marca,
            tipo='viaticos',
            nombre__startswith='Viáticos Pernocta'
        )
        gastos_adicionales = GastoComercial.objects.filter(
            escenario=escenario,
            marca=marca,
            tipo='transporte_vendedores',
            nombre__startswith='Mant/Deprec/Llantas'
        )
        gastos_comite = GastoComercial.objects.filter(
            escenario=escenario,
            marca=marca,
            tipo='transporte_vendedores',
            nombre__startswith='Comité Comercial'
        ).select_related('zona', 'zona__vendedor', 'zona__municipio_base_vendedor')

        # Parsear operacion_ids si se proporcionan
        operacion_ids_list = None
        if operacion_ids:
            try:
                operacion_ids_list = [int(x.strip()) for x in operacion_ids.split(',') if x.strip()]
            except ValueError:
                pass

        # Obtener zonas de la marca
        zonas = Zona.objects.filter(
            marca=marca,
            escenario=escenario,
            activo=True
        ).prefetch_related('municipios__municipio').select_related('vendedor', 'municipio_base_vendedor', 'operacion')

        # Filtrar por operaciones seleccionadas si se especifican
        if operacion_ids_list:
            zonas = zonas.filter(operacion_id__in=operacion_ids_list)

        # Construir detalle por zona
        detalle_zonas = []
        total_combustible = 0.0
        total_costos_adicionales = 0.0
        total_pernocta = 0.0
        total_km = 0.0

        for zona in zonas:
            # Buscar gastos de esta zona específica
            combustible_zona = gastos_combustible.filter(
                nombre=f'Combustible Lejanía - {zona.nombre}'
            ).first()
            adicionales_zona = gastos_adicionales.filter(
                nombre=f'Mant/Deprec/Llantas - {zona.nombre}'
            ).first()
            pernocta_zona = gastos_pernocta.filter(
                nombre=f'Viáticos Pernocta - {zona.nombre}'
            ).first()

            combustible_mensual = float(combustible_zona.valor_mensual) if combustible_zona else 0.0
            costos_adicionales_mensual = float(adicionales_zona.valor_mensual) if adicionales_zona else 0.0
            pernocta_mensual = float(pernocta_zona.valor_mensual) if pernocta_zona else 0.0

            # Generar detalle de municipios para visualización
            detalle_municipios = []
            base_vendedor = zona.municipio_base_vendedor or (config.municipio_bodega if config else None)

            if base_vendedor and config:
                consumo_km_galon = float(config.consumo_galon_km_moto if zona.tipo_vehiculo_comercial == 'MOTO' else config.consumo_galon_km_automovil)
                costo_adicional_km = float(config.costo_adicional_km_moto if zona.tipo_vehiculo_comercial == 'MOTO' else config.costo_adicional_km_automovil)
                precio_galon = float(config.precio_galon_gasolina)
                umbral = float(config.umbral_lejania_comercial_km)

                for zona_mun in zona.municipios.all():
                    municipio = zona_mun.municipio

                    # Si es visita local (mismo municipio que la base), no hay lejanía
                    if municipio.id == base_vendedor.id:
                        detalle_municipios.append({
                            'municipio': municipio.nombre,
                            'municipio_id': municipio.id,
                            'distancia_km': 0,
                            'distancia_efectiva_km': 0,
                            'visitas_por_periodo': zona_mun.visitas_por_periodo,
                            'visitas_mensuales': float(zona_mun.visitas_mensuales()),
                            'combustible_por_visita': 0,
                            'combustible_mensual': 0,
                            'costos_adicionales_mensual': 0,
                            'es_visita_local': True,
                        })
                        continue

                    # Visita a otro municipio: buscar en matriz
                    try:
                        matriz = MatrizDesplazamiento.objects.get(
                            origen_id=base_vendedor.id,
                            destino_id=municipio.id
                        )
                        distancia_km = float(matriz.distancia_km)
                    except MatrizDesplazamiento.DoesNotExist:
                        distancia_km = 0

                    distancia_efectiva = max(0, distancia_km - umbral)
                    visitas_mensuales = float(zona_mun.visitas_mensuales())

                    # Calcular combustible y costos adicionales por municipio
                    combustible_por_visita = 0.0
                    combustible_municipio = 0.0
                    costos_adicionales_municipio = 0.0
                    if distancia_efectiva > 0:
                        distancia_ida_vuelta = distancia_efectiva * 2
                        # Combustible
                        if consumo_km_galon > 0:
                            galones_por_visita = distancia_ida_vuelta / consumo_km_galon
                            combustible_por_visita = galones_por_visita * precio_galon
                            combustible_municipio = combustible_por_visita * visitas_mensuales
                        # Costos adicionales (mant, deprec, llantas)
                        costo_adicional_visita = distancia_ida_vuelta * costo_adicional_km
                        costos_adicionales_municipio = costo_adicional_visita * visitas_mensuales

                    detalle_municipios.append({
                        'municipio': municipio.nombre,
                        'municipio_id': municipio.id,
                        'distancia_km': distancia_km,
                        'distancia_efectiva_km': distancia_efectiva,
                        'visitas_por_periodo': zona_mun.visitas_por_periodo,
                        'visitas_mensuales': visitas_mensuales,
                        'combustible_por_visita': combustible_por_visita,
                        'combustible_mensual': combustible_municipio,
                        'costos_adicionales_mensual': costos_adicionales_municipio,
                        'es_visita_local': False,
                    })

            # Calcular km totales de la zona (ida y vuelta × visitas mensuales)
            km_zona_mensual = sum(
                m['distancia_km'] * 2 * m['visitas_mensuales']
                for m in detalle_municipios
            )

            # Construir detalle de pernocta si aplica
            detalle_pernocta = None
            if zona.requiere_pernocta and zona.noches_pernocta > 0 and config:
                desayuno = float(config.desayuno_comercial)
                almuerzo = float(config.almuerzo_comercial)
                cena = float(config.cena_comercial)
                alojamiento = float(config.alojamiento_comercial)
                gasto_por_noche = desayuno + almuerzo + cena + alojamiento
                periodos_mes = float(zona.periodos_por_mes())

                detalle_pernocta = {
                    'noches': zona.noches_pernocta,
                    'desayuno': desayuno,
                    'almuerzo': almuerzo,
                    'cena': cena,
                    'alojamiento': alojamiento,
                    'gasto_por_noche': gasto_por_noche,
                    'periodos_mes': periodos_mes,
                    'total_mensual': gasto_por_noche * zona.noches_pernocta * periodos_mes,
                }

            detalle_zonas.append({
                'zona_id': zona.id,
                'zona_nombre': zona.nombre,
                'vendedor': zona.vendedor.nombre if zona.vendedor else 'Sin asignar',
                'ciudad_base': base_vendedor.nombre if base_vendedor else 'Sin configurar',
                'tipo_vehiculo': zona.tipo_vehiculo_comercial,
                'frecuencia': zona.get_frecuencia_display(),
                'requiere_pernocta': zona.requiere_pernocta,
                'noches_pernocta': zona.noches_pernocta,
                'km_mensual': km_zona_mensual,
                'combustible_mensual': combustible_mensual,
                'costos_adicionales_mensual': costos_adicionales_mensual,
                'pernocta_mensual': pernocta_mensual,
                'total_mensual': combustible_mensual + costos_adicionales_mensual + pernocta_mensual,
                'detalle': {
                    'base': base_vendedor.nombre if base_vendedor else None,
                    'tipo_vehiculo': zona.tipo_vehiculo_comercial,
                    'costo_adicional_km': costo_adicional_km if base_vendedor and config else 0,
                    'municipios': detalle_municipios,
                    'pernocta': detalle_pernocta,
                }
            })

            total_combustible += combustible_mensual
            total_costos_adicionales += costos_adicionales_mensual
            total_pernocta += pernocta_mensual
            total_km += km_zona_mensual

        # Ordenar zonas de mayor a menor por total_mensual
        detalle_zonas.sort(key=lambda x: x['total_mensual'], reverse=True)

        # Construir datos del comité comercial (si está configurado)
        comite_data = None
        total_comite = 0.0
        if config and config.tiene_comite_comercial and config.municipio_comite:
            frecuencia_map = {'SEMANAL': 4, 'TRISEMANAL': 3, 'QUINCENAL': 2, 'MENSUAL': 1}
            viajes_mes = frecuencia_map.get(config.frecuencia_comite, 1)
            umbral = float(config.umbral_lejania_comercial_km)

            # Filtrar gastos de comité por operaciones si aplica
            gastos_comite_filtrados = gastos_comite
            if operacion_ids_list:
                gastos_comite_filtrados = gastos_comite.filter(zona__operacion_id__in=operacion_ids_list)

            # Agrupar gastos por zona (ahora hay 2 registros por zona: Combustible y Mant/Dep/Llan)
            gastos_por_zona = {}
            for gasto in gastos_comite_filtrados:
                zona = gasto.zona
                if not zona:
                    continue

                if zona.id not in gastos_por_zona:
                    gastos_por_zona[zona.id] = {
                        'zona': zona,
                        'combustible': 0.0,
                        'costos_adicionales': 0.0,
                    }

                # Identificar tipo de gasto por el nombre
                if '(Combustible)' in gasto.nombre:
                    gastos_por_zona[zona.id]['combustible'] = float(gasto.valor_mensual)
                elif '(Mant/Dep/Llan)' in gasto.nombre:
                    gastos_por_zona[zona.id]['costos_adicionales'] = float(gasto.valor_mensual)
                else:
                    # Registro con nomenclatura antigua - asignar a combustible por compatibilidad
                    gastos_por_zona[zona.id]['combustible'] = float(gasto.valor_mensual)

            detalle_comite = []
            for zona_id, datos in gastos_por_zona.items():
                zona = datos['zona']

                # Calcular distancia al comité para mostrar
                base_vendedor = zona.municipio_base_vendedor or (config.municipio_bodega if config else None)
                distancia_km = 0.0
                if base_vendedor:
                    try:
                        matriz = MatrizDesplazamiento.objects.get(
                            origen_id=base_vendedor.id,
                            destino_id=config.municipio_comite.id
                        )
                        distancia_km = float(matriz.distancia_km)
                    except MatrizDesplazamiento.DoesNotExist:
                        pass

                detalle_comite.append({
                    'zona_id': zona.id,
                    'zona_nombre': zona.nombre,
                    'vendedor': zona.vendedor.nombre if zona.vendedor else 'Sin asignar',
                    'ciudad_base': base_vendedor.nombre if base_vendedor else 'Sin configurar',
                    'tipo_vehiculo': zona.tipo_vehiculo_comercial,
                    'distancia_km': distancia_km,
                    'viajes_mes': viajes_mes,
                    'combustible_mensual': datos['combustible'],
                    'costos_adicionales_mensual': datos['costos_adicionales'],
                    'total_mensual': datos['combustible'] + datos['costos_adicionales'],
                })

            total_comite = sum(d['total_mensual'] for d in detalle_comite)

            if detalle_comite:
                comite_data = {
                    'municipio': config.municipio_comite.nombre,
                    'frecuencia': config.get_frecuencia_comite_display(),
                    'viajes_mes': viajes_mes,
                    'umbral_km': umbral,
                    'total_mensual': total_comite,
                    'detalle_por_zona': sorted(detalle_comite, key=lambda x: x['total_mensual'], reverse=True),
                }

        total_mensual = total_combustible + total_costos_adicionales + total_pernocta + total_comite
        return {
            'marca_id': marca_id,
            'marca_nombre': marca.nombre,
            'escenario_id': escenario_id,
            'escenario_nombre': escenario.nombre,
            'total_km_mensual': total_km,
            'total_combustible_mensual': total_combustible,
            'total_costos_adicionales_mensual': total_costos_adicionales,
            'total_pernocta_mensual': total_pernocta,
            'total_comite_mensual': total_comite,
            'total_mensual': total_mensual,
            'total_anual': total_mensual * 12,
            'zonas': detalle_zonas,
            'comite_comercial': comite_data,
        }

    except Escenario.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Escenario no encontrado: {escenario_id}")
    except Marca.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Marca no encontrada: {marca_id}")
    except Exception as e:
        logger.error(f"Error obteniendo detalle de lejanías comerciales: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/lejanias/logistica")
def obtener_detalle_lejanias_logistica(
    escenario_id: int,
    marca_id: str,
    operacion_ids: Optional[str] = None
) -> Dict[str, Any]:
    """
    Obtiene el detalle de lejanías logísticas por ruta/vehículo.

    Lee los totales desde GastoLogistico (calculados por signals de Django)
    y genera el detalle por ruta para visualización en frontend.

    Args:
        escenario_id: ID del escenario
        marca_id: ID de la marca
        operacion_ids: IDs de operaciones separados por coma (opcional, filtrado indirecto por municipios)

    Returns:
        Detalle de lejanías logísticas por ruta (vehículo/tercero)
    """
    try:
        from core.models import (
            Escenario, Marca, RutaLogistica, GastoLogistico,
            ConfiguracionLejania, MatrizDesplazamiento, Zona, ZonaMunicipio
        )
        from decimal import Decimal
        from django.db.models import Sum

        # Obtener escenario y marca
        escenario = Escenario.objects.get(pk=escenario_id)
        marca = Marca.objects.get(marca_id=marca_id)

        # Parsear operacion_ids si se proporcionan
        operacion_ids_list = None
        if operacion_ids:
            try:
                operacion_ids_list = [int(x.strip()) for x in operacion_ids.split(',') if x.strip()]
            except ValueError:
                pass

        # Filtrar municipios por operaciones (para filtrado indirecto de rutas)
        municipios_operaciones = None
        if operacion_ids_list:
            # Obtener zonas de las operaciones seleccionadas
            zonas_operaciones = Zona.objects.filter(
                escenario=escenario,
                marca=marca,
                operacion_id__in=operacion_ids_list,
                activo=True
            ).values_list('id', flat=True)
            # Obtener municipios de esas zonas
            municipios_operaciones = set(
                ZonaMunicipio.objects.filter(zona_id__in=zonas_operaciones)
                .values_list('municipio_id', flat=True)
            )

        # Obtener configuración de lejanías
        try:
            config = ConfiguracionLejania.objects.get(escenario=escenario)
        except ConfiguracionLejania.DoesNotExist:
            config = None

        # Leer gastos desde GastoLogistico (ya calculados por signals)
        gastos_combustible = GastoLogistico.objects.filter(
            escenario=escenario,
            marca=marca,
            tipo='combustible',
            nombre__startswith='Combustible -'
        )
        gastos_peajes = GastoLogistico.objects.filter(
            escenario=escenario,
            marca=marca,
            tipo='peajes',
            nombre__startswith='Peajes -'
        )
        gastos_viaticos = GastoLogistico.objects.filter(
            escenario=escenario,
            marca=marca,
            tipo='otros',
            nombre__startswith='Viáticos Ruta -'
        )
        gastos_flete = GastoLogistico.objects.filter(
            escenario=escenario,
            marca=marca,
            tipo='otros',
            nombre__startswith='Flete Base Tercero -'
        )

        # Obtener rutas logísticas de la marca
        rutas = RutaLogistica.objects.filter(
            marca=marca,
            escenario=escenario,
            activo=True
        ).prefetch_related('municipios__municipio').select_related('vehiculo')

        # Filtrar rutas por municipios de operaciones seleccionadas (filtrado indirecto)
        if municipios_operaciones is not None:
            # Una ruta se incluye si atiende al menos un municipio de las operaciones
            rutas_filtradas = []
            for ruta in rutas:
                muni_ids_ruta = set(rm.municipio_id for rm in ruta.municipios.all())
                if muni_ids_ruta & municipios_operaciones:  # Intersección
                    rutas_filtradas.append(ruta)
            rutas = rutas_filtradas

        # Construir detalle por ruta
        detalle_rutas = []
        total_flete_base = 0.0
        total_combustible = 0.0
        total_peaje = 0.0
        total_pernocta = 0.0
        total_pernocta_conductor = 0.0
        total_pernocta_auxiliar = 0.0
        total_parqueadero = 0.0
        # Separar auxiliar empresa (siempre paga la empresa, sin importar el esquema)
        total_auxiliar_empresa = 0.0

        for ruta in rutas:
            # Buscar gastos de esta ruta específica
            combustible_ruta = gastos_combustible.filter(
                nombre=f'Combustible - {ruta.nombre}'
            ).first()
            peaje_ruta = gastos_peajes.filter(
                nombre=f'Peajes - {ruta.nombre}'
            ).first()
            viaticos_ruta = gastos_viaticos.filter(
                nombre=f'Viáticos Ruta - {ruta.nombre}'
            ).first()
            flete_ruta = gastos_flete.filter(
                nombre=f'Flete Base Tercero - {ruta.nombre}'
            ).first()

            combustible_mensual = float(combustible_ruta.valor_mensual) if combustible_ruta else 0.0
            peaje_mensual = float(peaje_ruta.valor_mensual) if peaje_ruta else 0.0
            pernocta_mensual = float(viaticos_ruta.valor_mensual) if viaticos_ruta else 0.0
            flete_base_mensual = float(flete_ruta.valor_mensual) if flete_ruta else 0.0

            # Generar detalle de tramos para visualización
            detalle_tramos = []
            detalle_municipios = []
            bodega = config.municipio_bodega if config else None

            if bodega and ruta.vehiculo:
                municipios_ordenados = list(ruta.municipios.all().order_by('orden_visita'))
                puntos_circuito = [bodega] + [rm.municipio for rm in municipios_ordenados] + [bodega]

                # Calcular tramos
                for i in range(len(puntos_circuito) - 1):
                    origen = puntos_circuito[i]
                    destino = puntos_circuito[i + 1]
                    try:
                        matriz = MatrizDesplazamiento.objects.get(
                            origen_id=origen.id,
                            destino_id=destino.id
                        )
                        distancia_km = float(matriz.distancia_km)
                        peaje = float(matriz.peaje_ida or 0)
                    except MatrizDesplazamiento.DoesNotExist:
                        distancia_km = 0
                        peaje = 0

                    detalle_tramos.append({
                        'origen': origen.nombre,
                        'destino': destino.nombre,
                        'distancia_km': distancia_km,
                        'peaje': peaje,
                    })

                # Detalle municipios
                for ruta_mun in municipios_ordenados:
                    detalle_municipios.append({
                        'orden': ruta_mun.orden_visita,
                        'municipio': ruta_mun.municipio.nombre,
                        'municipio_id': ruta_mun.municipio.id,
                        'flete_base': float(ruta_mun.flete_base or 0),
                    })

            ruta_total = flete_base_mensual + combustible_mensual + peaje_mensual + pernocta_mensual

            # Calcular distancia total del circuito
            distancia_circuito = sum(t['distancia_km'] for t in detalle_tramos) if detalle_tramos else 0

            # Datos del vehículo
            vehiculo = ruta.vehiculo
            tipo_combustible = vehiculo.tipo_combustible if vehiculo else None
            consumo_galon_km = float(vehiculo.consumo_galon_km) if vehiculo and vehiculo.consumo_galon_km else 0

            # Calcular recorridos mensuales y combustible por recorrido
            recorridos_mensuales = float(ruta.viajes_por_periodo) * 4.33 if ruta.viajes_por_periodo else 0
            combustible_por_recorrido = combustible_mensual / recorridos_mensuales if recorridos_mensuales > 0 else 0
            peaje_por_recorrido = peaje_mensual / recorridos_mensuales if recorridos_mensuales > 0 else 0

            # Calcular componentes de pernocta (conductor, auxiliar, parqueadero)
            pernocta_conductor_mensual = 0.0
            pernocta_auxiliar_mensual = 0.0
            parqueadero_mensual = 0.0
            detalle_pernocta = None

            if ruta.requiere_pernocta and ruta.noches_pernocta > 0 and config:
                # Gasto por noche del conductor
                gasto_conductor_noche = (
                    float(config.desayuno_conductor or 0) +
                    float(config.almuerzo_conductor or 0) +
                    float(config.cena_conductor or 0) +
                    float(config.alojamiento_conductor or 0)
                )

                # Gasto por noche del auxiliar (por cada auxiliar)
                cantidad_auxiliares = vehiculo.cantidad_auxiliares if vehiculo else 1
                gasto_auxiliar_noche = (
                    float(config.desayuno_auxiliar or 0) +
                    float(config.almuerzo_auxiliar or 0) +
                    float(config.cena_auxiliar or 0) +
                    float(config.alojamiento_auxiliar or 0)
                ) * cantidad_auxiliares

                # Parqueadero por noche
                parqueadero_noche = float(config.parqueadero_logistica or 0)

                # Calcular mensuales
                noches_mes = ruta.noches_pernocta * recorridos_mensuales
                pernocta_conductor_mensual = gasto_conductor_noche * noches_mes
                pernocta_auxiliar_mensual = gasto_auxiliar_noche * noches_mes
                parqueadero_mensual = parqueadero_noche * noches_mes

                detalle_pernocta = {
                    'noches': ruta.noches_pernocta,
                    'recorridos_mes': recorridos_mensuales,
                    'noches_mes': noches_mes,
                    'conductor': {
                        'desayuno': float(config.desayuno_conductor or 0),
                        'almuerzo': float(config.almuerzo_conductor or 0),
                        'cena': float(config.cena_conductor or 0),
                        'alojamiento': float(config.alojamiento_conductor or 0),
                        'gasto_por_noche': gasto_conductor_noche,
                    },
                    'auxiliar': {
                        'cantidad': cantidad_auxiliares,
                        'desayuno': float(config.desayuno_auxiliar or 0),
                        'almuerzo': float(config.almuerzo_auxiliar or 0),
                        'cena': float(config.cena_auxiliar or 0),
                        'alojamiento': float(config.alojamiento_auxiliar or 0),
                        'gasto_por_noche': gasto_auxiliar_noche,
                    },
                    'parqueadero': parqueadero_noche,
                }

            detalle_rutas.append({
                'ruta_id': ruta.id,
                'ruta_nombre': ruta.nombre,
                'vehiculo': str(vehiculo) if vehiculo else None,
                'vehiculo_id': vehiculo.id if vehiculo else None,
                'esquema': vehiculo.esquema if vehiculo else None,
                'tipo_vehiculo': vehiculo.tipo_vehiculo if vehiculo else None,
                'tipo_combustible': tipo_combustible,
                'consumo_galon_km': consumo_galon_km,
                'frecuencia': ruta.get_frecuencia_display(),
                'viajes_por_periodo': ruta.viajes_por_periodo,
                'requiere_pernocta': ruta.requiere_pernocta,
                'noches_pernocta': ruta.noches_pernocta,
                'flete_base_mensual': flete_base_mensual,
                'combustible_mensual': combustible_mensual,
                'peaje_mensual': peaje_mensual,
                'pernocta_mensual': pernocta_mensual,
                'pernocta_conductor_mensual': pernocta_conductor_mensual,
                'pernocta_auxiliar_mensual': pernocta_auxiliar_mensual,
                'parqueadero_mensual': parqueadero_mensual,
                'total_mensual': ruta_total,
                'distancia_circuito_km': distancia_circuito,
                'detalle': {
                    'bodega': bodega.nombre if bodega else None,
                    'vehiculo': str(vehiculo) if vehiculo else None,
                    'tipo_combustible': tipo_combustible,
                    'consumo_km_galon': consumo_galon_km,
                    'recorridos_por_periodo': ruta.viajes_por_periodo,
                    'recorridos_mensuales': recorridos_mensuales,
                    'distancia_circuito_km': distancia_circuito,
                    'distancia_efectiva_km': max(0, distancia_circuito - (float(config.umbral_lejania_logistica_km) if config else 60)) if distancia_circuito else 0,
                    'combustible_por_recorrido': combustible_por_recorrido,
                    'peaje_por_recorrido': peaje_por_recorrido,
                    'municipios': detalle_municipios,
                    'tramos': detalle_tramos,
                    'pernocta': detalle_pernocta,
                }
            })

            total_flete_base += flete_base_mensual
            total_combustible += combustible_mensual
            total_peaje += peaje_mensual
            total_pernocta += pernocta_mensual
            total_pernocta_conductor += pernocta_conductor_mensual
            total_pernocta_auxiliar += pernocta_auxiliar_mensual
            total_parqueadero += parqueadero_mensual
            # El auxiliar SIEMPRE lo paga la empresa (sin importar esquema)
            total_auxiliar_empresa += pernocta_auxiliar_mensual

        total_mensual = total_flete_base + total_combustible + total_peaje + total_pernocta

        # Ordenar rutas de mayor a menor por total_mensual
        detalle_rutas.sort(key=lambda x: x['total_mensual'], reverse=True)

        return {
            'marca_id': marca_id,
            'marca_nombre': marca.nombre,
            'escenario_id': escenario_id,
            'escenario_nombre': escenario.nombre,
            'total_flete_base_mensual': total_flete_base,
            'total_combustible_mensual': total_combustible,
            'total_peaje_mensual': total_peaje,
            'total_pernocta_mensual': total_pernocta,
            'total_pernocta_conductor_mensual': total_pernocta_conductor,
            'total_pernocta_auxiliar_mensual': total_pernocta_auxiliar,
            'total_parqueadero_mensual': total_parqueadero,
            'total_auxiliar_empresa_mensual': total_auxiliar_empresa,
            'total_mensual': total_mensual,
            'total_anual': total_mensual * 12,
            'rutas': detalle_rutas
        }

    except Escenario.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Escenario no encontrado: {escenario_id}")
    except Marca.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Marca no encontrada: {marca_id}")
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
def obtener_datos_ventas(
    marca_id: str,
    escenario_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Obtiene las proyecciones de ventas de una marca.

    Args:
        marca_id: ID de la marca
        escenario_id: ID del escenario (opcional)

    Returns:
        Datos de ventas mensuales y resumen anual
    """
    try:
        loader = get_loader(escenario_id=escenario_id)
        datos = loader.cargar_marca_ventas(marca_id)
        return datos
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Marca no encontrada: {marca_id}")
    except Exception as e:
        logger.error(f"Error obteniendo datos de ventas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/marcas/{marca_id}/lista-precios")
def obtener_lista_precios(
    marca_id: str,
    escenario_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Obtiene la lista de precios de una marca con sus proyecciones de demanda.

    Args:
        marca_id: ID de la marca
        escenario_id: ID del escenario (opcional)

    Returns:
        Lista de productos con precios, demanda y resumen
    """
    try:
        from core.models import Marca, Escenario, ProyeccionVentasConfig

        marca = Marca.objects.get(marca_id=marca_id)

        filter_kwargs = {'marca': marca}
        if escenario_id:
            escenario = Escenario.objects.get(pk=escenario_id)
            filter_kwargs['escenario'] = escenario
            filter_kwargs['anio'] = escenario.anio

        config = ProyeccionVentasConfig.objects.filter(
            tipo='lista_precios',
            **filter_kwargs
        ).first()

        if not config:
            return {
                'tipo': None,
                'mensaje': 'No hay configuración de lista de precios para esta marca',
                'productos': [],
                'resumen': None
            }

        productos = []
        for lp in config.lista_precios.filter(activo=True).select_related('producto'):
            prod_data = {
                'id': lp.id,
                'producto_id': lp.producto.id,
                'sku': lp.producto.sku,
                'nombre': lp.producto.nombre,
                'metodo_captura': lp.metodo_captura,
                'precio_compra': float(lp.get_precio_compra_calculado() or 0),
                'precio_venta': float(lp.get_precio_venta_calculado() or 0),
                'margen_lista': float(lp.get_margen_lista() or 0),
            }

            # Agregar demanda si existe
            try:
                demanda = lp.proyeccion_demanda
                prod_data['demanda'] = {
                    'metodo': demanda.metodo_demanda,
                    'unidades_mensuales': demanda.get_unidades_mensuales(),
                    'ventas_mensuales': demanda.get_ventas_mensuales(),
                    'cmv_mensual': demanda.get_cmv_mensual(),
                    'total_unidades': demanda.get_total_unidades_anual(),
                    'total_ventas': demanda.get_total_ventas_anual(),
                    'total_cmv': demanda.get_total_cmv_anual(),
                }
            except AttributeError as e:
                # Demanda no configurada para este producto
                logger.debug(f"Demanda no disponible para producto {lp.producto.nombre}: {e}")
                prod_data['demanda'] = None
            except Exception as e:
                # Error inesperado procesando demanda
                logger.error(f"Error procesando demanda para {lp.producto.nombre}: {e}", exc_info=True)
                prod_data['demanda'] = None

            productos.append(prod_data)

        # Calcular resumen
        venta_anual = config.get_venta_anual()
        cmv_anual = config.get_cmv_anual()
        margen_prom = ((venta_anual - cmv_anual) / venta_anual * 100) if venta_anual > 0 else 0

        return {
            'tipo': 'lista_precios',
            'config_id': config.id,
            'marca_id': marca.marca_id,
            'marca_nombre': marca.nombre,
            'productos': productos,
            'resumen': {
                'total_productos': len(productos),
                'venta_anual': venta_anual,
                'cmv_anual': cmv_anual,
                'margen_lista_promedio': margen_prom,
            }
        }

    except Marca.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Marca no encontrada: {marca_id}")
    except Escenario.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Escenario no encontrado: {escenario_id}")
    except Exception as e:
        logger.error(f"Error obteniendo lista de precios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ventas/proyectadas")
def obtener_ventas_proyectadas(
    escenario_id: int,
    marca_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Obtiene las ventas proyectadas por mes desde ProyeccionVentasConfig.

    Args:
        escenario_id: ID del escenario
        marca_id: ID de la marca (opcional, si no se especifica retorna todas)

    Returns:
        Ventas proyectadas mensuales por marca
    """
    try:
        from core.models import Escenario, Marca, ProyeccionVentasConfig

        escenario = Escenario.objects.get(pk=escenario_id)

        # Filtrar por marca si se especifica
        if marca_id:
            marcas = Marca.objects.filter(marca_id=marca_id, activo=True)
        else:
            marcas = Marca.objects.filter(activo=True)

        resultado = {
            'escenario_id': escenario_id,
            'escenario_nombre': escenario.nombre,
            'anio': escenario.anio,
            'marcas': []
        }

        for marca in marcas:
            try:
                config = ProyeccionVentasConfig.objects.get(
                    marca=marca,
                    escenario=escenario,
                    anio=escenario.anio
                )
                ventas_mensuales = config.calcular_ventas_mensuales()
                total_anual = sum(ventas_mensuales.values())

                # Obtener CMV si es tipo lista_precios
                cmv_mensuales = config.calcular_cmv_mensuales() if config.tipo == 'lista_precios' else {}
                cmv_anual = sum(cmv_mensuales.values()) if cmv_mensuales else 0

                resultado['marcas'].append({
                    'marca_id': marca.marca_id,
                    'marca_nombre': marca.nombre,
                    'tipo': config.tipo,
                    'tipo_display': config.get_tipo_display(),
                    'ventas_mensuales': {k: float(v) for k, v in ventas_mensuales.items()},
                    'cmv_mensuales': {k: float(v) for k, v in cmv_mensuales.items()} if cmv_mensuales else {},
                    'total_anual': float(total_anual),
                    'cmv_anual': float(cmv_anual),
                    'margen_lista': float(total_anual - cmv_anual),
                    'promedio_mensual': float(total_anual / 12) if total_anual > 0 else 0
                })
            except ProyeccionVentasConfig.DoesNotExist:
                resultado['marcas'].append({
                    'marca_id': marca.marca_id,
                    'marca_nombre': marca.nombre,
                    'tipo': None,
                    'tipo_display': 'Sin configurar',
                    'ventas_mensuales': {},
                    'cmv_mensuales': {},
                    'total_anual': 0,
                    'cmv_anual': 0,
                    'margen_lista': 0,
                    'promedio_mensual': 0
                })

        return resultado

    except Escenario.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Escenario no encontrado: {escenario_id}")
    except Exception as e:
        logger.error(f"Error obteniendo ventas proyectadas: {e}")
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
    if hasattr(rubro, 'prestaciones') and rubro.prestaciones:
        rubro_dict['prestaciones'] = float(rubro.prestaciones)
    if hasattr(rubro, 'subsidio_transporte') and rubro.subsidio_transporte:
        rubro_dict['subsidio_transporte'] = float(rubro.subsidio_transporte)
    if hasattr(rubro, 'factor_prestacional') and rubro.factor_prestacional:
        rubro_dict['factor_prestacional'] = float(rubro.factor_prestacional)
    # Auxilios no prestacionales (JSON flexible)
    if hasattr(rubro, 'auxilios_no_prestacionales') and rubro.auxilios_no_prestacionales:
        rubro_dict['auxilios_no_prestacionales'] = {k: float(v) for k, v in rubro.auxilios_no_prestacionales.items()}
        rubro_dict['total_auxilios_no_prestacionales'] = float(rubro.total_auxilios_no_prestacionales)
    # Campo legacy para retrocompatibilidad
    if hasattr(rubro, 'total_auxilios_no_prestacionales'):
        rubro_dict['auxilio_adicional'] = float(rubro.total_auxilios_no_prestacionales)
    if hasattr(rubro, 'valor_unitario'):
        rubro_dict['valor_unitario'] = float(rubro.valor_unitario)
    if hasattr(rubro, 'tipo_vehiculo'):
        rubro_dict['tipo_vehiculo'] = rubro.tipo_vehiculo
    if hasattr(rubro, 'esquema'):
        rubro_dict['esquema'] = rubro.esquema
    if hasattr(rubro, 'criterio_prorrateo'):
        rubro_dict['criterio_prorrateo'] = rubro.criterio_prorrateo.value if rubro.criterio_prorrateo else None

    return rubro_dict


@app.get("/api/impuestos")
def obtener_impuestos(
    tipo: Optional[str] = None,
    activo: bool = True
) -> List[Dict[str, Any]]:
    """
    Obtiene los impuestos configurados.

    Args:
        tipo: Filtrar por tipo (renta, ica, iva, etc.)
        activo: Solo impuestos activos (default True)

    Returns:
        Lista de impuestos con su configuración
    """
    try:
        from core.models import Impuesto

        queryset = Impuesto.objects.all()

        if activo:
            queryset = queryset.filter(activo=True)

        if tipo:
            queryset = queryset.filter(tipo=tipo)

        impuestos = []
        for imp in queryset:
            impuestos.append({
                'id': imp.id,
                'nombre': imp.nombre,
                'tipo': imp.tipo,
                'tipo_display': imp.get_tipo_display(),
                'aplicacion': imp.aplicacion,
                'aplicacion_display': imp.get_aplicacion_display(),
                # Porcentaje en formato decimal para cálculos (33% -> 0.33)
                'porcentaje': float(imp.porcentaje) / 100 if imp.porcentaje else None,
                # Porcentaje en formato display (33% -> 33)
                'porcentaje_display': float(imp.porcentaje) if imp.porcentaje else None,
                'valor_fijo': float(imp.valor_fijo) if imp.valor_fijo else None,
                'periodicidad': imp.periodicidad,
                'periodicidad_display': imp.get_periodicidad_display(),
                'activo': imp.activo
            })

        return impuestos

    except Exception as e:
        logger.error(f"Error obteniendo impuestos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/impuestos/renta")
def obtener_tasa_renta() -> Dict[str, Any]:
    """
    Obtiene la tasa de impuesto de renta configurada.

    Returns:
        Tasa de renta en formato decimal (0.33 para 33%)
    """
    try:
        from core.models import Impuesto

        impuesto_renta = Impuesto.objects.filter(
            tipo='renta',
            aplicacion='sobre_utilidad',
            activo=True
        ).first()

        if not impuesto_renta:
            # Valor por defecto si no está configurado
            return {
                'configurado': False,
                'tasa': 0.33,
                'tasa_porcentaje': 33,
                'mensaje': 'Impuesto de renta no configurado, usando valor por defecto (33%)'
            }

        return {
            'configurado': True,
            'id': impuesto_renta.id,
            'nombre': impuesto_renta.nombre,
            'tasa': float(impuesto_renta.porcentaje) / 100,  # Para cálculos (0.33)
            'tasa_porcentaje': float(impuesto_renta.porcentaje),  # Para display (33)
            'periodicidad': impuesto_renta.periodicidad
        }

    except Exception as e:
        # Si hay error (ej: tabla no existe), retornar default en lugar de error
        logger.warning(f"Error obteniendo tasa de renta, usando default: {e}")
        return {
            'configurado': False,
            'tasa': 0.33,
            'tasa_porcentaje': 33,
            'mensaje': f'Error consultando impuestos, usando valor por defecto (33%)'
        }


@app.get("/api/impuestos/ica")
def obtener_tasa_ica() -> Dict[str, Any]:
    """
    Obtiene la tasa de ICA configurada.

    Returns:
        Tasa de ICA en formato decimal (0.0041 para 0.41%)
    """
    try:
        from core.models import Impuesto

        impuesto_ica = Impuesto.objects.filter(
            tipo='ica',
            aplicacion='sobre_ventas',
            activo=True
        ).first()

        if not impuesto_ica:
            return {
                'configurado': False,
                'tasa': 0,
                'tasa_porcentaje': 0,
                'mensaje': 'ICA no configurado'
            }

        return {
            'configurado': True,
            'id': impuesto_ica.id,
            'nombre': impuesto_ica.nombre,
            'tasa': float(impuesto_ica.porcentaje) / 100,  # Para cálculos (0.0041)
            'tasa_porcentaje': float(impuesto_ica.porcentaje),  # Para display (0.41)
            'periodicidad': impuesto_ica.periodicidad
        }

    except Exception as e:
        logger.warning(f"Error obteniendo tasa de ICA: {e}")
        return {
            'configurado': False,
            'tasa': 0,
            'tasa_porcentaje': 0,
            'mensaje': f'Error consultando ICA'
        }


# =============================================================================
# P&G POR ZONA Y MUNICIPIO - Endpoints para desglose geográfico
# =============================================================================

@app.get("/api/pyg/marca")
def obtener_pyg_marca(
    escenario_id: int,
    marca_id: str
) -> Dict[str, Any]:
    """
    Obtiene el P&G completo para una marca.

    Args:
        escenario_id: ID del escenario
        marca_id: ID de la marca

    Returns:
        P&G con desglose por comercial, logístico y administrativo
    """
    try:
        from core.models import Escenario, Marca
        from api.pyg_service import calcular_pyg_todas_zonas

        escenario = Escenario.objects.get(pk=escenario_id)
        marca = Marca.objects.get(marca_id=marca_id)

        # Calcular P&G de todas las zonas y sumar para obtener el total de la marca
        zonas = calcular_pyg_todas_zonas(escenario, marca)

        # Calcular totales sumando todas las zonas
        from decimal import Decimal
        total_comercial_personal = sum(z['comercial']['personal'] for z in zonas)
        total_comercial_gastos = sum(z['comercial']['gastos'] for z in zonas)
        total_logistico_personal = sum(z['logistico']['personal'] for z in zonas)
        total_logistico_gastos = sum(z['logistico']['gastos'] for z in zonas)
        total_admin_personal = sum(z['administrativo']['personal'] for z in zonas)
        total_admin_gastos = sum(z['administrativo']['gastos'] for z in zonas)

        resultado = {
            'comercial': {
                'personal': total_comercial_personal,
                'gastos': total_comercial_gastos,
                'total': total_comercial_personal + total_comercial_gastos
            },
            'logistico': {
                'personal': total_logistico_personal,
                'gastos': total_logistico_gastos,
                'total': total_logistico_personal + total_logistico_gastos
            },
            'administrativo': {
                'personal': total_admin_personal,
                'gastos': total_admin_gastos,
                'total': total_admin_personal + total_admin_gastos
            },
            'total_mensual': sum(z['total_mensual'] for z in zonas),
            'total_anual': sum(z['total_anual'] for z in zonas)
        }

        return {
            'escenario_id': escenario_id,
            'escenario_nombre': escenario.nombre,
            'marca_id': marca_id,
            'marca_nombre': marca.nombre,
            'pyg': _serializar_pyg(resultado)
        }

    except Escenario.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Escenario no encontrado: {escenario_id}")
    except Marca.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Marca no encontrada: {marca_id}")
    except Exception as e:
        logger.error(f"Error obteniendo P&G marca: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pyg/zonas")
def obtener_pyg_zonas(
    escenario_id: int,
    marca_id: str,
    operacion_ids: Optional[str] = None
) -> Dict[str, Any]:
    """
    Obtiene el P&G desglosado por zona comercial para una marca.
    Incluye ventas mensuales y configuración de descuentos para calcular rentabilidad.

    Args:
        escenario_id: ID del escenario
        marca_id: ID de la marca
        operacion_ids: IDs de operaciones separados por coma (opcional)

    Returns:
        Lista de P&G por zona con ventas, costos y rentabilidad
    """
    try:
        from core.models import (
            Escenario, Marca,
            ConfiguracionDescuentos, Impuesto
        )
        from api.pyg_service import calcular_pyg_todas_zonas

        escenario = Escenario.objects.get(pk=escenario_id)
        marca = Marca.objects.get(marca_id=marca_id)

        # Parsear operacion_ids si se proporcionan
        operacion_ids_list = None
        if operacion_ids:
            try:
                operacion_ids_list = [int(x.strip()) for x in operacion_ids.split(',') if x.strip()]
            except ValueError:
                pass

        zonas = calcular_pyg_todas_zonas(escenario, marca, operacion_ids=operacion_ids_list)

        # Obtener ventas mensuales de la marca (filtradas por operaciones si se especifican)
        ventas_por_marca = obtener_ventas_mensuales_por_marca(
            escenario_id=escenario_id,
            marcas_ids=[marca_id],
            operacion_ids=operacion_ids_list
        )
        # Extraer solo el diccionario de ventas, no la estructura completa
        ventas_mensuales = ventas_por_marca.get(marca_id, {}).get('ventas', {})

        # Obtener configuración de descuentos
        config_descuentos = None
        try:
            config = ConfiguracionDescuentos.objects.prefetch_related('tramos').get(
                marca=marca,
                activa=True
            )
            # Calcular descuento ponderado
            descuento_ponderado = 0.0
            tramos_data = []
            for tramo in config.tramos.all().order_by('orden'):
                peso = float(tramo.porcentaje_ventas) / 100
                descuento = float(tramo.porcentaje_descuento) / 100
                descuento_ponderado += peso * descuento
                tramos_data.append({
                    'orden': tramo.orden,
                    'porcentaje_ventas': float(tramo.porcentaje_ventas),
                    'porcentaje_descuento': float(tramo.porcentaje_descuento),
                })

            config_descuentos = {
                'descuento_pie_factura_ponderado': descuento_ponderado * 100,
                'tramos': tramos_data,
                'porcentaje_rebate': float(config.porcentaje_rebate),
                'aplica_descuento_financiero': config.aplica_descuento_financiero,
                'porcentaje_descuento_financiero': float(config.porcentaje_descuento_financiero),
                'aplica_cesantia_comercial': config.aplica_cesantia_comercial,
            }
        except ConfiguracionDescuentos.DoesNotExist:
            config_descuentos = {
                'descuento_pie_factura_ponderado': 0,
                'tramos': [],
                'porcentaje_rebate': 0,
                'aplica_descuento_financiero': False,
                'porcentaje_descuento_financiero': 0,
                'aplica_cesantia_comercial': False,
            }

        # Obtener tasa de impuesto de renta
        tasa_impuesto = 0.33  # Default
        try:
            impuesto_renta = Impuesto.objects.filter(
                tipo='renta',
                aplicacion='sobre_utilidad',
                activo=True
            ).first()
            if impuesto_renta:
                tasa_impuesto = float(impuesto_renta.porcentaje) / 100
        except Exception:
            pass

        # ICA ahora se calcula por zona usando la tasa de su operación
        # (cada zona tiene zona['zona']['tasa_ica'] desde pyg_service)

        # Calcular utilidad neta por zona para ordenar (usar mes actual como referencia)
        from datetime import datetime
        mes_actual = f"mes_{datetime.now().month}"
        ventas_mes_actual = ventas_mensuales.get(mes_actual, 0) if ventas_mensuales else 0

        def calcular_utilidad_neta_zona(zona):
            """Calcula la utilidad neta de una zona para ordenamiento"""
            participacion = float(zona['zona']['participacion_ventas']) / 100
            ventas_zona = ventas_mes_actual * participacion

            # Margen bruto
            descuento_ponderado = config_descuentos['descuento_pie_factura_ponderado'] / 100
            margen_bruto = ventas_zona * descuento_ponderado

            # Utilidad operacional (convertir total_mensual a float)
            total_mensual = float(zona['total_mensual'])
            utilidad_operacional = margen_bruto - total_mensual

            # Otros ingresos (rebate + descuento financiero)
            rebate = ventas_zona * (config_descuentos['porcentaje_rebate'] / 100)
            desc_financiero = ventas_zona * (config_descuentos['porcentaje_descuento_financiero'] / 100) if config_descuentos['aplica_descuento_financiero'] else 0
            otros_ingresos = rebate + desc_financiero

            # Utilidad antes de impuestos
            utilidad_antes_impuestos = utilidad_operacional + otros_ingresos

            # ICA (sobre ventas) - usar tasa de la operación de la zona
            tasa_ica_zona = zona['zona'].get('tasa_ica', 0)
            ica = ventas_zona * tasa_ica_zona

            # Utilidad neta (después de impuestos)
            utilidad_despues_ica = utilidad_antes_impuestos - ica
            impuesto = utilidad_despues_ica * tasa_impuesto if utilidad_despues_ica > 0 else 0
            utilidad_neta = utilidad_despues_ica - impuesto

            # Margen neto %
            margen_neto = (utilidad_neta / ventas_zona * 100) if ventas_zona > 0 else 0

            return margen_neto

        # Ordenar zonas por margen neto (de mayor a menor)
        # Si no hay ventas configuradas, ordenar por participación en ventas
        if ventas_mes_actual > 0:
            zonas_ordenadas = sorted(zonas, key=calcular_utilidad_neta_zona, reverse=True)
        else:
            # Sin ventas configuradas, ordenar por participación (mayor a menor)
            zonas_ordenadas = sorted(zonas, key=lambda z: z['zona']['participacion_ventas'], reverse=True)

        return {
            'escenario_id': escenario_id,
            'escenario_nombre': escenario.nombre,
            'marca_id': marca_id,
            'marca_nombre': marca.nombre,
            'zonas': [_serializar_pyg_zona(z) for z in zonas_ordenadas],
            'total_zonas': len(zonas_ordenadas),
            'ventas_mensuales': ventas_mensuales,
            'configuracion_descuentos': config_descuentos,
            'tasa_impuesto_renta': tasa_impuesto,
            # tasa_ica ahora está en cada zona (zona['zona']['tasa_ica'])
        }

    except Escenario.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Escenario no encontrado: {escenario_id}")
    except Marca.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Marca no encontrada: {marca_id}")
    except Exception as e:
        logger.error(f"Error obteniendo P&G zonas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/debug/rubros-detallado")
def diagnosticar_rubros_detallado(
    escenario_id: int,
    marca_id: str
) -> Dict[str, Any]:
    """
    Muestra exactamente qué rubros se envían al frontend para P&G Detallado.
    """
    try:
        # Crear simulador para obtener los rubros
        loader = get_loader(escenario_id=escenario_id)
        simulator = Simulator(loader=loader)
        simulator.cargar_marcas([marca_id])
        resultado = simulator.ejecutar_simulacion()

        marca_data = next((m for m in resultado.marcas if m.marca_id == marca_id), None)

        if not marca_data:
            raise HTTPException(status_code=404, detail="Marca no encontrada")

        # Analizar rubros comerciales
        rubros_comerciales_personal = [r for r in marca_data.rubros_individuales + marca_data.rubros_compartidos_asignados
                                      if r.categoria == 'comercial' and r.tipo == 'personal']
        rubros_comerciales_gastos = [r for r in marca_data.rubros_individuales + marca_data.rubros_compartidos_asignados
                                     if r.categoria == 'comercial' and r.tipo != 'personal']

        # Identificar lejanías
        lejanias_en_rubros = [r for r in rubros_comerciales_gastos
                             if 'Combustible Lejanía' in r.nombre or 'Viáticos Pernocta' in r.nombre]
        gastos_sin_lejanias = [r for r in rubros_comerciales_gastos
                              if 'Combustible Lejanía' not in r.nombre and 'Viáticos Pernocta' not in r.nombre]

        total_personal = sum(r.valor_total for r in rubros_comerciales_personal)
        total_lejanias_rubros = sum(r.valor_total for r in lejanias_en_rubros)
        total_gastos_sin_lejanias = sum(r.valor_total for r in gastos_sin_lejanias)

        # Total como lo calcula el frontend
        total_frontend = total_personal + total_gastos_sin_lejanias + float(marca_data.lejania_comercial)

        return {
            'marca': marca_data.nombre,
            'totales': {
                'personal': float(total_personal),
                'gastos_sin_lejanias': float(total_gastos_sin_lejanias),
                'lejanias_en_rubros': float(total_lejanias_rubros),
                'lejania_comercial_campo': float(marca_data.lejania_comercial),
                'total_frontend_calculado': float(total_frontend),
            },
            'conteos': {
                'rubros_personal': len(rubros_comerciales_personal),
                'rubros_gastos': len(rubros_comerciales_gastos),
                'lejanias_en_rubros': len(lejanias_en_rubros),
                'gastos_sin_lejanias': len(gastos_sin_lejanias),
            },
            'lejanias_detalle': [
                {'nombre': r.nombre, 'valor': float(r.valor_total)}
                for r in lejanias_en_rubros
            ]
        }

    except Exception as e:
        logger.error(f"Error en diagnóstico rubros: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ELIMINADO: /api/debug/diferencia-pyg - Redundante con /api/diagnostico/comparar-pyg


@app.get("/api/pyg/zona/{zona_id}")
def obtener_pyg_zona(
    zona_id: int,
    escenario_id: int
) -> Dict[str, Any]:
    """
    Obtiene el P&G para una zona específica.

    Args:
        zona_id: ID de la zona
        escenario_id: ID del escenario

    Returns:
        P&G de la zona con desglose
    """
    try:
        from core.models import Escenario, Zona
        from api.pyg_service import calcular_pyg_zona

        escenario = Escenario.objects.get(pk=escenario_id)
        zona = Zona.objects.get(pk=zona_id, escenario=escenario)

        resultado = calcular_pyg_zona(escenario, zona)

        return {
            'escenario_id': escenario_id,
            'escenario_nombre': escenario.nombre,
            'pyg': _serializar_pyg_zona(resultado)
        }

    except Escenario.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Escenario no encontrado: {escenario_id}")
    except Zona.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Zona no encontrada: {zona_id}")
    except Exception as e:
        logger.error(f"Error obteniendo P&G zona: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pyg/municipios")
def obtener_pyg_municipios(
    zona_id: int,
    escenario_id: int,
    marca_id: str
) -> Dict[str, Any]:
    """
    Obtiene el P&G desglosado por municipio para una zona.

    Args:
        zona_id: ID de la zona
        escenario_id: ID del escenario
        marca_id: ID de la marca

    Returns:
        Lista de P&G por municipio con ventas y configuración de descuentos
    """
    try:
        from core.models import (
            Escenario, Zona, Marca, Impuesto,
            ProyeccionVentasConfig, ConfiguracionDescuentos
        )
        from api.pyg_service import calcular_pyg_todos_municipios

        escenario = Escenario.objects.get(pk=escenario_id)
        zona = Zona.objects.get(pk=zona_id, escenario=escenario)
        marca = Marca.objects.get(marca_id=marca_id)

        municipios = calcular_pyg_todos_municipios(escenario, zona)

        # Obtener ventas mensuales de la marca
        ventas_mensuales = {}
        try:
            config_ventas = ProyeccionVentasConfig.objects.get(
                marca=marca,
                escenario=escenario,
                anio=escenario.anio
            )
            ventas_mensuales = {k: float(v) for k, v in config_ventas.calcular_ventas_mensuales().items()}
        except ProyeccionVentasConfig.DoesNotExist:
            pass

        # Obtener configuración de descuentos
        config_descuentos = None
        try:
            config = ConfiguracionDescuentos.objects.prefetch_related('tramos').get(
                marca=marca,
                activa=True
            )
            # Calcular descuento ponderado
            descuento_ponderado = 0.0
            tramos_data = []
            for tramo in config.tramos.all().order_by('orden'):
                peso = float(tramo.porcentaje_ventas) / 100
                descuento = float(tramo.porcentaje_descuento) / 100
                descuento_ponderado += peso * descuento
                tramos_data.append({
                    'orden': tramo.orden,
                    'porcentaje_ventas': float(tramo.porcentaje_ventas),
                    'porcentaje_descuento': float(tramo.porcentaje_descuento),
                })

            config_descuentos = {
                'descuento_pie_factura_ponderado': descuento_ponderado * 100,
                'tramos': tramos_data,
                'porcentaje_rebate': float(config.porcentaje_rebate),
                'aplica_descuento_financiero': config.aplica_descuento_financiero,
                'porcentaje_descuento_financiero': float(config.porcentaje_descuento_financiero),
                'aplica_cesantia_comercial': config.aplica_cesantia_comercial,
            }
        except ConfiguracionDescuentos.DoesNotExist:
            config_descuentos = {
                'descuento_pie_factura_ponderado': 0,
                'tramos': [],
                'porcentaje_rebate': 0,
                'aplica_descuento_financiero': False,
                'porcentaje_descuento_financiero': 0,
                'aplica_cesantia_comercial': False,
            }

        # Obtener tasa de impuesto de renta
        tasa_impuesto = 0.33  # Default
        try:
            impuesto_renta = Impuesto.objects.filter(
                tipo='renta',
                aplicacion='sobre_utilidad',
                activo=True
            ).first()
            if impuesto_renta:
                tasa_impuesto = float(impuesto_renta.porcentaje) / 100
        except Exception:
            pass

        # Obtener tasa de ICA
        tasa_ica = 0.0
        try:
            impuesto_ica = Impuesto.objects.filter(
                tipo='ica',
                aplicacion='sobre_ventas',
                activo=True
            ).first()
            if impuesto_ica:
                tasa_ica = float(impuesto_ica.porcentaje) / 100
        except Exception:
            pass

        return {
            'escenario_id': escenario_id,
            'escenario_nombre': escenario.nombre,
            'zona_id': zona_id,
            'zona_nombre': zona.nombre,
            'zona_participacion_ventas': float(zona.participacion_ventas),
            'marca_id': marca_id,
            'marca_nombre': marca.nombre,
            'municipios': [_serializar_pyg_municipio(m) for m in municipios],
            'total_municipios': len(municipios),
            'ventas_mensuales': ventas_mensuales,
            'configuracion_descuentos': config_descuentos,
            'tasa_impuesto_renta': tasa_impuesto,
            'tasa_ica': tasa_ica
        }

    except Escenario.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Escenario no encontrado: {escenario_id}")
    except Zona.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Zona no encontrada: {zona_id}")
    except Marca.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Marca no encontrada: {marca_id}")
    except Exception as e:
        logger.error(f"Error obteniendo P&G municipios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pyg/resumen")
def obtener_pyg_resumen(
    escenario_id: int,
    marca_id: str
) -> Dict[str, Any]:
    """
    Obtiene el resumen completo de P&G para una marca con desglose por zona.

    Args:
        escenario_id: ID del escenario
        marca_id: ID de la marca

    Returns:
        Resumen completo con total de marca y desglose por zonas
    """
    try:
        from core.models import Escenario, Marca
        from api.pyg_service import calcular_pyg_todas_zonas

        escenario = Escenario.objects.get(pk=escenario_id)
        marca = Marca.objects.get(marca_id=marca_id)

        zonas = calcular_pyg_todas_zonas(escenario, marca)

        # Calcular totales sumando todas las zonas
        total_comercial = sum(z['comercial']['total'] for z in zonas)
        total_logistico = sum(z['logistico']['total'] for z in zonas)
        total_administrativo = sum(z['administrativo']['total'] for z in zonas)
        total_mensual = total_comercial + total_logistico + total_administrativo

        resumen_total = {
            'comercial': {
                'personal': sum(z['comercial']['personal'] for z in zonas),
                'gastos': sum(z['comercial']['gastos'] for z in zonas),
                'total': total_comercial
            },
            'logistico': {
                'personal': sum(z['logistico']['personal'] for z in zonas),
                'gastos': sum(z['logistico']['gastos'] for z in zonas),
                'total': total_logistico
            },
            'administrativo': {
                'personal': sum(z['administrativo']['personal'] for z in zonas),
                'gastos': sum(z['administrativo']['gastos'] for z in zonas),
                'total': total_administrativo
            },
            'total_mensual': total_mensual,
            'total_anual': total_mensual * 12
        }

        return {
            'escenario_id': escenario_id,
            'escenario_nombre': escenario.nombre,
            'marca': {
                'id': marca.marca_id,
                'nombre': marca.nombre,
            },
            'total': _serializar_pyg(resumen_total),
            'zonas': [_serializar_pyg_zona(z) for z in zonas]
        }

    except Escenario.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Escenario no encontrado: {escenario_id}")
    except Marca.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Marca no encontrada: {marca_id}")
    except Exception as e:
        logger.error(f"Error obteniendo resumen P&G: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _serializar_pyg(pyg: Dict) -> Dict:
    """Serializa un diccionario de P&G a formato JSON-compatible."""
    def to_float(val):
        if val is None:
            return 0.0
        try:
            return float(val)
        except (TypeError, ValueError):
            return 0.0

    comercial = {
        'personal': to_float(pyg.get('comercial', {}).get('personal', 0)),
        'gastos': to_float(pyg.get('comercial', {}).get('gastos', 0)),
        'total': to_float(pyg.get('comercial', {}).get('total', 0)),
    }
    # Agregar lejanías si existen
    lejanias_comercial = pyg.get('comercial', {}).get('lejanias')
    if lejanias_comercial is not None:
        comercial['lejanias'] = to_float(lejanias_comercial)

    logistico = {
        'personal': to_float(pyg.get('logistico', {}).get('personal', 0)),
        'gastos': to_float(pyg.get('logistico', {}).get('gastos', 0)),
        'total': to_float(pyg.get('logistico', {}).get('total', 0)),
    }
    # Agregar lejanías si existen
    lejanias_logistico = pyg.get('logistico', {}).get('lejanias')
    if lejanias_logistico is not None:
        logistico['lejanias'] = to_float(lejanias_logistico)

    return {
        'comercial': comercial,
        'logistico': logistico,
        'administrativo': {
            'personal': to_float(pyg.get('administrativo', {}).get('personal', 0)),
            'gastos': to_float(pyg.get('administrativo', {}).get('gastos', 0)),
            'total': to_float(pyg.get('administrativo', {}).get('total', 0)),
        },
        'total_mensual': to_float(pyg.get('total_mensual', 0)),
        'total_anual': to_float(pyg.get('total_anual', 0)),
    }


def _serializar_pyg_zona(pyg_zona: Dict) -> Dict:
    """Serializa un P&G de zona."""
    resultado = _serializar_pyg(pyg_zona)
    resultado['zona'] = pyg_zona.get('zona', {})
    return resultado


def _serializar_pyg_municipio(pyg_mun: Dict) -> Dict:
    """Serializa un P&G de municipio."""
    resultado = _serializar_pyg(pyg_mun)
    resultado['municipio'] = pyg_mun.get('municipio', {})
    resultado['zona'] = pyg_mun.get('zona', {})
    return resultado


@app.get("/api/diagnostico/personal-detallado")
def diagnostico_personal_detallado(
    escenario_id: int,
    marca_id: str
) -> Dict[str, Any]:
    """
    Diagnóstico detallado del personal por categoría y tipo de asignación geográfica.
    Muestra cada persona, su costo y cómo se distribuye a las zonas.
    """
    try:
        from core.models import (
            Escenario, Marca, Zona,
            PersonalComercial, PersonalLogistico, PersonalAdministrativo,
            GastoComercial, GastoLogistico, GastoAdministrativo
        )
        from decimal import Decimal

        escenario = Escenario.objects.get(pk=escenario_id)
        marca = Marca.objects.get(marca_id=marca_id)

        # Obtener zonas activas
        zonas = list(Zona.objects.filter(
            escenario=escenario,
            marca=marca,
            activo=True
        ).order_by('nombre'))
        zonas_count = len(zonas) or 1
        suma_participaciones = sum(float(z.participacion_ventas or 0) for z in zonas)

        def procesar_personal(modelo, categoria):
            """Procesa personal de una categoría y calcula distribución."""
            items = []
            total_directo = Decimal('0')
            total_proporcional = Decimal('0')
            total_compartido = Decimal('0')
            total_distribuido = Decimal('0')

            personal_qs = modelo.objects.filter(escenario=escenario, marca=marca)

            for p in personal_qs:
                costo = Decimal(str(p.calcular_costo_mensual()))
                asignacion = getattr(p, 'tipo_asignacion_geo', 'proporcional')
                zona_asignada = getattr(p, 'zona', None)
                # Usar nombre del registro o tipo como fallback
                nombre_personal = getattr(p, 'nombre', '') or getattr(p, 'tipo', 'Sin nombre')

                # Calcular cuánto se distribuye realmente
                distribuido = Decimal('0')
                zona_destino = None

                if asignacion == 'directo':
                    if zona_asignada:
                        distribuido = costo
                        zona_destino = zona_asignada.nombre
                    else:
                        distribuido = Decimal('0')  # No tiene zona asignada, se pierde
                        zona_destino = "SIN ZONA (NO DISTRIBUIDO)"
                    total_directo += costo
                elif asignacion == 'proporcional':
                    # Se distribuye según participación de cada zona
                    distribuido = costo * (Decimal(str(suma_participaciones)) / 100)
                    zona_destino = f"Todas ({suma_participaciones:.1f}%)"
                    total_proporcional += costo
                elif asignacion == 'compartido':
                    # Se divide equitativamente entre zonas
                    distribuido = costo  # Total sí se distribuye
                    zona_destino = f"Equitativo ({zonas_count} zonas)"
                    total_compartido += costo

                total_distribuido += distribuido

                # Obtener desglose del cálculo para diagnóstico
                salario_base = float(getattr(p, 'salario_base', 0) or 0)
                cantidad = p.cantidad or 1

                items.append({
                    'nombre': f"{nombre_personal} ({p.cantidad})" if p.cantidad and p.cantidad > 1 else nombre_personal,
                    'cantidad': cantidad,
                    'salario_base': salario_base,
                    'costo_unitario': float(costo / cantidad) if cantidad else 0,
                    'costo_total': float(costo),
                    'asignacion': asignacion,
                    'zona_asignada': zona_asignada.nombre if zona_asignada else None,
                    'zona_destino': zona_destino,
                    'distribuido': float(distribuido),
                    'perdido': float(costo - distribuido) if distribuido < costo else 0
                })

            return {
                'items': items,
                'total_costo': float(total_directo + total_proporcional + total_compartido),
                'total_directo': float(total_directo),
                'total_proporcional': float(total_proporcional),
                'total_compartido': float(total_compartido),
                'total_distribuido': float(total_distribuido),
                'diferencia': float((total_directo + total_proporcional + total_compartido) - total_distribuido)
            }

        def procesar_gastos(modelo, categoria, filtro_excluir=None):
            """Procesa gastos de una categoría."""
            items = []
            total = Decimal('0')
            total_distribuido = Decimal('0')

            gastos_qs = modelo.objects.filter(escenario=escenario, marca=marca)

            for g in gastos_qs:
                nombre = g.nombre or 'Sin nombre'

                # Filtrar gastos que deben excluirse (lejanías, flota, etc.)
                if filtro_excluir and filtro_excluir(g):
                    continue

                valor = g.valor_mensual or Decimal('0')
                asignacion = getattr(g, 'tipo_asignacion_geo', 'proporcional')
                zona_asignada = getattr(g, 'zona', None)

                distribuido = Decimal('0')
                if asignacion == 'directo':
                    if zona_asignada:
                        distribuido = valor
                elif asignacion == 'proporcional':
                    distribuido = valor * (Decimal(str(suma_participaciones)) / 100)
                elif asignacion == 'compartido':
                    distribuido = valor

                total += valor
                total_distribuido += distribuido

                items.append({
                    'nombre': nombre,
                    'valor': float(valor),
                    'asignacion': asignacion,
                    'zona_asignada': zona_asignada.nombre if zona_asignada else None,
                    'distribuido': float(distribuido)
                })

            return {
                'items': items,
                'total': float(total),
                'total_distribuido': float(total_distribuido),
                'diferencia': float(total - total_distribuido)
            }

        # Filtros importados de pyg_service (centralizados)
        from api.pyg_service import (
            es_gasto_lejania_comercial,
            es_gasto_lejania_logistica,
            es_gasto_flota_vehiculos
        )

        def filtro_logistico(gasto):
            nombre = gasto.nombre or ''
            tipo = gasto.tipo or ''
            return es_gasto_lejania_logistica(nombre) or es_gasto_flota_vehiculos(nombre, tipo)

        # Procesar cada categoría
        comercial_personal = procesar_personal(PersonalComercial, 'comercial')
        comercial_gastos = procesar_gastos(GastoComercial, 'comercial', lambda g: es_gasto_lejania_comercial(g.nombre or ''))

        logistico_personal = procesar_personal(PersonalLogistico, 'logistico')
        logistico_gastos = procesar_gastos(GastoLogistico, 'logistico', filtro_logistico)

        administrativo_personal = procesar_personal(PersonalAdministrativo, 'administrativo')
        administrativo_gastos = procesar_gastos(GastoAdministrativo, 'administrativo')

        return {
            'escenario': {
                'id': escenario_id,
                'nombre': escenario.nombre
            },
            'marca': {
                'id': marca_id,
                'nombre': marca.nombre
            },
            'zonas': {
                'cantidad': zonas_count,
                'suma_participaciones': suma_participaciones,
                'lista': [{'id': z.id, 'nombre': z.nombre, 'participacion': float(z.participacion_ventas or 0)} for z in zonas]
            },
            'comercial': {
                'personal': comercial_personal,
                'gastos': comercial_gastos,
                'total_categoria': comercial_personal['total_costo'] + comercial_gastos['total'],
                'total_distribuido': comercial_personal['total_distribuido'] + comercial_gastos['total_distribuido'],
                'diferencia': comercial_personal['diferencia'] + comercial_gastos['diferencia']
            },
            'logistico': {
                'personal': logistico_personal,
                'gastos': logistico_gastos,
                'total_categoria': logistico_personal['total_costo'] + logistico_gastos['total'],
                'total_distribuido': logistico_personal['total_distribuido'] + logistico_gastos['total_distribuido'],
                'diferencia': logistico_personal['diferencia'] + logistico_gastos['diferencia']
            },
            'administrativo': {
                'personal': administrativo_personal,
                'gastos': administrativo_gastos,
                'total_categoria': administrativo_personal['total_costo'] + administrativo_gastos['total'],
                'total_distribuido': administrativo_personal['total_distribuido'] + administrativo_gastos['total_distribuido'],
                'diferencia': administrativo_personal['diferencia'] + administrativo_gastos['diferencia']
            }
        }

    except Escenario.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Escenario no encontrado: {escenario_id}")
    except Marca.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Marca no encontrada: {marca_id}")
    except Exception as e:
        logger.error(f"Error en diagnóstico personal detallado: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/diagnostico/comparar-pyg")
def diagnostico_comparar_pyg(
    escenario_id: int,
    marca_id: str
) -> Dict[str, Any]:
    """
    Diagnóstico completo que compara P&G Detallado vs P&G Zonas.
    Usa el simulador para obtener los valores exactos del P&G Detallado.
    """
    try:
        from core.models import Escenario, Marca, Zona
        from core.calculator_lejanias import CalculadoraLejanias
        from core.simulator import Simulator
        from utils.loaders_db import DataLoaderDB
        from api.pyg_service import (
            calcular_pyg_zona,
            es_gasto_lejania_comercial,
            es_gasto_lejania_logistica
        )
        from decimal import Decimal

        escenario = Escenario.objects.get(pk=escenario_id)
        marca_obj = Marca.objects.get(marca_id=marca_id)

        # =====================================================================
        # P&G DETALLADO - Usar el SIMULADOR para obtener valores exactos
        # Esto garantiza que los valores coincidan con lo que muestra el frontend
        # =====================================================================
        loader = DataLoaderDB(escenario_id=escenario_id)
        simulator = Simulator(loader=loader)
        simulator.cargar_marcas([marca_id])
        resultado = simulator.ejecutar_simulacion()

        # Encontrar la marca en los resultados
        marca_sim = next((m for m in resultado.marcas if m.marca_id == marca_id), None)
        if not marca_sim:
            raise HTTPException(status_code=404, detail=f"Marca {marca_id} no encontrada en simulación")

        # Agrupar rubros por categoría y tipo (igual que PyGDetallado.tsx)
        todos_rubros = marca_sim.rubros_individuales + marca_sim.rubros_compartidos_asignados

        personal_comercial = Decimal('0')
        gastos_comercial = Decimal('0')
        personal_logistico = Decimal('0')
        gastos_logistico = Decimal('0')
        flota_vehiculos = Decimal('0')
        personal_admin = Decimal('0')
        gastos_admin = Decimal('0')

        # Usar funciones centralizadas de pyg_service
        for rubro in todos_rubros:
            valor = Decimal(str(rubro.valor_total))
            nombre = rubro.nombre or ''

            if rubro.categoria == 'comercial':
                if rubro.tipo == 'personal':
                    personal_comercial += valor
                else:
                    # Excluir lejanías comerciales (se calculan dinámicamente)
                    if not es_gasto_lejania_comercial(nombre):
                        gastos_comercial += valor
            elif rubro.categoria == 'logistico':
                if rubro.tipo == 'vehiculo':
                    flota_vehiculos += valor
                elif rubro.tipo == 'personal':
                    personal_logistico += valor
                else:
                    # Excluir lejanías y fletes (se muestran aparte)
                    if not es_gasto_lejania_logistica(nombre):
                        gastos_logistico += valor
            elif rubro.categoria == 'administrativo':
                if rubro.tipo == 'personal':
                    personal_admin += valor
                else:
                    gastos_admin += valor

        # Lejanías (del simulador o calcular directamente)
        lejanias_comercial = Decimal(str(marca_sim.lejania_comercial or 0))
        lejanias_logistico = Decimal(str(marca_sim.lejania_logistica or 0))

        # Si no están en el simulador, calcular directamente
        if lejanias_comercial == 0 or lejanias_logistico == 0:
            calc = CalculadoraLejanias(escenario)
            zonas = Zona.objects.filter(escenario=escenario, marca=marca_obj, activo=True)

            if lejanias_comercial == 0:
                for zona in zonas:
                    lej = calc.calcular_lejania_comercial_zona(zona)
                    lejanias_comercial += lej['total_mensual']

            if lejanias_logistico == 0:
                lejanias_log = calc.calcular_lejanias_logisticas_marca(marca_obj)
                lejanias_logistico = (
                    lejanias_log['total_combustible_mensual'] +
                    lejanias_log['total_peaje_mensual'] +
                    lejanias_log['total_pernocta_mensual'] +
                    lejanias_log['total_flete_base_mensual']
                )

        total_comercial = personal_comercial + gastos_comercial + lejanias_comercial
        flota_total = flota_vehiculos  # Flete base ya incluido en lejanías
        total_logistico = flota_total + personal_logistico + gastos_logistico + lejanias_logistico
        total_admin = personal_admin + gastos_admin

        # Para el desglose de flota, usar la calculadora
        calc = CalculadoraLejanias(escenario)
        lejanias_log = calc.calcular_lejanias_logisticas_marca(marca_obj)
        flete_base = lejanias_log['total_flete_base_mensual']
        zonas = Zona.objects.filter(escenario=escenario, marca=marca_obj, activo=True)

        # =====================================================================
        # P&G ZONAS - Calcular sumando todas las zonas
        # =====================================================================
        zonas_pyg = []
        zonas_totales = {
            'comercial_personal': Decimal('0'),
            'comercial_gastos': Decimal('0'),
            'comercial_lejanias': Decimal('0'),
            'logistico_personal': Decimal('0'),
            'logistico_gastos': Decimal('0'),
            'logistico_lejanias': Decimal('0'),
            'admin_personal': Decimal('0'),
            'admin_gastos': Decimal('0'),
        }

        for zona in zonas:
            pyg_zona = calcular_pyg_zona(escenario, zona)
            zonas_pyg.append({
                'nombre': zona.nombre,
                'participacion': float(zona.participacion_ventas or 0),
                'comercial': float(pyg_zona['comercial']['total']),
                'logistico': float(pyg_zona['logistico']['total']),
                'administrativo': float(pyg_zona['administrativo']['total']),
                'total': float(pyg_zona['total_mensual'])
            })
            zonas_totales['comercial_personal'] += pyg_zona['comercial']['personal']
            zonas_totales['comercial_gastos'] += pyg_zona['comercial']['gastos']
            zonas_totales['comercial_lejanias'] += pyg_zona['comercial'].get('lejanias', Decimal('0'))
            zonas_totales['logistico_personal'] += pyg_zona['logistico']['personal']
            zonas_totales['logistico_gastos'] += pyg_zona['logistico']['gastos']
            zonas_totales['logistico_lejanias'] += pyg_zona['logistico'].get('lejanias', Decimal('0'))
            zonas_totales['admin_personal'] += pyg_zona['administrativo']['personal']
            zonas_totales['admin_gastos'] += pyg_zona['administrativo']['gastos']

        suma_participaciones = sum(float(z.participacion_ventas or 0) for z in zonas)

        # =====================================================================
        # COMPARACIÓN
        # =====================================================================
        detallado = {
            'comercial': {
                'personal': float(personal_comercial),
                'gastos': float(gastos_comercial),
                'lejanias': float(lejanias_comercial),
                'total': float(total_comercial)
            },
            'logistico': {
                'flota': float(flota_total),
                'personal': float(personal_logistico),
                'gastos': float(gastos_logistico),
                'lejanias': float(lejanias_logistico),
                'total': float(total_logistico)
            },
            'administrativo': {
                'personal': float(personal_admin),
                'gastos': float(gastos_admin),
                'total': float(total_admin)
            },
            'total': float(total_comercial + total_logistico + total_admin)
        }

        # En P&G Zonas, la flota está incluida en lejanías logísticas
        # porque _calcular_lejanias_zona incluye los costos fijos de vehículos
        zonas_sum = {
            'comercial': {
                'personal': float(zonas_totales['comercial_personal']),
                'gastos': float(zonas_totales['comercial_gastos']),
                'lejanias': float(zonas_totales['comercial_lejanias']),
                'total': float(zonas_totales['comercial_personal'] + zonas_totales['comercial_gastos'] + zonas_totales['comercial_lejanias'])
            },
            'logistico': {
                'flota': 0,  # En zonas, flota está incluida en lejanías
                'personal': float(zonas_totales['logistico_personal']),
                'gastos': float(zonas_totales['logistico_gastos']),
                'lejanias': float(zonas_totales['logistico_lejanias']),
                'total': float(zonas_totales['logistico_personal'] + zonas_totales['logistico_gastos'] + zonas_totales['logistico_lejanias'])
            },
            'administrativo': {
                'personal': float(zonas_totales['admin_personal']),
                'gastos': float(zonas_totales['admin_gastos']),
                'total': float(zonas_totales['admin_personal'] + zonas_totales['admin_gastos'])
            },
            'total': float(sum(z['total'] for z in zonas_pyg))
        }

        # Calcular diferencias
        def calc_diff(d, z):
            return {k: round(d.get(k, 0) - z.get(k, 0), 2) for k in set(d.keys()) | set(z.keys())}

        diferencias = {
            'comercial': calc_diff(detallado['comercial'], zonas_sum['comercial']),
            'logistico': calc_diff(detallado['logistico'], zonas_sum['logistico']),
            'administrativo': calc_diff(detallado['administrativo'], zonas_sum['administrativo']),
            'total': round(detallado['total'] - zonas_sum['total'], 2)
        }

        # Alertas de discrepancias significativas (> $1000)
        alertas = []
        for cat in ['comercial', 'logistico', 'administrativo']:
            for key, diff in diferencias[cat].items():
                if abs(diff) > 1000:
                    alertas.append({
                        'categoria': cat,
                        'campo': key,
                        'diferencia': diff,
                        'valor_detallado': detallado[cat].get(key, 0),
                        'valor_zonas': zonas_sum[cat].get(key, 0)
                    })

        return {
            'escenario': escenario.nombre,
            'marca': marca_obj.nombre,
            'suma_participaciones': suma_participaciones,
            'pyg_detallado': detallado,
            'pyg_zonas': zonas_sum,
            'diferencias': diferencias,
            'alertas': alertas,
            'desglose': {
                'flota_total': float(flota_vehiculos),
                'flete_base': float(flete_base),
                'lejanias_log_desglose': {
                    'combustible': float(lejanias_log['total_combustible_mensual']),
                    'peajes': float(lejanias_log['total_peaje_mensual']),
                    'pernocta': float(lejanias_log['total_pernocta_mensual'])
                }
            },
            'zonas_detalle': zonas_pyg
        }

    except Exception as e:
        logger.error(f"Error en diagnóstico comparar P&G: {e}")
        import traceback
        raise HTTPException(status_code=500, detail=f"{str(e)}\n{traceback.format_exc()}")


@app.get("/api/diagnostico/logistico-detallado")
def diagnostico_logistico_detallado(
    escenario_id: int,
    marca_id: str
) -> Dict[str, Any]:
    """
    Diagnóstico detallado de costos logísticos.
    Muestra cómo se distribuye cada rubro logístico a cada zona.
    """
    try:
        from core.models import Escenario, Marca, Zona, RutaLogistica, RutaMunicipio, ZonaMunicipio
        from core.calculator_lejanias import CalculadoraLejanias
        from core.simulator import Simulator
        from utils.loaders_db import DataLoaderDB
        from decimal import Decimal

        escenario = Escenario.objects.get(pk=escenario_id)
        marca_obj = Marca.objects.get(marca_id=marca_id)

        calc = CalculadoraLejanias(escenario)

        # 1. COSTOS POR MUNICIPIO (desde rutas logísticas)
        costos_por_municipio = calc.calcular_costos_logisticos_por_municipio(marca_obj)

        # 2. DISTRIBUCIÓN A ZONAS (lejanías)
        costos_por_zona = calc.distribuir_costos_logisticos_a_zonas(marca_obj)

        # 2b. DISTRIBUCIÓN DE FLOTA A ZONAS
        flota_por_zona = calc.distribuir_flota_a_zonas(marca_obj)

        # 3. RUBROS DEL SIMULADOR (para comparar)
        loader = DataLoaderDB(escenario_id=escenario_id)
        simulator = Simulator(loader=loader)
        simulator.cargar_marcas([marca_id])
        resultado = simulator.ejecutar_simulacion()
        marca_sim = next((m for m in resultado.marcas if m.marca_id == marca_id), None)

        rubros_logisticos = []
        total_flota = Decimal('0')
        total_personal = Decimal('0')
        total_gastos = Decimal('0')
        total_lejanias_sim = Decimal('0')

        if marca_sim:
            todos_rubros = marca_sim.rubros_individuales + marca_sim.rubros_compartidos_asignados
            for rubro in todos_rubros:
                if rubro.categoria == 'logistico':
                    valor = Decimal(str(rubro.valor_total))
                    rubros_logisticos.append({
                        'nombre': rubro.nombre,
                        'tipo': rubro.tipo,
                        'valor': float(valor),
                        'asignacion': str(rubro.tipo_asignacion) if hasattr(rubro, 'tipo_asignacion') else 'individual'
                    })
                    if rubro.tipo == 'vehiculo':
                        total_flota += valor
                    elif rubro.tipo == 'personal':
                        total_personal += valor
                    else:
                        total_gastos += valor

            # Lejanías del simulador
            total_lejanias_sim = Decimal(str(marca_sim.lejania_logistica or 0))

        # 4. RUTAS LOGÍSTICAS DETALLE
        rutas_detalle = []
        rutas = RutaLogistica.objects.filter(
            marca=marca_obj,
            escenario=escenario,
            activo=True
        ).prefetch_related('municipios__municipio').select_related('vehiculo')

        for ruta in rutas:
            municipios_ruta = []
            for rm in ruta.municipios.all().order_by('orden_visita'):
                # Ver qué zonas atienden este municipio
                zonas_municipio = ZonaMunicipio.objects.filter(
                    municipio=rm.municipio,
                    zona__marca=marca_obj,
                    zona__escenario=escenario,
                    zona__activo=True
                ).select_related('zona')

                zonas_list = [{
                    'zona_id': zm.zona.id,
                    'zona_nombre': zm.zona.nombre,
                    'venta_proyectada': float(zm.venta_proyectada or 0)
                } for zm in zonas_municipio]

                municipios_ruta.append({
                    'orden': rm.orden_visita,
                    'municipio_id': rm.municipio.id,
                    'municipio_nombre': rm.municipio.nombre,
                    'flete_base': float(rm.flete_base or 0),
                    'zonas_que_lo_atienden': zonas_list,
                    'cantidad_zonas': len(zonas_list)
                })

            rutas_detalle.append({
                'ruta_id': ruta.id,
                'ruta_nombre': ruta.nombre,
                'vehiculo': str(ruta.vehiculo) if ruta.vehiculo else None,
                'vehiculo_id': ruta.vehiculo.id if ruta.vehiculo else None,
                'esquema': ruta.vehiculo.esquema if ruta.vehiculo else None,
                'frecuencia': ruta.frecuencia,
                'viajes_por_periodo': ruta.viajes_por_periodo,
                'recorridos_mensuales': float(ruta.recorridos_mensuales()),
                'municipios': municipios_ruta
            })

        # 5. ZONAS CON SUS COSTOS ASIGNADOS
        zonas = Zona.objects.filter(escenario=escenario, marca=marca_obj, activo=True).order_by('nombre')
        zonas_detalle = []

        total_distribuido = Decimal('0')
        for zona in zonas:
            costo_zona = Decimal('0')
            detalle_municipios = []
            if zona.id in costos_por_zona:
                costo_zona = costos_por_zona[zona.id]['costo_logistico_total']
                detalle_municipios = costos_por_zona[zona.id]['detalle_municipios']
                total_distribuido += costo_zona

            # Flota asignada a esta zona
            flota_zona = Decimal('0')
            detalle_vehiculos = []
            if zona.id in flota_por_zona:
                flota_zona = flota_por_zona[zona.id]['costo_flota_total']
                detalle_vehiculos = flota_por_zona[zona.id]['detalle_vehiculos']

            # Separar flete fijo de lejanías
            flete_fijo_zona = Decimal('0')
            lejanias_zona = Decimal('0')
            if zona.id in costos_por_zona:
                flete_fijo_zona = costos_por_zona[zona.id].get('flete_fijo_total', Decimal('0'))
                lejanias_zona = costos_por_zona[zona.id].get('lejanias_total', Decimal('0'))

            zonas_detalle.append({
                'zona_id': zona.id,
                'zona_nombre': zona.nombre,
                'participacion_ventas': float(zona.participacion_ventas or 0),
                'flete_fijo_asignado': float(flete_fijo_zona),
                'lejanias_asignado': float(lejanias_zona),
                'costo_logistico_asignado': float(costo_zona),
                'costo_flota_asignado': float(flota_zona),
                'costo_total_asignado': float(costo_zona + flota_zona),
                'municipios_con_costo': detalle_municipios,
                'vehiculos_con_costo': detalle_vehiculos
            })

        # 6. RESUMEN
        total_costo_municipios = sum(
            Decimal(str(m['costo_total'])) for m in costos_por_municipio.values()
        )
        total_flota_distribuida = sum(
            Decimal(str(z['costo_flota_total'])) for z in flota_por_zona.values()
        )

        return {
            'escenario': escenario.nombre,
            'marca': marca_obj.nombre,
            'resumen': {
                'total_flota_simulador': float(total_flota),
                'total_flota_distribuida': float(total_flota_distribuida),
                'total_personal_simulador': float(total_personal),
                'total_gastos_simulador': float(total_gastos),
                'total_lejanias_simulador': float(total_lejanias_sim),
                'total_costo_por_municipios': float(total_costo_municipios),
                'total_distribuido_a_zonas': float(total_distribuido + total_flota_distribuida),
                'diferencia_lejanias': float(total_costo_municipios - total_distribuido),
                'diferencia_flota': float(total_flota - total_flota_distribuida)
            },
            'rubros_logisticos_simulador': rubros_logisticos,
            'costos_por_municipio': {
                str(k): {
                    'municipio_nombre': v['municipio_nombre'],
                    'flete_total': float(v['flete_total']),
                    'combustible_total': float(v['combustible_total']),
                    'peaje_total': float(v['peaje_total']),
                    'pernocta_total': float(v['pernocta_total']),
                    'costo_total': float(v['costo_total']),
                    'rutas': v['rutas']
                } for k, v in costos_por_municipio.items()
            },
            'rutas_logisticas': rutas_detalle,
            'distribucion_a_zonas': zonas_detalle
        }

    except Exception as e:
        logger.error(f"Error en diagnóstico logístico detallado: {e}")
        import traceback
        raise HTTPException(status_code=500, detail=f"{str(e)}\n{traceback.format_exc()}")


# =============================================================================
# OPERACIONES - Endpoints para P&G por Centro de Costos / Operación
# =============================================================================

@app.get("/api/operaciones")
def obtener_operaciones(escenario_id: int) -> Dict[str, Any]:
    """
    Lista todas las operaciones de un escenario.

    Args:
        escenario_id: ID del escenario

    Returns:
        Lista de operaciones con información básica
    """
    try:
        from core.models import Escenario
        from api.pyg_service import listar_operaciones

        escenario = Escenario.objects.get(pk=escenario_id)
        operaciones = listar_operaciones(escenario)

        return {
            'escenario_id': escenario_id,
            'escenario_nombre': escenario.nombre,
            'operaciones': operaciones
        }

    except Escenario.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Escenario no encontrado: {escenario_id}")
    except Exception as e:
        logger.error(f"Error listando operaciones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pyg/operaciones")
def obtener_pyg_operaciones(escenario_id: int) -> Dict[str, Any]:
    """
    Obtiene el P&G consolidado de todas las operaciones de un escenario.

    Args:
        escenario_id: ID del escenario

    Returns:
        Lista de P&G por operación con totales consolidados
    """
    try:
        from core.models import Escenario
        from api.pyg_service import calcular_pyg_todas_operaciones

        escenario = Escenario.objects.get(pk=escenario_id)
        operaciones_pyg = calcular_pyg_todas_operaciones(escenario)

        # Serializar cada operación
        operaciones_serializadas = []
        for op in operaciones_pyg:
            operaciones_serializadas.append({
                'operacion_id': op['operacion_id'],
                'operacion_nombre': op['operacion_nombre'],
                'operacion_codigo': op['operacion_codigo'],
                'cantidad_zonas': op['cantidad_zonas'],
                'cantidad_marcas': op['cantidad_marcas'],
                'pyg': _serializar_pyg(op['pyg'])
            })

        # Calcular totales del escenario
        total_mensual = sum(op['pyg'].get('total_mensual', 0) for op in operaciones_pyg)
        total_anual = sum(op['pyg'].get('total_anual', 0) for op in operaciones_pyg)

        return {
            'escenario_id': escenario_id,
            'escenario_nombre': escenario.nombre,
            'operaciones': operaciones_serializadas,
            'totales': {
                'total_mensual': float(total_mensual),
                'total_anual': float(total_anual),
                'cantidad_operaciones': len(operaciones_serializadas)
            }
        }

    except Escenario.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Escenario no encontrado: {escenario_id}")
    except Exception as e:
        logger.error(f"Error obteniendo P&G de operaciones: {e}")
        import traceback
        raise HTTPException(status_code=500, detail=f"{str(e)}\n{traceback.format_exc()}")


@app.get("/api/pyg/operacion/{operacion_id}")
def obtener_pyg_operacion(operacion_id: int) -> Dict[str, Any]:
    """
    Obtiene el P&G detallado de una operación específica.

    Args:
        operacion_id: ID de la operación

    Returns:
        P&G consolidado de la operación con desglose por marca
    """
    try:
        from core.models import Operacion
        from api.pyg_service import calcular_pyg_operacion

        operacion = Operacion.objects.select_related('escenario').get(pk=operacion_id)
        pyg_resultado = calcular_pyg_operacion(operacion.escenario, operacion)

        # Serializar marcas
        marcas_serializadas = []
        for marca_pyg in pyg_resultado.get('marcas', []):
            marcas_serializadas.append({
                'marca_id': marca_pyg['marca_id'],
                'marca_nombre': marca_pyg['marca_nombre'],
                'cantidad_zonas': marca_pyg['cantidad_zonas'],
                'pyg': _serializar_pyg(marca_pyg['pyg'])
            })

        return {
            'operacion_id': operacion_id,
            'operacion_nombre': operacion.nombre,
            'operacion_codigo': operacion.codigo,
            'escenario_id': operacion.escenario.id,
            'escenario_nombre': operacion.escenario.nombre,
            'cantidad_marcas': len(marcas_serializadas),
            'marcas': marcas_serializadas,
            'pyg_consolidado': _serializar_pyg(pyg_resultado.get('consolidado', {}))
        }

    except Operacion.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Operación no encontrada: {operacion_id}")
    except Exception as e:
        logger.error(f"Error obteniendo P&G de operación: {e}")
        import traceback
        raise HTTPException(status_code=500, detail=f"{str(e)}\n{traceback.format_exc()}")


@app.get("/api/pyg/marca/{marca_id}/operaciones")
def obtener_pyg_marca_por_operaciones(
    marca_id: str,
    escenario_id: int
) -> Dict[str, Any]:
    """
    Obtiene el P&G de una marca desglosado por operación.

    Args:
        marca_id: ID de la marca
        escenario_id: ID del escenario

    Returns:
        P&G de la marca con desglose por cada operación donde opera
    """
    try:
        from core.models import Escenario, Marca
        from api.pyg_service import calcular_pyg_marca_por_operaciones

        escenario = Escenario.objects.get(pk=escenario_id)
        marca = Marca.objects.get(marca_id=marca_id)

        pyg_resultado = calcular_pyg_marca_por_operaciones(escenario, marca)

        # Serializar operaciones
        operaciones_serializadas = []
        for op_pyg in pyg_resultado.get('operaciones', []):
            operaciones_serializadas.append({
                'operacion_id': op_pyg['operacion_id'],
                'operacion_nombre': op_pyg['operacion_nombre'],
                'operacion_codigo': op_pyg['operacion_codigo'],
                'cantidad_zonas': op_pyg['cantidad_zonas'],
                'pyg': _serializar_pyg(op_pyg['pyg'])
            })

        return {
            'escenario_id': escenario_id,
            'escenario_nombre': escenario.nombre,
            'marca_id': marca_id,
            'marca_nombre': marca.nombre,
            'cantidad_operaciones': len(operaciones_serializadas),
            'operaciones': operaciones_serializadas,
            'pyg_consolidado': _serializar_pyg(pyg_resultado.get('consolidado', {}))
        }

    except Escenario.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Escenario no encontrado: {escenario_id}")
    except Marca.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Marca no encontrada: {marca_id}")
    except Exception as e:
        logger.error(f"Error obteniendo P&G de marca por operaciones: {e}")
        import traceback
        raise HTTPException(status_code=500, detail=f"{str(e)}\n{traceback.format_exc()}")


@app.get("/api/marcas/por-operaciones")
def obtener_marcas_por_operaciones(
    escenario_id: int,
    operacion_ids: Optional[str] = None
) -> Dict[str, Any]:
    """
    Lista las marcas disponibles filtradas por operaciones.
    Si no se especifican operaciones, devuelve todas las marcas del escenario.

    Args:
        escenario_id: ID del escenario
        operacion_ids: IDs de operaciones separados por coma (ej: "1,2,3")

    Returns:
        Lista de marcas con sus operaciones asociadas
    """
    try:
        from core.models import Escenario, Marca, MarcaOperacion, Operacion

        escenario = Escenario.objects.get(pk=escenario_id)

        # Si se especifican operaciones, filtrar marcas por esas operaciones
        if operacion_ids:
            ids = [int(id.strip()) for id in operacion_ids.split(',') if id.strip()]
            # Obtener marcas que tienen relación con esas operaciones
            marca_ids = MarcaOperacion.objects.filter(
                operacion_id__in=ids,
                operacion__escenario=escenario,
                activo=True
            ).values_list('marca_id', flat=True).distinct()
            marcas = Marca.objects.filter(id__in=marca_ids, activa=True)
        else:
            # Sin filtro, devolver todas las marcas activas del escenario
            # (marcas que tienen al menos una zona en el escenario)
            from core.models import Zona
            marca_ids = Zona.objects.filter(
                escenario=escenario,
                activo=True
            ).values_list('marca_id', flat=True).distinct()
            marcas = Marca.objects.filter(id__in=marca_ids, activa=True)

        # Construir respuesta con operaciones de cada marca
        marcas_data = []
        for marca in marcas:
            # Obtener operaciones de esta marca en el escenario
            operaciones_marca = MarcaOperacion.objects.filter(
                marca=marca,
                operacion__escenario=escenario,
                activo=True
            ).select_related('operacion')

            operaciones_data = [{
                'id': mo.operacion.id,
                'nombre': mo.operacion.nombre,
                'codigo': mo.operacion.codigo,
            } for mo in operaciones_marca]

            marcas_data.append({
                'id': marca.id,
                'marca_id': marca.marca_id,
                'nombre': marca.nombre,
                'operaciones': operaciones_data
            })

        return {
            'escenario_id': escenario_id,
            'escenario_nombre': escenario.nombre,
            'filtro_operaciones': operacion_ids,
            'marcas': marcas_data
        }

    except Escenario.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Escenario no encontrado: {escenario_id}")
    except Exception as e:
        logger.error(f"Error obteniendo marcas por operaciones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/distribucion/cascada")
def obtener_distribucion_cascada(
    escenario_id: int,
    marca_id: str,
    operacion_ids: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retorna la cascada de distribución de ventas:
    ProyeccionVentasConfig → MarcaOperacion → Zona → ZonaMunicipio

    Args:
        escenario_id: ID del escenario
        marca_id: ID de la marca (ej: 'M1')
        operacion_ids: IDs de operaciones separados por coma (opcional, ej: '1,2,3')

    Returns:
        Dict con la cascada completa y validaciones
    """
    try:
        from decimal import Decimal
        from core.models import (
            Escenario, Marca, ProyeccionVentasConfig,
            MarcaOperacion, Zona, ZonaMunicipio,
            ProyeccionManual, TipologiaProyeccion
        )

        escenario = Escenario.objects.get(pk=escenario_id)
        marca = Marca.objects.get(marca_id=marca_id)

        # Obtener venta total mensual de ProyeccionVentasConfig
        venta_total_mensual = Decimal('0')
        venta_anual = Decimal('0')
        ventas_mensuales = {}
        fuente_proyeccion = None
        tipologias_detalle = []

        try:
            config = ProyeccionVentasConfig.objects.get(
                marca=marca,
                escenario=escenario,
                anio=escenario.anio
            )
            ventas_mensuales = config.calcular_ventas_mensuales()
            if ventas_mensuales:
                venta_total_mensual = sum(ventas_mensuales.values()) / len(ventas_mensuales)
                venta_anual = sum(ventas_mensuales.values())

            # Determinar fuente de la proyección
            try:
                manual = config.proyeccion_manual
                ventas_manual = manual.get_ventas_mensuales()
                if sum(ventas_manual.values()) > 0:
                    fuente_proyeccion = 'manual'
                else:
                    fuente_proyeccion = 'tipologias'
            except ProyeccionManual.DoesNotExist:
                fuente_proyeccion = 'tipologias'

            # Si es desde tipologías, obtener el detalle
            if fuente_proyeccion == 'tipologias':
                for tip in config.tipologias.all():
                    tipologias_detalle.append({
                        'nombre': tip.nombre,
                        'clientes': tip.numero_clientes,
                        'visitas': tip.visitas_mes,
                        'efectividad': float(tip.efectividad),
                        'ticket': float(tip.ticket_promedio),
                        'crec_clientes': float(tip.crecimiento_clientes),
                        'crec_ticket': float(tip.crecimiento_ticket),
                        'venta_mes1': float(tip.get_venta_mensual_inicial()),
                        'venta_anual': float(tip.get_venta_anual()),
                    })

        except ProyeccionVentasConfig.DoesNotExist:
            pass

        # Parsear operacion_ids si se proporcionan
        operacion_ids_list = None
        if operacion_ids:
            try:
                operacion_ids_list = [int(x.strip()) for x in operacion_ids.split(',') if x.strip()]
            except ValueError:
                pass

        # Obtener MarcaOperacion (distribución por operación)
        marcas_operacion = MarcaOperacion.objects.filter(
            marca=marca,
            operacion__escenario=escenario,
            activo=True
        ).select_related('operacion')

        # Filtrar por operaciones seleccionadas si se especifican
        if operacion_ids_list:
            marcas_operacion = marcas_operacion.filter(operacion_id__in=operacion_ids_list)

        marcas_operacion = marcas_operacion.order_by('operacion__nombre')

        # Calcular total de participaciones
        total_participacion_operaciones = sum(mo.participacion_ventas for mo in marcas_operacion)

        # Construir cascada de operaciones
        operaciones_data = []
        for mo in marcas_operacion:
            # Obtener zonas de esta operación
            zonas = Zona.objects.filter(
                marca=marca,
                escenario=escenario,
                operacion=mo.operacion,
                activo=True
            ).order_by('nombre')

            total_participacion_zonas = sum(z.participacion_ventas for z in zonas)

            # Construir datos de zonas con sus municipios
            zonas_data = []
            for zona in zonas:
                # Obtener municipios de la zona
                zona_municipios = ZonaMunicipio.objects.filter(
                    zona=zona
                ).select_related('municipio').order_by('municipio__nombre')

                total_participacion_municipios = sum(zm.participacion_ventas for zm in zona_municipios)

                municipios_data = [{
                    'id': zm.id,
                    'municipio_id': zm.municipio.id,
                    'nombre': zm.municipio.nombre,
                    'departamento': zm.municipio.departamento,
                    'participacion_ventas': float(zm.participacion_ventas),
                    'venta_proyectada': float(zm.venta_proyectada),
                } for zm in zona_municipios]

                zonas_data.append({
                    'id': zona.id,
                    'nombre': zona.nombre,
                    'participacion_ventas': float(zona.participacion_ventas),
                    'venta_proyectada': float(zona.venta_proyectada),
                    'municipios': municipios_data,
                    'municipios_count': len(municipios_data),
                    'validacion': {
                        'suma_participaciones': float(total_participacion_municipios),
                        'es_valido': abs(total_participacion_municipios - Decimal('100')) < Decimal('0.01')
                    }
                })

            operaciones_data.append({
                'id': mo.id,
                'operacion_id': mo.operacion.id,
                'nombre': mo.operacion.nombre,
                'codigo': mo.operacion.codigo,
                'participacion_ventas': float(mo.participacion_ventas),
                'venta_proyectada': float(mo.venta_proyectada),
                'zonas': zonas_data,
                'zonas_count': len(zonas_data),
                'validacion': {
                    'suma_participaciones': float(total_participacion_zonas),
                    'es_valido': abs(total_participacion_zonas - Decimal('100')) < Decimal('0.01')
                }
            })

        return {
            'marca': {
                'id': marca.id,
                'marca_id': marca.marca_id,
                'nombre': marca.nombre,
                'venta_total_mensual': float(venta_total_mensual),
                'venta_anual': float(venta_anual),
                'ventas_mensuales': {k: float(v) for k, v in ventas_mensuales.items()}
            },
            'escenario': {
                'id': escenario.id,
                'nombre': escenario.nombre,
                'anio': escenario.anio
            },
            'operaciones': operaciones_data,
            'validacion': {
                'suma_participaciones_operaciones': float(total_participacion_operaciones),
                'operaciones_valido': abs(total_participacion_operaciones - Decimal('100')) < Decimal('0.01')
            },
            'proyeccion': {
                'fuente': fuente_proyeccion,
                'tipologias': tipologias_detalle
            }
        }

    except Escenario.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Escenario no encontrado: {escenario_id}")
    except Marca.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Marca no encontrada: {marca_id}")
    except Exception as e:
        logger.error(f"Error obteniendo cascada de distribución: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
