"""
Servicio de P&G para la API FastAPI.
Reimplementa la lógica de PyGService usando core.models (alias de admin_panel.core.models).
"""
from decimal import Decimal
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def calcular_pyg_zona(escenario, zona) -> Dict:
    """
    Calcula el P&G para una zona comercial específica.

    Distribuye costos según tipo_asignacion_geo:
    - directo: 100% si zona coincide
    - proporcional: según participacion_ventas
    - compartido: equitativo entre zonas
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

    # Calcular costos comerciales
    comercial = _distribuir_costos_a_zona(
        escenario, zona, participacion, zonas_count,
        PersonalComercial, GastoComercial
    )

    # Calcular costos logísticos
    logistico = _distribuir_costos_a_zona(
        escenario, zona, participacion, zonas_count,
        PersonalLogistico, GastoLogistico
    )

    # Calcular costos administrativos (siempre equitativo)
    administrativo = _distribuir_admin_a_zona(
        escenario, zona, zonas_count
    )

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


def _distribuir_costos_a_zona(
    escenario, zona, participacion: Decimal, zonas_count: int,
    modelo_personal, modelo_gasto
) -> Dict:
    """Distribuye costos de personal y gastos a una zona según tipo_asignacion_geo."""
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

    # Gastos
    gastos_qs = modelo_gasto.objects.filter(
        escenario=escenario,
        marca=marca
    )
    for g in gastos_qs:
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
