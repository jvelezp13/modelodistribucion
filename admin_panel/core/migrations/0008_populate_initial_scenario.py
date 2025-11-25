# Data migration to populate initial scenario

from django.db import migrations

def create_initial_scenario(apps, schema_editor):
    Escenario = apps.get_model('core', 'Escenario')
    PersonalComercial = apps.get_model('core', 'PersonalComercial')
    PersonalLogistico = apps.get_model('core', 'PersonalLogistico')
    PersonalAdministrativo = apps.get_model('core', 'PersonalAdministrativo')
    Vehiculo = apps.get_model('core', 'Vehiculo')
    GastoComercial = apps.get_model('core', 'GastoComercial')
    GastoLogistico = apps.get_model('core', 'GastoLogistico')
    GastoAdministrativo = apps.get_model('core', 'GastoAdministrativo')
    ProyeccionVentas = apps.get_model('core', 'ProyeccionVentas')

    # Create default scenario
    default_scenario, created = Escenario.objects.get_or_create(
        nombre="Plan 2025",
        anio=2025,
        defaults={
            'tipo': 'planeado',
            'periodo_tipo': 'anual',
            'activo': True,
            'aprobado': True,
            'notas': 'Escenario inicial creado automáticamente por migración'
        }
    )

    # Update all existing records to use this scenario
    PersonalComercial.objects.filter(escenario__isnull=True).update(escenario=default_scenario)
    PersonalLogistico.objects.filter(escenario__isnull=True).update(escenario=default_scenario)
    PersonalAdministrativo.objects.filter(escenario__isnull=True).update(escenario=default_scenario)
    Vehiculo.objects.filter(escenario__isnull=True).update(escenario=default_scenario)
    GastoComercial.objects.filter(escenario__isnull=True).update(escenario=default_scenario)
    GastoLogistico.objects.filter(escenario__isnull=True).update(escenario=default_scenario)
    GastoAdministrativo.objects.filter(escenario__isnull=True).update(escenario=default_scenario)
    ProyeccionVentas.objects.filter(escenario__isnull=True).update(escenario=default_scenario)

def reverse_initial_scenario(apps, schema_editor):
    # We don't want to delete the scenario or clear the fields on reverse
    # as it might cause data loss if we re-apply.
    # But strictly speaking, reverse should undo.
    # For safety, we'll just pass.
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_add_budget_scenarios'),
    ]

    operations = [
        migrations.RunPython(create_initial_scenario, reverse_initial_scenario),
    ]
