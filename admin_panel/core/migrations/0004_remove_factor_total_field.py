# Generated migration to remove factor_total field (now a calculated property)

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_add_logistic_profile_types'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='factorprestacional',
            name='factor_total',
        ),
    ]
