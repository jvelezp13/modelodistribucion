# Generated migration for adding logistic profile types
# This migration adds new profile choices for logistics personnel

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_configuraciondescuentos_tramodescuentofactura'),
    ]

    operations = [
        migrations.AlterField(
            model_name='factorprestacional',
            name='perfil',
            field=models.CharField(
                choices=[
                    ('comercial', 'Comercial'),
                    ('administrativo', 'Administrativo'),
                    ('logistico', 'Logístico'),
                    ('logistico_bodega', 'Logístico Bodega'),
                    ('logistico_calle', 'Logístico Calle'),
                    ('aprendiz_sena', 'Aprendiz SENA')
                ],
                max_length=50,
                unique=True,
                verbose_name='Perfil'
            ),
        ),
        migrations.AlterField(
            model_name='personallogistico',
            name='perfil_prestacional',
            field=models.CharField(
                choices=[
                    ('logistico', 'Logístico'),
                    ('logistico_bodega', 'Logístico Bodega'),
                    ('logistico_calle', 'Logístico Calle'),
                    ('administrativo', 'Administrativo')
                ],
                default='logistico',
                max_length=20
            ),
        ),
    ]
