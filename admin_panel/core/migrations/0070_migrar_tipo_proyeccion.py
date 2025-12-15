# Generated manually - Migración de datos para tipo de proyección

from django.db import migrations


def migrar_tipo_proyeccion(apps, schema_editor):
    """
    Migra los valores del campo tipo:
    - 'manual' -> 'simple'
    - Los otros valores obsoletos se convierten a 'simple' también
      (crecimiento, precio_unidades, canal, penetracion)
    """
    ProyeccionVentasConfig = apps.get_model('core', 'ProyeccionVentasConfig')

    # Convertir 'manual' a 'simple'
    ProyeccionVentasConfig.objects.filter(tipo='manual').update(tipo='simple')

    # Convertir otros métodos obsoletos a 'simple' para no perder datos
    # El usuario podrá reconfigurarlos después
    ProyeccionVentasConfig.objects.filter(
        tipo__in=['crecimiento', 'precio_unidades', 'canal', 'penetracion']
    ).update(tipo='simple')


def reverse_migration(apps, schema_editor):
    """
    Revertir: simple -> manual
    Nota: Esta reversión es aproximada, no restaura los tipos originales
    """
    ProyeccionVentasConfig = apps.get_model('core', 'ProyeccionVentasConfig')
    ProyeccionVentasConfig.objects.filter(tipo='simple').update(tipo='manual')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0069_redisenar_proyeccion_ventas'),
    ]

    operations = [
        migrations.RunPython(migrar_tipo_proyeccion, reverse_migration),
    ]
