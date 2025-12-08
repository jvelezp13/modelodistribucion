# Generated manually for auxilios_no_prestacionales JSON field

from django.db import migrations, models


def migrate_auxilio_to_json(apps, schema_editor):
    """Migra datos existentes de auxilio_adicional al nuevo campo JSON."""
    PersonalComercial = apps.get_model('core', 'PersonalComercial')
    PersonalLogistico = apps.get_model('core', 'PersonalLogistico')
    PersonalAdministrativo = apps.get_model('core', 'PersonalAdministrativo')

    for Model in [PersonalComercial, PersonalLogistico, PersonalAdministrativo]:
        for obj in Model.objects.filter(auxilio_adicional__gt=0):
            obj.auxilios_no_prestacionales = {'otros': float(obj.auxilio_adicional)}
            obj.save(update_fields=['auxilios_no_prestacionales'])


def reverse_migrate(apps, schema_editor):
    """Revierte la migración: copia el total del JSON al campo antiguo."""
    PersonalComercial = apps.get_model('core', 'PersonalComercial')
    PersonalLogistico = apps.get_model('core', 'PersonalLogistico')
    PersonalAdministrativo = apps.get_model('core', 'PersonalAdministrativo')

    for Model in [PersonalComercial, PersonalLogistico, PersonalAdministrativo]:
        for obj in Model.objects.exclude(auxilios_no_prestacionales={}):
            if obj.auxilios_no_prestacionales:
                total = sum(obj.auxilios_no_prestacionales.values())
                obj.auxilio_adicional = total
                obj.save(update_fields=['auxilio_adicional'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0056_add_auxilio_adicional_to_personal'),
    ]

    operations = [
        # Agregar campo JSON a PersonalComercial
        migrations.AddField(
            model_name='personalcomercial',
            name='auxilios_no_prestacionales',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Auxilios que NO generan prestaciones. Ej: {cuota_carro: 500000, arriendo_vivienda: 800000, bono_alimentacion: 200000, rodamiento: 150000}',
                verbose_name='Auxilios No Prestacionales'
            ),
        ),
        # Agregar campo JSON a PersonalLogistico
        migrations.AddField(
            model_name='personallogistico',
            name='auxilios_no_prestacionales',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Auxilios que NO generan prestaciones. Ej: {cuota_carro: 500000, arriendo_vivienda: 800000, bono_alimentacion: 200000, rodamiento: 150000}',
                verbose_name='Auxilios No Prestacionales'
            ),
        ),
        # Agregar campo JSON a PersonalAdministrativo
        migrations.AddField(
            model_name='personaladministrativo',
            name='auxilios_no_prestacionales',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Auxilios que NO generan prestaciones. Ej: {cuota_carro: 500000, arriendo_vivienda: 800000, bono_alimentacion: 200000, rodamiento: 150000}',
                verbose_name='Auxilios No Prestacionales'
            ),
        ),
        # Migrar datos existentes
        migrations.RunPython(migrate_auxilio_to_json, reverse_migrate),
        # Actualizar verbose_name del campo antiguo (deprecado)
        migrations.AlterField(
            model_name='personalcomercial',
            name='auxilio_adicional',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=12,
                verbose_name='Auxilio Adicional (Deprecado)'
            ),
        ),
        migrations.AlterField(
            model_name='personallogistico',
            name='auxilio_adicional',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='DEPRECADO - Usar auxilios_no_prestacionales',
                max_digits=12,
                verbose_name='Auxilio Adicional (Deprecado)'
            ),
        ),
        migrations.AlterField(
            model_name='personaladministrativo',
            name='auxilio_adicional',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='DEPRECADO - Usar auxilios_no_prestacionales',
                max_digits=12,
                verbose_name='Auxilio Adicional (Deprecado)'
            ),
        ),
    ]
