"""
Custom AdminSite para DxV con agrupaciones lógicas
"""
from django.contrib import admin
from django.contrib.admin.apps import AdminConfig
from django.urls import path


class DxVAdminSite(admin.AdminSite):
    site_header = "Sistema DxV - Panel de Administración"
    site_title = "DxV Admin"
    index_title = "Gestión de Distribución y Ventas"

    def get_urls(self):
        """Agregar URLs personalizadas"""
        from .views import distribucion_ventas, guardar_distribucion_ventas

        urls = super().get_urls()
        custom_urls = [
            path('distribucion-ventas/',
                 self.admin_view(distribucion_ventas),
                 name='distribucion_ventas'),
            path('distribucion-ventas/guardar/',
                 self.admin_view(guardar_distribucion_ventas),
                 name='guardar_distribucion_ventas'),
        ]
        return custom_urls + urls

    # Definir el orden de los grupos y modelos
    # Links personalizados (vistas custom)
    CUSTOM_LINKS = {
        'Ventas y Proyecciones': [
            {
                'name': 'Distribución de Ventas',
                'url_name': 'admin:distribucion_ventas',
                'object_name': '_distribucion_ventas',
            },
        ],
    }

    ADMIN_ORDERING = {
        'Configuración Base': [
            'Marca',
            'Escenario',
            'ParametrosMacro',
            'FactorPrestacional',
            'Impuesto',
            'ConfiguracionDescuentos',
            'PoliticaRecursosHumanos',
        ],
        'Ventas y Proyecciones': [
            '_distribucion_ventas',  # Link personalizado
            'ProyeccionVentasConfig',
            'PlantillaEstacional',
        ],
        'Catálogos de Ventas': [
            'CanalVenta',
            'CategoriaProducto',
            'Producto',
            'DefinicionMercado',
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
        from django.urls import reverse

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

        # Agregar links personalizados al diccionario
        for group_name, links in self.CUSTOM_LINKS.items():
            for link in links:
                models_dict[link['object_name']] = {
                    'name': link['name'],
                    'object_name': link['object_name'],
                    'admin_url': reverse(link['url_name']),
                    'add_url': None,
                    'view_only': True,
                }

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
