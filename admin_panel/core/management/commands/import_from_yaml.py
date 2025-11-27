"""
Management command para importar datos desde archivos YAML a PostgreSQL
"""
import sys
import yaml
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import (
    Marca, PersonalComercial, PersonalLogistico,
    Vehiculo, ProyeccionVentas,
    ParametrosMacro, FactorPrestacional
)


class Command(BaseCommand):
    help = 'Importa datos desde archivos YAML a PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-path',
            type=str,
            default='../data',
            help='Ruta a la carpeta data con los archivos YAML'
        )
        parser.add_argument(
            '--config-path',
            type=str,
            default='../config',
            help='Ruta a la carpeta config con los archivos YAML'
        )

    def handle(self, *args, **options):
        data_path = Path(options['data_path'])
        config_path = Path(options['config_path'])

        self.stdout.write(self.style.SUCCESS('=== Iniciando Importación desde YAML ===\n'))

        try:
            with transaction.atomic():
                # 1. Importar parámetros macro
                self.import_parametros_macro(config_path)

                # 2. Importar factores prestacionales
                self.import_factores_prestacionales(config_path)

                # 3. Importar marcas
                self.import_marcas(config_path)

                # 4. Importar datos de cada marca
                self.import_datos_marcas(data_path)

            self.stdout.write(self.style.SUCCESS('\n✅ Importación completada exitosamente'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error durante la importación: {str(e)}'))
            import traceback
            traceback.print_exc()

    def import_parametros_macro(self, config_path):
        """Importa parámetros macroeconómicos"""
        self.stdout.write('[1/6] Importando parámetros macroeconómicos...')

        filepath = config_path / 'parametros_macro.yaml'
        if not filepath.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠️  Archivo no encontrado: {filepath}'))
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        params = data.get('parametros', {})
        anio = params.get('anio', 2025)

        obj, created = ParametrosMacro.objects.update_or_create(
            anio=anio,
            defaults={
                'ipc': params.get('ipc', 0.052),
                'ipt': params.get('ipt', 0.065),
                'salario_minimo_legal': params.get('salario_minimo_legal_2025', 1423900),
                'subsidio_transporte': params.get('subsidio_transporte_2025', 200000),
                'incremento_salarios': params.get('incremento_salarios', 0.052),
                'activo': True
            }
        )

        action = 'creado' if created else 'actualizado'
        self.stdout.write(self.style.SUCCESS(f'  ✓ Parámetros {anio} {action}'))

    def import_factores_prestacionales(self, config_path):
        """Importa factores prestacionales"""
        self.stdout.write('[2/6] Importando factores prestacionales...')

        filepath = config_path / 'factores_prestacionales.yaml'
        if not filepath.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠️  Archivo no encontrado: {filepath}'))
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        perfiles_map = {
            'comercial': 'comercial',
            'administrativo': 'administrativo',
            'logistico': 'logistico',
            'aprendiz_sena': 'aprendiz_sena'
        }

        for perfil_key, perfil_value in perfiles_map.items():
            if perfil_key not in data:
                continue

            perfil_data = data[perfil_key]

            obj, created = FactorPrestacional.objects.update_or_create(
                perfil=perfil_value,
                defaults={
                    'salud': perfil_data.get('salud', 0),
                    'pension': perfil_data.get('pension', 0),
                    'arl': perfil_data.get('arl', 0),
                    'caja_compensacion': perfil_data.get('caja_compensacion', 0),
                    'icbf': perfil_data.get('icbf', 0),
                    'sena': perfil_data.get('sena', 0),
                    'cesantias': perfil_data.get('cesantias', 0),
                    'intereses_cesantias': perfil_data.get('intereses_cesantias', 0),
                    'prima': perfil_data.get('prima', 0),
                    'vacaciones': perfil_data.get('vacaciones', 0),
                    'factor_total': perfil_data.get('factor_total', 0),
                }
            )

            action = 'creado' if created else 'actualizado'
            self.stdout.write(self.style.SUCCESS(f'  ✓ Factor {perfil_value} {action}'))

    def import_marcas(self, config_path):
        """Importa la configuración de marcas"""
        self.stdout.write('[3/6] Importando marcas...')

        filepath = config_path / 'marcas.yaml'
        if not filepath.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠️  Archivo no encontrado: {filepath}'))
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        marcas_list = data.get('marcas', [])

        for marca_data in marcas_list:
            marca, created = Marca.objects.update_or_create(
                marca_id=marca_data['id'],
                defaults={
                    'nombre': marca_data['nombre'],
                    'descripcion': marca_data.get('descripcion', ''),
                    'activa': marca_data.get('activa', True),
                    'color': marca_data.get('color', '#1f77b4'),
                }
            )

            action = 'creada' if created else 'actualizada'
            self.stdout.write(self.style.SUCCESS(f'  ✓ Marca {marca.nombre} {action}'))

    def import_datos_marcas(self, data_path):
        """Importa datos de personal, vehículos y ventas de cada marca"""
        self.stdout.write('[4/6] Importando datos de marcas...')

        marcas_dir = data_path / 'marcas'
        if not marcas_dir.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠️  Carpeta no encontrada: {marcas_dir}'))
            return

        for marca_dir in marcas_dir.iterdir():
            if not marca_dir.is_dir():
                continue

            marca_id = marca_dir.name

            try:
                marca = Marca.objects.get(marca_id=marca_id)
            except Marca.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  ⚠️  Marca no encontrada: {marca_id}'))
                continue

            self.stdout.write(f'\n  Procesando marca: {marca.nombre}')

            # Importar personal comercial
            self.import_personal_comercial(marca, marca_dir)

            # Importar personal logístico y vehículos
            self.import_logistica(marca, marca_dir)

            # Importar proyecciones de ventas
            self.import_ventas(marca, marca_dir)

    def import_personal_comercial(self, marca, marca_dir):
        """Importa personal comercial de una marca"""
        filepath = marca_dir / 'comercial.yaml'
        if not filepath.exists():
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        recursos = data.get('recursos_comerciales', {})

        # Limpiar personal comercial existente
        PersonalComercial.objects.filter(marca=marca).delete()

        count = 0
        for tipo_personal, empleados_list in recursos.items():
            if not isinstance(empleados_list, list):
                empleados_list = [empleados_list]

            for empleado_data in empleados_list:
                tipo = empleado_data.get('tipo', tipo_personal)
                cantidad = empleado_data.get('cantidad', 0)
                salario_base = empleado_data.get('salario_base', 0)

                if cantidad == 0 or salario_base == 0:
                    continue

                PersonalComercial.objects.create(
                    marca=marca,
                    tipo=tipo,
                    cantidad=cantidad,
                    salario_base=salario_base,
                    perfil_prestacional=empleado_data.get('perfil_prestacional', 'comercial'),
                    asignacion=empleado_data.get('asignacion', 'individual'),
                    auxilio_adicional=empleado_data.get('auxilio_adicional', 0),
                    porcentaje_dedicacion=empleado_data.get('porcentaje_dedicacion'),
                    criterio_prorrateo=empleado_data.get('criterio_prorrateo'),
                )
                count += 1

        self.stdout.write(f'    ✓ {count} registros de personal comercial importados')

    def import_logistica(self, marca, marca_dir):
        """Importa datos logísticos de una marca"""
        filepath = marca_dir / 'logistica.yaml'
        if not filepath.exists():
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Limpiar datos existentes
        PersonalLogistico.objects.filter(marca=marca).delete()
        Vehiculo.objects.filter(marca=marca).delete()

        # Importar vehículos
        vehiculos_config = data.get('vehiculos', {})
        count_vehiculos = 0

        for esquema in ['renting', 'tradicional']:
            for vehiculo_data in vehiculos_config.get(esquema, []):
                tipo_vehiculo = vehiculo_data.get('tipo')
                cantidad = vehiculo_data.get('cantidad', 0)

                if cantidad == 0:
                    continue

                Vehiculo.objects.create(
                    marca=marca,
                    tipo_vehiculo=tipo_vehiculo,
                    esquema=esquema,
                    cantidad=cantidad,
                    asignacion=vehiculo_data.get('asignacion', 'individual'),
                    kilometraje_promedio_mensual=vehiculo_data.get('kilometraje_promedio_mensual', 3000),
                    porcentaje_uso=vehiculo_data.get('porcentaje_uso'),
                    criterio_prorrateo=vehiculo_data.get('criterio_prorrateo'),
                )
                count_vehiculos += 1

        self.stdout.write(f'    ✓ {count_vehiculos} vehículos importados')

        # Importar personal logístico
        personal_config = data.get('personal', {})
        count_personal = 0

        for tipo_personal, empleados_list in personal_config.items():
            if not isinstance(empleados_list, list):
                empleados_list = [empleados_list]

            for empleado_data in empleados_list:
                cantidad = empleado_data.get('cantidad', 0)
                salario_base = empleado_data.get('salario_base', 0)

                if cantidad == 0 or salario_base == 0:
                    continue

                # Mapear tipo_personal a las opciones del modelo
                tipo_map = {
                    'conductores': 'conductor',
                    'auxiliares_entrega': 'auxiliar_entrega',
                    'coordinador_logistica': 'coordinador_logistica',
                    'supervisor_bodega': 'supervisor_bodega',
                    'operarios_bodega': 'operario_bodega',
                }

                tipo = tipo_map.get(tipo_personal, tipo_personal)

                PersonalLogistico.objects.create(
                    marca=marca,
                    tipo=tipo,
                    cantidad=cantidad,
                    salario_base=salario_base,
                    perfil_prestacional=empleado_data.get('perfil_prestacional', 'logistico'),
                    asignacion=empleado_data.get('asignacion', 'individual'),
                    porcentaje_dedicacion=empleado_data.get('porcentaje_dedicacion'),
                    criterio_prorrateo=empleado_data.get('criterio_prorrateo'),
                )
                count_personal += 1

        self.stdout.write(f'    ✓ {count_personal} registros de personal logístico importados')

    def import_ventas(self, marca, marca_dir):
        """Importa proyecciones de ventas de una marca"""
        filepath = marca_dir / 'ventas.yaml'
        if not filepath.exists():
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        ventas_mensuales = data.get('ventas_mensuales', {})
        if not ventas_mensuales:
            return

        # Limpiar proyecciones existentes
        ProyeccionVentas.objects.filter(marca=marca).delete()

        count = 0
        anio = 2025  # Puedes hacerlo configurable

        for mes, ventas in ventas_mensuales.items():
            ProyeccionVentas.objects.create(
                marca=marca,
                anio=anio,
                mes=mes,
                ventas=ventas
            )
            count += 1

        self.stdout.write(f'    ✓ {count} proyecciones de ventas importadas')
