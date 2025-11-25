from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum, Q
from .models import (
    PersonalComercial, PersonalLogistico, PersonalAdministrativo,
    PoliticaRecursosHumanos, ParametrosMacro,
    GastoComercial, GastoLogistico, GastoAdministrativo,
    Escenario
)

def calculate_hr_expenses(escenario):
    """
    Recalcula los gastos de Dotación y Exámenes Médicos para un escenario dado.
    """
    if not escenario:
        return

    try:
        politica = PoliticaRecursosHumanos.objects.get(anio=escenario.anio, activo=True)
    except PoliticaRecursosHumanos.DoesNotExist:
        # Si no hay política para ese año, no podemos calcular nada
        return

    try:
        macro = ParametrosMacro.objects.get(anio=escenario.anio, activo=True)
        smlv = macro.salario_minimo_legal
    except ParametrosMacro.DoesNotExist:
        # Necesitamos el SMLV para calcular topes de dotación
        return

    # Definir topes y costos
    tope_dotacion = politica.tope_smlv_dotacion * smlv
    
    # --- 1. GASTOS COMERCIALES ---
    personal_comercial = PersonalComercial.objects.filter(escenario=escenario)
    
    # Dotación Comercial
    count_dotacion_com = personal_comercial.filter(salario_base__lte=tope_dotacion).count()
    valor_dotacion_com = (count_dotacion_com * politica.valor_dotacion_completa * politica.frecuencia_dotacion_anual) / 12
    
    if valor_dotacion_com > 0:
        GastoComercial.objects.update_or_create(
            escenario=escenario,
            tipo='dotacion',
            defaults={
                'nombre': 'Provisión Dotación y EPP',
                'valor_mensual': valor_dotacion_com,
                'marca_id': personal_comercial.first().marca_id if personal_comercial.exists() else None # Asignar a una marca por defecto o manejar lógica de marcas
            }
        )
        # Nota: La lógica de marcas es compleja si hay múltiples marcas en el escenario. 
        # Por simplicidad, aquí asumimos que si el escenario es por marca, se asigna. 
        # Si el escenario es global, se asigna a la primera marca encontrada o se requiere lógica más fina.
        # MEJORA: Iterar por marca si el escenario tiene personal de múltiples marcas.
    
    # Exámenes Comercial
    count_com = personal_comercial.count()
    # Ingreso (Rotación) + Periódico (1 al año)
    valor_examenes_com = (count_com * politica.costo_examen_ingreso_comercial * (politica.tasa_rotacion_anual / 100) / 12) + \
                         (count_com * politica.costo_examen_periodico_comercial / 12)

    if valor_examenes_com > 0:
        GastoComercial.objects.update_or_create(
            escenario=escenario,
            tipo='examenes',
            defaults={
                'nombre': 'Provisión Exámenes Médicos',
                'valor_mensual': valor_examenes_com,
                'marca_id': personal_comercial.first().marca_id if personal_comercial.exists() else None
            }
        )

    # --- 2. GASTOS LOGÍSTICOS ---
    personal_logistico = PersonalLogistico.objects.filter(escenario=escenario)
    
    # Dotación Logística
    count_dotacion_log = personal_logistico.filter(salario_base__lte=tope_dotacion).count()
    valor_dotacion_log = (count_dotacion_log * politica.valor_dotacion_completa * politica.frecuencia_dotacion_anual) / 12
    
    if valor_dotacion_log > 0:
        GastoLogistico.objects.update_or_create(
            escenario=escenario,
            tipo='dotacion',
            defaults={
                'nombre': 'Provisión Dotación y EPP',
                'valor_mensual': valor_dotacion_log,
                'marca_id': personal_logistico.first().marca_id if personal_logistico.exists() else None
            }
        )

    # Exámenes Logística
    count_log = personal_logistico.count()
    valor_examenes_log = (count_log * politica.costo_examen_ingreso_operativo * (politica.tasa_rotacion_anual / 100) / 12) + \
                         (count_log * politica.costo_examen_periodico_operativo / 12)

    if valor_examenes_log > 0:
        GastoLogistico.objects.update_or_create(
            escenario=escenario,
            tipo='examenes',
            defaults={
                'nombre': 'Provisión Exámenes Médicos',
                'valor_mensual': valor_examenes_log,
                'marca_id': personal_logistico.first().marca_id if personal_logistico.exists() else None
            }
        )

    # --- 3. GASTOS ADMINISTRATIVOS ---
    personal_admin = PersonalAdministrativo.objects.filter(escenario=escenario)
    
    # Dotación Administrativa
    count_dotacion_admin = personal_admin.filter(salario_base__lte=tope_dotacion).count()
    valor_dotacion_admin = (count_dotacion_admin * politica.valor_dotacion_completa * politica.frecuencia_dotacion_anual) / 12
    
    if valor_dotacion_admin > 0:
        GastoAdministrativo.objects.update_or_create(
            escenario=escenario,
            tipo='dotacion',
            defaults={
                'nombre': 'Provisión Dotación y EPP',
                'valor_mensual': valor_dotacion_admin,
                'marca_id': personal_admin.first().marca_id if personal_admin.exists() else None
            }
        )

    # Exámenes Administrativos
    count_admin = personal_admin.count()
    valor_examenes_admin = (count_admin * politica.costo_examen_ingreso_operativo * (politica.tasa_rotacion_anual / 100) / 12) + \
                           (count_admin * politica.costo_examen_periodico_operativo / 12)

    if valor_examenes_admin > 0:
        GastoAdministrativo.objects.update_or_create(
            escenario=escenario,
            tipo='examenes',
            defaults={
                'nombre': 'Provisión Exámenes Médicos',
                'valor_mensual': valor_examenes_admin,
                'marca_id': personal_admin.first().marca_id if personal_admin.exists() else None
            }
        )


@receiver([post_save, post_delete], sender=PersonalComercial)
@receiver([post_save, post_delete], sender=PersonalLogistico)
@receiver([post_save, post_delete], sender=PersonalAdministrativo)
def update_expenses_on_personnel_change(sender, instance, **kwargs):
    """
    Disparador cuando cambia el personal.
    """
    if instance.escenario:
        calculate_hr_expenses(instance.escenario)

@receiver(post_save, sender=PoliticaRecursosHumanos)
def update_expenses_on_policy_change(sender, instance, **kwargs):
    """
    Disparador cuando cambia la política (afecta a todos los escenarios de ese año).
    """
    escenarios = Escenario.objects.filter(anio=instance.anio)
    for escenario in escenarios:
        calculate_hr_expenses(escenario)
