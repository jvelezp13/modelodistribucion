"""
Management command para importar matriz de desplazamientos desde Excel
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import Municipio, MatrizDesplazamiento
import pandas as pd
import os


class Command(BaseCommand):
    help = 'Importa matriz de desplazamientos desde archivo Excel'

    def add_arguments(self, parser):
        parser.add_argument(
            'excel_file',
            type=str,
            help='Ruta al archivo Excel con la matriz de desplazamientos'
        )
        parser.add_argument(
            '--sheet',
            type=str,
            default=0,
            help='Nombre o índice de la hoja Excel (default: primera hoja)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular importación sin guardar en BD'
        )

    def handle(self, *args, **options):
        excel_file = options['excel_file']
        sheet = options['sheet']
        dry_run = options['dry_run']

        # Verificar que el archivo existe
        if not os.path.exists(excel_file):
            raise CommandError(f'Archivo no encontrado: {excel_file}')

        self.stdout.write(self.style.SUCCESS(f'\n📁 Leyendo archivo: {excel_file}'))

        try:
            # Leer Excel
            df = pd.read_excel(excel_file, sheet_name=sheet)

            self.stdout.write(f'   Filas encontradas: {len(df)}')
            self.stdout.write(f'   Columnas: {", ".join(df.columns)}\n')

            # Validar columnas requeridas
            columnas_requeridas = ['Origen', 'Destino', 'Distancia (km)', 'Tiempo (Minutos)']
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]

            if columnas_faltantes:
                raise CommandError(
                    f'Columnas faltantes en el Excel: {", ".join(columnas_faltantes)}'
                )

            # Estadísticas iniciales
            municipios_origen = df['Origen'].nunique()
            municipios_destino = df['Destino'].nunique()
            todos_municipios = set(df['Origen'].unique()) | set(df['Destino'].unique())

            self.stdout.write(f'📊 Estadísticas:')
            self.stdout.write(f'   Municipios únicos: {len(todos_municipios)}')
            self.stdout.write(f'   Orígenes únicos: {municipios_origen}')
            self.stdout.write(f'   Destinos únicos: {municipios_destino}')
            self.stdout.write(f'   Total rutas: {len(df)}\n')

            if dry_run:
                self.stdout.write(self.style.WARNING('⚠️  Modo DRY-RUN - No se guardará nada\n'))

            # Importar con transacción
            with transaction.atomic():
                municipios_creados = 0
                municipios_existentes = 0
                rutas_creadas = 0
                rutas_actualizadas = 0
                errores = []

                # 1. Crear/obtener municipios
                self.stdout.write('🏙️  Procesando municipios...')
                municipios_dict = {}

                for nombre_municipio in sorted(todos_municipios):
                    try:
                        # Extraer nombre y departamento
                        if ',' in nombre_municipio:
                            nombre, departamento = nombre_municipio.split(',', 1)
                            nombre = nombre.strip()
                            departamento = departamento.strip()
                        else:
                            nombre = nombre_municipio.strip()
                            departamento = 'Antioquia'  # Default

                        # Buscar o crear municipio
                        municipio, created = Municipio.objects.get_or_create(
                            nombre=nombre,
                            departamento=departamento,
                            defaults={
                                'codigo_dane': f'TEMP_{nombre[:5]}',
                                'activo': True
                            }
                        )

                        municipios_dict[nombre_municipio] = municipio

                        if created:
                            municipios_creados += 1
                            self.stdout.write(f'   ✅ Creado: {municipio}')
                        else:
                            municipios_existentes += 1

                    except Exception as e:
                        error_msg = f'Error creando municipio {nombre_municipio}: {str(e)}'
                        errores.append(error_msg)
                        self.stdout.write(self.style.ERROR(f'   ❌ {error_msg}'))

                self.stdout.write(f'\n   Municipios creados: {municipios_creados}')
                self.stdout.write(f'   Municipios existentes: {municipios_existentes}\n')

                # 2. Crear/actualizar rutas
                self.stdout.write('🛣️  Procesando rutas...')

                for idx, row in df.iterrows():
                    try:
                        origen_nombre = row['Origen']
                        destino_nombre = row['Destino']
                        distancia = float(row['Distancia (km)'])
                        tiempo = int(row['Tiempo (Minutos)'])

                        origen = municipios_dict.get(origen_nombre)
                        destino = municipios_dict.get(destino_nombre)

                        if not origen or not destino:
                            error_msg = f'Municipio no encontrado en fila {idx+1}'
                            errores.append(error_msg)
                            continue

                        # Crear o actualizar ruta
                        ruta, created = MatrizDesplazamiento.objects.update_or_create(
                            origen=origen,
                            destino=destino,
                            defaults={
                                'distancia_km': distancia,
                                'tiempo_minutos': tiempo,
                            }
                        )

                        if created:
                            rutas_creadas += 1
                            if rutas_creadas <= 5:  # Mostrar solo las primeras 5
                                self.stdout.write(f'   ✅ {ruta}')
                        else:
                            rutas_actualizadas += 1

                    except Exception as e:
                        error_msg = f'Error en fila {idx+1}: {str(e)}'
                        errores.append(error_msg)
                        self.stdout.write(self.style.ERROR(f'   ❌ {error_msg}'))

                # Mostrar resumen
                self.stdout.write('\n' + '='*70)
                self.stdout.write(self.style.SUCCESS('📊 RESUMEN DE IMPORTACIÓN'))
                self.stdout.write('='*70)
                self.stdout.write(f'\n🏙️  Municipios:')
                self.stdout.write(f'   Creados: {municipios_creados}')
                self.stdout.write(f'   Existentes: {municipios_existentes}')
                self.stdout.write(f'\n🛣️  Rutas:')
                self.stdout.write(f'   Creadas: {rutas_creadas}')
                self.stdout.write(f'   Actualizadas: {rutas_actualizadas}')

                if errores:
                    self.stdout.write(f'\n❌ Errores: {len(errores)}')
                    self.stdout.write('\nPrimeros 5 errores:')
                    for error in errores[:5]:
                        self.stdout.write(f'   - {error}')

                if dry_run:
                    self.stdout.write(self.style.WARNING('\n⚠️  DRY-RUN: Revertiendo transacción...'))
                    raise CommandError('Dry-run completado (transacción revertida)')
                else:
                    self.stdout.write(self.style.SUCCESS('\n✅ Importación completada exitosamente!'))

        except CommandError:
            raise
        except Exception as e:
            raise CommandError(f'Error durante la importación: {str(e)}')
