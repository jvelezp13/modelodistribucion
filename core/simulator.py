"""
Motor de Simulación Principal.

Este es el componente central que orquesta todo el sistema:
1. Carga configuraciones y datos de marcas
2. Crea instancias de Marca con sus recursos
3. Calcula costos individuales por marca
4. Distribuye gastos compartidos con el Allocator
5. Genera resultados consolidados y por marca
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

from models.marca import Marca
from models.rubro import Rubro, TipoAsignacion, CriterioProrrateo, RubroPersonal, RubroVehiculo
from core.allocator import Allocator
from core.calculator_nomina import CalculadoraNomina
from core.calculator_vehiculos import CalculadoraVehiculos
from utils.loaders import DataLoader

logger = logging.getLogger(__name__)


@dataclass
class ResultadoSimulacion:
    """Resultado de una simulación completa."""
    marcas: List[Marca]
    consolidado: Dict[str, Any]
    rubros_compartidos: List[Rubro]
    asignaciones_prorrateo: Dict[str, List[Dict[str, Any]]]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'marcas': [m.to_dict() for m in self.marcas],
            'consolidado': self.consolidado,
            'rubros_compartidos': [r.to_dict() for r in self.rubros_compartidos],
            'asignaciones_prorrateo': self.asignaciones_prorrateo,
            'metadata': self.metadata
        }


class Simulator:
    """
    Motor principal de simulación.

    Orquesta todo el sistema para generar simulaciones completas
    de costos y márgenes para distribuidores multimarcas.
    """

    def __init__(self, loader: Optional[DataLoader] = None):
        """
        Inicializa el simulator.

        Args:
            loader: DataLoader para cargar datos
        """
        self.loader = loader or DataLoader()
        self.calc_nomina = CalculadoraNomina(self.loader)
        self.calc_vehiculos = CalculadoraVehiculos(self.loader)

        # Configuraciones
        self._config_empresa = None
        self._config_marcas = None
        self._parametros_macro = None

        # Estado de la simulación
        self.marcas: List[Marca] = []
        self.rubros_compartidos: List[Rubro] = []

        logger.info("Simulator inicializado")

    def _cargar_configuraciones(self):
        """Carga todas las configuraciones necesarias."""
        self._config_empresa = self.loader.cargar_config_empresa()
        self._config_marcas = self.loader.cargar_config_marcas()
        self._parametros_macro = self.loader.cargar_parametros_macro()
        logger.info("Configuraciones cargadas")

    def _crear_marca_desde_datos(self, datos_marca: Dict[str, Any]) -> Marca:
        """
        Crea una instancia de Marca desde los datos cargados.

        Args:
            datos_marca: Datos completos de la marca (comercial + logística + ventas)

        Returns:
            Instancia de Marca
        """
        marca_id = datos_marca['marca_id']

        # Datos comerciales
        comercial = datos_marca.get('comercial', {})
        nombre = comercial.get('nombre', marca_id)
        ventas_mensuales = comercial.get('proyeccion_ventas_mensual', 0)

        # Datos logísticos
        logistica = datos_marca.get('logistica', {})
        volumen_m3 = logistica.get('proyeccion_volumen', {}).get('metros_cubicos_mensuales', 0)
        volumen_ton = logistica.get('proyeccion_volumen', {}).get('toneladas_mensuales', 0)
        pallets = logistica.get('proyeccion_volumen', {}).get('pallets_mensuales', 0)

        # Datos de ventas
        ventas = datos_marca.get('ventas', {})
        ventas_anuales = ventas.get('resumen_anual', {}).get('total_ventas_anuales', ventas_mensuales * 12)

        # Crear marca
        marca = Marca(
            marca_id=marca_id,
            nombre=nombre,
            ventas_mensuales=ventas_mensuales,
            ventas_anuales=ventas_anuales,
            volumen_m3_mensual=volumen_m3,
            volumen_ton_mensual=volumen_ton,
            pallets_mensuales=pallets
        )

        logger.info(f"Marca creada: {marca.nombre} (ventas: ${ventas_mensuales:,.0f})")

        return marca

    def _procesar_rubros_comerciales(
        self,
        marca: Marca,
        datos_comercial: Dict[str, Any]
    ):
        """
        Procesa y agrega rubros comerciales a una marca.

        Args:
            marca: Marca a la que agregar rubros
            datos_comercial: Datos comerciales de la marca
        """
        recursos = datos_comercial.get('recursos_comerciales', {})

        # Procesar TODOS los tipos de personal comercial
        # (vendedores, supervisores, auxiliares, coordinadores, etc.)
        for tipo_personal, empleados_list in recursos.items():
            # Puede ser una lista de grupos de empleados
            if not isinstance(empleados_list, list):
                empleados_list = [empleados_list]

            for empleado_data in empleados_list:
                # Para vendedores, el tipo está dentro del diccionario
                tipo = empleado_data.get('tipo', tipo_personal)
                cantidad = empleado_data.get('cantidad', 0)
                salario_base = empleado_data.get('salario_base', 0)
                perfil = empleado_data.get('perfil_prestacional', 'comercial')
                asignacion_str = empleado_data.get('asignacion', 'individual')

                if cantidad == 0 or salario_base == 0:
                    continue

                # Calcular costo con la calculadora
                costo = self.calc_nomina.calcular_costo_empleado(
                    salario_base=salario_base,
                    perfil=perfil
                )

                # Crear rubro
                rubro = RubroPersonal(
                    id=f"{tipo}_{marca.marca_id}",
                    nombre=f"{tipo.replace('_', ' ').title()}",
                    categoria='comercial',
                    tipo='personal',
                    tipo_asignacion=TipoAsignacion(asignacion_str),
                    marca_id=marca.marca_id if asignacion_str == 'individual' else None,
                    cantidad=cantidad,
                    salario_base=salario_base,
                    prestaciones=costo.prestaciones,
                    subsidio_transporte=costo.subsidio_transporte,
                    factor_prestacional=0.402 if perfil == 'comercial' else 0.378
                )

                if rubro.es_individual():
                    marca.agregar_rubro_individual(rubro)
                    marca.empleados_comerciales += cantidad
                else:
                    # Los compartidos se procesan después
                    criterio_str = empleado_data.get('criterio_prorrateo', 'ventas')
                    rubro.criterio_prorrateo = CriterioProrrateo(criterio_str)
                    rubro.porcentaje_dedicacion = empleado_data.get('porcentaje_dedicacion')
                    self.rubros_compartidos.append(rubro)

        logger.debug(f"Rubros comerciales procesados para {marca.nombre}")

    def _procesar_rubros_logisticos(
        self,
        marca: Marca,
        datos_logistica: Dict[str, Any]
    ):
        """
        Procesa y agrega rubros logísticos a una marca.

        Args:
            marca: Marca a la que agregar rubros
            datos_logistica: Datos logísticos de la marca
        """
        # Procesar vehículos
        vehiculos_config = datos_logistica.get('vehiculos', {})

        # Renting
        for vehiculo_data in vehiculos_config.get('renting', []):
            tipo_vehiculo = vehiculo_data.get('tipo')
            cantidad = vehiculo_data.get('cantidad', 0)
            asignacion_str = vehiculo_data.get('asignacion', 'individual')

            if cantidad == 0:
                continue

            # Calcular costo
            costo = self.calc_vehiculos.calcular_costo_renting(
                tipo_vehiculo=tipo_vehiculo,
                cantidad=cantidad
            )

            # Crear rubro
            rubro = RubroVehiculo(
                id=f"vehiculo_{tipo_vehiculo}_renting_{marca.marca_id}",
                nombre=f"Vehículo {tipo_vehiculo.upper()} (Renting)",
                categoria='logistica',
                tipo='vehiculo',
                tipo_asignacion=TipoAsignacion(asignacion_str),
                marca_id=marca.marca_id if asignacion_str == 'individual' else None,
                cantidad=cantidad,
                tipo_vehiculo=tipo_vehiculo,
                esquema='renting',
                valor_unitario=costo.costo_unitario_mensual
            )

            if rubro.es_individual():
                marca.agregar_rubro_individual(rubro)
            else:
                criterio_str = vehiculo_data.get('criterio_prorrateo', 'volumen')
                rubro.criterio_prorrateo = CriterioProrrateo(criterio_str)
                rubro.porcentaje_dedicacion = vehiculo_data.get('porcentaje_uso')
                self.rubros_compartidos.append(rubro)

        # Tradicional (similar)
        for vehiculo_data in vehiculos_config.get('tradicional', []):
            tipo_vehiculo = vehiculo_data.get('tipo')
            cantidad = vehiculo_data.get('cantidad', 0)
            asignacion_str = vehiculo_data.get('asignacion', 'individual')

            if cantidad == 0:
                continue

            costo = self.calc_vehiculos.calcular_costo_tradicional(
                tipo_vehiculo=tipo_vehiculo,
                cantidad=cantidad
            )

            rubro = RubroVehiculo(
                id=f"vehiculo_{tipo_vehiculo}_tradicional_{marca.marca_id}",
                nombre=f"Vehículo {tipo_vehiculo.upper()} (Propio)",
                categoria='logistica',
                tipo='vehiculo',
                tipo_asignacion=TipoAsignacion(asignacion_str),
                marca_id=marca.marca_id if asignacion_str == 'individual' else None,
                cantidad=cantidad,
                tipo_vehiculo=tipo_vehiculo,
                esquema='tradicional',
                valor_unitario=costo.costo_unitario_mensual
            )

            if rubro.es_individual():
                marca.agregar_rubro_individual(rubro)
            else:
                criterio_str = vehiculo_data.get('criterio_prorrateo', 'volumen')
                rubro.criterio_prorrateo = CriterioProrrateo(criterio_str)
                self.rubros_compartidos.append(rubro)

        # Procesar personal logístico
        personal_config = datos_logistica.get('personal', {})

        for tipo_personal, empleados_list in personal_config.items():
            # Puede ser una lista de grupos de empleados
            if not isinstance(empleados_list, list):
                empleados_list = [empleados_list]

            for empleado_data in empleados_list:
                cantidad = empleado_data.get('cantidad', 0)
                salario_base = empleado_data.get('salario_base', 0)
                perfil = empleado_data.get('perfil_prestacional', 'logistico')
                asignacion_str = empleado_data.get('asignacion', 'individual')

                if cantidad == 0 or salario_base == 0:
                    continue

                # Calcular costo con la calculadora
                costo = self.calc_nomina.calcular_costo_empleado(
                    salario_base=salario_base,
                    perfil=perfil
                )

                # Crear rubro
                rubro = RubroPersonal(
                    id=f"{tipo_personal}_{marca.marca_id}",
                    nombre=f"{tipo_personal.replace('_', ' ').title()}",
                    categoria='logistica',
                    tipo='personal',
                    tipo_asignacion=TipoAsignacion(asignacion_str),
                    marca_id=marca.marca_id if asignacion_str == 'individual' else None,
                    cantidad=cantidad,
                    salario_base=salario_base,
                    prestaciones=costo.prestaciones,
                    subsidio_transporte=costo.subsidio_transporte,
                    factor_prestacional=0.402 if perfil == 'logistico' else 0.378
                )

                if rubro.es_individual():
                    marca.agregar_rubro_individual(rubro)
                    marca.empleados_logisticos += cantidad
                else:
                    criterio_str = empleado_data.get('criterio_prorrateo', 'volumen')
                    rubro.criterio_prorrateo = CriterioProrrateo(criterio_str)
                    rubro.porcentaje_dedicacion = empleado_data.get('porcentaje_dedicacion')
                    self.rubros_compartidos.append(rubro)

        logger.debug(f"Rubros logísticos procesados para {marca.nombre}")

    def _procesar_rubros_compartidos_admin(self):
        """
        Procesa rubros administrativos compartidos.

        Estos son rubros que NO pertenecen a ninguna marca específica.
        """
        try:
            datos_admin = self.loader.cargar_compartidos_administrativo()
        except FileNotFoundError:
            logger.warning("No se encontró archivo de administrativos compartidos")
            return

        # Procesar personal administrativo
        personal = datos_admin.get('personal_administrativo', {})

        for puesto, config in personal.items():
            cantidad = config.get('cantidad', 0)
            if cantidad == 0:
                continue

            # Determinar si es honorarios o salario
            if config.get('tipo_contrato') == 'honorarios':
                valor_mensual = config.get('honorarios_mensuales', 0)
            else:
                salario_base = config.get('salario_base', 0)
                perfil = config.get('perfil_prestacional', 'administrativo')

                costo = self.calc_nomina.calcular_costo_empleado(
                    salario_base=salario_base,
                    perfil=perfil
                )
                valor_mensual = costo.costo_mensual

            # Crear rubro compartido
            criterio_str = config.get('criterio_prorrateo', 'ventas')

            rubro = Rubro(
                id=f"admin_{puesto}",
                nombre=config.get('descripcion', puesto.replace('_', ' ').title()),
                categoria='administrativa',
                tipo='personal',
                tipo_asignacion=TipoAsignacion.COMPARTIDO,
                criterio_prorrateo=CriterioProrrateo(criterio_str),
                cantidad=cantidad,
                valor_unitario=valor_mensual
            )

            self.rubros_compartidos.append(rubro)

        logger.debug("Rubros administrativos compartidos procesados")

    def cargar_marcas(self, marcas_ids: Optional[List[str]] = None):
        """
        Carga las marcas especificadas (o todas las disponibles).

        Args:
            marcas_ids: Lista de IDs de marcas a cargar. Si es None, carga todas.
        """
        if marcas_ids is None:
            marcas_ids = self.loader.listar_marcas()

        self.marcas = []
        self.rubros_compartidos = []

        for marca_id in marcas_ids:
            try:
                # Cargar datos completos de la marca
                datos_marca = self.loader.cargar_marca_completa(marca_id)

                # Crear marca
                marca = self._crear_marca_desde_datos(datos_marca)

                # Procesar rubros individuales
                self._procesar_rubros_comerciales(marca, datos_marca.get('comercial', {}))
                self._procesar_rubros_logisticos(marca, datos_marca.get('logistica', {}))

                self.marcas.append(marca)

            except Exception as e:
                logger.error(f"Error cargando marca '{marca_id}': {e}")

        # Procesar rubros compartidos administrativos
        self._procesar_rubros_compartidos_admin()

        logger.info(
            f"Cargadas {len(self.marcas)} marcas y "
            f"{len(self.rubros_compartidos)} rubros compartidos"
        )

    def ejecutar_simulacion(self) -> ResultadoSimulacion:
        """
        Ejecuta la simulación completa.

        Returns:
            ResultadoSimulacion con todos los resultados
        """
        logger.info("Iniciando simulación...")

        # Validar que haya marcas cargadas
        if not self.marcas:
            raise ValueError("No hay marcas cargadas. Ejecute cargar_marcas() primero.")

        # Crear allocator
        allocator = Allocator(self.marcas)

        # Asignar rubros compartidos
        asignaciones = allocator.asignar_rubros_compartidos(self.rubros_compartidos)

        # Agregar rubros compartidos a cada marca
        for marca in self.marcas:
            rubros_asignados = asignaciones.get(marca.marca_id, [])

            for asignacion in rubros_asignados:
                # Crear un rubro "virtual" con el valor prorrateado
                rubro_original = next(
                    (r for r in self.rubros_compartidos if r.id == asignacion['rubro_id']),
                    None
                )

                if rubro_original:
                    # Clonar el rubro pero con el valor asignado
                    rubro_asignado = Rubro(
                        id=rubro_original.id,
                        nombre=rubro_original.nombre,
                        categoria=rubro_original.categoria,
                        tipo=rubro_original.tipo,
                        tipo_asignacion=TipoAsignacion.COMPARTIDO,
                        criterio_prorrateo=rubro_original.criterio_prorrateo,
                        cantidad=1,
                        valor_unitario=asignacion['valor_asignado'],
                        valor_total=asignacion['valor_asignado']
                    )

                    marca.agregar_rubro_compartido(rubro_asignado)

        # Calcular consolidado
        consolidado = self._calcular_consolidado()

        # Crear resultado
        resultado = ResultadoSimulacion(
            marcas=self.marcas,
            consolidado=consolidado,
            rubros_compartidos=self.rubros_compartidos,
            asignaciones_prorrateo=asignaciones,
            metadata={
                'total_marcas': len(self.marcas),
                'total_rubros_compartidos': len(self.rubros_compartidos),
                'fecha_simulacion': '2025-11-10'  # TODO: usar fecha real
            }
        )

        logger.info("Simulación completada exitosamente")

        return resultado

    def _calcular_consolidado(self) -> Dict[str, Any]:
        """
        Calcula métricas consolidadas de todas las marcas.

        Returns:
            Dict con métricas consolidadas
        """
        total_ventas = sum(m.ventas_mensuales for m in self.marcas)
        total_costos = sum(m.costo_total for m in self.marcas)

        return {
            'total_ventas_mensuales': total_ventas,
            'total_ventas_anuales': total_ventas * 12,
            'total_costos_mensuales': total_costos,
            'total_costos_anuales': total_costos * 12,
            'margen_consolidado': (total_ventas - total_costos) / total_ventas if total_ventas > 0 else 0,
            'costo_comercial_total': sum(m.costo_comercial for m in self.marcas),
            'costo_logistico_total': sum(m.costo_logistico for m in self.marcas),
            'costo_administrativo_total': sum(m.costo_administrativo for m in self.marcas),
            'total_empleados': sum(m.total_empleados for m in self.marcas)
        }


# Función de conveniencia
def simular_modelo_completo(marcas_ids: Optional[List[str]] = None) -> ResultadoSimulacion:
    """
    Función de conveniencia para ejecutar una simulación completa.

    Args:
        marcas_ids: IDs de marcas a simular. Si es None, simula todas.

    Returns:
        ResultadoSimulacion
    """
    simulator = Simulator()
    simulator.cargar_marcas(marcas_ids)
    return simulator.ejecutar_simulacion()
