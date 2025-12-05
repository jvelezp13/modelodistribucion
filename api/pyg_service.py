"""
Servicio de P&G para la API FastAPI.
Reimplementa la lógica de PyGService usando core.models (alias de admin_panel.core.models).
"""
from decimal import Decimal
from typing import Dict, List
import logging

from core.calculator_lejanias import CalculadoraLejanias

logger = logging.getLogger(__name__)


def calcular_pyg_zona(escenario, zona, admin_totales: Dict = None) -> Dict:
    """
    Calcula el P&G para una zona comercial específica.

    Distribuye costos según tipo_asignacion_geo:
    - directo: 100% si zona coincide
    - proporcional: según participacion_ventas
    - compartido: equitativo entre zonas

    Las lejanías se calculan:
    - Comerciales: directamente para esta zona específica
    - Logísticas: proporcionalmente según participación en ventas de la marca

    Args:
        escenario: Escenario activo
        zona: Zona a calcular
        admin_totales: Dict opcional con {'personal': X, 'gastos': Y} ya calculados
                       por el simulador. Si no se pasa, se calculará internamente.
    """
    from core.models import (
        Zona, PersonalComercial, GastoComercial,
        PersonalLogistico, GastoLogistico,
        PersonalAdministrativo, GastoAdministrativo
    )

    marca = zona.marca
    participacion = (zona.participacion_ventas or Decimal('0')) / 100

    # Contar zonas de la marca
    zonas_marca = Zona.objects.filter(
        escenario=escenario,
        marca=marca,
        activo=True
    )
    zonas_count = zonas_marca.count() or 1

    # Calcular costos comerciales (personal + gastos fijos)
    comercial = _distribuir_costos_a_zona(
        escenario, zona, participacion, zonas_count,
        PersonalComercial, GastoComercial
    )

    # Calcular costos logísticos (personal + gastos fijos)
    logistico = _distribuir_costos_a_zona(
        escenario, zona, participacion, zonas_count,
        PersonalLogistico, GastoLogistico
    )

    # Calcular costos administrativos (siempre equitativo entre zonas)
    if admin_totales:
        # Usar los totales ya calculados por el simulador
        factor_zona = Decimal('1') / zonas_count
        administrativo = {
            'personal': Decimal(str(admin_totales['personal'])) * factor_zona,
            'gastos': Decimal(str(admin_totales['gastos'])) * factor_zona,
            'total': (Decimal(str(admin_totales['personal'])) + Decimal(str(admin_totales['gastos']))) * factor_zona
        }
    else:
        # Calcular usando el simulador (menos eficiente, pero funciona)
        administrativo = _distribuir_admin_a_zona(escenario, zona, zonas_count)

    # Calcular lejanías dinámicas usando CalculadoraLejanias
    lejanias = _calcular_lejanias_zona(escenario, zona, participacion)

    # Agregar lejanías a los totales de comercial y logístico
    comercial['lejanias'] = lejanias['comercial']
    comercial['total'] += lejanias['comercial']

    logistico['lejanias'] = lejanias['logistica']
    logistico['total'] += lejanias['logistica']

    total_mensual = comercial['total'] + logistico['total'] + administrativo['total']

    return {
        'zona': {
            'id': zona.id,
            'nombre': zona.nombre,
            'participacion_ventas': float(zona.participacion_ventas or 0),
        },
        'comercial': comercial,
        'logistico': logistico,
        'administrativo': administrativo,
        'total_mensual': total_mensual,
        'total_anual': total_mensual * 12
    }


def _es_gasto_lejania_logistica(gasto) -> bool:
    """
    Identifica gastos que son parte de rutas logísticas y NO deben sumarse
    porque ya están calculados dinámicamente por CalculadoraLejanias.

    Estos gastos son creados por signals cuando se configura una ruta,
    pero pueden estar desincronizados con el cálculo real.
    Por eso excluimos TODOS los gastos de rutas y usamos el cálculo dinámico.

    Se excluyen:
    - Combustible de rutas
    - Peajes de rutas
    - Viáticos/Pernocta de rutas
    - Flete Base Tercero (ya incluido en el cálculo de lejanías totales)
    """
    nombre = gasto.nombre or ''
    return (
        nombre.startswith('Combustible - ') or
        nombre.startswith('Peajes - ') or
        nombre.startswith('Viáticos Ruta - ') or
        nombre.startswith('Flete Base Tercero - ')
    )


def _es_gasto_flota_vehiculos(gasto) -> bool:
    """
    Identifica gastos que corresponden a la Flota de Vehículos.

    Estos gastos se crean automáticamente desde la tabla Vehiculo por signals
    y NO deben sumarse en 'gastos' porque ya están contabilizados en P&G Detallado
    como rubros de tipo='vehiculo'.

    Los gastos de flota incluyen:
    - Canon Renting
    - Depreciación
    - Mantenimiento
    - Seguros
    - Monitoreo GPS
    - Lavado/Parqueadero
    """
    nombre = gasto.nombre or ''
    tipo = gasto.tipo or ''

    # Excluir por tipo de gasto (todos los relacionados con vehículos)
    tipos_flota = [
        'canon_renting',
        'depreciacion_vehiculo',
        'mantenimiento_vehiculos',
        'lavado_vehiculos',
        'parqueadero_vehiculos',
        'monitoreo_satelital',
    ]
    if tipo in tipos_flota:
        return True

    # Excluir por nombre específico (creados por signals)
    nombres_flota = [
        'Canon Renting Flota',
        'Depreciación Flota Propia',
        'Mantenimiento Flota Propia',
        'Seguros Flota Propia',
        'Aseo y Limpieza Vehículos',
        'Parqueaderos',
        'Monitoreo Satelital (GPS)',
        'Seguro de Mercancía',
    ]
    if nombre in nombres_flota:
        return True

    return False


def _es_gasto_lejania_comercial(gasto) -> bool:
    """
    Identifica gastos que son parte de lejanías comerciales y NO deben sumarse
    porque ya están calculados en el simulador como parte de Zona comercial.
    """
    nombre = gasto.nombre or ''
    return (
        nombre.startswith('Combustible Lejanía') or
        nombre.startswith('Viáticos Pernocta')
    )


def _calcular_lejanias_zona(escenario, zona, participacion: Decimal) -> Dict:
    """
    Calcula las lejanías para una zona específica usando CalculadoraLejanias.

    - Lejanías comerciales: se calculan directamente para la zona
    - Lejanías logísticas: se prorratean según participación de la zona en ventas de marca

    NOTA: Las lejanías logísticas incluyen:
    - Flete base de rutas (terceros)
    - Combustible, peajes, pernocta
    - Costos fijos de vehículos (monitoreo, seguros, etc.) - calculados aparte
    """
    from core.models import Vehiculo

    try:
        calc = CalculadoraLejanias(escenario)
        marca = zona.marca

        # Lejanía comercial: directa para esta zona
        lejania_comercial_zona = calc.calcular_lejania_comercial_zona(zona)
        comercial_total = lejania_comercial_zona['total_mensual']

        # Lejanía logística: calcular para toda la marca y prorratear
        logistica_marca = calc.calcular_lejanias_logisticas_marca(marca)

        # El cálculo de lejanías incluye flete_base pero NO los costos fijos de vehículos
        # (monitoreo, seguros mercancía, etc.) que están en la tabla Vehiculo.
        # Necesitamos agregar esos costos para que coincida con P&G Detallado.
        costos_fijos_vehiculos = Decimal('0')
        vehiculos = Vehiculo.objects.filter(escenario=escenario, marca=marca)
        for v in vehiculos:
            # Costos que aplican a todos los esquemas (incluyendo terceros)
            costos_fijos_vehiculos += (v.costo_monitoreo_mensual + v.costo_seguro_mercancia_mensual) * v.cantidad
            # Costos adicionales para renting y tradicional
            if v.esquema in ['renting', 'tradicional']:
                costos_fijos_vehiculos += (v.costo_lavado_mensual + v.costo_parqueadero_mensual) * v.cantidad
                if v.esquema == 'renting':
                    costos_fijos_vehiculos += v.canon_renting * v.cantidad
                elif v.esquema == 'tradicional':
                    if v.vida_util_anios > 0:
                        depreciacion = (v.costo_compra - v.valor_residual) / (v.vida_util_anios * 12)
                        costos_fijos_vehiculos += depreciacion * v.cantidad
                    costos_fijos_vehiculos += (v.costo_mantenimiento_mensual + v.costo_seguro_mensual) * v.cantidad

        # Total logístico = lejanías de rutas + costos fijos de vehículos
        logistica_rutas = logistica_marca['total_mensual']
        logistica_total = (logistica_rutas + costos_fijos_vehiculos) * participacion

        return {
            'comercial': comercial_total,
            'logistica': logistica_total,
            'total': comercial_total + logistica_total
        }
    except Exception as e:
        logger.warning(f"Error calculando lejanías para zona {zona.nombre}: {e}")
        return {
            'comercial': Decimal('0'),
            'logistica': Decimal('0'),
            'total': Decimal('0')
        }


def _distribuir_costos_a_zona(
    escenario, zona, participacion: Decimal, zonas_count: int,
    modelo_personal, modelo_gasto
) -> Dict:
    """
    Distribuye costos de personal y gastos a una zona según tipo_asignacion_geo.

    Para gastos logísticos:
    - Excluye gastos de lejanías (ya calculados dinámicamente por CalculadoraLejanias)
    - Excluye gastos de flota de vehículos (ya calculados desde tabla Vehiculo en _calcular_lejanias_zona)

    Esto es consistente con P&G Detallado que separa:
    - Personal: desde tabla Personal*
    - Gastos: desde tabla Gasto* (excluyendo lejanías y flota)
    - Flota: desde tabla Vehiculo
    - Lejanías: desde CalculadoraLejanias
    """
    from core.models import GastoLogistico, GastoComercial

    marca = zona.marca
    personal_total = Decimal('0')
    gastos_total = Decimal('0')

    # Personal
    personal_qs = modelo_personal.objects.filter(
        escenario=escenario,
        marca=marca
    )
    for p in personal_qs:
        costo = Decimal(str(p.calcular_costo_mensual()))
        asignacion_geo = getattr(p, 'tipo_asignacion_geo', 'proporcional')
        zona_asignada = getattr(p, 'zona', None)

        if asignacion_geo == 'directo':
            if zona_asignada and zona_asignada.id == zona.id:
                personal_total += costo
        elif asignacion_geo == 'proporcional':
            personal_total += costo * participacion
        elif asignacion_geo == 'compartido':
            personal_total += costo / zonas_count

    # Gastos - excluir lejanías y flota (calculados aparte)
    gastos_qs = modelo_gasto.objects.filter(
        escenario=escenario,
        marca=marca
    )
    for g in gastos_qs:
        # Excluir gastos de lejanías que ya están en el cálculo dinámico
        if modelo_gasto == GastoLogistico and _es_gasto_lejania_logistica(g):
            continue
        if modelo_gasto == GastoComercial and _es_gasto_lejania_comercial(g):
            continue

        # Excluir gastos de flota de vehículos (se calculan desde tabla Vehiculo)
        # Esto evita doble conteo ya que _calcular_lejanias_zona incluye costos de vehículos
        if modelo_gasto == GastoLogistico and _es_gasto_flota_vehiculos(g):
            continue

        asignacion_geo = getattr(g, 'tipo_asignacion_geo', 'proporcional')
        zona_asignada = getattr(g, 'zona', None)

        if asignacion_geo == 'directo':
            if zona_asignada and zona_asignada.id == zona.id:
                gastos_total += g.valor_mensual
        elif asignacion_geo == 'proporcional':
            gastos_total += g.valor_mensual * participacion
        elif asignacion_geo == 'compartido':
            gastos_total += g.valor_mensual / zonas_count

    return {
        'personal': personal_total,
        'gastos': gastos_total,
        'total': personal_total + gastos_total
    }


def _distribuir_admin_a_zona(escenario, zona, zonas_count: int) -> Dict:
    """
    Distribuye costos administrativos a una zona (siempre equitativo entre zonas).

    Usa el SIMULADOR para obtener los valores exactos de admin (igual que P&G Detallado),
    luego divide equitativamente entre las zonas de la marca.
    """
    from core.simulator import Simulator
    from utils.loaders_db import DataLoaderDB

    marca = zona.marca

    # Usar el simulador para obtener los valores exactos de admin
    # Esto garantiza que coincida con P&G Detallado
    loader = DataLoaderDB(escenario_id=escenario.id)
    simulator = Simulator(loader=loader)
    simulator.cargar_marcas([marca.marca_id])
    resultado = simulator.ejecutar_simulacion()

    # Encontrar la marca en los resultados
    marca_sim = next((m for m in resultado.marcas if m.marca_id == marca.marca_id), None)

    if not marca_sim:
        # Fallback si no se encuentra
        return {
            'personal': Decimal('0'),
            'gastos': Decimal('0'),
            'total': Decimal('0')
        }

    # Sumar rubros administrativos del simulador
    personal_total = Decimal('0')
    gastos_total = Decimal('0')

    todos_rubros = marca_sim.rubros_individuales + marca_sim.rubros_compartidos_asignados
    for rubro in todos_rubros:
        if rubro.categoria == 'administrativo':
            valor = Decimal(str(rubro.valor_total))
            if rubro.tipo == 'personal':
                personal_total += valor
            else:
                gastos_total += valor

    # Los costos admin se distribuyen equitativamente entre zonas
    factor_zona = Decimal('1') / zonas_count

    return {
        'personal': personal_total * factor_zona,
        'gastos': gastos_total * factor_zona,
        'total': (personal_total + gastos_total) * factor_zona
    }


def calcular_pyg_todas_zonas(escenario, marca) -> List[Dict]:
    """
    Calcula P&G para todas las zonas de una marca.

    Distribución de costos:
    - Comercial: personal y gastos proporcionales por participación, lejanías directas por zona
    - Logístico: distribuido según municipios atendidos y venta proyectada
    - Administrativo: equitativo entre zonas
    """
    from core.models import Zona
    from core.simulator import Simulator
    from utils.loaders_db import DataLoaderDB
    from core.calculator_lejanias import CalculadoraLejanias

    zonas = Zona.objects.filter(
        escenario=escenario,
        marca=marca,
        activo=True
    ).order_by('nombre')

    zonas_count = zonas.count() or 1

    # Ejecutar simulador UNA vez para obtener totales correctos
    loader = DataLoaderDB(escenario_id=escenario.id)
    simulator = Simulator(loader=loader)
    simulator.cargar_marcas([marca.marca_id])
    resultado = simulator.ejecutar_simulacion()

    # Encontrar la marca en los resultados
    marca_sim = next((m for m in resultado.marcas if m.marca_id == marca.marca_id), None)

    # Totales por categoría del simulador (igual que P&G Detallado)
    totales_marca = {
        'comercial_personal': Decimal('0'),
        'comercial_gastos': Decimal('0'),
        'logistico_personal': Decimal('0'),
        'logistico_gastos': Decimal('0'),
        'logistico_flota': Decimal('0'),
        'admin_personal': Decimal('0'),
        'admin_gastos': Decimal('0'),
    }

    if marca_sim:
        todos_rubros = marca_sim.rubros_individuales + marca_sim.rubros_compartidos_asignados

        # Funciones de filtrado (igual que main.py diagnóstico)
        def es_gasto_logistico_filtrable(nombre: str) -> bool:
            return (
                nombre.startswith('Combustible - ') or
                nombre.startswith('Peajes - ') or
                nombre.startswith('Viáticos Ruta - ') or
                nombre.startswith('Flete Base Tercero - ') or
                nombre == 'Flete Transporte (Tercero)'
            )

        def es_gasto_comercial_lejania(nombre: str) -> bool:
            return 'Combustible Lejanía' in nombre or 'Viáticos Pernocta' in nombre

        for rubro in todos_rubros:
            valor = Decimal(str(rubro.valor_total))
            nombre = rubro.nombre or ''

            if rubro.categoria == 'comercial':
                if rubro.tipo == 'personal':
                    totales_marca['comercial_personal'] += valor
                elif not es_gasto_comercial_lejania(nombre):
                    totales_marca['comercial_gastos'] += valor
            elif rubro.categoria == 'logistico':
                if rubro.tipo == 'vehiculo':
                    totales_marca['logistico_flota'] += valor
                elif rubro.tipo == 'personal':
                    totales_marca['logistico_personal'] += valor
                elif not es_gasto_logistico_filtrable(nombre):
                    totales_marca['logistico_gastos'] += valor
            elif rubro.categoria == 'administrativo':
                if rubro.tipo == 'personal':
                    totales_marca['admin_personal'] += valor
                else:
                    totales_marca['admin_gastos'] += valor

    # Calculadora de lejanías
    calc = CalculadoraLejanias(escenario)

    # Distribuir costos logísticos a zonas según municipios atendidos
    # Esto incluye: flete + combustible + peajes + pernocta de rutas
    costos_logisticos_por_zona = calc.distribuir_costos_logisticos_a_zonas(marca)

    # Distribuir costos fijos de vehículos (flota) según rutas que atienden
    flota_por_zona = calc.distribuir_flota_a_zonas(marca)

    # Calcular P&G por zona
    resultados = []
    for zona in zonas:
        participacion = (zona.participacion_ventas or Decimal('0')) / 100

        # Lejanía comercial es específica por zona (vendedor)
        lej_comercial_zona = calc.calcular_lejania_comercial_zona(zona)['total_mensual']

        # Comercial: personal y gastos proporcionales, lejanía directa
        comercial = {
            'personal': totales_marca['comercial_personal'] * participacion,
            'gastos': totales_marca['comercial_gastos'] * participacion,
            'lejanias': lej_comercial_zona,
            'total': (totales_marca['comercial_personal'] + totales_marca['comercial_gastos']) * participacion + lej_comercial_zona
        }

        # Logístico: personal y gastos proporcionales
        # Lejanías y flota se distribuyen según municipios atendidos por las rutas
        costo_logistico_zona = Decimal('0')
        if zona.id in costos_logisticos_por_zona:
            costo_logistico_zona = costos_logisticos_por_zona[zona.id]['costo_logistico_total']

        # Flota de vehículos: distribuida según rutas que atienden cada zona
        flota_zona = Decimal('0')
        if zona.id in flota_por_zona:
            flota_zona = flota_por_zona[zona.id]['costo_flota_total']

        logistico = {
            'personal': totales_marca['logistico_personal'] * participacion,
            'gastos': totales_marca['logistico_gastos'] * participacion,
            'lejanias': costo_logistico_zona + flota_zona,
            'total': (totales_marca['logistico_personal'] + totales_marca['logistico_gastos']) * participacion + costo_logistico_zona + flota_zona
        }

        # Administrativo: equitativo entre zonas
        factor_zona = Decimal('1') / zonas_count
        administrativo = {
            'personal': totales_marca['admin_personal'] * factor_zona,
            'gastos': totales_marca['admin_gastos'] * factor_zona,
            'total': (totales_marca['admin_personal'] + totales_marca['admin_gastos']) * factor_zona
        }

        total_mensual = comercial['total'] + logistico['total'] + administrativo['total']

        resultados.append({
            'zona': {
                'id': zona.id,
                'nombre': zona.nombre,
                'participacion_ventas': float(zona.participacion_ventas or 0),
            },
            'comercial': comercial,
            'logistico': logistico,
            'administrativo': administrativo,
            'total_mensual': total_mensual,
            'total_anual': total_mensual * 12
        })

    return resultados


def calcular_pyg_municipio(escenario, zona_municipio) -> Dict:
    """
    Calcula el P&G para un municipio dentro de una zona.

    El costo del municipio es:
    Costo_Zona × (participacion_ventas_municipio / 100)

    La participación se obtiene de VentaMunicipio (tabla de ventas por municipio)
    ya que ZonaMunicipio solo tiene la relación zona-municipio sin ventas.
    """
    from core.models import VentaMunicipio

    zona = zona_municipio.zona
    municipio = zona_municipio.municipio

    # Obtener participación desde VentaMunicipio
    participacion_ventas = Decimal('0')
    try:
        venta_mun = VentaMunicipio.objects.get(
            marca=zona.marca,
            escenario=escenario,
            municipio=municipio
        )
        participacion_ventas = venta_mun.participacion_ventas or Decimal('0')
    except VentaMunicipio.DoesNotExist:
        pass

    participacion_mun = participacion_ventas / 100

    # Obtener P&G de la zona
    pyg_zona = calcular_pyg_zona(escenario, zona)

    # Multiplicar por participación del municipio
    comercial = {
        'personal': pyg_zona['comercial']['personal'] * participacion_mun,
        'gastos': pyg_zona['comercial']['gastos'] * participacion_mun,
        'total': pyg_zona['comercial']['total'] * participacion_mun
    }
    logistico = {
        'personal': pyg_zona['logistico']['personal'] * participacion_mun,
        'gastos': pyg_zona['logistico']['gastos'] * participacion_mun,
        'total': pyg_zona['logistico']['total'] * participacion_mun
    }
    administrativo = {
        'personal': pyg_zona['administrativo']['personal'] * participacion_mun,
        'gastos': pyg_zona['administrativo']['gastos'] * participacion_mun,
        'total': pyg_zona['administrativo']['total'] * participacion_mun
    }

    total_mensual = comercial['total'] + logistico['total'] + administrativo['total']

    # Calcular participación total (zona × municipio)
    part_total = (zona.participacion_ventas or Decimal('0')) * participacion_ventas / 100

    return {
        'municipio': {
            'id': municipio.id,
            'nombre': municipio.nombre,
            'codigo_dane': municipio.codigo_dane,
            'participacion_ventas': float(participacion_ventas),
            'participacion_total': float(part_total),
        },
        'zona': {
            'id': zona.id,
            'nombre': zona.nombre,
        },
        'comercial': comercial,
        'logistico': logistico,
        'administrativo': administrativo,
        'total_mensual': total_mensual,
        'total_anual': total_mensual * 12
    }


def calcular_pyg_todos_municipios(escenario, zona) -> List[Dict]:
    """Calcula P&G para todos los municipios de una zona."""
    from core.models import ZonaMunicipio

    municipios = ZonaMunicipio.objects.filter(
        zona=zona
    ).select_related('municipio').order_by('municipio__nombre')

    return [calcular_pyg_municipio(escenario, zm) for zm in municipios]
