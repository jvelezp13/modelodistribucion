from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum, Q
from decimal import Decimal
import logging

from .models import (
    PersonalComercial, PersonalLogistico, PersonalAdministrativo,
    PoliticaRecursosHumanos, ParametrosMacro,
    GastoComercial, GastoLogistico, GastoAdministrativo,
    Escenario, Marca, Vehiculo,
    Zona, ZonaMunicipio, RutaLogistica, RutaMunicipio,
    ConfiguracionLejania, MatrizDesplazamiento
)

logger = logging.getLogger(__name__)

def calculate_hr_expenses(escenario):
    """
    Recalcula los gastos de Dotación, EPP y Exámenes Médicos para un escenario dado.
    Agrupa por Marca para asignar correctamente el gasto.
    """
    if not escenario:
        return

    try:
        politica = PoliticaRecursosHumanos.objects.get(anio=escenario.anio, activo=True)
    except PoliticaRecursosHumanos.DoesNotExist:
        return

    try:
        macro = ParametrosMacro.objects.get(anio=escenario.anio, activo=True)
        smlv = macro.salario_minimo_legal
    except ParametrosMacro.DoesNotExist:
        return

    tope_dotacion = politica.tope_smlv_dotacion * smlv
    
    # Función auxiliar para procesar gastos por grupo (marca, tipo_asignacion_geo, zona)
    def process_expenses(model_personal, model_gasto, tipo_personal):
        qs = model_personal.objects.filter(escenario=escenario)

        # Agrupar por (marca, tipo_asignacion_geo, zona) para respetar la asignación del personal
        # Usar values para obtener grupos únicos
        grupos = qs.values('marca', 'tipo_asignacion_geo', 'zona').distinct()

        # Limpiar gastos de provisiones existentes para este escenario y modelo
        # (se recrearán con los valores correctos)
        model_gasto.objects.filter(
            escenario=escenario,
            tipo__in=['dotacion', 'epp', 'examenes']
        ).delete()

        for grupo in grupos:
            marca_id = grupo['marca']
            tipo_asig_geo = grupo['tipo_asignacion_geo'] or 'proporcional'
            zona_id = grupo['zona']

            # Filtrar personal de este grupo
            personal_grupo = qs.filter(
                marca_id=marca_id,
                tipo_asignacion_geo=tipo_asig_geo,
                zona_id=zona_id
            )

            # Obtener objetos relacionados
            marca_obj = Marca.objects.get(pk=marca_id) if marca_id else None
            zona_obj = None
            if zona_id and tipo_asig_geo == 'directo':
                from .models import Zona
                zona_obj = Zona.objects.get(pk=zona_id)

            asignacion = 'compartido' if marca_id is None else 'individual'

            # Sumar cantidad de empleados
            count_total = personal_grupo.aggregate(total=Sum('cantidad'))['total'] or 0
            if count_total == 0:
                continue

            # Generar nombre descriptivo para el gasto
            if zona_obj:
                nombre_suffix = f" - {zona_obj.nombre}"
            else:
                nombre_suffix = ""

            # --- 1. DOTACIÓN (Aplica a todos con salario <= tope) ---
            count_dotacion = personal_grupo.filter(salario_base__lte=tope_dotacion).aggregate(
                total=Sum('cantidad')
            )['total'] or 0
            valor_dotacion = (count_dotacion * politica.valor_dotacion_completa) / politica.frecuencia_dotacion_meses

            if valor_dotacion > 0:
                model_gasto.objects.create(
                    escenario=escenario,
                    tipo='dotacion',
                    marca=marca_obj,
                    nombre=f'Provisión Dotación{nombre_suffix}',
                    valor_mensual=valor_dotacion,
                    asignacion=asignacion,
                    tipo_asignacion_geo=tipo_asig_geo,
                    zona=zona_obj
                )

            # --- 2. EXÁMENES MÉDICOS ---
            if tipo_personal == 'comercial':
                costo_ingreso = politica.costo_examen_ingreso_comercial
                costo_periodico = politica.costo_examen_periodico_comercial
            else:
                costo_ingreso = politica.costo_examen_ingreso_operativo
                costo_periodico = politica.costo_examen_periodico_operativo

            valor_examenes = (count_total * costo_ingreso * (politica.tasa_rotacion_anual / 100) / 12) + \
                             (count_total * costo_periodico / 12)

            if valor_examenes > 0:
                model_gasto.objects.create(
                    escenario=escenario,
                    tipo='examenes',
                    marca=marca_obj,
                    nombre=f'Provisión Exámenes Médicos{nombre_suffix}',
                    valor_mensual=valor_examenes,
                    asignacion=asignacion,
                    tipo_asignacion_geo=tipo_asig_geo,
                    zona=zona_obj
                )

            # --- 3. EPP (SOLO COMERCIAL) ---
            if tipo_personal == 'comercial':
                valor_epp = (count_total * politica.valor_epp_anual_comercial) / politica.frecuencia_epp_meses

                if valor_epp > 0:
                    model_gasto.objects.create(
                        escenario=escenario,
                        tipo='epp',
                        marca=marca_obj,
                        nombre=f'Provisión EPP (Comercial){nombre_suffix}',
                        valor_mensual=valor_epp,
                        asignacion=asignacion,
                        tipo_asignacion_geo=tipo_asig_geo,
                        zona=zona_obj
                    )

    # Ejecutar para cada tipo de personal
    process_expenses(PersonalComercial, GastoComercial, 'comercial')
    process_expenses(PersonalLogistico, GastoLogistico, 'logistico')
    process_expenses(PersonalAdministrativo, GastoAdministrativo, 'administrativo')


@receiver([post_save, post_delete], sender=PersonalComercial)
@receiver([post_save, post_delete], sender=PersonalLogistico)
@receiver([post_save, post_delete], sender=PersonalAdministrativo)
def update_expenses_on_personnel_change(sender, instance, **kwargs):
    if instance.escenario:
        calculate_hr_expenses(instance.escenario)

@receiver(post_save, sender=PoliticaRecursosHumanos)
def update_expenses_on_policy_change(sender, instance, **kwargs):
    # Obtener todos los escenarios del año de la política
    escenarios = Escenario.objects.filter(anio=instance.anio)
    for escenario in escenarios:
        calculate_hr_expenses(escenario)

def calculate_logistic_expenses(escenario):
    """
    Recalcula los gastos logísticos FIJOS basados en la flota de vehículos.

    NOTA: El combustible, peajes y flete de terceros se calculan desde los
    Recorridos Logísticos, no desde aquí. Esta función solo procesa costos
    fijos del vehículo.
    """
    if not escenario:
        return

    # Obtener todas las marcas con vehículos en este escenario
    qs_vehiculos = Vehiculo.objects.filter(escenario=escenario)
    marcas_ids = set(qs_vehiculos.values_list('marca', flat=True))

    for marca_id in marcas_ids:
        marca_obj = Marca.objects.get(pk=marca_id)
        vehiculos_marca = qs_vehiculos.filter(marca=marca_obj)

        # Inicializar acumuladores por tipo de gasto (solo costos FIJOS)
        total_renting = 0
        total_depreciacion = 0
        total_mantenimiento = 0
        total_seguros = 0
        total_seguros_mercancia = 0
        total_lavado = 0
        total_parqueadero = 0
        total_monitoreo = 0

        for v in vehiculos_marca:
            # Costos comunes para TODOS los esquemas
            total_monitoreo += v.costo_monitoreo_mensual * v.cantidad
            total_seguros_mercancia += v.costo_seguro_mercancia_mensual * v.cantidad

            if v.esquema == 'tercero':
                # Para terceros, el flete base viene de los Recorridos Logísticos
                pass

            elif v.esquema in ['renting', 'tradicional']:
                # Costos comunes para Propio y Renting
                total_lavado += v.costo_lavado_mensual * v.cantidad
                total_parqueadero += v.costo_parqueadero_mensual * v.cantidad

                # NOTA: El combustible se calcula en los Recorridos Logísticos

                if v.esquema == 'renting':
                    # Renting: Canon * Cantidad
                    total_renting += v.canon_renting * v.cantidad

                elif v.esquema == 'tradicional':  # Propio
                    # Depreciación: (Costo - Residual) / (Vida Util * 12) * Cantidad
                    if v.vida_util_anios > 0:
                        depreciacion_mensual = (v.costo_compra - v.valor_residual) / (v.vida_util_anios * 12)
                        total_depreciacion += depreciacion_mensual * v.cantidad

                    # Mantenimiento
                    total_mantenimiento += v.costo_mantenimiento_mensual * v.cantidad

                    # Seguros
                    total_seguros += v.costo_seguro_mensual * v.cantidad

        # Función helper para actualizar/borrar gasto
        def update_gasto(tipo, nombre, valor):
            if valor > 0:
                GastoLogistico.objects.update_or_create(
                    escenario=escenario,
                    tipo=tipo,
                    marca=marca_obj,
                    nombre=nombre,  # Incluir nombre en el lookup para permitir múltiples registros del mismo tipo
                    defaults={
                        'valor_mensual': valor,
                        'asignacion': 'individual'
                    }
                )
            else:
                GastoLogistico.objects.filter(escenario=escenario, tipo=tipo, marca=marca_obj, nombre=nombre).delete()

        # Actualizar cada rubro (solo costos FIJOS del vehículo)
        # NOTA: flete_tercero y combustible se calculan desde los Recorridos Logísticos
        update_gasto('canon_renting', 'Canon Renting Flota', total_renting)
        update_gasto('depreciacion_vehiculo', 'Depreciación Flota Propia', total_depreciacion)
        update_gasto('mantenimiento_vehiculos', 'Mantenimiento Flota Propia', total_mantenimiento)
        update_gasto('seguros_carga', 'Seguros Flota Propia', total_seguros)
        update_gasto('lavado_vehiculos', 'Aseo y Limpieza Vehículos', total_lavado)
        update_gasto('parqueadero_vehiculos', 'Parqueaderos', total_parqueadero)
        update_gasto('monitoreo_satelital', 'Monitoreo Satelital (GPS)', total_monitoreo)
        update_gasto('seguros_carga', 'Seguro de Mercancía', total_seguros_mercancia)


@receiver([post_save, post_delete], sender=Vehiculo)
def update_logistic_expenses_on_vehicle_change(sender, instance, **kwargs):
    if instance.escenario:
        calculate_logistic_expenses(instance.escenario)

@receiver(post_save, sender=ParametrosMacro)
def update_expenses_on_macro_change(sender, instance, **kwargs):
    # Actualizar gastos logísticos (por precio combustible) y RRHH (por SMLV)
    escenarios = Escenario.objects.filter(anio=instance.anio)
    for escenario in escenarios:
        calculate_hr_expenses(escenario)
        calculate_logistic_expenses(escenario)
        calculate_lejanias_comerciales(escenario)
        calculate_lejanias_logisticas(escenario)


# =============================================================================
# LEJANÍAS COMERCIALES (Combustible + Pernocta por Zona Comercial)
# =============================================================================

def calculate_lejanias_comerciales(escenario):
    """
    Calcula y persiste los gastos de lejanías comerciales por zona.

    Crea registros en GastoComercial para:
    - Combustible (tipo='transporte_vendedores')
    - Viáticos/Pernocta (tipo='viaticos')

    Cada gasto se asigna directamente a la zona correspondiente.
    """
    if not escenario:
        return

    try:
        config = ConfiguracionLejania.objects.get(escenario=escenario)
    except ConfiguracionLejania.DoesNotExist:
        logger.warning(f"No hay ConfiguracionLejania para escenario {escenario}")
        return

    # Obtener todas las zonas activas del escenario
    zonas = Zona.objects.filter(
        escenario=escenario,
        activo=True
    ).select_related('marca', 'municipio_base_vendedor')

    for zona in zonas:
        marca = zona.marca
        if not marca:
            continue

        # Calcular lejanías para esta zona
        resultado = _calcular_lejania_comercial_zona(zona, config)

        combustible = resultado['combustible_mensual']
        pernocta = resultado['pernocta_mensual']

        # Guardar combustible como gasto comercial
        if combustible > 0:
            GastoComercial.objects.update_or_create(
                escenario=escenario,
                tipo='transporte_vendedores',
                marca=marca,
                nombre=f'Combustible Lejanía - {zona.nombre}',
                defaults={
                    'valor_mensual': combustible,
                    'asignacion': 'individual',
                    'tipo_asignacion_geo': 'directo',
                    'zona': zona,
                }
            )
        else:
            GastoComercial.objects.filter(
                escenario=escenario,
                tipo='transporte_vendedores',
                marca=marca,
                nombre=f'Combustible Lejanía - {zona.nombre}'
            ).delete()

        # Guardar viáticos/pernocta como gasto comercial
        if pernocta > 0:
            GastoComercial.objects.update_or_create(
                escenario=escenario,
                tipo='viaticos',
                marca=marca,
                nombre=f'Viáticos Pernocta - {zona.nombre}',
                defaults={
                    'valor_mensual': pernocta,
                    'asignacion': 'individual',
                    'tipo_asignacion_geo': 'directo',
                    'zona': zona,
                }
            )
        else:
            GastoComercial.objects.filter(
                escenario=escenario,
                tipo='viaticos',
                marca=marca,
                nombre=f'Viáticos Pernocta - {zona.nombre}'
            ).delete()


def _calcular_lejania_comercial_zona(zona, config):
    """
    Calcula lejanía comercial mensual para una zona.

    Returns:
        dict con combustible_mensual, pernocta_mensual, total_mensual
    """
    combustible_total = Decimal('0')
    pernocta_total = Decimal('0')

    # Base del vendedor
    base_vendedor = zona.municipio_base_vendedor or config.municipio_bodega
    if not base_vendedor:
        return {'combustible_mensual': Decimal('0'), 'pernocta_mensual': Decimal('0'), 'total_mensual': Decimal('0')}

    # Consumo según tipo de vehículo
    if zona.tipo_vehiculo_comercial == 'MOTO':
        consumo_km_galon = config.consumo_galon_km_moto
    else:
        consumo_km_galon = config.consumo_galon_km_automovil

    precio_galon = config.precio_galon_gasolina
    umbral = config.umbral_lejania_comercial_km

    # Calcular combustible por cada municipio de la zona
    for zona_mun in zona.municipios.all():
        municipio = zona_mun.municipio

        # Si es visita local (mismo municipio que la base), no hay lejanía
        if municipio.id == base_vendedor.id:
            continue

        # Visita a otro municipio: buscar en matriz
        try:
            matriz = MatrizDesplazamiento.objects.get(
                origen_id=base_vendedor.id,
                destino_id=municipio.id
            )
            distancia_km = matriz.distancia_km
        except MatrizDesplazamiento.DoesNotExist:
            continue

        distancia_efectiva = max(Decimal('0'), distancia_km - umbral)
        visitas_mensuales = zona_mun.visitas_mensuales()

        if distancia_efectiva > 0 and consumo_km_galon > 0:
            distancia_ida_vuelta = distancia_efectiva * 2
            galones_por_visita = distancia_ida_vuelta / consumo_km_galon
            costo_combustible_visita = galones_por_visita * precio_galon
            combustible_total += costo_combustible_visita * visitas_mensuales

    # Calcular pernocta (a nivel de zona)
    if zona.requiere_pernocta and zona.noches_pernocta > 0:
        gasto_por_noche = (
            config.desayuno_comercial +
            config.almuerzo_comercial +
            config.cena_comercial +
            config.alojamiento_comercial
        )
        periodos_mes = zona.periodos_por_mes()
        pernocta_total = gasto_por_noche * zona.noches_pernocta * periodos_mes

    return {
        'combustible_mensual': combustible_total,
        'pernocta_mensual': pernocta_total,
        'total_mensual': combustible_total + pernocta_total
    }


# =============================================================================
# LEJANÍAS LOGÍSTICAS (Combustible + Peajes + Pernocta por Ruta Logística)
# =============================================================================

def calculate_lejanias_logisticas(escenario):
    """
    Calcula y persiste los gastos de lejanías logísticas por ruta.

    Crea registros en GastoLogistico para:
    - Combustible (tipo='combustible')
    - Peajes (tipo='peajes')
    - Viáticos/Pernocta conductor y auxiliar (tipo='otros')

    Gastos se distribuyen proporcional a ventas (proporcional) por zona.
    """
    if not escenario:
        return

    try:
        config = ConfiguracionLejania.objects.get(escenario=escenario)
    except ConfiguracionLejania.DoesNotExist:
        logger.warning(f"No hay ConfiguracionLejania para escenario {escenario}")
        return

    # Obtener todas las rutas activas del escenario
    rutas = RutaLogistica.objects.filter(
        escenario=escenario,
        activo=True
    ).select_related('marca', 'vehiculo')

    for ruta in rutas:
        marca = ruta.marca
        if not marca:
            continue

        resultado = _calcular_lejania_logistica_ruta(ruta, config)

        combustible = resultado['combustible_mensual']
        peajes = resultado['peaje_mensual']
        pernocta = resultado['pernocta_mensual']
        flete_base = resultado['flete_base_mensual']

        # Helper para guardar gasto logístico con asignación proporcional
        def save_gasto(tipo, nombre, valor):
            if valor > 0:
                GastoLogistico.objects.update_or_create(
                    escenario=escenario,
                    tipo=tipo,
                    marca=marca,
                    nombre=nombre,
                    defaults={
                        'valor_mensual': valor,
                        'asignacion': 'individual',
                        'tipo_asignacion_geo': 'proporcional',
                        'zona': None,  # Proporcional no asigna zona directa
                    }
                )
            else:
                GastoLogistico.objects.filter(
                    escenario=escenario,
                    tipo=tipo,
                    marca=marca,
                    nombre=nombre
                ).delete()

        # Guardar cada tipo de gasto
        save_gasto('combustible', f'Combustible - {ruta.nombre}', combustible)
        save_gasto('peajes', f'Peajes - {ruta.nombre}', peajes)
        save_gasto('otros', f'Viáticos Ruta - {ruta.nombre}', pernocta)

        # Flete base solo aplica para terceros
        if ruta.vehiculo and ruta.vehiculo.esquema == 'tercero':
            save_gasto('otros', f'Flete Base Tercero - {ruta.nombre}', flete_base)


def _calcular_lejania_logistica_ruta(ruta, config):
    """
    Calcula lejanía logística mensual para una ruta (circuito).

    Returns:
        dict con flete_base_mensual, combustible_mensual, peaje_mensual, pernocta_mensual, total_mensual
    """
    flete_base_total = Decimal('0')
    combustible_total = Decimal('0')
    peaje_total = Decimal('0')
    pernocta_total = Decimal('0')

    bodega = config.municipio_bodega
    if not bodega:
        return _resultado_vacio_logistica()

    vehiculo = ruta.vehiculo
    if not vehiculo:
        return _resultado_vacio_logistica()

    # Consumo y precio según vehículo
    consumo_km_galon = vehiculo.consumo_galon_km or Decimal('30')
    if vehiculo.tipo_combustible == 'gasolina':
        precio_galon = config.precio_galon_gasolina
    else:
        precio_galon = config.precio_galon_acpm

    recorridos_mensuales = ruta.recorridos_mensuales()
    umbral = config.umbral_lejania_logistica_km

    # Obtener municipios ordenados
    municipios_ordenados = list(ruta.municipios.all().order_by('orden_visita'))
    if not municipios_ordenados:
        return _resultado_vacio_logistica()

    # Calcular flete base
    for ruta_mun in municipios_ordenados:
        flete_base = ruta_mun.flete_base or Decimal('0')
        flete_base_total += flete_base * recorridos_mensuales

    # Calcular circuito: Bodega → Mun1 → ... → MunN → Bodega
    puntos_circuito = [bodega] + [rm.municipio for rm in municipios_ordenados] + [bodega]

    distancia_total = Decimal('0')
    peaje_circuito = Decimal('0')

    for i in range(len(puntos_circuito) - 1):
        origen = puntos_circuito[i]
        destino = puntos_circuito[i + 1]

        try:
            matriz = MatrizDesplazamiento.objects.get(
                origen_id=origen.id,
                destino_id=destino.id
            )
            distancia_total += matriz.distancia_km
            peaje_circuito += matriz.peaje_ida or Decimal('0')
        except MatrizDesplazamiento.DoesNotExist:
            pass

    # Aplicar umbral y calcular combustible
    distancia_efectiva = max(Decimal('0'), distancia_total - umbral)
    if distancia_efectiva > 0 and consumo_km_galon > 0:
        galones_circuito = distancia_efectiva / consumo_km_galon
        combustible_total = galones_circuito * precio_galon * recorridos_mensuales

    # Peajes
    peaje_total = peaje_circuito * recorridos_mensuales

    # Pernocta (conductor + auxiliar + parqueadero)
    if ruta.requiere_pernocta and ruta.noches_pernocta > 0:
        # Conductor
        gasto_conductor = (
            config.desayuno_conductor +
            config.almuerzo_conductor +
            config.cena_conductor +
            config.alojamiento_conductor
        )

        # Auxiliar(es) - usar cantidad_auxiliares del vehículo
        cantidad_auxiliares = ruta.vehiculo.cantidad_auxiliares if ruta.vehiculo else 1
        gasto_auxiliar = (
            config.desayuno_auxiliar +
            config.almuerzo_auxiliar +
            config.cena_auxiliar +
            config.alojamiento_auxiliar
        ) * cantidad_auxiliares

        parqueadero = config.parqueadero_logistica

        pernocta_total = (gasto_conductor + gasto_auxiliar + parqueadero) * ruta.noches_pernocta * recorridos_mensuales

    return {
        'flete_base_mensual': flete_base_total,
        'combustible_mensual': combustible_total,
        'peaje_mensual': peaje_total,
        'pernocta_mensual': pernocta_total,
        'total_mensual': flete_base_total + combustible_total + peaje_total + pernocta_total
    }


def _resultado_vacio_logistica():
    """Retorna resultado vacío para lejanías logísticas"""
    return {
        'flete_base_mensual': Decimal('0'),
        'combustible_mensual': Decimal('0'),
        'peaje_mensual': Decimal('0'),
        'pernocta_mensual': Decimal('0'),
        'total_mensual': Decimal('0')
    }


# =============================================================================
# SIGNALS PARA RECÁLCULO DE LEJANÍAS
# =============================================================================

@receiver([post_save, post_delete], sender=Zona)
@receiver([post_save, post_delete], sender=ZonaMunicipio)
def update_lejanias_on_zona_change(sender, instance, **kwargs):
    """Recalcula lejanías comerciales cuando cambian zonas o municipios"""
    escenario = None
    if sender == Zona:
        escenario = instance.escenario
    elif sender == ZonaMunicipio:
        escenario = instance.zona.escenario if instance.zona else None

    if escenario:
        calculate_lejanias_comerciales(escenario)


@receiver([post_save, post_delete], sender=RutaLogistica)
@receiver([post_save, post_delete], sender=RutaMunicipio)
def update_lejanias_on_ruta_change(sender, instance, **kwargs):
    """Recalcula lejanías logísticas cuando cambian rutas o municipios"""
    escenario = None
    if sender == RutaLogistica:
        escenario = instance.escenario
    elif sender == RutaMunicipio:
        escenario = instance.ruta.escenario if instance.ruta else None

    if escenario:
        calculate_lejanias_logisticas(escenario)


@receiver(post_save, sender=ConfiguracionLejania)
def update_lejanias_on_config_change(sender, instance, **kwargs):
    """Recalcula todas las lejanías cuando cambia la configuración"""
    if instance.escenario:
        calculate_lejanias_comerciales(instance.escenario)
        calculate_lejanias_logisticas(instance.escenario)


@receiver(post_save, sender=MatrizDesplazamiento)
def update_lejanias_on_matriz_change(sender, instance, **kwargs):
    """
    Recalcula lejanías cuando cambia la matriz de desplazamiento.
    Afecta todos los escenarios del mismo año.
    """
    # Las matrices no tienen escenario directo, así que recalculamos todos los escenarios activos
    escenarios = Escenario.objects.filter(activo=True)
    for escenario in escenarios:
        calculate_lejanias_comerciales(escenario)
        calculate_lejanias_logisticas(escenario)
