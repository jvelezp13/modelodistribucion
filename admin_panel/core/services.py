"""
Servicios de negocio para el sistema DxV

Incluye:
- EscenarioService: duplicación y proyección de escenarios
- PyGService: cálculo de P&G por marca, zona y municipio
"""
from decimal import Decimal
from typing import Dict, List, Optional
from django.db import transaction
from django.db.models import Sum, Q

from .models import (
    Escenario, ParametrosMacro, PersonalComercial, PersonalLogistico,
    PersonalAdministrativo, Vehiculo, GastoComercial, GastoLogistico,
    GastoAdministrativo, Zona, ZonaMunicipio, RutaLogistica, RutaMunicipio,
    ProyeccionVentasConfig, ProyeccionManual, ProyeccionCrecimiento,
    ProyeccionProducto, ProyeccionCanal, ProyeccionPenetracion,
    Marca, FactorPrestacional
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


# =============================================================================
# P&G SERVICE - Cálculo de Estado de Resultados por Marca/Zona/Municipio
# =============================================================================

class PyGService:
    """
    Servicio para calcular el P&G (Estado de Resultados) a diferentes niveles.

    Todos los gastos tienen un campo tipo_asignacion_geo:
    - 'directo': Se asigna 100% a la zona especificada
    - 'proporcional': Se distribuye según participacion_ventas de cada zona
    - 'compartido': Se distribuye equitativamente entre todas las zonas
    """

    def __init__(self, escenario: Escenario):
        self.escenario = escenario
        self._cache_zonas = {}
        self._cache_marcas_count = None

    # =========================================================================
    # P&G POR MARCA (Consolidado)
    # =========================================================================

    def get_pyg_marca(self, marca: Marca) -> Dict:
        """
        Calcula el P&G completo para una marca.

        Returns:
            {
                'comercial': {...},
                'logistico': {...},
                'administrativo': {...},
                'total_mensual': Decimal,
                'total_anual': Decimal
            }
        """
        comercial = self._get_costos_comerciales_marca(marca)
        logistico = self._get_costos_logisticos_marca(marca)
        administrativo = self._get_costos_administrativos_marca(marca)

        total_mensual = comercial['total'] + logistico['total'] + administrativo['total']

        return {
            'comercial': comercial,
            'logistico': logistico,
            'administrativo': administrativo,
            'total_mensual': total_mensual,
            'total_anual': total_mensual * 12
        }

    def _get_costos_comerciales_marca(self, marca: Marca) -> Dict:
        """Obtiene costos comerciales totales de una marca"""
        personal_qs = PersonalComercial.objects.filter(
            escenario=self.escenario,
            marca=marca
        )
        personal_total = sum(p.calcular_costo_mensual() for p in personal_qs)

        gastos_qs = GastoComercial.objects.filter(
            escenario=self.escenario,
            marca=marca
        )
        gastos_total = gastos_qs.aggregate(total=Sum('valor_mensual'))['total'] or Decimal('0')

        return {
            'personal': personal_total,
            'gastos': gastos_total,
            'total': Decimal(str(personal_total)) + gastos_total,
            'detalle_personal': list(personal_qs.values('nombre', 'tipo', 'cantidad', 'salario_base')),
            'detalle_gastos': list(gastos_qs.values('nombre', 'tipo', 'valor_mensual'))
        }

    def _get_costos_logisticos_marca(self, marca: Marca) -> Dict:
        """Obtiene costos logísticos totales de una marca"""
        personal_qs = PersonalLogistico.objects.filter(
            escenario=self.escenario,
            marca=marca
        )
        personal_total = sum(p.calcular_costo_mensual() for p in personal_qs)

        gastos_qs = GastoLogistico.objects.filter(
            escenario=self.escenario,
            marca=marca
        )
        gastos_total = gastos_qs.aggregate(total=Sum('valor_mensual'))['total'] or Decimal('0')

        return {
            'personal': personal_total,
            'gastos': gastos_total,
            'total': Decimal(str(personal_total)) + gastos_total,
            'detalle_personal': list(personal_qs.values('nombre', 'tipo', 'cantidad', 'salario_base')),
            'detalle_gastos': list(gastos_qs.values('nombre', 'tipo', 'valor_mensual'))
        }

    def _get_costos_administrativos_marca(self, marca: Marca) -> Dict:
        """Obtiene costos administrativos de una marca (incluyendo prorrateados)"""
        marcas_count = self._get_marcas_count()

        # Personal individual
        personal_individual = PersonalAdministrativo.objects.filter(
            escenario=self.escenario,
            marca=marca,
            asignacion='individual'
        )
        personal_individual_total = sum(p.calcular_costo_mensual() for p in personal_individual)

        # Personal compartido (prorrateo equitativo)
        personal_compartido = PersonalAdministrativo.objects.filter(
            escenario=self.escenario,
            marca__isnull=True,
            asignacion='compartido'
        )
        personal_compartido_total = sum(
            p.calcular_costo_mensual() / marcas_count for p in personal_compartido
        )

        personal_total = personal_individual_total + personal_compartido_total

        # Gastos individuales
        gastos_individual = GastoAdministrativo.objects.filter(
            escenario=self.escenario,
            marca=marca,
            asignacion='individual'
        )
        gastos_individual_total = gastos_individual.aggregate(
            total=Sum('valor_mensual')
        )['total'] or Decimal('0')

        # Gastos compartidos
        gastos_compartido = GastoAdministrativo.objects.filter(
            escenario=self.escenario,
            marca__isnull=True,
            asignacion='compartido'
        )
        gastos_compartido_sum = gastos_compartido.aggregate(
            total=Sum('valor_mensual')
        )['total'] or Decimal('0')
        gastos_compartido_total = gastos_compartido_sum / marcas_count

        gastos_total = gastos_individual_total + gastos_compartido_total

        return {
            'personal': personal_total,
            'gastos': gastos_total,
            'total': Decimal(str(personal_total)) + gastos_total,
            'detalle_personal': list(personal_individual.values('nombre', 'tipo', 'cantidad', 'salario_base')),
            'detalle_gastos': list(gastos_individual.values('nombre', 'tipo', 'valor_mensual'))
        }

    # =========================================================================
    # P&G POR ZONA COMERCIAL
    # =========================================================================

    def get_pyg_zona(self, zona: Zona) -> Dict:
        """
        Calcula el P&G para una zona comercial específica.

        Distribuye costos según tipo_asignacion_geo:
        - directo: 100% si zona coincide
        - proporcional: según participacion_ventas
        - compartido: equitativo entre zonas

        Returns:
            {
                'zona': {...},
                'comercial': {...},
                'logistico': {...},
                'administrativo': {...},
                'total_mensual': Decimal,
                'total_anual': Decimal
            }
        """
        marca = zona.marca
        participacion = (zona.participacion_ventas or Decimal('0')) / 100
        zonas_marca = self._get_zonas_marca(marca)
        zonas_count = len(zonas_marca) or 1

        comercial = self._distribuir_costos_a_zona(
            zona, participacion, zonas_count,
            PersonalComercial, GastoComercial
        )
        logistico = self._distribuir_costos_a_zona(
            zona, participacion, zonas_count,
            PersonalLogistico, GastoLogistico
        )
        administrativo = self._distribuir_admin_a_zona(zona, zonas_count)

        total_mensual = comercial['total'] + logistico['total'] + administrativo['total']

        return {
            'zona': {
                'id': zona.id,
                'nombre': zona.nombre,
                'participacion_ventas': float(zona.participacion_ventas or 0),
            },
            'comercial': comercial,
            'logistico': logistico,
            'administrativo': administrativo,
            'total_mensual': total_mensual,
            'total_anual': total_mensual * 12
        }

    def _distribuir_costos_a_zona(
        self, zona: Zona, participacion: Decimal, zonas_count: int,
        modelo_personal, modelo_gasto
    ) -> Dict:
        """Distribuye costos de personal y gastos a una zona según tipo_asignacion_geo."""
        marca = zona.marca
        personal_total = Decimal('0')
        gastos_total = Decimal('0')

        # Personal
        personal_qs = modelo_personal.objects.filter(
            escenario=self.escenario,
            marca=marca
        )
        for p in personal_qs:
            costo = Decimal(str(p.calcular_costo_mensual()))
            asignacion_geo = getattr(p, 'tipo_asignacion_geo', 'proporcional')
            zona_asignada = getattr(p, 'zona', None)

            if asignacion_geo == 'directo':
                if zona_asignada and zona_asignada.id == zona.id:
                    personal_total += costo
            elif asignacion_geo == 'proporcional':
                personal_total += costo * participacion
            elif asignacion_geo == 'compartido':
                personal_total += costo / zonas_count

        # Gastos
        gastos_qs = modelo_gasto.objects.filter(
            escenario=self.escenario,
            marca=marca
        )
        for g in gastos_qs:
            asignacion_geo = getattr(g, 'tipo_asignacion_geo', 'proporcional')
            zona_asignada = getattr(g, 'zona', None)

            if asignacion_geo == 'directo':
                if zona_asignada and zona_asignada.id == zona.id:
                    gastos_total += g.valor_mensual
            elif asignacion_geo == 'proporcional':
                gastos_total += g.valor_mensual * participacion
            elif asignacion_geo == 'compartido':
                gastos_total += g.valor_mensual / zonas_count

        return {
            'personal': personal_total,
            'gastos': gastos_total,
            'total': personal_total + gastos_total
        }

    def _distribuir_admin_a_zona(self, zona: Zona, zonas_count: int) -> Dict:
        """Distribuye costos administrativos a una zona (siempre equitativo)."""
        marca = zona.marca
        marcas_count = self._get_marcas_count()

        # Los costos admin se distribuyen: primero por marca, luego por zona
        admin_marca = self._get_costos_administrativos_marca(marca)
        factor_zona = Decimal('1') / zonas_count

        return {
            'personal': admin_marca['personal'] * factor_zona,
            'gastos': admin_marca['gastos'] * factor_zona,
            'total': admin_marca['total'] * factor_zona
        }

    # =========================================================================
    # P&G POR MUNICIPIO
    # =========================================================================

    def get_pyg_municipio(self, zona_municipio: ZonaMunicipio) -> Dict:
        """
        Calcula el P&G para un municipio dentro de una zona.

        El costo del municipio es:
        Costo_Zona × (participacion_ventas_municipio / 100)

        Returns:
            {
                'municipio': {...},
                'zona': {...},
                'comercial': {...},
                'logistico': {...},
                'administrativo': {...},
                'total_mensual': Decimal,
                'total_anual': Decimal
            }
        """
        zona = zona_municipio.zona
        participacion_mun = (zona_municipio.participacion_ventas or Decimal('0')) / 100

        # Obtener P&G de la zona
        pyg_zona = self.get_pyg_zona(zona)

        # Multiplicar por participación del municipio
        comercial = {
            'personal': pyg_zona['comercial']['personal'] * participacion_mun,
            'gastos': pyg_zona['comercial']['gastos'] * participacion_mun,
            'total': pyg_zona['comercial']['total'] * participacion_mun
        }
        logistico = {
            'personal': pyg_zona['logistico']['personal'] * participacion_mun,
            'gastos': pyg_zona['logistico']['gastos'] * participacion_mun,
            'total': pyg_zona['logistico']['total'] * participacion_mun
        }
        administrativo = {
            'personal': pyg_zona['administrativo']['personal'] * participacion_mun,
            'gastos': pyg_zona['administrativo']['gastos'] * participacion_mun,
            'total': pyg_zona['administrativo']['total'] * participacion_mun
        }

        total_mensual = comercial['total'] + logistico['total'] + administrativo['total']

        # Calcular participación total (zona × municipio)
        part_total = (zona.participacion_ventas or Decimal('0')) * (zona_municipio.participacion_ventas or Decimal('0')) / 100

        return {
            'municipio': {
                'id': zona_municipio.municipio.id,
                'nombre': zona_municipio.municipio.nombre,
                'participacion_ventas': float(zona_municipio.participacion_ventas or 0),
                'participacion_total': float(part_total),
            },
            'zona': {
                'id': zona.id,
                'nombre': zona.nombre,
            },
            'comercial': comercial,
            'logistico': logistico,
            'administrativo': administrativo,
            'total_mensual': total_mensual,
            'total_anual': total_mensual * 12
        }

    # =========================================================================
    # RESÚMENES Y REPORTES
    # =========================================================================

    def get_pyg_todas_zonas(self, marca: Marca) -> List[Dict]:
        """Calcula P&G para todas las zonas de una marca."""
        zonas = Zona.objects.filter(
            escenario=self.escenario,
            marca=marca,
            activo=True
        ).order_by('nombre')

        return [self.get_pyg_zona(zona) for zona in zonas]

    def get_pyg_todos_municipios(self, zona: Zona) -> List[Dict]:
        """Calcula P&G para todos los municipios de una zona."""
        municipios = ZonaMunicipio.objects.filter(
            zona=zona
        ).select_related('municipio').order_by('municipio__nombre')

        return [self.get_pyg_municipio(zm) for zm in municipios]

    def get_resumen_marca(self, marca: Marca) -> Dict:
        """
        Resumen completo de P&G para una marca con desglose por zona.

        Returns:
            {
                'marca': {...},
                'total': {...},
                'zonas': [...]
            }
        """
        pyg_total = self.get_pyg_marca(marca)
        pyg_zonas = self.get_pyg_todas_zonas(marca)

        return {
            'marca': {
                'id': marca.id,
                'nombre': marca.nombre,
            },
            'total': pyg_total,
            'zonas': pyg_zonas
        }

    # =========================================================================
    # HELPERS CON CACHE
    # =========================================================================

    def _get_zonas_marca(self, marca: Marca) -> List[Zona]:
        """Obtiene las zonas activas de una marca (con cache)."""
        if marca.id not in self._cache_zonas:
            self._cache_zonas[marca.id] = list(
                Zona.objects.filter(
                    escenario=self.escenario,
                    marca=marca,
                    activo=True
                )
            )
        return self._cache_zonas[marca.id]

    def _get_marcas_count(self) -> int:
        """Obtiene el conteo de marcas activas (con cache)."""
        if self._cache_marcas_count is None:
            self._cache_marcas_count = Marca.objects.filter(activo=True).count() or 1
        return self._cache_marcas_count


# =============================================================================
# FUNCIONES DE CONVENIENCIA
# =============================================================================

def calcular_pyg_marca(escenario: Escenario, marca: Marca) -> Dict:
    """Calcula P&G para una marca."""
    service = PyGService(escenario)
    return service.get_pyg_marca(marca)


def calcular_pyg_zona(escenario: Escenario, zona: Zona) -> Dict:
    """Calcula P&G para una zona."""
    service = PyGService(escenario)
    return service.get_pyg_zona(zona)


def calcular_pyg_municipio(escenario: Escenario, zona_municipio: ZonaMunicipio) -> Dict:
    """Calcula P&G para un municipio."""
    service = PyGService(escenario)
    return service.get_pyg_municipio(zona_municipio)


def calcular_resumen_completo(escenario: Escenario, marca: Marca) -> Dict:
    """Calcula resumen completo de P&G con desglose por zona."""
    service = PyGService(escenario)
    return service.get_resumen_marca(marca)
