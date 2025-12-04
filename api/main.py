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
        escenario_id: ID del escenario (opcional)

    Returns:
        Resultado de la simulación serializado con desglose mensual de ventas
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

        # Agregar desglose mensual de ventas desde ProyeccionVentasConfig
        if escenario_id:
            ventas_mensuales_por_marca = obtener_ventas_mensuales_por_marca(
                escenario_id, marcas_seleccionadas
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
                }

        logger.info(f"Simulación completada exitosamente")
        return resultado_dict

    except Exception as e:
        logger.error(f"Error ejecutando simulación: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def obtener_ventas_mensuales_por_marca(
    escenario_id: int,
    marcas_ids: List[str]
) -> Dict[str, Dict[str, float]]:
    """
    Obtiene el desglose mensual de ventas para cada marca desde ProyeccionVentasConfig.

    Returns:
        Dict con marca_id como key y dict de ventas mensuales como value
    """
    try:
        from core.models import Escenario, Marca, ProyeccionVentasConfig

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
                ventas = config.calcular_ventas_mensuales()
                resultado[marca_id] = {k: float(v) for k, v in ventas.items()}
            except (Marca.DoesNotExist, ProyeccionVentasConfig.DoesNotExist):
                resultado[marca_id] = {}

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
                }

            except (Marca.DoesNotExist, ConfiguracionDescuentos.DoesNotExist):
                resultado[marca_id] = {
                    'tiene_configuracion': False,
                    'descuento_pie_factura_ponderado': 0,
                    'tramos': [],
                    'porcentaje_rebate': 0,
                    'aplica_descuento_financiero': False,
                    'porcentaje_descuento_financiero': 0,
                }

        return resultado

    except Exception as e:
        logger.warning(f"Error obteniendo configuración de descuentos: {e}")
        return {}


@app.get("/api/lejanias/comercial")
def obtener_detalle_lejanias_comercial(
    escenario_id: int,
    marca_id: str
) -> Dict[str, Any]:
    """
    Obtiene el detalle de lejanías comerciales por zona.

    Lee los totales desde GastoComercial (calculados por signals de Django)
    y genera el detalle por zona para visualización en frontend.

    Args:
        escenario_id: ID del escenario
        marca_id: ID de la marca

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

        # Obtener zonas de la marca
        zonas = Zona.objects.filter(
            marca=marca,
            escenario=escenario,
            activo=True
        ).prefetch_related('municipios__municipio').select_related('vendedor', 'municipio_base_vendedor')

        # Construir detalle por zona
        detalle_zonas = []
        total_combustible = 0.0
        total_pernocta = 0.0

        for zona in zonas:
            # Buscar gastos de esta zona específica
            combustible_zona = gastos_combustible.filter(
                nombre=f'Combustible Lejanía - {zona.nombre}'
            ).first()
            pernocta_zona = gastos_pernocta.filter(
                nombre=f'Viáticos Pernocta - {zona.nombre}'
            ).first()

            combustible_mensual = float(combustible_zona.valor_mensual) if combustible_zona else 0.0
            pernocta_mensual = float(pernocta_zona.valor_mensual) if pernocta_zona else 0.0

            # Generar detalle de municipios para visualización
            detalle_municipios = []
            base_vendedor = zona.municipio_base_vendedor or (config.municipio_bodega if config else None)

            if base_vendedor and config:
                consumo_km_galon = float(config.consumo_galon_km_moto if zona.tipo_vehiculo_comercial == 'MOTO' else config.consumo_galon_km_automovil)
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

                    # Calcular combustible por municipio
                    combustible_por_visita = 0.0
                    combustible_municipio = 0.0
                    if distancia_efectiva > 0 and consumo_km_galon > 0:
                        distancia_ida_vuelta = distancia_efectiva * 2
                        galones_por_visita = distancia_ida_vuelta / consumo_km_galon
                        combustible_por_visita = galones_por_visita * precio_galon
                        combustible_municipio = combustible_por_visita * visitas_mensuales

                    detalle_municipios.append({
                        'municipio': municipio.nombre,
                        'municipio_id': municipio.id,
                        'distancia_km': distancia_km,
                        'distancia_efectiva_km': distancia_efectiva,
                        'visitas_por_periodo': zona_mun.visitas_por_periodo,
                        'visitas_mensuales': visitas_mensuales,
                        'combustible_por_visita': combustible_por_visita,
                        'combustible_mensual': combustible_municipio,
                        'es_visita_local': False,
                    })

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
                'combustible_mensual': combustible_mensual,
                'pernocta_mensual': pernocta_mensual,
                'total_mensual': combustible_mensual + pernocta_mensual,
                'detalle': {
                    'base': base_vendedor.nombre if base_vendedor else None,
                    'tipo_vehiculo': zona.tipo_vehiculo_comercial,
                    'municipios': detalle_municipios,
                    'pernocta': detalle_pernocta,
                }
            })

            total_combustible += combustible_mensual
            total_pernocta += pernocta_mensual

        # Ordenar zonas de mayor a menor por total_mensual
        detalle_zonas.sort(key=lambda x: x['total_mensual'], reverse=True)

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
    marca_id: str
) -> Dict[str, Any]:
    """
    Obtiene el detalle de lejanías logísticas por ruta/vehículo.

    Lee los totales desde GastoLogistico (calculados por signals de Django)
    y genera el detalle por ruta para visualización en frontend.

    Args:
        escenario_id: ID del escenario
        marca_id: ID de la marca

    Returns:
        Detalle de lejanías logísticas por ruta (vehículo/tercero)
    """
    try:
        from core.models import (
            Escenario, Marca, RutaLogistica, GastoLogistico,
            ConfiguracionLejania, MatrizDesplazamiento
        )
        from decimal import Decimal
        from django.db.models import Sum

        # Obtener escenario y marca
        escenario = Escenario.objects.get(pk=escenario_id)
        marca = Marca.objects.get(marca_id=marca_id)

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

                resultado['marcas'].append({
                    'marca_id': marca.marca_id,
                    'marca_nombre': marca.nombre,
                    'metodo': config.metodo,
                    'metodo_display': config.get_metodo_display(),
                    'ventas_mensuales': {k: float(v) for k, v in ventas_mensuales.items()},
                    'total_anual': float(total_anual),
                    'promedio_mensual': float(total_anual / 12) if total_anual > 0 else 0
                })
            except ProyeccionVentasConfig.DoesNotExist:
                resultado['marcas'].append({
                    'marca_id': marca.marca_id,
                    'marca_nombre': marca.nombre,
                    'metodo': None,
                    'metodo_display': 'Sin configurar',
                    'ventas_mensuales': {},
                    'total_anual': 0,
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
    marca_id: str
) -> Dict[str, Any]:
    """
    Obtiene el P&G desglosado por zona comercial para una marca.
    Incluye ventas mensuales y configuración de descuentos para calcular rentabilidad.

    Args:
        escenario_id: ID del escenario
        marca_id: ID de la marca

    Returns:
        Lista de P&G por zona con ventas, costos y rentabilidad
    """
    try:
        from core.models import (
            Escenario, Marca, ProyeccionVentasConfig,
            ConfiguracionDescuentos, Impuesto
        )
        from api.pyg_service import calcular_pyg_todas_zonas

        escenario = Escenario.objects.get(pk=escenario_id)
        marca = Marca.objects.get(marca_id=marca_id)

        zonas = calcular_pyg_todas_zonas(escenario, marca)

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
            }
        except ConfiguracionDescuentos.DoesNotExist:
            config_descuentos = {
                'descuento_pie_factura_ponderado': 0,
                'tramos': [],
                'porcentaje_rebate': 0,
                'aplica_descuento_financiero': False,
                'porcentaje_descuento_financiero': 0,
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

            # Utilidad neta (después de impuestos)
            impuesto = utilidad_antes_impuestos * tasa_impuesto if utilidad_antes_impuestos > 0 else 0
            utilidad_neta = utilidad_antes_impuestos - impuesto

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


@app.get("/api/debug/diferencia-pyg")
def diagnosticar_diferencia_pyg(
    escenario_id: int,
    marca_id: str
) -> Dict[str, Any]:
    """
    Diagnostica diferencias entre P&G Detallado y P&G por Zonas.
    """
    try:
        from core.models import (
            Escenario, Marca, Zona,
            PersonalComercial, GastoComercial
        )
        from api.pyg_service import calcular_pyg_todas_zonas
        from decimal import Decimal

        escenario = Escenario.objects.get(pk=escenario_id)
        marca = Marca.objects.get(marca_id=marca_id)

        # TOTAL DETALLADO
        personal_comercial = PersonalComercial.objects.filter(escenario=escenario, marca=marca)
        total_personal = sum(float(p.calcular_costo_mensual()) for p in personal_comercial)

        gastos_comerciales = GastoComercial.objects.filter(escenario=escenario, marca=marca)
        total_gastos = sum(float(g.valor_mensual) for g in gastos_comerciales)

        total_detallado = total_personal + total_gastos

        # TOTAL ZONAS
        zonas_pyg = calcular_pyg_todas_zonas(escenario, marca)
        total_zonas = sum(float(z['comercial']['total']) for z in zonas_pyg)

        # DIFERENCIA
        diferencia = total_detallado - total_zonas

        # PARTICIPACIONES
        zonas_activas = Zona.objects.filter(escenario=escenario, marca=marca, activo=True)
        suma_participaciones = sum(float(z.participacion_ventas or 0) for z in zonas_activas)

        # POR TIPO
        personal_por_tipo = {}
        for tipo in ['directo', 'proporcional', 'compartido']:
            qs = personal_comercial.filter(tipo_asignacion_geo=tipo)
            personal_por_tipo[tipo] = {
                'count': qs.count(),
                'total': sum(float(p.calcular_costo_mensual()) for p in qs)
            }

        gastos_por_tipo = {}
        for tipo in ['directo', 'proporcional', 'compartido']:
            qs = gastos_comerciales.filter(tipo_asignacion_geo=tipo)
            gastos_por_tipo[tipo] = {
                'count': qs.count(),
                'total': sum(float(g.valor_mensual) for g in qs)
            }

        return {
            'escenario': escenario.nombre,
            'marca': marca.nombre,
            'total_detallado': total_detallado,
            'total_personal': total_personal,
            'total_gastos': total_gastos,
            'total_zonas': total_zonas,
            'diferencia': diferencia,
            'diferencia_porcentaje': (diferencia / total_detallado * 100) if total_detallado > 0 else 0,
            'suma_participaciones': suma_participaciones,
            'personal_por_tipo': personal_por_tipo,
            'gastos_por_tipo': gastos_por_tipo,
        }

    except Exception as e:
        logger.error(f"Error en diagnóstico: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    escenario_id: int
) -> Dict[str, Any]:
    """
    Obtiene el P&G desglosado por municipio para una zona.

    Args:
        zona_id: ID de la zona
        escenario_id: ID del escenario

    Returns:
        Lista de P&G por municipio
    """
    try:
        from core.models import Escenario, Zona
        from api.pyg_service import calcular_pyg_todos_municipios

        escenario = Escenario.objects.get(pk=escenario_id)
        zona = Zona.objects.get(pk=zona_id, escenario=escenario)

        municipios = calcular_pyg_todos_municipios(escenario, zona)

        return {
            'escenario_id': escenario_id,
            'escenario_nombre': escenario.nombre,
            'zona_id': zona_id,
            'zona_nombre': zona.nombre,
            'municipios': [_serializar_pyg_municipio(m) for m in municipios],
            'total_municipios': len(municipios)
        }

    except Escenario.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Escenario no encontrado: {escenario_id}")
    except Zona.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Zona no encontrada: {zona_id}")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
