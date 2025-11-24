# Migration to add increment indices system

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_add_individual_assignment_administrative'),
    ]

    operations = [
        # Expand ParametrosMacro with new indices
        migrations.AlterField(
            model_name='parametrosmacro',
            name='ipc',
            field=models.DecimalField(decimal_places=5, help_text='Índice de Precios al Consumidor', max_digits=6, verbose_name='IPC (%)'),
        ),
        migrations.AlterField(
            model_name='parametrosmacro',
            name='ipt',
            field=models.DecimalField(decimal_places=5, help_text='Índice de Precios al Transportador', max_digits=6, verbose_name='IPT (%)'),
        ),
        migrations.AlterField(
            model_name='parametrosmacro',
            name='incremento_salarios',
            field=models.DecimalField(decimal_places=5, help_text='Incremento general de salarios', max_digits=6, verbose_name='Incremento Salarios General (%)'),
        ),
        migrations.AddField(
            model_name='parametrosmacro',
            name='incremento_salario_minimo',
            field=models.DecimalField(decimal_places=5, default=0, help_text='Incremento específico del salario mínimo (puede diferir del general)', max_digits=6, verbose_name='Incremento Salario Mínimo (%)'),
        ),
        migrations.AddField(
            model_name='parametrosmacro',
            name='incremento_combustible',
            field=models.DecimalField(decimal_places=5, default=0, help_text='Índice de incremento de combustibles', max_digits=6, verbose_name='Incremento Combustible (%)'),
        ),
        migrations.AddField(
            model_name='parametrosmacro',
            name='incremento_arriendos',
            field=models.DecimalField(decimal_places=5, default=0, help_text='Usualmente igual al IPC', max_digits=6, verbose_name='Incremento Arriendos (%)'),
        ),
        migrations.AddField(
            model_name='parametrosmacro',
            name='incremento_personalizado_1',
            field=models.DecimalField(decimal_places=5, default=0, max_digits=6, verbose_name='Índice Personalizado 1 (%)'),
        ),
        migrations.AddField(
            model_name='parametrosmacro',
            name='nombre_personalizado_1',
            field=models.CharField(blank=True, help_text="Ej: 'Incremento Tecnología', 'Incremento Servicios Públicos'", max_length=100, verbose_name='Nombre Índice Personalizado 1'),
        ),
        migrations.AddField(
            model_name='parametrosmacro',
            name='incremento_personalizado_2',
            field=models.DecimalField(decimal_places=5, default=0, max_digits=6, verbose_name='Índice Personalizado 2 (%)'),
        ),
        migrations.AddField(
            model_name='parametrosmacro',
            name='nombre_personalizado_2',
            field=models.CharField(blank=True, help_text="Ej: 'Incremento Seguros', 'Incremento Mantenimiento'", max_length=100, verbose_name='Nombre Índice Personalizado 2'),
        ),
        
        # Add indice_incremento to all budget models
        migrations.AddField(
            model_name='personalcomercial',
            name='indice_incremento',
            field=models.CharField(choices=[('salarios', 'Incremento Salarios General'), ('salario_minimo', 'Incremento Salario Mínimo'), ('ipc', 'IPC (Índice de Precios al Consumidor)'), ('ipt', 'IPT (Índice de Precios al Transportador)'), ('combustible', 'Incremento Combustible'), ('arriendos', 'Incremento Arriendos'), ('personalizado_1', 'Índice Personalizado 1'), ('personalizado_2', 'Índice Personalizado 2'), ('fijo', 'Sin Incremento (Valor Fijo)')], default='salarios', help_text='Índice a usar para proyecciones de años futuros', max_length=20, verbose_name='Índice de Incremento'),
        ),
        migrations.AddField(
            model_name='personallogistico',
            name='indice_incremento',
            field=models.CharField(choices=[('salarios', 'Incremento Salarios General'), ('salario_minimo', 'Incremento Salario Mínimo'), ('ipc', 'IPC (Índice de Precios al Consumidor)'), ('ipt', 'IPT (Índice de Precios al Transportador)'), ('combustible', 'Incremento Combustible'), ('arriendos', 'Incremento Arriendos'), ('personalizado_1', 'Índice Personalizado 1'), ('personalizado_2', 'Índice Personalizado 2'), ('fijo', 'Sin Incremento (Valor Fijo)')], default='salarios', help_text='Índice a usar para proyecciones de años futuros', max_length=20, verbose_name='Índice de Incremento'),
        ),
        migrations.AddField(
            model_name='personaladministrativo',
            name='indice_incremento',
            field=models.CharField(choices=[('salarios', 'Incremento Salarios General'), ('salario_minimo', 'Incremento Salario Mínimo'), ('ipc', 'IPC (Índice de Precios al Consumidor)'), ('ipt', 'IPT (Índice de Precios al Transportador)'), ('combustible', 'Incremento Combustible'), ('arriendos', 'Incremento Arriendos'), ('personalizado_1', 'Índice Personalizado 1'), ('personalizado_2', 'Índice Personalizado 2'), ('fijo', 'Sin Incremento (Valor Fijo)')], default='salarios', help_text='Índice a usar para proyecciones de años futuros', max_length=20, verbose_name='Índice de Incremento'),
        ),
        migrations.AddField(
            model_name='vehiculo',
            name='indice_incremento',
            field=models.CharField(choices=[('salarios', 'Incremento Salarios General'), ('salario_minimo', 'Incremento Salario Mínimo'), ('ipc', 'IPC (Índice de Precios al Consumidor)'), ('ipt', 'IPT (Índice de Precios al Transportador)'), ('combustible', 'Incremento Combustible'), ('arriendos', 'Incremento Arriendos'), ('personalizado_1', 'Índice Personalizado 1'), ('personalizado_2', 'Índice Personalizado 2'), ('fijo', 'Sin Incremento (Valor Fijo)')], default='combustible', help_text='Índice a usar para proyecciones de años futuros', max_length=20, verbose_name='Índice de Incremento'),
        ),
        migrations.AddField(
            model_name='gastoadministrativo',
            name='indice_incremento',
            field=models.CharField(choices=[('salarios', 'Incremento Salarios General'), ('salario_minimo', 'Incremento Salario Mínimo'), ('ipc', 'IPC (Índice de Precios al Consumidor)'), ('ipt', 'IPT (Índice de Precios al Transportador)'), ('combustible', 'Incremento Combustible'), ('arriendos', 'Incremento Arriendos'), ('personalizado_1', 'Índice Personalizado 1'), ('personalizado_2', 'Índice Personalizado 2'), ('fijo', 'Sin Incremento (Valor Fijo)')], default='arriendos', help_text="Índice a usar para proyecciones de años futuros. Usar 'arriendos' para arriendos, 'ipc' para otros gastos", max_length=20, verbose_name='Índice de Incremento'),
        ),
        migrations.AddField(
            model_name='gastocomercial',
            name='indice_incremento',
            field=models.CharField(choices=[('salarios', 'Incremento Salarios General'), ('salario_minimo', 'Incremento Salario Mínimo'), ('ipc', 'IPC (Índice de Precios al Consumidor)'), ('ipt', 'IPT (Índice de Precios al Transportador)'), ('combustible', 'Incremento Combustible'), ('arriendos', 'Incremento Arriendos'), ('personalizado_1', 'Índice Personalizado 1'), ('personalizado_2', 'Índice Personalizado 2'), ('fijo', 'Sin Incremento (Valor Fijo)')], default='ipc', help_text='Índice a usar para proyecciones de años futuros', max_length=20, verbose_name='Índice de Incremento'),
        ),
        migrations.AddField(
            model_name='gastologistico',
            name='indice_incremento',
            field=models.CharField(choices=[('salarios', 'Incremento Salarios General'), ('salario_minimo', 'Incremento Salario Mínimo'), ('ipc', 'IPC (Índice de Precios al Consumidor)'), ('ipt', 'IPT (Índice de Precios al Transportador)'), ('combustible', 'Incremento Combustible'), ('arriendos', 'Incremento Arriendos'), ('personalizado_1', 'Índice Personalizado 1'), ('personalizado_2', 'Índice Personalizado 2'), ('fijo', 'Sin Incremento (Valor Fijo)')], default='combustible', help_text="Índice a usar para proyecciones de años futuros. Usar 'combustible' para gastos de vehículos", max_length=20, verbose_name='Índice de Incremento'),
        ),
    ]
