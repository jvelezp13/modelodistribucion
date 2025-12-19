"""
Servicios de negocio para el sistema DxV

Incluye:
- EscenarioService: duplicación y proyección de escenarios
"""
from decimal import Decimal
from typing import Dict, List
from django.db import transaction

from .models import (
    Escenario, ParametrosMacro, PersonalComercial, PersonalLogistico,
    PersonalAdministrativo, Vehiculo, GastoComercial, GastoLogistico,
    GastoAdministrativo, Zona, ZonaMunicipio, ZonaMarca, RutaLogistica, RutaMunicipio,
    ProyeccionVentasConfig, ProyeccionManual, TipologiaProyeccion,
    Marca, FactorPrestacional,
    # Modelos intermedios para asignación multi-marca
    PersonalComercialMarca, PersonalLogisticoMarca, PersonalAdministrativoMarca,
    GastoComercialMarca, GastoLogisticoMarca, GastoAdministrativoMarca
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
        # PERSONAL COMERCIAL (con asignaciones de marca)
        # =====================
        for item in PersonalComercial.objects.filter(escenario=source):
            incremento = get_factor(getattr(item, 'indice_incremento', 'salarios'))
            nuevo = copiar_instancia(
                item,
                override={'escenario': target},
                campos_monetarios=get_campos_monetarios(item),
                factor_incremento=incremento,
                sufijo_nombre=""
            )
            # Copiar asignaciones de marca
            for asig in item.asignaciones_marca.all():
                PersonalComercialMarca.objects.create(
                    personal=nuevo,
                    marca=asig.marca,
                    porcentaje=asig.porcentaje
                )

        # =====================
        # PERSONAL LOGÍSTICO (con asignaciones de marca)
        # =====================
        for item in PersonalLogistico.objects.filter(escenario=source):
            incremento = get_factor(getattr(item, 'indice_incremento', 'salarios'))
            nuevo = copiar_instancia(
                item,
                override={'escenario': target},
                campos_monetarios=get_campos_monetarios(item),
                factor_incremento=incremento,
                sufijo_nombre=""
            )
            # Copiar asignaciones de marca
            for asig in item.asignaciones_marca.all():
                PersonalLogisticoMarca.objects.create(
                    personal=nuevo,
                    marca=asig.marca,
                    porcentaje=asig.porcentaje
                )

        # =====================
        # PERSONAL ADMINISTRATIVO (con asignaciones de marca)
        # =====================
        for item in PersonalAdministrativo.objects.filter(escenario=source):
            incremento = get_factor(getattr(item, 'indice_incremento', 'salarios'))
            nuevo = copiar_instancia(
                item,
                override={'escenario': target},
                campos_monetarios=get_campos_monetarios(item),
                factor_incremento=incremento,
                sufijo_nombre=""
            )
            # Copiar asignaciones de marca
            for asig in item.asignaciones_marca.all():
                PersonalAdministrativoMarca.objects.create(
                    personal=nuevo,
                    marca=asig.marca,
                    porcentaje=asig.porcentaje
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
        # GASTOS COMERCIALES (con asignaciones de marca)
        # =====================
        for item in GastoComercial.objects.filter(escenario=source):
            incremento = get_factor(getattr(item, 'indice_incremento', 'ipc'))
            nuevo = copiar_instancia(
                item,
                override={'escenario': target},
                campos_monetarios=get_campos_monetarios(item),
                factor_incremento=incremento,
                sufijo_nombre=""
            )
            # Copiar asignaciones de marca
            for asig in item.asignaciones_marca.all():
                GastoComercialMarca.objects.create(
                    gasto=nuevo,
                    marca=asig.marca,
                    porcentaje=asig.porcentaje
                )

        # =====================
        # GASTOS LOGÍSTICOS (con asignaciones de marca)
        # =====================
        for item in GastoLogistico.objects.filter(escenario=source):
            incremento = get_factor(getattr(item, 'indice_incremento', 'ipc'))
            nuevo = copiar_instancia(
                item,
                override={'escenario': target},
                campos_monetarios=get_campos_monetarios(item),
                factor_incremento=incremento,
                sufijo_nombre=""
            )
            # Copiar asignaciones de marca
            for asig in item.asignaciones_marca.all():
                GastoLogisticoMarca.objects.create(
                    gasto=nuevo,
                    marca=asig.marca,
                    porcentaje=asig.porcentaje
                )

        # =====================
        # GASTOS ADMINISTRATIVOS (con asignaciones de marca)
        # =====================
        for item in GastoAdministrativo.objects.filter(escenario=source):
            incremento = get_factor(getattr(item, 'indice_incremento', 'ipc'))
            nuevo = copiar_instancia(
                item,
                override={'escenario': target},
                campos_monetarios=get_campos_monetarios(item),
                factor_incremento=incremento,
                sufijo_nombre=""
            )
            # Copiar asignaciones de marca
            for asig in item.asignaciones_marca.all():
                GastoAdministrativoMarca.objects.create(
                    gasto=nuevo,
                    marca=asig.marca,
                    porcentaje=asig.porcentaje
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
            # Copiar asignaciones de marca (multi-marca)
            for asig in ZonaMarca.objects.filter(zona=zona):
                ZonaMarca.objects.create(
                    zona=nueva_zona,
                    marca=asig.marca,
                    porcentaje=asig.porcentaje
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

            # Copiar tipologías de cliente
            for tipologia in TipologiaProyeccion.objects.filter(config=config):
                copiar_instancia(
                    tipologia,
                    override={'config': nueva_config},
                    sufijo_nombre=""
                )

            # Copiar proyección manual (ajuste estacional)
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


