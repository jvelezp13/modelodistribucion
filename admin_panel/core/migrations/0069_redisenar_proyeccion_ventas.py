# Generated manually for rediseño de proyección de ventas

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0068_add_costos_adicionales_km'),
    ]

    operations = [
        # 1. Renombrar campo metodo -> tipo en ProyeccionVentasConfig
        migrations.RenameField(
            model_name='proyeccionventasconfig',
            old_name='metodo',
            new_name='tipo',
        ),

        # 2. Actualizar choices y default del campo tipo
        migrations.AlterField(
            model_name='proyeccionventasconfig',
            name='tipo',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('simple', 'Valores Directos Mensuales'),
                    ('lista_precios', 'Lista de Precios'),
                ],
                default='simple',
                verbose_name='Tipo de Proyección'
            ),
        ),

        # 3. Actualizar help_text de plantilla_estacional
        migrations.AlterField(
            model_name='proyeccionventasconfig',
            name='plantilla_estacional',
            field=models.ForeignKey(
                blank=True,
                help_text='Distribución mensual a aplicar (solo para tipo simple)',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='proyecciones',
                to='core.plantillaestacional',
                verbose_name='Plantilla Estacional'
            ),
        ),

        # 4. Crear modelo ListaPreciosProducto
        migrations.CreateModel(
            name='ListaPreciosProducto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('metodo_captura', models.CharField(
                    choices=[
                        ('directo', 'Precios Directos'),
                        ('descuento_sobre_venta', '% Descuento sobre Precio Venta'),
                        ('margen_sobre_compra', '% Margen sobre Precio Compra'),
                    ],
                    default='directo',
                    max_length=25,
                    verbose_name='Método de Captura'
                )),
                ('precio_compra', models.DecimalField(
                    blank=True,
                    decimal_places=2,
                    help_text='Precio que paga el distribuidor a la marca',
                    max_digits=12,
                    null=True,
                    verbose_name='Precio Compra'
                )),
                ('precio_venta', models.DecimalField(
                    blank=True,
                    decimal_places=2,
                    help_text='Precio de venta sugerido al cliente final',
                    max_digits=12,
                    null=True,
                    verbose_name='Precio Venta'
                )),
                ('porcentaje_descuento', models.DecimalField(
                    blank=True,
                    decimal_places=2,
                    help_text='% que se descuenta del precio de venta para obtener precio compra',
                    max_digits=5,
                    null=True,
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(100)
                    ],
                    verbose_name='% Descuento'
                )),
                ('porcentaje_margen', models.DecimalField(
                    blank=True,
                    decimal_places=2,
                    help_text='% que se agrega al precio de compra para obtener precio venta',
                    max_digits=5,
                    null=True,
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(500)
                    ],
                    verbose_name='% Margen'
                )),
                ('activo', models.BooleanField(default=True, verbose_name='Activo')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_modificacion', models.DateTimeField(auto_now=True)),
                ('config', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='lista_precios',
                    to='core.proyeccionventasconfig',
                    verbose_name='Configuración'
                )),
                ('producto', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='lista_precios_proyecciones',
                    to='core.producto',
                    verbose_name='Producto/SKU'
                )),
            ],
            options={
                'db_table': 'dxv_lista_precios_producto',
                'verbose_name': 'Producto en Lista de Precios',
                'verbose_name_plural': 'Productos en Lista de Precios',
                'unique_together': {('config', 'producto')},
            },
        ),

        # 5. Crear modelo ProyeccionDemandaProducto
        migrations.CreateModel(
            name='ProyeccionDemandaProducto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('metodo_demanda', models.CharField(
                    choices=[
                        ('ticket_visitas', 'Ticket × Visitas × Efectividad'),
                        ('precio_unidades', 'Precio × Unidades Estimadas'),
                    ],
                    default='precio_unidades',
                    max_length=20,
                    verbose_name='Método de Cálculo'
                )),
                ('ticket_promedio', models.DecimalField(
                    blank=True,
                    decimal_places=2,
                    help_text='Valor promedio de compra por visita',
                    max_digits=12,
                    null=True,
                    verbose_name='Ticket Promedio ($)'
                )),
                ('visitas_mensuales', models.IntegerField(
                    blank=True,
                    help_text='Número de visitas comerciales por mes',
                    null=True,
                    verbose_name='Visitas por Mes'
                )),
                ('tasa_efectividad', models.DecimalField(
                    blank=True,
                    decimal_places=2,
                    help_text='Porcentaje de visitas que resultan en venta',
                    max_digits=5,
                    null=True,
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(100)
                    ],
                    verbose_name='Tasa Efectividad (%)'
                )),
                ('unidades_enero', models.IntegerField(default=0, verbose_name='Unid. Enero')),
                ('unidades_febrero', models.IntegerField(default=0, verbose_name='Unid. Febrero')),
                ('unidades_marzo', models.IntegerField(default=0, verbose_name='Unid. Marzo')),
                ('unidades_abril', models.IntegerField(default=0, verbose_name='Unid. Abril')),
                ('unidades_mayo', models.IntegerField(default=0, verbose_name='Unid. Mayo')),
                ('unidades_junio', models.IntegerField(default=0, verbose_name='Unid. Junio')),
                ('unidades_julio', models.IntegerField(default=0, verbose_name='Unid. Julio')),
                ('unidades_agosto', models.IntegerField(default=0, verbose_name='Unid. Agosto')),
                ('unidades_septiembre', models.IntegerField(default=0, verbose_name='Unid. Septiembre')),
                ('unidades_octubre', models.IntegerField(default=0, verbose_name='Unid. Octubre')),
                ('unidades_noviembre', models.IntegerField(default=0, verbose_name='Unid. Noviembre')),
                ('unidades_diciembre', models.IntegerField(default=0, verbose_name='Unid. Diciembre')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_modificacion', models.DateTimeField(auto_now=True)),
                ('lista_precio', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='proyeccion_demanda',
                    to='core.listapreciosproducto',
                    verbose_name='Producto'
                )),
            ],
            options={
                'db_table': 'dxv_proyeccion_demanda_producto',
                'verbose_name': 'Proyección de Demanda',
                'verbose_name_plural': 'Proyecciones de Demanda',
            },
        ),
    ]
