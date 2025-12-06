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


def calcular_pyg_todas_zonas(escenario, marca) -> List[Dict]:
    """
    Calcula P&G para todas las zonas de una marca.

    Distribución de costos respetando tipo_asignacion_geo:
    - directo: 100% a la zona asignada
    - proporcional: según participacion_ventas de la zona
    - compartido: equitativo entre todas las zonas

    Lejanías:
    - Comerciales: directas por zona (calculadas por CalculadoraLejanias)
    - Logísticas: distribuidas según municipios atendidos por las rutas
    """
    from core.models import (
        Zona, PersonalComercial, GastoComercial,
        PersonalLogistico, GastoLogistico
    )
    from core.calculator_lejanias import CalculadoraLejanias
    from core.simulator import Simulator
    from utils.loaders_db import DataLoaderDB

    zonas = Zona.objects.filter(
        escenario=escenario,
        marca=marca,
        activo=True
    ).order_by('nombre')

    zonas_list = list(zonas)
    zonas_count = len(zonas_list) or 1

    # Obtener totales administrativos desde el Simulador (incluye compartidos prorrateados)
    # Esto garantiza consistencia con P&G Detallado
    loader = DataLoaderDB(escenario_id=escenario.id)
    simulator = Simulator(loader=loader)
    simulator.cargar_marcas([marca.marca_id])
    resultado_sim = simulator.ejecutar_simulacion()
    marca_sim = next((m for m in resultado_sim.marcas if m.marca_id == marca.marca_id), None)

    # Calcular totales administrativos de la marca
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

    # Función para distribuir un costo según tipo_asignacion_geo
    def distribuir_costo(costo: Decimal, tipo_asignacion: str, zona_asignada_id: int, zona: Zona) -> Decimal:
        participacion = (zona.participacion_ventas or Decimal('0')) / 100

        if tipo_asignacion == 'directo':
            if zona_asignada_id and zona_asignada_id == zona.id:
                return costo
            return Decimal('0')
        elif tipo_asignacion == 'proporcional':
            return costo * participacion
        elif tipo_asignacion == 'compartido':
            return costo / zonas_count
        else:
            # Default: proporcional
            return costo * participacion

    # Calculadora de lejanías
    calc = CalculadoraLejanias(escenario)

    # Distribuir costos logísticos a zonas según municipios atendidos
    costos_logisticos_por_zona = calc.distribuir_costos_logisticos_a_zonas(marca)

    # Distribuir costos fijos de vehículos (flota) según rutas que atienden
    flota_por_zona = calc.distribuir_flota_a_zonas(marca)

    # Calcular P&G por zona
    resultados = []
    for zona in zonas_list:
        # === COMERCIAL ===
        comercial_personal = Decimal('0')
        comercial_gastos = Decimal('0')

        # Personal comercial
        for p in PersonalComercial.objects.filter(escenario=escenario, marca=marca):
            costo = Decimal(str(p.calcular_costo_mensual()))
            tipo_asignacion = getattr(p, 'tipo_asignacion_geo', 'proporcional')
            zona_asignada_id = p.zona_id if hasattr(p, 'zona_id') else None
            comercial_personal += distribuir_costo(costo, tipo_asignacion, zona_asignada_id, zona)

        # Gastos comerciales (excluyendo lejanías)
        for g in GastoComercial.objects.filter(escenario=escenario, marca=marca):
            if es_gasto_lejania_comercial(g.nombre or ''):
                continue
            costo = g.valor_mensual or Decimal('0')
            tipo_asignacion = getattr(g, 'tipo_asignacion_geo', 'proporcional')
            zona_asignada_id = g.zona_id if hasattr(g, 'zona_id') else None
            comercial_gastos += distribuir_costo(costo, tipo_asignacion, zona_asignada_id, zona)

        # Lejanía comercial es específica por zona (vendedor)
        lej_comercial_zona = calc.calcular_lejania_comercial_zona(zona)['total_mensual']

        comercial = {
            'personal': comercial_personal,
            'gastos': comercial_gastos,
            'lejanias': lej_comercial_zona,
            'total': comercial_personal + comercial_gastos + lej_comercial_zona
        }

        # === LOGÍSTICO ===
        logistico_personal = Decimal('0')
        logistico_gastos = Decimal('0')

        # Personal logístico
        for p in PersonalLogistico.objects.filter(escenario=escenario, marca=marca):
            costo = Decimal(str(p.calcular_costo_mensual()))
            tipo_asignacion = getattr(p, 'tipo_asignacion_geo', 'proporcional')
            zona_asignada_id = p.zona_id if hasattr(p, 'zona_id') else None
            logistico_personal += distribuir_costo(costo, tipo_asignacion, zona_asignada_id, zona)

        # Gastos logísticos (excluyendo los que se calculan en lejanías)
        for g in GastoLogistico.objects.filter(escenario=escenario, marca=marca):
            if es_gasto_lejania_logistica(g.nombre or ''):
                continue
            costo = g.valor_mensual or Decimal('0')
            tipo_asignacion = getattr(g, 'tipo_asignacion_geo', 'proporcional')
            zona_asignada_id = g.zona_id if hasattr(g, 'zona_id') else None
            logistico_gastos += distribuir_costo(costo, tipo_asignacion, zona_asignada_id, zona)

        # Lejanías logísticas (distribuidas por rutas/municipios)
        costo_logistico_zona = Decimal('0')
        if zona.id in costos_logisticos_por_zona:
            costo_logistico_zona = costos_logisticos_por_zona[zona.id]['costo_logistico_total']

        # Flota de vehículos
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
        # Los costos administrativos vienen del Simulador (incluye compartidos prorrateados)
        # Se distribuyen equitativamente entre las zonas de la marca
        factor_zona = Decimal('1') / zonas_count

        administrativo = {
            'personal': admin_personal_marca * factor_zona,
            'gastos': admin_gastos_marca * factor_zona,
            'total': (admin_personal_marca + admin_gastos_marca) * factor_zona
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


def calcular_pyg_todos_municipios(escenario, zona) -> List[Dict]:
    """
    Calcula P&G para todos los municipios de una zona.

    Lógica: Toma el P&G de la zona (calculado con calcular_pyg_todas_zonas)
    y lo distribuye proporcionalmente según ZonaMunicipio.participacion_ventas.

    Esto garantiza que la suma de municipios = total de la zona.
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
    # Este campo ya contiene el peso relativo dentro de la zona (suma = 100%)
    pesos_relativos = {}
    ventas_proyectadas = {}
    for zm in zona_municipios:
        # participacion_ventas ya está en % (0-100), convertir a decimal (0-1)
        pesos_relativos[zm.municipio.id] = (zm.participacion_ventas or Decimal('0')) / 100
        ventas_proyectadas[zm.municipio.id] = zm.venta_proyectada or Decimal('0')

    # Obtener P&G de la zona usando la MISMA función que la vista de zonas
    # Esto garantiza consistencia entre ambas vistas
    pyg_todas_zonas = calcular_pyg_todas_zonas(escenario, marca)
    pyg_zona = next((z for z in pyg_todas_zonas if z['zona']['id'] == zona.id), None)

    if not pyg_zona:
        return []

    # Construir resultado para cada municipio
    # Todos los costos se distribuyen proporcionalmente según peso del municipio en la zona
    resultados = []
    for zm in zona_municipios:
        mun_id = zm.municipio.id
        peso = pesos_relativos.get(mun_id, Decimal('0'))
        venta_proy = ventas_proyectadas.get(mun_id, Decimal('0'))

        # Convertir valores de pyg_zona a Decimal para cálculos precisos
        comercial_personal = Decimal(str(pyg_zona['comercial']['personal']))
        comercial_gastos = Decimal(str(pyg_zona['comercial']['gastos']))
        comercial_lejanias = Decimal(str(pyg_zona['comercial'].get('lejanias', 0)))
        comercial_total = Decimal(str(pyg_zona['comercial']['total']))

        logistico_personal = Decimal(str(pyg_zona['logistico']['personal']))
        logistico_gastos = Decimal(str(pyg_zona['logistico']['gastos']))
        logistico_lejanias = Decimal(str(pyg_zona['logistico'].get('lejanias', 0)))
        logistico_total = Decimal(str(pyg_zona['logistico']['total']))

        admin_personal = Decimal(str(pyg_zona['administrativo']['personal']))
        admin_gastos = Decimal(str(pyg_zona['administrativo']['gastos']))
        admin_total = Decimal(str(pyg_zona['administrativo']['total']))

        # Distribuir proporcionalmente por peso del municipio
        comercial = {
            'personal': comercial_personal * peso,
            'gastos': comercial_gastos * peso,
            'lejanias': comercial_lejanias * peso,
            'total': comercial_total * peso
        }

        logistico = {
            'personal': logistico_personal * peso,
            'gastos': logistico_gastos * peso,
            'lejanias': logistico_lejanias * peso,
            'total': logistico_total * peso
        }

        administrativo = {
            'personal': admin_personal * peso,
            'gastos': admin_gastos * peso,
            'total': admin_total * peso
        }

        total_mensual = comercial['total'] + logistico['total'] + administrativo['total']

        # Participación sobre la marca = participación_zona × peso_municipio_en_zona
        part_zona_decimal = Decimal(str(pyg_zona['zona']['participacion_ventas'])) / 100
        part_total = part_zona_decimal * peso * 100  # Volver a %

        resultados.append({
            'municipio': {
                'id': mun_id,
                'nombre': zm.municipio.nombre,
                'codigo_dane': zm.municipio.codigo_dane,
                'venta_proyectada': float(venta_proy),
                'participacion_zona': float(peso * 100),  # % dentro de la zona
                'participacion_total': float(part_total),  # % sobre la marca
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
