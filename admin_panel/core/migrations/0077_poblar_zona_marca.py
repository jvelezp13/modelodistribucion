# Migration to populate ZonaMarca from legacy marca field
from decimal import Decimal
from django.db import migrations


def migrate_zonas_forward(apps, schema_editor):
    """Migrar Zona: crear asignaciones desde campo marca existente"""
    Zona = apps.get_model('core', 'Zona')
    ZonaMarca = apps.get_model('core', 'ZonaMarca')

    for zona in Zona.objects.filter(marca__isnull=False):
        # Verificar si ya tiene asignaciones (por si se corre de nuevo)
        if not ZonaMarca.objects.filter(zona=zona).exists():
            # Crear asignación al 100% para la marca actual
            ZonaMarca.objects.create(
                zona=zona,
                marca_id=zona.marca_id,
                porcentaje=Decimal('100')
            )


def migrate_zonas_reverse(apps, schema_editor):
    """Revertir: restaurar campo marca desde asignaciones"""
    Zona = apps.get_model('core', 'Zona')
    ZonaMarca = apps.get_model('core', 'ZonaMarca')

    for zona in Zona.objects.all():
        # Obtener la marca con mayor porcentaje
        asignacion = ZonaMarca.objects.filter(zona=zona).order_by('-porcentaje').first()
        if asignacion:
            zona.marca_id = asignacion.marca_id
            zona.save(update_fields=['marca_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0076_crear_zona_marca'),
    ]

    operations = [
        migrations.RunPython(migrate_zonas_forward, migrate_zonas_reverse),
    ]
