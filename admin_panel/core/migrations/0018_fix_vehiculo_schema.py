# Generated manually to fix vehiculo schema issues
# This migration ensures the Vehiculo table is in sync with the model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_remove_vehiculo_banco_remove_vehiculo_conductor_and_more'),
    ]

    operations = [
        # Drop each column separately with IF EXISTS to avoid errors
        migrations.RunSQL(
            sql="ALTER TABLE dxv_vehiculo DROP COLUMN IF EXISTS banco CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="ALTER TABLE dxv_vehiculo DROP COLUMN IF EXISTS conductor CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="ALTER TABLE dxv_vehiculo DROP COLUMN IF EXISTS numero_cuenta CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="ALTER TABLE dxv_vehiculo DROP COLUMN IF EXISTS numero_documento CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="ALTER TABLE dxv_vehiculo DROP COLUMN IF EXISTS placa CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="ALTER TABLE dxv_vehiculo DROP COLUMN IF EXISTS propietario CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="ALTER TABLE dxv_vehiculo DROP COLUMN IF EXISTS tipo_cuenta CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="ALTER TABLE dxv_vehiculo DROP COLUMN IF EXISTS tipo_documento CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
