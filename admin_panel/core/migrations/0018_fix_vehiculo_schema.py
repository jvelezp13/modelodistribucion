# Generated manually to fix vehiculo schema issues
# This migration ensures the Vehiculo table is in sync with the model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_remove_vehiculo_banco_remove_vehiculo_conductor_and_more'),
    ]

    operations = [
        # This is a no-op migration that just ensures Django's migration state
        # is in sync with the actual database schema.
        # If there are any orphaned columns, we try to remove them again.
        migrations.RunSQL(
            # Drop columns if they still exist (PostgreSQL syntax)
            sql=[
                "ALTER TABLE dxv_vehiculo DROP COLUMN IF EXISTS banco CASCADE;",
                "ALTER TABLE dxv_vehiculo DROP COLUMN IF EXISTS conductor CASCADE;",
                "ALTER TABLE dxv_vehiculo DROP COLUMN IF EXISTS numero_cuenta CASCADE;",
                "ALTER TABLE dxv_vehiculo DROP COLUMN IF EXISTS numero_documento CASCADE;",
                "ALTER TABLE dxv_vehiculo DROP COLUMN IF EXISTS placa CASCADE;",
                "ALTER TABLE dxv_vehiculo DROP COLUMN IF EXISTS propietario CASCADE;",
                "ALTER TABLE dxv_vehiculo DROP COLUMN IF EXISTS tipo_cuenta CASCADE;",
                "ALTER TABLE dxv_vehiculo DROP COLUMN IF EXISTS tipo_documento CASCADE;",
            ],
            reverse_sql=[
                # No reverse - we can't restore dropped columns
            ],
        ),
    ]
