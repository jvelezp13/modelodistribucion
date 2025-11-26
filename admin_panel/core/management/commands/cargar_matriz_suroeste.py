"""
Management command SIMPLE para cargar matriz del Suroeste Antioqueño
NO necesita archivo Excel - los datos ya están incluidos
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Municipio, MatrizDesplazamiento
from .datos_matriz_suroeste import MUNICIPIOS, RUTAS


class Command(BaseCommand):
    help = 'Carga matriz de desplazamientos del Suroeste Antioqueño (550 rutas, 24 municipios)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🚀 CARGANDO MATRIZ DEL SUROESTE ANTIOQUEÑO'))
        self.stdout.write('='*70 + '\n')

        with transaction.atomic():
            municipios_creados = 0
            municipios_existentes = 0
            rutas_creadas = 0
            rutas_actualizadas = 0

            # 1. Crear municipios
            self.stdout.write('🏙️  Creando municipios...')
            municipios_dict = {}

            for mun_data in MUNICIPIOS:
                municipio, created = Municipio.objects.get_or_create(
                    nombre=mun_data['nombre'],
                    departamento=mun_data['departamento'],
                    defaults={
                        'codigo_dane': f"MUN_{mun_data['nombre'][:5].upper()}",
                        'activo': True
                    }
                )
                municipios_dict[mun_data['nombre']] = municipio

                if created:
                    municipios_creados += 1
                    if municipios_creados <= 5:
                        self.stdout.write(f"   ✅ {municipio}")
                else:
                    municipios_existentes += 1

            self.stdout.write(f'\n   Total creados: {municipios_creados}')
            self.stdout.write(f'   Total existentes: {municipios_existentes}\n')

            # 2. Crear rutas
            self.stdout.write('🛣️  Creando rutas...')
            for idx, ruta_data in enumerate(RUTAS, 1):
                origen = municipios_dict[ruta_data['origen']]
                destino = municipios_dict[ruta_data['destino']]

                ruta, created = MatrizDesplazamiento.objects.update_or_create(
                    origen=origen,
                    destino=destino,
                    defaults={
                        'distancia_km': ruta_data['distancia_km'],
                        'tiempo_minutos': ruta_data['tiempo_minutos'],
                    }
                )

                if created:
                    rutas_creadas += 1
                    if rutas_creadas <= 5:
                        self.stdout.write(f"   ✅ {ruta}")
                else:
                    rutas_actualizadas += 1

                # Mostrar progreso cada 100 rutas
                if idx % 100 == 0:
                    self.stdout.write(f"   ... {idx}/{len(RUTAS)} rutas procesadas")

            # Resumen
            self.stdout.write('\n' + '='*70)
            self.stdout.write(self.style.SUCCESS('📊 RESUMEN'))
            self.stdout.write('='*70)
            self.stdout.write(f'\n🏙️  Municipios:')
            self.stdout.write(f'   ✅ Creados: {municipios_creados}')
            self.stdout.write(f'   ℹ️  Existentes: {municipios_existentes}')
            self.stdout.write(f'\n🛣️  Rutas:')
            self.stdout.write(f'   ✅ Creadas: {rutas_creadas}')
            self.stdout.write(f'   ℹ️  Actualizadas: {rutas_actualizadas}')
            self.stdout.write(self.style.SUCCESS('\n✅ ¡IMPORTACIÓN COMPLETADA EXITOSAMENTE!\n'))
