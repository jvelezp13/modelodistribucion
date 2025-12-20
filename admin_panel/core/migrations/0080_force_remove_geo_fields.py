# Force removal of geographic fields from PersonalComercial table

from django.db import migrations


def remove_geo_fields(apps, schema_editor):
    """Remove tipo_asignacion_geo and zona_id fields if they exist"""
    with schema_editor.connection.cursor() as cursor:
        # Check if columns exist and drop them
        cursor.execute("""
            DO $$
            BEGIN
                -- Drop tipo_asignacion_geo if exists
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name='dxv_personal_comercial'
                    AND column_name='tipo_asignacion_geo'
                ) THEN
                    ALTER TABLE dxv_personal_comercial DROP COLUMN tipo_asignacion_geo;
                END IF;

                -- Drop zona_id if exists
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name='dxv_personal_comercial'
                    AND column_name='zona_id'
                ) THEN
                    ALTER TABLE dxv_personal_comercial DROP COLUMN zona_id;
                END IF;
            END $$;
        """)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0079_remove_personal_comercial_geo_fields'),
    ]

    operations = [
        migrations.RunPython(remove_geo_fields, reverse_code=migrations.RunPython.noop),
    ]
