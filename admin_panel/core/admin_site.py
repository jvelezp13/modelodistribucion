"""
Custom AdminSite para DxV con agrupaciones lógicas
"""
from django.contrib import admin
from django.contrib.admin.apps import AdminConfig


class DxVAdminSite(admin.AdminSite):
    site_header = "Sistema DxV - Panel de Administración"
    site_title = "DxV Admin"
    index_title = "Gestión de Distribución y Ventas"

    # Definir el orden de los grupos y modelos
    ADMIN_ORDERING = {
        'Configuración Base': [
            'Marca',
            'Escenario',
            'ParametrosMacro',
            'FactorPrestacional',
            'Impuesto',
            'ConfiguracionDescuentos',
            'TramoDescuentoFactura',
            'PoliticaRecursosHumanos',
        ],
        'Ventas y Proyecciones': [
            'ProyeccionVentas',
            'VolumenOperacion',
        ],
        'Comercial': [
            'PersonalComercial',
            'Zona',
            'GastoComercial',
        ],
        'Logística': [
            'PersonalLogistico',
            'Vehiculo',
            'RutaLogistica',
            'ConfiguracionLejania',
            'GastoLogistico',
        ],
        'Administrativo': [
            'PersonalAdministrativo',
            'GastoAdministrativo',
        ],
        'Datos Geográficos': [
            'Municipio',
            'MatrizDesplazamiento',
        ],
    }

    def get_app_list(self, request, app_label=None):
        """
        Reorganiza los modelos en grupos lógicos personalizados
        """
        # Obtener la lista original
        original_app_list = super().get_app_list(request, app_label)

        # Si se solicita un app específico, devolver el original
        if app_label:
            return original_app_list

        # Crear diccionario de modelos por nombre
        models_dict = {}
        for app in original_app_list:
            for model in app['models']:
                model_name = model['object_name']
                models_dict[model_name] = model
                # Quitar el link de "add" para que no aparezca el +
                model['add_url'] = None

        # Construir nueva lista de apps con grupos personalizados
        new_app_list = []

        for group_name, model_names in self.ADMIN_ORDERING.items():
            models = []
            for model_name in model_names:
                if model_name in models_dict:
                    models.append(models_dict[model_name])

            if models:  # Solo agregar el grupo si tiene modelos
                new_app_list.append({
                    'name': group_name,
                    'app_label': group_name.lower().replace(' ', '_'),
                    'app_url': '#',  # No hay URL de app
                    'has_module_perms': True,
                    'models': models,
                })

        return new_app_list


# Instancia del admin personalizado
dxv_admin_site = DxVAdminSite(name='dxv_admin')
