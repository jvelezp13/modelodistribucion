from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum, Q
from decimal import Decimal
from collections import defaultdict
import logging

from .models import (
    PersonalComercial, PersonalLogistico, PersonalAdministrativo,
    PoliticaRecursosHumanos, ParametrosMacro,
    GastoComercial, GastoLogistico, GastoAdministrativo,
    Escenario, Marca, Vehiculo,
    Zona, ZonaMunicipio, RutaLogistica, RutaMunicipio,
    ConfiguracionLejania, MatrizDesplazamiento,
    # Modelos through para asignación multi-marca
    PersonalComercialMarca, PersonalLogisticoMarca, PersonalAdministrativoMarca,
    GastoComercialMarca, GastoLogisticoMarca, GastoAdministrativoMarca,
    ZonaMarca
)

logger = logging.getLogger(__name__)

def calculate_hr_expenses(escenario):
    """
    Recalcula los gastos de Dotación, EPP y Exámenes Médicos para un escenario dado.

    Usa el sistema multi-marca: agrupa por zona/operación/tipo_asignacion_geo,
    calcula la distribución ponderada de marcas del personal, y crea gastos
    con asignaciones multi-marca proporcionales.
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

    def process_expenses(model_personal, model_gasto, model_gasto_marca, tipo_personal):
        """
        Procesa gastos RRHH para un tipo de personal.
        Agrupa SIN marca, calcula distribución ponderada de marcas.
        """
        try:
            qs = model_personal.objects.filter(escenario=escenario).prefetch_related('asignaciones_marca__marca')

            # Verificar campos disponibles en el modelo
            campos_modelo = [f.name for f in model_personal._meta.get_fields()]
            tiene_zona = 'zona' in campos_modelo
            tiene_operacion = 'operacion' in campos_modelo

            # Campos para agrupar (SIN marca - usaremos through table)
            campos_base = ['tipo_asignacion_geo']
            if tiene_operacion:
                campos_base.extend(['tipo_asignacion_operacion', 'operacion', 'criterio_prorrateo_operacion'])

            grupos = []

            # Fase 1: Personal con tipo_asignacion_geo = 'directo' (agrupa por zona)
            if tiene_zona:
                campos_directos = campos_base + ['zona']
                grupos_directos = qs.filter(tipo_asignacion_geo='directo').order_by().values(
                    *campos_directos
                ).distinct()
                grupos.extend(list(grupos_directos))

            # Fase 2: Personal con tipo_asignacion_geo != 'directo' o NULL
            grupos_no_directos = qs.exclude(tipo_asignacion_geo='directo').order_by().values(
                *campos_base
            ).distinct()
            grupos.extend(list(grupos_no_directos))

            # Limpiar gastos de provisiones existentes para este escenario y modelo
            model_gasto.objects.filter(
                escenario=escenario,
                tipo__in=['dotacion', 'epp', 'examenes']
            ).delete()
        except Exception as e:
            logger.error(f"ERROR en process_expenses({tipo_personal}) - setup: {str(e)}", exc_info=True)
            return

        for grupo in grupos:
            try:
                tipo_asig_geo_original = grupo['tipo_asignacion_geo']
                zona_id = grupo.get('zona', None)

                # Campos de operación (heredados del personal)
                tipo_asig_op = grupo.get('tipo_asignacion_operacion', 'individual')
                operacion_id = grupo.get('operacion', None)
                criterio_prorrateo_op = grupo.get('criterio_prorrateo_operacion', None)

                # Construir filtro SIN marca
                filtro = {}

                # Filtro por zona (solo si tipo='directo')
                if tiene_zona and 'zona' in grupo:
                    filtro['zona_id'] = zona_id

                # Filtro por tipo_asignacion_geo
                if tipo_asig_geo_original is not None:
                    filtro['tipo_asignacion_geo'] = tipo_asig_geo_original
                else:
                    filtro['tipo_asignacion_geo__isnull'] = True

                # Filtro por operación (si el modelo lo soporta)
                if tiene_operacion:
                    if tipo_asig_op is not None:
                        filtro['tipo_asignacion_operacion'] = tipo_asig_op
                    if operacion_id is not None:
                        filtro['operacion_id'] = operacion_id
                    else:
                        filtro['operacion_id__isnull'] = True

                personal_grupo = qs.filter(**filtro)

                # Aplicar defaults
                tipo_asig_geo = tipo_asig_geo_original or 'proporcional'

                # Obtener objetos relacionados
                zona_obj = None
                if zona_id and tipo_asig_geo == 'directo':
                    zona_obj = Zona.objects.get(pk=zona_id)

                from .models import Operacion
                operacion_obj = None
                if operacion_id:
                    operacion_obj = Operacion.objects.get(pk=operacion_id)

                # Sumar cantidad de empleados
                count_total = personal_grupo.aggregate(total=Sum('cantidad'))['total'] or 0
                if count_total == 0:
                    continue

                # =======================================================
                # CALCULAR DISTRIBUCIÓN PONDERADA DE MARCAS
                # Cada personal tiene asignaciones de marca con porcentajes.
                # Ponderamos por cantidad de empleados de cada personal.
                # =======================================================
                distribucion_marcas = defaultdict(Decimal)
                total_ponderado = Decimal('0')

                for personal in personal_grupo:
                    cantidad = Decimal(str(personal.cantidad))
                    # Obtener distribución de marcas del personal
                    for asig in personal.asignaciones_marca.all():
                        peso = cantidad * (asig.porcentaje / Decimal('100'))
                        distribucion_marcas[asig.marca_id] += peso
                        total_ponderado += peso

                # Normalizar a porcentajes (deben sumar 100%)
                marcas_porcentajes = {}
                if total_ponderado > 0:
                    for marca_id, peso in distribucion_marcas.items():
                        marcas_porcentajes[marca_id] = (peso / total_ponderado) * Decimal('100')

                # Si no hay asignaciones de marca, no crear gastos
                if not marcas_porcentajes:
                    continue

                # Generar nombre descriptivo para el gasto
                nombre_parts = []
                if operacion_obj:
                    nombre_parts.append(operacion_obj.nombre)
                if zona_obj:
                    nombre_parts.append(zona_obj.nombre)

                if nombre_parts:
                    nombre_suffix = f" - {' / '.join(nombre_parts)}"
                else:
                    nombre_suffix = f" ({tipo_asig_geo})"

            except Exception as e:
                logger.error(f"ERROR procesando grupo en {tipo_personal}: {str(e)}", exc_info=True)
                continue

            # Helper para agregar campos opcionales según el modelo de gasto
            def agregar_campos_opcionales(datos_gasto):
                campos_gasto = [f.name for f in model_gasto._meta.get_fields()]
                if 'zona' in campos_gasto:
                    datos_gasto['zona'] = zona_obj
                if 'operacion' in campos_gasto:
                    datos_gasto['operacion'] = operacion_obj
                if 'tipo_asignacion_operacion' in campos_gasto:
                    datos_gasto['tipo_asignacion_operacion'] = tipo_asig_op or 'individual'
                if 'criterio_prorrateo_operacion' in campos_gasto:
                    datos_gasto['criterio_prorrateo_operacion'] = criterio_prorrateo_op
                return datos_gasto

            # Helper para crear gasto con asignaciones multi-marca
            def crear_gasto_con_marcas(tipo_gasto, nombre, valor):
                if valor <= 0:
                    return

                datos_gasto = agregar_campos_opcionales({
                    'escenario': escenario,
                    'tipo': tipo_gasto,
                    'marca': None,  # No usar FK antiguo
                    'nombre': nombre,
                    'valor_mensual': valor,
                    'asignacion': 'compartido',  # Siempre compartido con multi-marca
                    'tipo_asignacion_geo': tipo_asig_geo,
                    'indice_incremento': 'ipc',
                })
                gasto = model_gasto.objects.create(**datos_gasto)

                # Crear asignaciones de marca
                for marca_id, porcentaje in marcas_porcentajes.items():
                    marca_obj = Marca.objects.get(pk=marca_id)
                    # Determinar el nombre del campo FK en el modelo through
                    if 'gasto' in [f.name for f in model_gasto_marca._meta.get_fields()]:
                        model_gasto_marca.objects.create(
                            gasto=gasto,
                            marca=marca_obj,
                            porcentaje=porcentaje
                        )
                    else:
                        # Fallback - no debería ocurrir
                        logger.warning(f"Modelo {model_gasto_marca} no tiene campo 'gasto'")

            # --- 1. DOTACIÓN (Aplica a todos con salario <= tope) ---
            count_dotacion = personal_grupo.filter(salario_base__lte=tope_dotacion).aggregate(
                total=Sum('cantidad')
            )['total'] or 0
            valor_dotacion = (count_dotacion * politica.valor_dotacion_completa) / politica.frecuencia_dotacion_meses

            crear_gasto_con_marcas('dotacion', f'Provisión Dotación{nombre_suffix}', valor_dotacion)

            # --- 2. EXÁMENES MÉDICOS ---
            if tipo_personal == 'comercial':
                costo_ingreso = politica.costo_examen_ingreso_comercial
                costo_periodico = politica.costo_examen_periodico_comercial
            else:
                costo_ingreso = politica.costo_examen_ingreso_operativo
                costo_periodico = politica.costo_examen_periodico_operativo

            valor_examenes = (count_total * costo_ingreso * (politica.tasa_rotacion_anual / 100) / 12) + \
                             (count_total * costo_periodico / 12)

            crear_gasto_con_marcas('examenes', f'Provisión Exámenes Médicos{nombre_suffix}', valor_examenes)

            # --- 3. EPP (SOLO COMERCIAL) ---
            if tipo_personal == 'comercial':
                valor_epp = (count_total * politica.valor_epp_anual_comercial) / politica.frecuencia_epp_meses
                crear_gasto_con_marcas('epp', f'Provisión EPP (Comercial){nombre_suffix}', valor_epp)

    # Ejecutar para cada tipo de personal con su modelo through correspondiente
    process_expenses(PersonalComercial, GastoComercial, GastoComercialMarca, 'comercial')
    process_expenses(PersonalLogistico, GastoLogistico, GastoLogisticoMarca, 'logistico')
    process_expenses(PersonalAdministrativo, GastoAdministrativo, GastoAdministrativoMarca, 'administrativo')


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

    MULTI-MARCA: Si la zona tiene múltiples marcas, crea UN gasto
    con asignaciones_marca proporcionales.

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
    ).select_related('municipio_base_vendedor').prefetch_related('asignaciones_marca__marca')

    for zona in zonas:
        # Obtener distribución de marcas de la zona
        distribucion = zona.get_distribucion_marcas()
        if not distribucion:
            continue

        # Calcular lejanías para esta zona
        resultado = _calcular_lejania_comercial_zona(zona, config)

        combustible = resultado['combustible_mensual']
        costos_adicionales = resultado['costos_adicionales_mensual']
        pernocta = resultado['pernocta_mensual']

        # Helper para crear/actualizar gasto con multi-marca
        def _crear_gasto_multimarca(tipo, nombre, valor):
            if valor > 0:
                # Buscar gasto existente por nombre y zona
                gasto, created = GastoComercial.objects.update_or_create(
                    escenario=escenario,
                    tipo=tipo,
                    nombre=nombre,
                    zona=zona,
                    defaults={
                        'valor_mensual': valor,
                        'marca': None,  # No usar FK legacy
                        'asignacion': 'compartido' if zona.es_compartido else 'individual',
                        'tipo_asignacion_geo': 'directo',
                    }
                )
                # Actualizar asignaciones de marca
                GastoComercialMarca.objects.filter(gasto=gasto).delete()
                for marca_id, porcentaje_decimal in distribucion.items():
                    marca_obj = Marca.objects.get(marca_id=marca_id)
                    GastoComercialMarca.objects.create(
                        gasto=gasto,
                        marca=marca_obj,
                        porcentaje=porcentaje_decimal * Decimal('100')
                    )
            else:
                # Eliminar gasto si valor es 0
                GastoComercial.objects.filter(
                    escenario=escenario,
                    tipo=tipo,
                    nombre=nombre,
                    zona=zona
                ).delete()

        _crear_gasto_multimarca('transporte_vendedores', f'Combustible Lejanía - {zona.nombre}', combustible)
        _crear_gasto_multimarca('transporte_vendedores', f'Mant/Deprec/Llantas - {zona.nombre}', costos_adicionales)
        _crear_gasto_multimarca('viaticos', f'Viáticos Pernocta - {zona.nombre}', pernocta)

    # Calcular costos del comité comercial (si está configurado)
    _calcular_comite_comercial(escenario, config)


def _calcular_lejania_comercial_zona(zona, config):
    """
    Calcula lejanía comercial mensual para una zona.

    Returns:
        dict con combustible_mensual, costos_adicionales_mensual, pernocta_mensual, total_mensual
    """
    combustible_total = Decimal('0')
    costos_adicionales_total = Decimal('0')
    pernocta_total = Decimal('0')

    # Base del vendedor
    base_vendedor = zona.municipio_base_vendedor or config.municipio_bodega
    if not base_vendedor:
        return {
            'combustible_mensual': Decimal('0'),
            'costos_adicionales_mensual': Decimal('0'),
            'pernocta_mensual': Decimal('0'),
            'total_mensual': Decimal('0')
        }

    # Consumo y costo adicional según tipo de vehículo
    if zona.tipo_vehiculo_comercial == 'MOTO':
        consumo_km_galon = config.consumo_galon_km_moto
        costo_adicional_km = config.costo_adicional_km_moto
    else:
        consumo_km_galon = config.consumo_galon_km_automovil
        costo_adicional_km = config.costo_adicional_km_automovil

    precio_galon = config.precio_galon_gasolina
    umbral = config.umbral_lejania_comercial_km

    # Calcular combustible y costos adicionales por cada municipio de la zona
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

        if distancia_efectiva > 0:
            distancia_ida_vuelta = distancia_efectiva * 2

            # Combustible
            if consumo_km_galon > 0:
                galones_por_visita = distancia_ida_vuelta / consumo_km_galon
                costo_combustible_visita = galones_por_visita * precio_galon
                combustible_total += costo_combustible_visita * visitas_mensuales

            # Costos adicionales (mantenimiento, depreciación, llantas)
            costo_adicional_visita = distancia_ida_vuelta * costo_adicional_km
            costos_adicionales_total += costo_adicional_visita * visitas_mensuales

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
        'costos_adicionales_mensual': costos_adicionales_total,
        'pernocta_mensual': pernocta_total,
        'total_mensual': combustible_total + costos_adicionales_total + pernocta_total
    }


def _calcular_comite_comercial(escenario, config):
    """
    Calcula y persiste los costos de desplazamiento al comité comercial para cada zona/vendedor.

    MULTI-MARCA: Si la zona tiene múltiples marcas, crea UN gasto
    con asignaciones_marca proporcionales.

    El comité comercial es una reunión periódica donde todos los vendedores se desplazan
    a un municipio fijo. Aplica el mismo umbral de lejanía comercial.
    """
    if not config.tiene_comite_comercial or not config.municipio_comite:
        # Eliminar gastos de comité previos si ya no aplica
        GastoComercial.objects.filter(
            escenario=escenario,
            nombre__startswith='Comité Comercial'
        ).delete()
        return

    frecuencia_map = {'SEMANAL': 4, 'TRISEMANAL': 3, 'QUINCENAL': 2, 'MENSUAL': 1}
    viajes_mes = frecuencia_map.get(config.frecuencia_comite, 1)
    umbral = config.umbral_lejania_comercial_km

    # Obtener todas las zonas activas del escenario
    zonas = Zona.objects.filter(
        escenario=escenario,
        activo=True
    ).select_related('municipio_base_vendedor', 'vendedor').prefetch_related('asignaciones_marca__marca')

    zonas_procesadas = set()

    for zona in zonas:
        # Obtener distribución de marcas de la zona
        distribucion = zona.get_distribucion_marcas()
        if not distribucion:
            continue

        zonas_procesadas.add(zona.id)

        # Base del vendedor
        base_vendedor = zona.municipio_base_vendedor or config.municipio_bodega
        if not base_vendedor:
            # Eliminar gastos previos si existen
            GastoComercial.objects.filter(
                escenario=escenario,
                nombre__startswith=f'Comité Comercial',
                zona=zona
            ).delete()
            continue

        # Calcular distancia al municipio del comité
        try:
            matriz = MatrizDesplazamiento.objects.get(
                origen_id=base_vendedor.id,
                destino_id=config.municipio_comite.id
            )
            distancia_km = matriz.distancia_km
        except MatrizDesplazamiento.DoesNotExist:
            distancia_km = Decimal('0')

        # Aplicar umbral (mismo que lejanías comerciales)
        distancia_efectiva = max(Decimal('0'), distancia_km - umbral)

        # Nota: NO excluimos zonas con distancia_efectiva == 0
        # El vendedor sigue asistiendo al comité aunque esté en el mismo municipio (costo $0)

        distancia_ida_vuelta = distancia_efectiva * 2

        # Determinar tipo de vehículo y costos
        if zona.tipo_vehiculo_comercial == 'MOTO':
            consumo_km_galon = config.consumo_galon_km_moto
            costo_adicional_km = config.costo_adicional_km_moto
        else:
            consumo_km_galon = config.consumo_galon_km_automovil
            costo_adicional_km = config.costo_adicional_km_automovil

        # Combustible mensual
        combustible_mes = Decimal('0')
        if consumo_km_galon > 0:
            galones_mes = (distancia_ida_vuelta * viajes_mes) / consumo_km_galon
            combustible_mes = galones_mes * config.precio_galon_gasolina

        # Costos adicionales mensual (mantenimiento, depreciación, llantas)
        costos_adicionales_mes = distancia_ida_vuelta * costo_adicional_km * viajes_mes

        # Helper para crear/actualizar gasto con multi-marca
        def _crear_gasto_comite_multimarca(nombre, valor):
            gasto, created = GastoComercial.objects.update_or_create(
                escenario=escenario,
                tipo='transporte_vendedores',
                nombre=nombre,
                zona=zona,
                defaults={
                    'valor_mensual': valor,
                    'marca': None,  # No usar FK legacy
                    'asignacion': 'compartido' if zona.es_compartido else 'individual',
                    'tipo_asignacion_geo': 'directo',
                }
            )
            # Actualizar asignaciones de marca
            GastoComercialMarca.objects.filter(gasto=gasto).delete()
            for marca_id, porcentaje_decimal in distribucion.items():
                marca_obj = Marca.objects.get(marca_id=marca_id)
                GastoComercialMarca.objects.create(
                    gasto=gasto,
                    marca=marca_obj,
                    porcentaje=porcentaje_decimal * Decimal('100')
                )

        # Guardar como DOS registros separados (igual que las zonas comerciales)
        _crear_gasto_comite_multimarca(f'Comité Comercial (Combustible) - {zona.nombre}', combustible_mes)
        _crear_gasto_comite_multimarca(f'Comité Comercial (Mant/Dep/Llan) - {zona.nombre}', costos_adicionales_mes)

    # Limpiar gastos de comité de zonas que ya no existen o no están activas
    GastoComercial.objects.filter(
        escenario=escenario,
        nombre__startswith='Comité Comercial'
    ).exclude(zona_id__in=zonas_procesadas).delete()


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
    ).select_related('marca', 'vehiculo', 'operacion')

    for ruta in rutas:
        marca = ruta.marca
        if not marca:
            continue

        resultado = _calcular_lejania_logistica_ruta(ruta, config)

        combustible = resultado['combustible_mensual']
        peajes = resultado['peaje_mensual']
        pernocta = resultado['pernocta_mensual']
        flete_base = resultado['flete_base_mensual']

        # Obtener campos de asignación de marca de la ruta
        asignacion_marca = ruta.asignacion or 'individual'

        # Obtener campos de operación de la ruta
        tipo_asig_op = ruta.tipo_asignacion_operacion or 'individual'
        operacion_obj = ruta.operacion
        criterio_prorrateo_op = ruta.criterio_prorrateo_operacion

        # Helper para guardar gasto logístico heredando marca y operación de la ruta
        def save_gasto(tipo, nombre, valor):
            if valor > 0:
                GastoLogistico.objects.update_or_create(
                    escenario=escenario,
                    tipo=tipo,
                    marca=marca,
                    nombre=nombre,
                    defaults={
                        'valor_mensual': valor,
                        'tipo_asignacion_geo': 'proporcional',
                        'zona': None,  # Proporcional no asigna zona directa
                        # Heredar asignación de marca de la ruta
                        'asignacion': asignacion_marca,
                        # Heredar operación de la ruta
                        'tipo_asignacion_operacion': tipo_asig_op,
                        'operacion': operacion_obj,
                        'criterio_prorrateo_operacion': criterio_prorrateo_op,
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
