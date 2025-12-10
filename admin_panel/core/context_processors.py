"""
Context processors para el admin de DxV.
Provee escenario y marca global a todos los templates.
"""
from django.db import OperationalError, ProgrammingError


def _empty_context():
    """Retorna contexto vacío para cuando hay errores."""
    return {
        'global_escenarios': [],
        'global_marcas': [],
        'global_escenario_id': None,
        'global_marca_id': None,
        'global_escenario': None,
        'global_marca': None,
    }


def global_filters(request):
    """
    Agrega escenario y marca seleccionados globalmente a todos los templates.
    Los valores se guardan en sesión.
    """
    # Verificar que tenemos sesión disponible
    if not hasattr(request, 'session'):
        return _empty_context()

    try:
        from .models import Escenario, Marca

        # Obtener escenarios y marcas disponibles
        escenarios = list(Escenario.objects.filter(activo=True).order_by('-anio', 'nombre'))
        marcas = list(Marca.objects.filter(activo=True).order_by('nombre'))

        # Obtener selección actual de sesión
        escenario_id = request.session.get('global_escenario_id')
        marca_id = request.session.get('global_marca_id')  # None = "Todas"

        # Si no hay escenario seleccionado, usar el primero activo
        if not escenario_id and escenarios:
            escenario_id = escenarios[0].id
            request.session['global_escenario_id'] = escenario_id

        # Obtener objetos
        escenario_actual = None
        marca_actual = None

        if escenario_id:
            try:
                escenario_actual = Escenario.objects.get(pk=escenario_id)
            except Escenario.DoesNotExist:
                escenario_id = None
                if 'global_escenario_id' in request.session:
                    del request.session['global_escenario_id']

        if marca_id:
            try:
                marca_actual = Marca.objects.get(pk=marca_id)
            except Marca.DoesNotExist:
                marca_id = None
                if 'global_marca_id' in request.session:
                    del request.session['global_marca_id']

        return {
            'global_escenarios': escenarios,
            'global_marcas': marcas,
            'global_escenario_id': escenario_id,
            'global_marca_id': marca_id,
            'global_escenario': escenario_actual,
            'global_marca': marca_actual,
        }

    except (OperationalError, ProgrammingError, Exception):
        # Base de datos no disponible o cualquier otro error
        return _empty_context()
