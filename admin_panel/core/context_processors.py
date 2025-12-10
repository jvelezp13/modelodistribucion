"""
Context processors para el admin de DxV.
Provee escenario y marca global a todos los templates.
"""
from django.db import OperationalError, ProgrammingError


def global_filters(request):
    """
    Agrega escenario y marca seleccionados globalmente a todos los templates.
    Los valores se guardan en sesión.
    """
    try:
        from .models import Escenario, Marca

        # Obtener escenarios y marcas disponibles
        escenarios = Escenario.objects.filter(activo=True).order_by('-anio', 'nombre')
        marcas = Marca.objects.filter(activo=True).order_by('nombre')

        # Obtener selección actual de sesión
        escenario_id = request.session.get('global_escenario_id')
        marca_id = request.session.get('global_marca_id')  # None = "Todas"

        # Si no hay escenario seleccionado, usar el primero activo
        if not escenario_id and escenarios.exists():
            escenario_id = escenarios.first().id
            request.session['global_escenario_id'] = escenario_id

        # Obtener objetos
        escenario_actual = None
        marca_actual = None

        if escenario_id:
            try:
                escenario_actual = Escenario.objects.get(pk=escenario_id)
            except Escenario.DoesNotExist:
                pass

        if marca_id:
            try:
                marca_actual = Marca.objects.get(pk=marca_id)
            except Marca.DoesNotExist:
                pass

        return {
            'global_escenarios': escenarios,
            'global_marcas': marcas,
            'global_escenario_id': escenario_id,
            'global_marca_id': marca_id,
            'global_escenario': escenario_actual,
            'global_marca': marca_actual,
        }

    except (OperationalError, ProgrammingError):
        # Base de datos no disponible aún (durante migraciones, etc.)
        return {
            'global_escenarios': [],
            'global_marcas': [],
            'global_escenario_id': None,
            'global_marca_id': None,
            'global_escenario': None,
            'global_marca': None,
        }
