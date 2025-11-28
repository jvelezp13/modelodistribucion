"""
Servicios de negocio para el sistema DxV
"""
from django.db import transaction
from .models import (
    Escenario, ParametrosMacro, PersonalComercial, PersonalLogistico,
    PersonalAdministrativo, Vehiculo, GastoComercial, GastoLogistico,
    GastoAdministrativo, Zona, ZonaMunicipio, RutaLogistica, RutaMunicipio,
    ProyeccionVentasConfig, ProyeccionManual, ProyeccionCrecimiento,
    ProyeccionProducto, ProyeccionCanal, ProyeccionPenetracion
)
from .utils import copiar_instancia, get_campos_monetarios


class EscenarioService:
    """Servicio para operaciones con Escenarios"""

    @staticmethod
    def get_incremento_valor(indice_nombre, macros):
        """
        Obtiene el valor decimal del incremento basado en el nombre del índice
        y los parámetros macroeconómicos del año destino.

        Los valores en ParametrosMacro están en formato 0-100 (ej: 9.5 = 9.5%).
        Esta función los convierte a decimal (0.095) para usar en cálculos.
        """
        if not macros:
            return 0

        if indice_nombre == 'fijo':
            return 0

        mapping = {
            'salarios': macros.incremento_salarios,
            'salario_minimo': macros.incremento_salario_minimo,
            'ipc': macros.ipc,
            'ipt': macros.ipt,
            'combustible': macros.incremento_combustible,
            'arriendos': macros.incremento_arriendos,
            'personalizado_1': macros.incremento_personalizado_1,
            'personalizado_2': macros.incremento_personalizado_2,
        }

        valor = mapping.get(indice_nombre, 0)
        # Convertir de porcentaje (0-100) a decimal (0-1)
        return float(valor) / 100.0 if valor else 0

    @classmethod
    def duplicar_escenario(cls, escenario_id, nuevo_nombre=None):
        """
        Crea una copia exacta de un escenario (mismo año, mismos valores).
        Útil para crear variantes de un escenario base.
        """
        source = Escenario.objects.get(pk=escenario_id)

        if not nuevo_nombre:
            nuevo_nombre = f"{source.nombre} (Copia)"

        with transaction.atomic():
            # 1. Crear nuevo escenario
            new_scenario = copiar_instancia(
                source,
                override={
                    'nombre': nuevo_nombre,
                    'activo': False,
                    'notas': f"Duplicado desde: {source.nombre}"
                },
                sufijo_nombre=""
            )

            # 2. Copiar todos los datos relacionados (sin incrementos)
            cls._copiar_datos_escenario(source, new_scenario, factor_incremento=0)

            return new_scenario

    @classmethod
    def proyectar_escenario(cls, escenario_id, nuevo_anio, nuevo_nombre=None):
        """
        Crea un nuevo escenario basado en uno existente, proyectando los valores
        según los índices macroeconómicos del año destino.
        """
        source = Escenario.objects.get(pk=escenario_id)

        if not nuevo_nombre:
            nuevo_nombre = f"{source.nombre} (Proyección {nuevo_anio})"

        # Obtener macros del año destino
        try:
            macros = ParametrosMacro.objects.get(anio=nuevo_anio)
        except ParametrosMacro.DoesNotExist:
            macros = None

        with transaction.atomic():
            # 1. Crear nuevo escenario
            new_scenario = copiar_instancia(
                source,
                override={
                    'nombre': nuevo_nombre,
                    'tipo': 'planeado',
                    'anio': nuevo_anio,
                    'activo': False,
                    'notas': f"Proyectado desde: {source.nombre} ({source.anio})"
                },
                sufijo_nombre=""
            )

            # 2. Copiar y proyectar datos
            cls._copiar_datos_escenario(source, new_scenario, macros=macros, nuevo_anio=nuevo_anio)

            return new_scenario

    @classmethod
    def _copiar_datos_escenario(cls, source, target, macros=None, nuevo_anio=None, factor_incremento=None):
        """
        Copia todos los datos de un escenario a otro usando copiado dinámico.
        Si macros está presente, aplica incrementos según índices.
        Si factor_incremento=0, copia valores exactos.
        """

        def get_factor(indice_nombre):
            if factor_incremento is not None:
                return factor_incremento
            return cls.get_incremento_valor(indice_nombre, macros)

        # =====================
        # PERSONAL COMERCIAL
        # =====================
        for item in PersonalComercial.objects.filter(escenario=source):
            incremento = get_factor(getattr(item, 'indice_incremento', 'salarios'))
            copiar_instancia(
                item,
                override={'escenario': target},
                campos_monetarios=get_campos_monetarios(item),
                factor_incremento=incremento,
                sufijo_nombre=""
            )

        # =====================
        # PERSONAL LOGÍSTICO
        # =====================
        for item in PersonalLogistico.objects.filter(escenario=source):
            incremento = get_factor(getattr(item, 'indice_incremento', 'salarios'))
            copiar_instancia(
                item,
                override={'escenario': target},
                campos_monetarios=get_campos_monetarios(item),
                factor_incremento=incremento,
                sufijo_nombre=""
            )

        # =====================
        # PERSONAL ADMINISTRATIVO
        # =====================
        for item in PersonalAdministrativo.objects.filter(escenario=source):
            incremento = get_factor(getattr(item, 'indice_incremento', 'salarios'))
            copiar_instancia(
                item,
                override={'escenario': target},
                campos_monetarios=get_campos_monetarios(item),
                factor_incremento=incremento,
                sufijo_nombre=""
            )

        # =====================
        # VEHÍCULOS
        # =====================
        vehiculos_map = {}  # Mapeo de vehículo viejo -> nuevo (para rutas)
        for item in Vehiculo.objects.filter(escenario=source):
            nuevo_vehiculo = copiar_instancia(
                item,
                override={'escenario': target},
                sufijo_nombre=""
            )
            vehiculos_map[item.pk] = nuevo_vehiculo

        # =====================
        # GASTOS COMERCIALES
        # =====================
        for item in GastoComercial.objects.filter(escenario=source):
            incremento = get_factor(getattr(item, 'indice_incremento', 'ipc'))
            copiar_instancia(
                item,
                override={'escenario': target},
                campos_monetarios=get_campos_monetarios(item),
                factor_incremento=incremento,
                sufijo_nombre=""
            )

        # =====================
        # GASTOS LOGÍSTICOS
        # =====================
        for item in GastoLogistico.objects.filter(escenario=source):
            incremento = get_factor(getattr(item, 'indice_incremento', 'ipc'))
            copiar_instancia(
                item,
                override={'escenario': target},
                campos_monetarios=get_campos_monetarios(item),
                factor_incremento=incremento,
                sufijo_nombre=""
            )

        # =====================
        # GASTOS ADMINISTRATIVOS
        # =====================
        for item in GastoAdministrativo.objects.filter(escenario=source):
            incremento = get_factor(getattr(item, 'indice_incremento', 'ipc'))
            copiar_instancia(
                item,
                override={'escenario': target},
                campos_monetarios=get_campos_monetarios(item),
                factor_incremento=incremento,
                sufijo_nombre=""
            )

        # =====================
        # ZONAS COMERCIALES
        # =====================
        for zona in Zona.objects.filter(escenario=source):
            nueva_zona = copiar_instancia(
                zona,
                override={'escenario': target},
                sufijo_nombre=""
            )
            # Copiar municipios de la zona
            for zm in ZonaMunicipio.objects.filter(zona=zona):
                copiar_instancia(
                    zm,
                    override={'zona': nueva_zona},
                    sufijo_nombre=""
                )

        # =====================
        # RUTAS LOGÍSTICAS
        # =====================
        incremento_flete = get_factor('ipc')
        for ruta in RutaLogistica.objects.filter(escenario=source):
            nuevo_vehiculo = vehiculos_map.get(ruta.vehiculo_id) if ruta.vehiculo_id else None
            nueva_ruta = copiar_instancia(
                ruta,
                override={
                    'escenario': target,
                    'vehiculo': nuevo_vehiculo
                },
                sufijo_nombre=""
            )
            # Copiar municipios de la ruta
            for rm in RutaMunicipio.objects.filter(ruta=ruta):
                copiar_instancia(
                    rm,
                    override={'ruta': nueva_ruta},
                    campos_monetarios=get_campos_monetarios(rm),
                    factor_incremento=incremento_flete,
                    sufijo_nombre=""
                )

        # =====================
        # PROYECCIÓN DE VENTAS
        # =====================
        anio_destino = nuevo_anio or source.anio
        incremento_ventas = get_factor('ipc')

        for config in ProyeccionVentasConfig.objects.filter(escenario=source):
            nueva_config = copiar_instancia(
                config,
                override={
                    'escenario': target,
                    'anio': anio_destino
                },
                sufijo_nombre=""
            )

            # Copiar datos según el método
            if config.metodo == 'manual':
                try:
                    manual = ProyeccionManual.objects.get(config=config)
                    copiar_instancia(
                        manual,
                        override={'config': nueva_config},
                        campos_monetarios=get_campos_monetarios(manual),
                        factor_incremento=incremento_ventas,
                        sufijo_nombre=""
                    )
                except ProyeccionManual.DoesNotExist:
                    pass

            elif config.metodo == 'crecimiento':
                try:
                    crec = ProyeccionCrecimiento.objects.get(config=config)
                    copiar_instancia(
                        crec,
                        override={'config': nueva_config},
                        campos_monetarios=get_campos_monetarios(crec),
                        factor_incremento=incremento_ventas,
                        sufijo_nombre=""
                    )
                except ProyeccionCrecimiento.DoesNotExist:
                    pass

            elif config.metodo == 'precio_unidades':
                for prod in ProyeccionProducto.objects.filter(config=config):
                    copiar_instancia(
                        prod,
                        override={'config': nueva_config},
                        campos_monetarios=get_campos_monetarios(prod),
                        factor_incremento=incremento_ventas,
                        sufijo_nombre=""
                    )

            elif config.metodo == 'canal':
                for canal in ProyeccionCanal.objects.filter(config=config):
                    copiar_instancia(
                        canal,
                        override={'config': nueva_config},
                        campos_monetarios=get_campos_monetarios(canal),
                        factor_incremento=incremento_ventas,
                        sufijo_nombre=""
                    )

            elif config.metodo == 'penetracion':
                try:
                    pen = ProyeccionPenetracion.objects.get(config=config)
                    copiar_instancia(
                        pen,
                        override={'config': nueva_config},
                        sufijo_nombre=""
                    )
                except ProyeccionPenetracion.DoesNotExist:
                    pass
