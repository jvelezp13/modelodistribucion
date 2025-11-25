# Migration to add budget scenarios system

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_add_increment_indices'),
    ]

    operations = [
        migrations.CreateModel(
            name='Escenario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(help_text="Ej: 'Plan 2025', 'Real Q1 2025'", max_length=200, verbose_name='Nombre')),
                ('tipo', models.CharField(choices=[('planeado', 'Planeado'), ('sugerido_marca', 'Sugerido por Marca'), ('real', 'Real Ejecutado')], max_length=20, verbose_name='Tipo de Escenario')),
                ('anio', models.IntegerField(verbose_name='Año')),
                ('periodo_tipo', models.CharField(choices=[('anual', 'Anual'), ('trimestral', 'Trimestral'), ('mensual', 'Mensual')], default='anual', max_length=20, verbose_name='Tipo de Periodo')),
                ('periodo_numero', models.IntegerField(blank=True, help_text='1-4 para trimestral, 1-12 para mensual. Dejar vacío para anual', null=True, verbose_name='Número de Periodo')),
                ('activo', models.BooleanField(default=False, help_text='Escenario activo para simulación', verbose_name='Activo')),
                ('aprobado', models.BooleanField(default=False, help_text='Para workflow de aprobación', verbose_name='Aprobado')),
                ('notas', models.TextField(blank=True, verbose_name='Notas')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_modificacion', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Escenario',
                'verbose_name_plural': 'Escenarios',
                'db_table': 'dxv_escenario',
                'ordering': ['-anio', '-periodo_numero', 'tipo'],
                'unique_together': {('nombre', 'anio')},
            },
        ),
        migrations.AddField(
            model_name='gastoadministrativo',
            name='escenario',
            field=models.ForeignKey(blank=True, help_text='Escenario al que pertenece este registro', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='gasto_administrativo_items', to='core.escenario', verbose_name='Escenario'),
        ),
        migrations.AddField(
            model_name='gastocomercial',
            name='escenario',
            field=models.ForeignKey(blank=True, help_text='Escenario al que pertenece este registro', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='gasto_comercial_items', to='core.escenario', verbose_name='Escenario'),
        ),
        migrations.AddField(
            model_name='gastologistico',
            name='escenario',
            field=models.ForeignKey(blank=True, help_text='Escenario al que pertenece este registro', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='gasto_logistico_items', to='core.escenario', verbose_name='Escenario'),
        ),
        migrations.AddField(
            model_name='personaladministrativo',
            name='escenario',
            field=models.ForeignKey(blank=True, help_text='Escenario al que pertenece este registro', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='personal_administrativo_items', to='core.escenario', verbose_name='Escenario'),
        ),
        migrations.AddField(
            model_name='personalcomercial',
            name='escenario',
            field=models.ForeignKey(blank=True, help_text='Escenario al que pertenece este registro', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='personal_comercial_items', to='core.escenario', verbose_name='Escenario'),
        ),
        migrations.AddField(
            model_name='personallogistico',
            name='escenario',
            field=models.ForeignKey(blank=True, help_text='Escenario al que pertenece este registro', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='personal_logistico_items', to='core.escenario', verbose_name='Escenario'),
        ),
        migrations.AddField(
            model_name='proyeccionventas',
            name='escenario',
            field=models.ForeignKey(blank=True, help_text='Escenario al que pertenece este registro', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='proyeccion_ventas_items', to='core.escenario', verbose_name='Escenario'),
        ),
        migrations.AddField(
            model_name='vehiculo',
            name='escenario',
            field=models.ForeignKey(blank=True, help_text='Escenario al que pertenece este registro', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='vehiculo_items', to='core.escenario', verbose_name='Escenario'),
        ),
    ]
