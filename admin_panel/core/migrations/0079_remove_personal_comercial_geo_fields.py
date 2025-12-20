# Generated manually to remove geographic assignment fields from PersonalComercial

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0078_make_personal_comercial_marca_nullable'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='personalcomercial',
            name='tipo_asignacion_geo',
        ),
        migrations.RemoveField(
            model_name='personalcomercial',
            name='zona',
        ),
    ]
