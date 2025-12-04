"""
Servicio de P&G para la API FastAPI.
Reimplementa la lógica de PyGService usando core.models (alias de admin_panel.core.models).
"""
from decimal import Decimal
from typing import Dict, List
import logging

from core.calculator_lejanias import CalculadoraLejanias

logger = logging.getLogger(__name__)


def calcular_pyg_zona(escenario, zona) -> Dict:
    """
    Calcula el P&G para una zona comercial específica.

    Distribuye costos según tipo_asignacion_geo:
    - directo: 100% si zona coincide
    - proporcional: según participacion_ventas
    - compartido: equitativo entre zonas

    Las lejanías se calculan:
    - Comerciales: directamente para esta zona específica
    - Logísticas: proporcionalmente según participación en ventas de la marca
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

    # Calcular costos administrativos (siempre equitativo)
    administrativo = _distribuir_admin_a_zona(
        escenario, zona, zonas_count
    )

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
    Identifica gastos que son parte de lejanías logísticas y NO deben sumarse
    porque ya están calculados en el simulador como parte de RutaLogistica.

    Estos gastos son creados por signals cuando se configura una ruta,
    pero su valor ya está incluido en el cálculo de lejanías del simulador.
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
      NOTA: Las lejanías logísticas NO incluyen flete_base, que se contabiliza
      en Flota de Vehículos (gastos fijos).
    """
    try:
        calc = CalculadoraLejanias(escenario)

        # Lejanía comercial: directa para esta zona
        lejania_comercial_zona = calc.calcular_lejania_comercial_zona(zona)
        comercial_total = lejania_comercial_zona['total_mensual']

        # Lejanía logística: calcular para toda la marca y prorratear
        # Las rutas logísticas no están asociadas a zonas, sino a la marca completa
        logistica_marca = calc.calcular_lejanias_logisticas_marca(zona.marca)

        # IMPORTANTE: Excluir flete_base de lejanías porque ya está en Flota de Vehículos
        # Lejanías = combustible + peajes + pernocta (costos variables de ruta)
        # Flete base = costo fijo por operación del vehículo/tercero
        lejanias_sin_flete = (
            logistica_marca['total_combustible_mensual'] +
            logistica_marca['total_peaje_mensual'] +
            logistica_marca['total_pernocta_mensual']
        )
        logistica_total = lejanias_sin_flete * participacion

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
    """Distribuye costos de personal y gastos a una zona según tipo_asignacion_geo."""
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

    # Gastos - filtrar lejanías y flota que ya están calculados aparte
    gastos_qs = modelo_gasto.objects.filter(
        escenario=escenario,
        marca=marca
    )
    for g in gastos_qs:
        # Excluir gastos de lejanías que ya están en el cálculo del simulador
        if modelo_gasto == GastoLogistico and _es_gasto_lejania_logistica(g):
            continue
        # Excluir gastos de flota de vehículos (ya están en Flota de Vehículos)
        if modelo_gasto == GastoLogistico and _es_gasto_flota_vehiculos(g):
            continue
        if modelo_gasto == GastoComercial and _es_gasto_lejania_comercial(g):
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
    """Distribuye costos administrativos a una zona (siempre equitativo)."""
    from core.models import PersonalAdministrativo, GastoAdministrativo, Marca

    marca = zona.marca

    # Contar marcas para prorrateo
    marcas_count = Marca.objects.filter(activa=True).count() or 1

    # Costos admin de la marca
    personal_marca = Decimal('0')
    gastos_marca = Decimal('0')

    # Personal administrativo de la marca
    for p in PersonalAdministrativo.objects.filter(escenario=escenario, marca=marca):
        personal_marca += Decimal(str(p.calcular_costo_mensual()))

    # Personal administrativo compartido (se prorratean entre marcas)
    for p in PersonalAdministrativo.objects.filter(escenario=escenario, marca__isnull=True):
        personal_marca += Decimal(str(p.calcular_costo_mensual())) / marcas_count

    # Gastos administrativos de la marca
    for g in GastoAdministrativo.objects.filter(escenario=escenario, marca=marca):
        gastos_marca += g.valor_mensual

    # Gastos administrativos compartidos
    for g in GastoAdministrativo.objects.filter(escenario=escenario, marca__isnull=True):
        gastos_marca += g.valor_mensual / marcas_count

    # Los costos admin se distribuyen equitativamente entre zonas
    factor_zona = Decimal('1') / zonas_count

    return {
        'personal': personal_marca * factor_zona,
        'gastos': gastos_marca * factor_zona,
        'total': (personal_marca + gastos_marca) * factor_zona
    }


def calcular_pyg_todas_zonas(escenario, marca) -> List[Dict]:
    """Calcula P&G para todas las zonas de una marca."""
    from core.models import Zona

    zonas = Zona.objects.filter(
        escenario=escenario,
        marca=marca,
        activo=True
    ).order_by('nombre')

    return [calcular_pyg_zona(escenario, zona) for zona in zonas]


def calcular_pyg_municipio(escenario, zona_municipio) -> Dict:
    """
    Calcula el P&G para un municipio dentro de una zona.

    El costo del municipio es:
    Costo_Zona × (participacion_ventas_municipio / 100)
    """
    zona = zona_municipio.zona
    participacion_mun = (zona_municipio.participacion_ventas or Decimal('0')) / 100

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
    part_total = (zona.participacion_ventas or Decimal('0')) * (zona_municipio.participacion_ventas or Decimal('0')) / 100

    return {
        'municipio': {
            'id': zona_municipio.municipio.id,
            'nombre': zona_municipio.municipio.nombre,
            'codigo_dane': zona_municipio.municipio.codigo_dane,
            'participacion_ventas': float(zona_municipio.participacion_ventas or 0),
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
