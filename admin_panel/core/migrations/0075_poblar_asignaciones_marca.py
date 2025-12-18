# Generated migration to populate marca assignments from legacy fields
from decimal import Decimal
from django.db import migrations


def migrate_personal_comercial(apps, schema_editor):
    """Migrar PersonalComercial: crear asignaciones desde campo marca existente"""
    PersonalComercial = apps.get_model('core', 'PersonalComercial')
    PersonalComercialMarca = apps.get_model('core', 'PersonalComercialMarca')

    for pc in PersonalComercial.objects.filter(marca__isnull=False):
        # Verificar si ya tiene asignaciones (por si se corre de nuevo)
        if not PersonalComercialMarca.objects.filter(personal=pc).exists():
            if pc.asignacion == 'individual' or not pc.porcentaje_dedicacion:
                # Individual: 100% a la marca
                PersonalComercialMarca.objects.create(
                    personal=pc,
                    marca_id=pc.marca_id,
                    porcentaje=Decimal('100')
                )
            else:
                # Compartido: usar porcentaje_dedicacion (0-1) * 100
                porcentaje = (pc.porcentaje_dedicacion or Decimal('0')) * 100
                if porcentaje > 0:
                    PersonalComercialMarca.objects.create(
                        personal=pc,
                        marca_id=pc.marca_id,
                        porcentaje=porcentaje
                    )


def migrate_personal_logistico(apps, schema_editor):
    """Migrar PersonalLogistico"""
    PersonalLogistico = apps.get_model('core', 'PersonalLogistico')
    PersonalLogisticoMarca = apps.get_model('core', 'PersonalLogisticoMarca')

    for pl in PersonalLogistico.objects.filter(marca__isnull=False):
        if not PersonalLogisticoMarca.objects.filter(personal=pl).exists():
            if pl.asignacion == 'individual' or not pl.porcentaje_dedicacion:
                PersonalLogisticoMarca.objects.create(
                    personal=pl,
                    marca_id=pl.marca_id,
                    porcentaje=Decimal('100')
                )
            else:
                porcentaje = (pl.porcentaje_dedicacion or Decimal('0')) * 100
                if porcentaje > 0:
                    PersonalLogisticoMarca.objects.create(
                        personal=pl,
                        marca_id=pl.marca_id,
                        porcentaje=porcentaje
                    )


def migrate_personal_administrativo(apps, schema_editor):
    """Migrar PersonalAdministrativo"""
    PersonalAdministrativo = apps.get_model('core', 'PersonalAdministrativo')
    PersonalAdministrativoMarca = apps.get_model('core', 'PersonalAdministrativoMarca')
    Marca = apps.get_model('core', 'Marca')

    for pa in PersonalAdministrativo.objects.all():
        if not PersonalAdministrativoMarca.objects.filter(personal=pa).exists():
            if pa.marca_id:
                # Tiene marca asignada: 100%
                PersonalAdministrativoMarca.objects.create(
                    personal=pa,
                    marca_id=pa.marca_id,
                    porcentaje=Decimal('100')
                )
            elif pa.asignacion == 'compartido':
                # Compartido sin marca específica: distribuir equitativamente entre marcas activas
                marcas_activas = list(Marca.objects.filter(activa=True))
                if marcas_activas:
                    porcentaje_equitativo = Decimal('100') / len(marcas_activas)
                    for marca in marcas_activas:
                        PersonalAdministrativoMarca.objects.create(
                            personal=pa,
                            marca=marca,
                            porcentaje=porcentaje_equitativo
                        )


def migrate_gasto_comercial(apps, schema_editor):
    """Migrar GastoComercial"""
    GastoComercial = apps.get_model('core', 'GastoComercial')
    GastoComercialMarca = apps.get_model('core', 'GastoComercialMarca')

    for gc in GastoComercial.objects.filter(marca__isnull=False):
        if not GastoComercialMarca.objects.filter(gasto=gc).exists():
            # Gastos comerciales siempre 100% a la marca
            GastoComercialMarca.objects.create(
                gasto=gc,
                marca_id=gc.marca_id,
                porcentaje=Decimal('100')
            )


def migrate_gasto_logistico(apps, schema_editor):
    """Migrar GastoLogistico"""
    GastoLogistico = apps.get_model('core', 'GastoLogistico')
    GastoLogisticoMarca = apps.get_model('core', 'GastoLogisticoMarca')

    for gl in GastoLogistico.objects.filter(marca__isnull=False):
        if not GastoLogisticoMarca.objects.filter(gasto=gl).exists():
            GastoLogisticoMarca.objects.create(
                gasto=gl,
                marca_id=gl.marca_id,
                porcentaje=Decimal('100')
            )


def migrate_gasto_administrativo(apps, schema_editor):
    """Migrar GastoAdministrativo"""
    GastoAdministrativo = apps.get_model('core', 'GastoAdministrativo')
    GastoAdministrativoMarca = apps.get_model('core', 'GastoAdministrativoMarca')
    Marca = apps.get_model('core', 'Marca')

    for ga in GastoAdministrativo.objects.all():
        if not GastoAdministrativoMarca.objects.filter(gasto=ga).exists():
            if ga.marca_id:
                GastoAdministrativoMarca.objects.create(
                    gasto=ga,
                    marca_id=ga.marca_id,
                    porcentaje=Decimal('100')
                )
            elif ga.asignacion == 'compartido':
                # Compartido: distribuir equitativamente
                marcas_activas = list(Marca.objects.filter(activa=True))
                if marcas_activas:
                    porcentaje_equitativo = Decimal('100') / len(marcas_activas)
                    for marca in marcas_activas:
                        GastoAdministrativoMarca.objects.create(
                            gasto=ga,
                            marca=marca,
                            porcentaje=porcentaje_equitativo
                        )


def migrate_all_forward(apps, schema_editor):
    """Ejecutar todas las migraciones de datos"""
    migrate_personal_comercial(apps, schema_editor)
    migrate_personal_logistico(apps, schema_editor)
    migrate_personal_administrativo(apps, schema_editor)
    migrate_gasto_comercial(apps, schema_editor)
    migrate_gasto_logistico(apps, schema_editor)
    migrate_gasto_administrativo(apps, schema_editor)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0074_crear_modelos_asignacion_marca'),
    ]

    operations = [
        migrations.RunPython(migrate_all_forward, migrations.RunPython.noop),
    ]
