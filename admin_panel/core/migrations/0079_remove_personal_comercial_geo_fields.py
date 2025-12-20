# Generated manually to remove geographic assignment fields from PersonalComercial

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0078_make_personal_comercial_marca_nullable'),
    ]

    operations = [
        # Primero hacemos los campos nullable para evitar errores
        migrations.RunSQL(
            sql="""
                ALTER TABLE dxv_personal_comercial
                ALTER COLUMN tipo_asignacion_geo DROP NOT NULL;
            """,
            reverse_sql="""
                ALTER TABLE dxv_personal_comercial
                ALTER COLUMN tipo_asignacion_geo SET NOT NULL;
            """
        ),
        migrations.RunSQL(
            sql="""
                ALTER TABLE dxv_personal_comercial
                ALTER COLUMN zona_id DROP NOT NULL;
            """,
            reverse_sql="""
                ALTER TABLE dxv_personal_comercial
                ALTER COLUMN zona_id SET NOT NULL;
            """
        ),
        # Ahora eliminamos los campos
        migrations.RunSQL(
            sql="""
                ALTER TABLE dxv_personal_comercial
                DROP COLUMN IF EXISTS tipo_asignacion_geo;
            """,
            reverse_sql=migrations.RunSQL.noop
        ),
        migrations.RunSQL(
            sql="""
                ALTER TABLE dxv_personal_comercial
                DROP COLUMN IF EXISTS zona_id;
            """,
            reverse_sql=migrations.RunSQL.noop
        ),
    ]
