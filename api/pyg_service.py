"""
Servicio de P&G para la API FastAPI.
Reimplementa la lógica de PyGService usando core.models (alias de admin_panel.core.models).
"""
from decimal import Decimal
from typing import Dict, List, Optional
import logging

from django.db.models import Sum
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

    # Obtener información de la operación (si existe)
    operacion_info = None
    tasa_ica = Decimal('0')
    if zona.operacion:
        operacion_info = {
            'id': zona.operacion.id,
            'nombre': zona.operacion.nombre,
            'codigo': zona.operacion.codigo,
        }
        # tasa_ica viene en porcentaje (0-100), convertir a decimal (0-1)
        tasa_ica = (zona.operacion.tasa_ica or Decimal('0')) / Decimal('100')

    return {
        'zona': {
            'id': zona.id,
            'nombre': zona.nombre,
            'participacion_ventas': float(zona.participacion_ventas or 0),
            'operacion': operacion_info,
            'tasa_ica': float(tasa_ica),  # Ya convertido a decimal (0-1)
        },
        'comercial': comercial,
        'logistico': logistico,
        'administrativo': administrativo,
        'total_mensual': total_mensual,
        'total_anual': total_mensual * 12
    }


# =============================================================================
# FILTROS DE GASTOS - Funciones centralizadas para identificar tipos de gastos
# Usadas por pyg_service.py y main.py para evitar duplicación
# =============================================================================

# Constantes para filtros de flota
TIPOS_FLOTA = [
    'canon_renting',
    'depreciacion_vehiculo',
    'mantenimiento_vehiculos',
    'lavado_vehiculos',
    'parqueadero_vehiculos',
    'monitoreo_satelital',
]

NOMBRES_FLOTA = [
    'Canon Renting Flota',
    'Depreciación Flota Propia',
    'Mantenimiento Flota Propia',
    'Seguros Flota Propia',
    'Aseo y Limpieza Vehículos',
    'Parqueaderos',
    'Monitoreo Satelital (GPS)',
    'Seguro de Mercancía',
]


def es_gasto_lejania_logistica(nombre: str) -> bool:
    """
    Identifica gastos que son parte de rutas logísticas y NO deben sumarse
    porque ya están calculados dinámicamente por CalculadoraLejanias.

    Se excluyen:
    - Combustible de rutas
    - Peajes de rutas
    - Viáticos/Pernocta de rutas
    - Flete Base Tercero
    - Flete Transporte (Tercero)
    """
    return (
        nombre.startswith('Combustible - ') or
        nombre.startswith('Peajes - ') or
        nombre.startswith('Viáticos Ruta - ') or
        nombre.startswith('Flete Base Tercero - ') or
        nombre == 'Flete Transporte (Tercero)'
    )


def es_gasto_flota_vehiculos(nombre: str, tipo: str = '') -> bool:
    """
    Identifica gastos que corresponden a la Flota de Vehículos.

    Estos gastos se crean automáticamente desde la tabla Vehiculo por signals
    y NO deben sumarse en 'gastos' porque ya están contabilizados en P&G Detallado
    como rubros de tipo='vehiculo'.
    """
    return tipo in TIPOS_FLOTA or nombre in NOMBRES_FLOTA


def es_gasto_lejania_comercial(nombre: str) -> bool:
    """
    Identifica gastos que son parte de lejanías comerciales y NO deben sumarse
    porque ya están calculados en el simulador como parte de Zona comercial.
    """
    return (
        nombre.startswith('Combustible Lejanía') or
        nombre.startswith('Viáticos Pernocta')
    )


def _calcular_lejanias_zona(escenario, zona, participacion: Decimal) -> Dict:
    """
    Calcula las lejanías para una zona específica usando CalculadoraLejanias.

    - Lejanías comerciales: se calculan directamente para la zona + comité comercial
    - Lejanías logísticas: se prorratean según participación de la zona en ventas de marca

    NOTA: Las lejanías logísticas incluyen:
    - Flete base de rutas (terceros)
    - Combustible, peajes, pernocta
    - Costos fijos de vehículos (monitoreo, seguros, etc.) - calculados aparte
    """
    from core.models import Vehiculo, GastoComercial

    try:
        calc = CalculadoraLejanias(escenario)
        marca = zona.marca

        # Lejanía comercial: directa para esta zona
        lejania_comercial_zona = calc.calcular_lejania_comercial_zona(zona)
        comercial_total = lejania_comercial_zona['total_mensual']

        # Agregar costo del comité comercial para esta zona (ambos registros: Combustible y Mant/Dep/Llan)
        comite_gastos = GastoComercial.objects.filter(
            escenario=escenario,
            nombre__startswith=f'Comité Comercial',
            zona=zona
        )
        for comite_gasto in comite_gastos:
            comercial_total += Decimal(str(comite_gasto.valor_mensual))

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
        nombre = g.nombre or ''
        tipo = g.tipo or ''

        # Excluir gastos de lejanías que ya están en el cálculo dinámico
        if modelo_gasto == GastoLogistico and es_gasto_lejania_logistica(nombre):
            continue
        if modelo_gasto == GastoComercial and es_gasto_lejania_comercial(nombre):
            continue

        # Excluir gastos de flota de vehículos (se calculan desde tabla Vehiculo)
        if modelo_gasto == GastoLogistico and es_gasto_flota_vehiculos(nombre, tipo):
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


def calcular_pyg_todas_zonas(escenario, marca, operacion_ids: Optional[List[int]] = None) -> List[Dict]:
    """
    Calcula P&G para todas las zonas de una marca.

    Distribución de costos respetando tipo_asignacion_geo:
    - directo: 100% a la zona asignada
    - proporcional: según participacion_ventas de la zona
    - compartido: equitativo entre todas las zonas

    Lejanías:
    - Comerciales: directas por zona (calculadas por CalculadoraLejanias)
    - Logísticas: distribuidas según municipios atendidos por las rutas

    OPTIMIZACIÓN: Pre-carga todos los datos una sola vez antes del loop.

    Args:
        escenario: Escenario activo
        marca: Marca a calcular
        operacion_ids: Lista opcional de IDs de operaciones para filtrar zonas
    """
    from core.models import (
        Zona, PersonalComercial, GastoComercial,
        PersonalLogistico, GastoLogistico
    )
    from core.calculator_lejanias import CalculadoraLejanias
    from core.simulator import Simulator
    from utils.loaders_db import DataLoaderDB

    # Filtro base de zonas
    zonas_filter = {
        'escenario': escenario,
        'marca': marca,
        'activo': True
    }

    zonas = Zona.objects.filter(**zonas_filter)

    # Filtrar por operaciones si se especifican
    if operacion_ids:
        zonas = zonas.filter(operacion_id__in=operacion_ids)

    zonas = zonas.order_by('nombre')

    zonas_list = list(zonas)
    zonas_count = len(zonas_list) or 1

    # =========================================================================
    # PRE-CARGA DE DATOS (una sola vez, antes del loop)
    # =========================================================================

    # 1. Pre-cargar todo el personal y gastos (evita N+1 queries)
    todo_personal_comercial = list(PersonalComercial.objects.filter(
        escenario=escenario, marca=marca
    ))
    todo_gasto_comercial = [
        g for g in GastoComercial.objects.filter(escenario=escenario, marca=marca)
        if not es_gasto_lejania_comercial(g.nombre or '')
    ]
    todo_personal_logistico = list(PersonalLogistico.objects.filter(
        escenario=escenario, marca=marca
    ))
    todo_gasto_logistico = [
        g for g in GastoLogistico.objects.filter(escenario=escenario, marca=marca)
        if not es_gasto_lejania_logistica(g.nombre or '')
    ]

    # 2. Pre-calcular costos de personal (evita llamar calcular_costo_mensual múltiples veces)
    costos_personal_comercial = [
        {
            'costo': Decimal(str(p.calcular_costo_mensual())),
            'tipo_asignacion': getattr(p, 'tipo_asignacion_geo', 'proporcional'),
            'zona_id': p.zona_id if hasattr(p, 'zona_id') else None
        }
        for p in todo_personal_comercial
    ]
    costos_personal_logistico = [
        {
            'costo': Decimal(str(p.calcular_costo_mensual())),
            'tipo_asignacion': getattr(p, 'tipo_asignacion_geo', 'proporcional'),
            'zona_id': p.zona_id if hasattr(p, 'zona_id') else None
        }
        for p in todo_personal_logistico
    ]
    costos_gastos_comercial = [
        {
            'costo': g.valor_mensual or Decimal('0'),
            'tipo_asignacion': getattr(g, 'tipo_asignacion_geo', 'proporcional'),
            'zona_id': g.zona_id if hasattr(g, 'zona_id') else None
        }
        for g in todo_gasto_comercial
    ]
    costos_gastos_logistico = [
        {
            'costo': g.valor_mensual or Decimal('0'),
            'tipo_asignacion': getattr(g, 'tipo_asignacion_geo', 'proporcional'),
            'zona_id': g.zona_id if hasattr(g, 'zona_id') else None
        }
        for g in todo_gasto_logistico
    ]

    # 3. Obtener totales administrativos desde el Simulador
    loader = DataLoaderDB(escenario_id=escenario.id)
    simulator = Simulator(loader=loader)
    simulator.cargar_marcas([marca.marca_id])
    resultado_sim = simulator.ejecutar_simulacion()
    marca_sim = next((m for m in resultado_sim.marcas if m.marca_id == marca.marca_id), None)

    admin_personal_marca = Decimal('0')
    admin_gastos_marca = Decimal('0')
    if marca_sim:
        todos_rubros = marca_sim.rubros_individuales + marca_sim.rubros_compartidos_asignados
        for rubro in todos_rubros:
            if rubro.categoria == 'administrativo':
                valor = Decimal(str(rubro.valor_total))
                if rubro.tipo == 'personal':
                    admin_personal_marca += valor
                else:
                    admin_gastos_marca += valor

    # 4. Calculadora de lejanías (pre-calcular distribuciones)
    calc = CalculadoraLejanias(escenario)
    costos_logisticos_por_zona = calc.distribuir_costos_logisticos_a_zonas(marca)
    flota_por_zona = calc.distribuir_flota_a_zonas(marca)

    # 5. Pre-calcular lejanías comerciales por zona (incluyendo comité comercial)
    lejanias_comerciales_por_zona = {}
    for zona in zonas_list:
        # Lejanía comercial base (combustible + mant/deprec + pernocta)
        lejania_base = calc.calcular_lejania_comercial_zona(zona)['total_mensual']

        # Agregar costo del comité comercial para esta zona (ambos registros: Combustible y Mant/Dep/Llan)
        comite_costo = GastoComercial.objects.filter(
            escenario=escenario,
            nombre__startswith='Comité Comercial',
            zona=zona
        ).aggregate(total=Sum('valor_mensual'))['total'] or Decimal('0')

        lejanias_comerciales_por_zona[zona.id] = lejania_base + comite_costo

    # =========================================================================
    # FUNCIÓN DE DISTRIBUCIÓN
    # =========================================================================
    def distribuir_costo(costo: Decimal, tipo_asignacion: str, zona_asignada_id: int, zona_id: int, participacion: Decimal) -> Decimal:
        if tipo_asignacion == 'directo':
            if zona_asignada_id and zona_asignada_id == zona_id:
                return costo
            return Decimal('0')
        elif tipo_asignacion == 'proporcional':
            return costo * participacion
        elif tipo_asignacion == 'compartido':
            return costo / zonas_count
        else:
            return costo * participacion

    # =========================================================================
    # CALCULAR P&G POR ZONA (usando datos pre-cargados)
    # =========================================================================
    resultados = []
    for zona in zonas_list:
        participacion = (zona.participacion_ventas or Decimal('0')) / 100

        # === COMERCIAL ===
        comercial_personal = sum(
            distribuir_costo(p['costo'], p['tipo_asignacion'], p['zona_id'], zona.id, participacion)
            for p in costos_personal_comercial
        )
        comercial_gastos = sum(
            distribuir_costo(g['costo'], g['tipo_asignacion'], g['zona_id'], zona.id, participacion)
            for g in costos_gastos_comercial
        )
        lej_comercial_zona = lejanias_comerciales_por_zona.get(zona.id, Decimal('0'))

        comercial = {
            'personal': comercial_personal,
            'gastos': comercial_gastos,
            'lejanias': lej_comercial_zona,
            'total': comercial_personal + comercial_gastos + lej_comercial_zona
        }

        # === LOGÍSTICO ===
        logistico_personal = sum(
            distribuir_costo(p['costo'], p['tipo_asignacion'], p['zona_id'], zona.id, participacion)
            for p in costos_personal_logistico
        )
        logistico_gastos = sum(
            distribuir_costo(g['costo'], g['tipo_asignacion'], g['zona_id'], zona.id, participacion)
            for g in costos_gastos_logistico
        )

        costo_logistico_zona = Decimal('0')
        if zona.id in costos_logisticos_por_zona:
            costo_logistico_zona = costos_logisticos_por_zona[zona.id]['costo_logistico_total']

        flota_zona = Decimal('0')
        if zona.id in flota_por_zona:
            flota_zona = flota_por_zona[zona.id]['costo_flota_total']

        logistico = {
            'personal': logistico_personal,
            'gastos': logistico_gastos,
            'lejanias': costo_logistico_zona + flota_zona,
            'total': logistico_personal + logistico_gastos + costo_logistico_zona + flota_zona
        }

        # === ADMINISTRATIVO ===
        factor_zona = Decimal('1') / zonas_count

        administrativo = {
            'personal': admin_personal_marca * factor_zona,
            'gastos': admin_gastos_marca * factor_zona,
            'total': (admin_personal_marca + admin_gastos_marca) * factor_zona
        }

        total_mensual = comercial['total'] + logistico['total'] + administrativo['total']

        # Obtener información de la operación (si existe)
        operacion_info = None
        tasa_ica = Decimal('0')
        if zona.operacion:
            operacion_info = {
                'id': zona.operacion.id,
                'nombre': zona.operacion.nombre,
                'codigo': zona.operacion.codigo,
            }
            # tasa_ica viene en porcentaje (0-100), convertir a decimal (0-1)
            tasa_ica = (zona.operacion.tasa_ica or Decimal('0')) / Decimal('100')

        resultados.append({
            'zona': {
                'id': zona.id,
                'nombre': zona.nombre,
                'participacion_ventas': float(zona.participacion_ventas or 0),
                'operacion': operacion_info,
                'tasa_ica': float(tasa_ica),  # Ya convertido a decimal (0-1)
            },
            'comercial': comercial,
            'logistico': logistico,
            'administrativo': administrativo,
            'total_mensual': total_mensual,
            'total_anual': total_mensual * 12
        })

    return resultados


def calcular_pyg_todos_municipios(escenario, zona) -> List[Dict]:
    """
    Calcula P&G para todos los municipios de una zona.

    Lógica MEJORADA:
    - Lejanías COMERCIALES (combustible): Se calculan REALMENTE por municipio según distancia
    - Pernocta comercial: Se prorratea por participación (es a nivel de zona/viaje)
    - Personal y gastos fijos: Se prorratean por participación
    - Lejanías LOGÍSTICAS: Se prorratean (dependen de rutas, no de municipios)
    - Administrativo: Se prorratea por participación

    Esto hace que municipios más lejanos tengan mayor costo y menor margen.
    """
    from core.models import ZonaMunicipio

    marca = zona.marca

    # Obtener municipios de la zona con su participación ya calculada
    zona_municipios = ZonaMunicipio.objects.filter(
        zona=zona
    ).select_related('municipio').order_by('municipio__nombre')

    if not zona_municipios.exists():
        return []

    # Usar directamente ZonaMunicipio.participacion_ventas
    pesos_relativos = {}
    ventas_proyectadas = {}
    for zm in zona_municipios:
        pesos_relativos[zm.municipio.id] = (zm.participacion_ventas or Decimal('0')) / 100
        ventas_proyectadas[zm.municipio.id] = zm.venta_proyectada or Decimal('0')

    # Obtener P&G de la zona usando la MISMA función que la vista de zonas
    pyg_todas_zonas = calcular_pyg_todas_zonas(escenario, marca)
    pyg_zona = next((z for z in pyg_todas_zonas if z['zona']['id'] == zona.id), None)

    if not pyg_zona:
        return []

    # =========================================================================
    # CALCULAR LEJANÍAS COMERCIALES REALES POR MUNICIPIO
    # =========================================================================
    calculadora = CalculadoraLejanias(escenario)
    lejania_zona = calculadora.calcular_lejania_comercial_zona(zona)

    # Crear diccionario de combustible por municipio_id
    combustible_por_municipio = {}
    if lejania_zona.get('detalle') and lejania_zona['detalle'].get('municipios'):
        for mun_detalle in lejania_zona['detalle']['municipios']:
            mun_id = mun_detalle.get('municipio_id')
            if mun_id:
                combustible_por_municipio[mun_id] = Decimal(str(mun_detalle.get('combustible_mensual', 0)))

    # Pernocta total de la zona (se prorrateará por participación)
    pernocta_zona = lejania_zona.get('pernocta_mensual', Decimal('0'))
    if not isinstance(pernocta_zona, Decimal):
        pernocta_zona = Decimal(str(pernocta_zona))

    # =========================================================================
    # CONSTRUIR RESULTADO POR MUNICIPIO
    # =========================================================================
    resultados = []
    for zm in zona_municipios:
        mun_id = zm.municipio.id
        peso = pesos_relativos.get(mun_id, Decimal('0'))
        venta_proy = ventas_proyectadas.get(mun_id, Decimal('0'))

        # Convertir valores de pyg_zona a Decimal
        comercial_personal = Decimal(str(pyg_zona['comercial']['personal']))
        comercial_gastos = Decimal(str(pyg_zona['comercial']['gastos']))

        logistico_personal = Decimal(str(pyg_zona['logistico']['personal']))
        logistico_gastos = Decimal(str(pyg_zona['logistico']['gastos']))
        logistico_lejanias = Decimal(str(pyg_zona['logistico'].get('lejanias', 0)))

        admin_personal = Decimal(str(pyg_zona['administrativo']['personal']))
        admin_gastos = Decimal(str(pyg_zona['administrativo']['gastos']))

        # ---------------------------------------------------------------------
        # COMERCIAL: Lejanías REALES por municipio, resto prorrateado
        # ---------------------------------------------------------------------
        combustible_real = combustible_por_municipio.get(mun_id, Decimal('0'))
        pernocta_prorrateada = pernocta_zona * peso
        lejania_comercial_mun = combustible_real + pernocta_prorrateada

        comercial = {
            'personal': comercial_personal * peso,
            'gastos': comercial_gastos * peso,
            'lejanias': lejania_comercial_mun,
            'combustible': combustible_real,  # Detalle: combustible real
            'pernocta': pernocta_prorrateada,  # Detalle: pernocta prorrateada
            'total': (comercial_personal * peso) + (comercial_gastos * peso) + lejania_comercial_mun
        }

        # ---------------------------------------------------------------------
        # LOGÍSTICO: Todo prorrateado (depende de rutas, no de municipios)
        # ---------------------------------------------------------------------
        logistico = {
            'personal': logistico_personal * peso,
            'gastos': logistico_gastos * peso,
            'lejanias': logistico_lejanias * peso,
            'total': (logistico_personal + logistico_gastos + logistico_lejanias) * peso
        }

        # ---------------------------------------------------------------------
        # ADMINISTRATIVO: Prorrateado
        # ---------------------------------------------------------------------
        administrativo = {
            'personal': admin_personal * peso,
            'gastos': admin_gastos * peso,
            'total': (admin_personal + admin_gastos) * peso
        }

        total_mensual = comercial['total'] + logistico['total'] + administrativo['total']

        # Participación sobre la marca
        part_zona_decimal = Decimal(str(pyg_zona['zona']['participacion_ventas'])) / 100
        part_total = part_zona_decimal * peso * 100

        resultados.append({
            'municipio': {
                'id': mun_id,
                'nombre': zm.municipio.nombre,
                'codigo_dane': zm.municipio.codigo_dane,
                'venta_proyectada': float(venta_proy),
                'participacion_zona': float(peso * 100),
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
        })

    return resultados


# =============================================================================
# FUNCIONES P&G POR OPERACIÓN
# =============================================================================

def calcular_pyg_operacion(escenario, operacion) -> Dict:
    """
    Calcula P&G consolidado para una operación (todas las marcas).

    1. Obtiene todas las marcas de la operación (vía MarcaOperacion)
    2. Para cada marca: calcula P&G de sus zonas en la operación
    3. Consolida totales

    Args:
        escenario: Escenario activo
        operacion: Operación a calcular

    Returns:
        Dict con P&G por marca y consolidado de la operación
    """
    from core.models import MarcaOperacion, Zona

    # Obtener marcas de esta operación
    marcas_operacion = MarcaOperacion.objects.filter(
        operacion=operacion,
        activo=True
    ).select_related('marca')

    resultado_por_marca = {}
    totales = {
        'comercial': {'personal': Decimal('0'), 'gastos': Decimal('0'), 'lejanias': Decimal('0'), 'total': Decimal('0')},
        'logistico': {'personal': Decimal('0'), 'gastos': Decimal('0'), 'lejanias': Decimal('0'), 'total': Decimal('0')},
        'administrativo': {'personal': Decimal('0'), 'gastos': Decimal('0'), 'total': Decimal('0')},
    }

    for mo in marcas_operacion:
        marca = mo.marca

        # Obtener zonas de esta marca en esta operación
        zonas = Zona.objects.filter(
            escenario=escenario,
            marca=marca,
            operacion=operacion,
            activo=True
        )

        if not zonas.exists():
            continue

        # Calcular P&G para cada zona y sumar
        marca_totales = {
            'comercial': {'personal': Decimal('0'), 'gastos': Decimal('0'), 'lejanias': Decimal('0'), 'total': Decimal('0')},
            'logistico': {'personal': Decimal('0'), 'gastos': Decimal('0'), 'lejanias': Decimal('0'), 'total': Decimal('0')},
            'administrativo': {'personal': Decimal('0'), 'gastos': Decimal('0'), 'total': Decimal('0')},
        }

        for zona in zonas:
            pyg_zona = calcular_pyg_zona(escenario, zona)

            # Sumar a totales de marca
            for cat in ['comercial', 'logistico']:
                marca_totales[cat]['personal'] += Decimal(str(pyg_zona[cat]['personal']))
                marca_totales[cat]['gastos'] += Decimal(str(pyg_zona[cat]['gastos']))
                marca_totales[cat]['lejanias'] += Decimal(str(pyg_zona[cat].get('lejanias', 0)))
                marca_totales[cat]['total'] += Decimal(str(pyg_zona[cat]['total']))

            marca_totales['administrativo']['personal'] += Decimal(str(pyg_zona['administrativo']['personal']))
            marca_totales['administrativo']['gastos'] += Decimal(str(pyg_zona['administrativo']['gastos']))
            marca_totales['administrativo']['total'] += Decimal(str(pyg_zona['administrativo']['total']))

        resultado_por_marca[marca.marca_id] = {
            'marca': {
                'id': marca.marca_id,
                'nombre': marca.nombre,
            },
            **marca_totales,
            'total_mensual': marca_totales['comercial']['total'] + marca_totales['logistico']['total'] + marca_totales['administrativo']['total'],
        }

        # Acumular en totales de operación
        for cat in ['comercial', 'logistico']:
            totales[cat]['personal'] += marca_totales[cat]['personal']
            totales[cat]['gastos'] += marca_totales[cat]['gastos']
            totales[cat]['lejanias'] += marca_totales[cat]['lejanias']
            totales[cat]['total'] += marca_totales[cat]['total']

        totales['administrativo']['personal'] += marca_totales['administrativo']['personal']
        totales['administrativo']['gastos'] += marca_totales['administrativo']['gastos']
        totales['administrativo']['total'] += marca_totales['administrativo']['total']

    total_mensual = totales['comercial']['total'] + totales['logistico']['total'] + totales['administrativo']['total']

    return {
        'operacion': {
            'id': operacion.id,
            'nombre': operacion.nombre,
            'codigo': operacion.codigo,
        },
        'por_marca': resultado_por_marca,
        'consolidado': totales,
        'total_mensual': total_mensual,
        'total_anual': total_mensual * 12
    }


def calcular_pyg_todas_operaciones(escenario) -> List[Dict]:
    """
    Calcula P&G para todas las operaciones de un escenario.

    Args:
        escenario: Escenario activo

    Returns:
        Lista de Dict con P&G por operación
    """
    from core.models import Operacion

    operaciones = Operacion.objects.filter(
        escenario=escenario,
        activa=True
    ).order_by('nombre')

    return [calcular_pyg_operacion(escenario, op) for op in operaciones]


def calcular_pyg_marca_por_operaciones(escenario, marca) -> Dict:
    """
    Calcula P&G de una marca desglosado por operación.

    Retorna el consolidado de la marca y el desglose por cada operación donde opera.

    Args:
        escenario: Escenario activo
        marca: Marca a calcular

    Returns:
        Dict con P&G por operación y consolidado de la marca
    """
    from core.models import MarcaOperacion, Zona

    # Obtener operaciones donde participa esta marca
    marcas_operacion = MarcaOperacion.objects.filter(
        marca=marca,
        operacion__escenario=escenario,
        operacion__activa=True,
        activo=True
    ).select_related('operacion')

    resultado_por_operacion = {}
    totales = {
        'comercial': {'personal': Decimal('0'), 'gastos': Decimal('0'), 'lejanias': Decimal('0'), 'total': Decimal('0')},
        'logistico': {'personal': Decimal('0'), 'gastos': Decimal('0'), 'lejanias': Decimal('0'), 'total': Decimal('0')},
        'administrativo': {'personal': Decimal('0'), 'gastos': Decimal('0'), 'total': Decimal('0')},
    }

    for mo in marcas_operacion:
        operacion = mo.operacion

        # Obtener zonas de esta marca en esta operación
        zonas = Zona.objects.filter(
            escenario=escenario,
            marca=marca,
            operacion=operacion,
            activo=True
        )

        if not zonas.exists():
            continue

        # Calcular P&G para cada zona y sumar
        op_totales = {
            'comercial': {'personal': Decimal('0'), 'gastos': Decimal('0'), 'lejanias': Decimal('0'), 'total': Decimal('0')},
            'logistico': {'personal': Decimal('0'), 'gastos': Decimal('0'), 'lejanias': Decimal('0'), 'total': Decimal('0')},
            'administrativo': {'personal': Decimal('0'), 'gastos': Decimal('0'), 'total': Decimal('0')},
        }

        for zona in zonas:
            pyg_zona = calcular_pyg_zona(escenario, zona)

            # Sumar a totales de operación
            for cat in ['comercial', 'logistico']:
                op_totales[cat]['personal'] += Decimal(str(pyg_zona[cat]['personal']))
                op_totales[cat]['gastos'] += Decimal(str(pyg_zona[cat]['gastos']))
                op_totales[cat]['lejanias'] += Decimal(str(pyg_zona[cat].get('lejanias', 0)))
                op_totales[cat]['total'] += Decimal(str(pyg_zona[cat]['total']))

            op_totales['administrativo']['personal'] += Decimal(str(pyg_zona['administrativo']['personal']))
            op_totales['administrativo']['gastos'] += Decimal(str(pyg_zona['administrativo']['gastos']))
            op_totales['administrativo']['total'] += Decimal(str(pyg_zona['administrativo']['total']))

        resultado_por_operacion[operacion.codigo] = {
            'operacion': {
                'id': operacion.id,
                'nombre': operacion.nombre,
                'codigo': operacion.codigo,
            },
            'participacion_ventas': float(mo.participacion_ventas),
            **op_totales,
            'total_mensual': op_totales['comercial']['total'] + op_totales['logistico']['total'] + op_totales['administrativo']['total'],
        }

        # Acumular en totales de marca
        for cat in ['comercial', 'logistico']:
            totales[cat]['personal'] += op_totales[cat]['personal']
            totales[cat]['gastos'] += op_totales[cat]['gastos']
            totales[cat]['lejanias'] += op_totales[cat]['lejanias']
            totales[cat]['total'] += op_totales[cat]['total']

        totales['administrativo']['personal'] += op_totales['administrativo']['personal']
        totales['administrativo']['gastos'] += op_totales['administrativo']['gastos']
        totales['administrativo']['total'] += op_totales['administrativo']['total']

    total_mensual = totales['comercial']['total'] + totales['logistico']['total'] + totales['administrativo']['total']

    return {
        'marca': {
            'id': marca.marca_id,
            'nombre': marca.nombre,
        },
        'por_operacion': resultado_por_operacion,
        'consolidado': totales,
        'total_mensual': total_mensual,
        'total_anual': total_mensual * 12
    }


def listar_operaciones(escenario) -> List[Dict]:
    """
    Lista todas las operaciones de un escenario con información básica.

    Incluye:
    - tasa_ica: Tasa de ICA de la operación (porcentaje 0-100)
    - venta_total: Suma de venta_proyectada de todas las MarcaOperacion

    Args:
        escenario: Escenario activo

    Returns:
        Lista de Dict con información de cada operación
    """
    from core.models import Operacion, MarcaOperacion
    from django.db.models import Sum

    operaciones = Operacion.objects.filter(
        escenario=escenario,
        activa=True
    ).order_by('nombre')

    resultado = []
    for op in operaciones:
        # Calcular venta total desde MarcaOperacion.venta_proyectada
        venta_total = MarcaOperacion.objects.filter(
            operacion=op,
            activo=True
        ).aggregate(total=Sum('venta_proyectada'))['total'] or Decimal('0')

        resultado.append({
            'id': op.id,
            'nombre': op.nombre,
            'codigo': op.codigo,
            'municipio_base': op.municipio_base.nombre if op.municipio_base else None,
            'cantidad_marcas': op.marcas_asociadas.filter(activo=True).count(),
            'cantidad_zonas': op.zonas.filter(activo=True).count(),
            'tasa_ica': float(op.tasa_ica or Decimal('0')),  # Porcentaje 0-100
            'venta_total': float(venta_total),
        })

    return resultado
