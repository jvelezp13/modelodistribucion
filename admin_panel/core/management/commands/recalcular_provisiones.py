"""
Comando de Django para recalcular todas las provisiones de RRHH.
Uso: python manage.py recalcular_provisiones
"""
from django.core.management.base import BaseCommand
from core.models import Escenario
from core.signals import calculate_hr_expenses


class Command(BaseCommand):
    help = 'Recalcula las provisiones (Dotación, EPP, Exámenes) para todos los escenarios'

    def add_arguments(self, parser):
        parser.add_argument(
            '--escenario',
            type=int,
            help='ID del escenario específico a recalcular (opcional, por defecto recalcula todos los activos)',
        )

    def handle(self, *args, **options):
        escenario_id = options.get('escenario')

        if escenario_id:
            # Recalcular un escenario específico
            try:
                escenario = Escenario.objects.get(pk=escenario_id)
                self.stdout.write(f'Recalculando provisiones para: {escenario.nombre}')
                calculate_hr_expenses(escenario)
                self.stdout.write(self.style.SUCCESS(f'✅ Provisiones recalculadas para {escenario.nombre}'))
            except Escenario.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Escenario con ID {escenario_id} no encontrado'))
        else:
            # Recalcular todos los escenarios activos
            escenarios = Escenario.objects.filter(activo=True)
            self.stdout.write(f'Recalculando provisiones para {escenarios.count()} escenarios activos...')
            
            for esc in escenarios:
                self.stdout.write(f'  - {esc.nombre}...')
                calculate_hr_expenses(esc)
            
            self.stdout.write(self.style.SUCCESS(f'✅ Provisiones recalculadas para {escenarios.count()} escenarios'))
