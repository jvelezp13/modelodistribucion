from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum, Q
from .models import (
    PersonalComercial, PersonalLogistico, PersonalAdministrativo,
    PoliticaRecursosHumanos, ParametrosMacro,
    GastoComercial, GastoLogistico, GastoAdministrativo,
    Escenario, Marca, Vehiculo
)

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
    
    # Función auxiliar para procesar gastos por grupo de marcas
    def process_expenses(model_personal, model_gasto, tipo_personal):
        # Obtener todas las marcas presentes en el personal de este escenario + None (compartidos)
        qs = model_personal.objects.filter(escenario=escenario)
        marcas_ids = set(qs.values_list('marca', flat=True)) # Incluye None si hay compartidos
        
        for marca_id in marcas_ids:
            # Filtrar personal para esta marca (o None)
            if marca_id is None:
                personal_grupo = qs.filter(marca__isnull=True)
                marca_obj = None
                asignacion = 'compartido'
            else:
                personal_grupo = qs.filter(marca_id=marca_id)
                marca_obj = Marca.objects.get(pk=marca_id)
                asignacion = 'individual'
            
            count_total = personal_grupo.count()
            if count_total == 0:
                continue

            # --- 1. DOTACIÓN (Aplica a todos con salario <= tope) ---
            count_dotacion = personal_grupo.filter(salario_base__lte=tope_dotacion).count()
            valor_dotacion = (count_dotacion * politica.valor_dotacion_completa * politica.frecuencia_dotacion_anual) / 12
            
            if valor_dotacion > 0:
                model_gasto.objects.update_or_create(
                    escenario=escenario,
                    tipo='dotacion',
                    marca=marca_obj,
                    defaults={
                        'nombre': 'Provisión Dotación',
                        'valor_mensual': valor_dotacion,
                        'asignacion': asignacion
                    }
                )
            else:
                # Si baja a cero, borrar el registro si existe
                model_gasto.objects.filter(escenario=escenario, tipo='dotacion', marca=marca_obj).delete()

            # --- 2. EXÁMENES MÉDICOS ---
            # Definir costos según tipo de personal
            if tipo_personal == 'comercial':
                costo_ingreso = politica.costo_examen_ingreso_comercial
                costo_periodico = politica.costo_examen_periodico_comercial
            else:
                costo_ingreso = politica.costo_examen_ingreso_operativo
                costo_periodico = politica.costo_examen_periodico_operativo
            
            valor_examenes = (count_total * costo_ingreso * (politica.tasa_rotacion_anual / 100) / 12) + \
                             (count_total * costo_periodico / 12)

            if valor_examenes > 0:
                model_gasto.objects.update_or_create(
                    escenario=escenario,
                    tipo='examenes',
                    marca=marca_obj,
                    defaults={
                        'nombre': 'Provisión Exámenes Médicos',
                        'valor_mensual': valor_examenes,
                        'asignacion': asignacion
                    }
                )
            else:
                model_gasto.objects.filter(escenario=escenario, tipo='examenes', marca=marca_obj).delete()

            # --- 3. EPP (SOLO COMERCIAL) ---
            if tipo_personal == 'comercial':
                # EPP aplica a TODOS los comerciales (o definir criterio, aquí asumimos todos)
                valor_epp = (count_total * politica.valor_epp_anual_comercial * politica.frecuencia_epp_anual) / 12
                
                if valor_epp > 0:
                    model_gasto.objects.update_or_create(
                        escenario=escenario,
                        tipo='epp',
                        marca=marca_obj,
                        defaults={
                            'nombre': 'Provisión EPP (Comercial)',
                            'valor_mensual': valor_epp,
                            'asignacion': asignacion
                        }
                    )
                else:
                    model_gasto.objects.filter(escenario=escenario, tipo='epp', marca=marca_obj).delete()

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
    for escenario in escenarios:
        calculate_hr_expenses(escenario)

def calculate_logistic_expenses(escenario):
    """
    Recalcula los gastos logísticos automáticos basados en la flota de vehículos.
    """
    if not escenario:
        return

    try:
        macro = ParametrosMacro.objects.get(anio=escenario.anio, activo=True)
        precio_galon = macro.precio_galon_combustible
    except ParametrosMacro.DoesNotExist:
        precio_galon = 0

    # Obtener todas las marcas con vehículos en este escenario
    qs_vehiculos = Vehiculo.objects.filter(escenario=escenario)
    marcas_ids = set(qs_vehiculos.values_list('marca', flat=True))

    for marca_id in marcas_ids:
        marca_obj = Marca.objects.get(pk=marca_id)
        vehiculos_marca = qs_vehiculos.filter(marca=marca_obj)
        
        # Inicializar acumuladores por tipo de gasto
        total_flete = 0
        total_renting = 0
        total_depreciacion = 0
        total_mantenimiento = 0
        total_seguros = 0
        total_combustible = 0
        total_lavado = 0
        total_parqueadero = 0
        total_monitoreo = 0

        for v in vehiculos_marca:
            if v.esquema == 'tercero':
                # Flete: Valor Flete * Cantidad
                total_flete += v.valor_flete_mensual * v.cantidad
            
            elif v.esquema in ['renting', 'tradicional']:
                # Costos comunes para Propio y Renting
                total_lavado += v.costo_lavado_mensual * v.cantidad
                total_parqueadero += v.costo_parqueadero_mensual * v.cantidad
                total_monitoreo += v.costo_monitoreo_mensual * v.cantidad

                # Combustible (común)
                if v.consumo_galon_km > 0:
                    galones = v.kilometraje_promedio_mensual / v.consumo_galon_km
                    total_combustible += galones * precio_galon * v.cantidad

                if v.esquema == 'renting':
                    # Renting: Canon * Cantidad
                    total_renting += v.canon_renting * v.cantidad
                    
                elif v.esquema == 'tradicional': # Propio
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
                    defaults={
                        'nombre': nombre,
                        'valor_mensual': valor,
                        'asignacion': 'individual'
                    }
                )
            else:
                GastoLogistico.objects.filter(escenario=escenario, tipo=tipo, marca=marca_obj).delete()

        # Actualizar cada rubro
        update_gasto('flete_tercero', 'Flete Transporte (Tercero)', total_flete)
        update_gasto('canon_renting', 'Canon Renting Flota', total_renting)
        update_gasto('depreciacion_vehiculo', 'Depreciación Flota Propia', total_depreciacion)
        update_gasto('mantenimiento_vehiculos', 'Mantenimiento Flota Propia', total_mantenimiento)
        update_gasto('seguros_carga', 'Seguros Flota Propia', total_seguros) # Usamos seguros_carga o creamos uno nuevo? Reutilicemos por ahora o 'otros'
        update_gasto('combustible', 'Combustible Flota', total_combustible)
        update_gasto('lavado_vehiculos', 'Aseo y Limpieza Vehículos', total_lavado)
        update_gasto('parqueadero_vehiculos', 'Parqueaderos', total_parqueadero)
        update_gasto('monitoreo_satelital', 'Monitoreo Satelital (GPS)', total_monitoreo)


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
