# Generated manually to make marca field nullable in PersonalComercial

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0077_poblar_zona_marca'),
    ]

    operations = [
        migrations.AlterField(
            model_name='personalcomercial',
            name='marca',
            field=models.ForeignKey(
                blank=True,
                help_text='DEPRECADO: Usar asignaciones multi-marca en su lugar',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='personal_comercial',
                to='core.marca'
            ),
        ),
    ]
