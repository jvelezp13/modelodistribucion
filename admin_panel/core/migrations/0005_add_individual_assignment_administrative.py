# Generated migration to add individual assignment to administrative items

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_remove_factor_total_field'),
    ]

    operations = [
        # PersonalAdministrativo changes
        migrations.AddField(
            model_name='personaladministrativo',
            name='marca',
            field=models.ForeignKey(
                blank=True,
                help_text='Dejar vacío si es compartido entre todas las marcas',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='personal_administrativo',
                to='core.marca',
                verbose_name='Marca'
            ),
        ),
        migrations.AlterField(
            model_name='personaladministrativo',
            name='asignacion',
            field=models.CharField(
                choices=[
                    ('individual', 'Individual (asignado a una marca)'),
                    ('compartido', 'Compartido entre marcas')
                ],
                default='compartido',
                max_length=20
            ),
        ),
        migrations.AlterField(
            model_name='personaladministrativo',
            name='criterio_prorrateo',
            field=models.CharField(
                blank=True,
                choices=[
                    ('ventas', 'Por Ventas'),
                    ('headcount', 'Por Headcount'),
                    ('equitativo', 'Equitativo')
                ],
                default='equitativo',
                help_text='Solo aplica para asignación compartida',
                max_length=20,
                null=True
            ),
        ),
        
        # GastoAdministrativo changes
        migrations.AddField(
            model_name='gastoadministrativo',
            name='marca',
            field=models.ForeignKey(
                blank=True,
                help_text='Dejar vacío si es compartido entre todas las marcas',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='gastos_administrativos',
                to='core.marca',
                verbose_name='Marca'
            ),
        ),
        migrations.AddField(
            model_name='gastoadministrativo',
            name='asignacion',
            field=models.CharField(
                choices=[
                    ('individual', 'Individual (asignado a una marca)'),
                    ('compartido', 'Compartido entre marcas')
                ],
                default='compartido',
                max_length=20
            ),
        ),
        migrations.AlterField(
            model_name='gastoadministrativo',
            name='criterio_prorrateo',
            field=models.CharField(
                blank=True,
                choices=[
                    ('ventas', 'Por Ventas'),
                    ('headcount', 'Por Headcount'),
                    ('equitativo', 'Equitativo')
                ],
                default='ventas',
                help_text='Solo aplica para asignación compartida',
                max_length=20,
                null=True
            ),
        ),
    ]
