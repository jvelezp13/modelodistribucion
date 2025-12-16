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
from core.calculator_descuentos import CalculadoraDescuentos
from core.calculator_lejanias import CalculadoraLejanias
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
        self.calc_descuentos = CalculadoraDescuentos()
        self.calc_lejanias = None  # Se inicializa con escenario en ejecutar_simulacion()

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

        # Datos de CMV (para tipo lista_precios)
        tipo_proyeccion = comercial.get('tipo_proyeccion', 'simple')
        cmv_mensual = comercial.get('cmv_mensual', 0)
        margen_lista_mensual = comercial.get('margen_lista_mensual', 0)

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

        # Aplicar datos de CMV si es tipo lista_precios
        marca.aplicar_cmv(
            tipo_proyeccion=tipo_proyeccion,
            cmv_mensual=cmv_mensual,
            margen_lista_mensual=margen_lista_mensual
        )

        if tipo_proyeccion == 'lista_precios':
            logger.info(f"Marca creada: {marca.nombre} (ventas: ${ventas_mensuales:,.0f}, CMV: ${cmv_mensual:,.0f}, Margen Lista: ${margen_lista_mensual:,.0f})")
        else:
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
                    nombre=empleado_data.get('nombre', tipo.replace('_', ' ').title()),
                    categoria='comercial',
                    tipo='personal',
                    tipo_asignacion=TipoAsignacion(asignacion_str),
                    marca_id=marca.marca_id if asignacion_str == 'individual' else None,
                    cantidad=cantidad,
                    salario_base=salario_base,
                    prestaciones=costo.prestaciones,
                    subsidio_transporte=costo.subsidio_transporte,
                    factor_prestacional=0.402 if perfil == 'comercial' else 0.378,
                    auxilios_no_prestacionales=empleado_data.get('auxilios_no_prestacionales', {})
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

        # Procesar gastos comerciales
        gastos = datos_comercial.get('gastos_comerciales', [])
        for gasto_data in gastos:
            valor_mensual = gasto_data.get('valor_mensual', 0)
            if valor_mensual == 0:
                continue

            asignacion_str = gasto_data.get('asignacion', 'individual')

            # Crear rubro de gasto
            rubro = Rubro(
                id=f"gasto_com_{gasto_data.get('tipo')}_{marca.marca_id}",
                nombre=gasto_data.get('nombre', gasto_data.get('tipo', 'Gasto')),
                categoria='comercial',
                tipo='gasto',
                tipo_asignacion=TipoAsignacion(asignacion_str),
                marca_id=marca.marca_id if asignacion_str == 'individual' else None,
                valor_unitario=valor_mensual,
                cantidad=1
            )

            if rubro.es_individual():
                marca.agregar_rubro_individual(rubro)
            else:
                criterio_str = gasto_data.get('criterio_prorrateo', 'ventas')
                rubro.criterio_prorrateo = CriterioProrrateo(criterio_str)
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
            nombre_vehiculo = vehiculo_data.get('nombre', f"Vehículo {tipo_vehiculo.upper()} (Renting)")

            if cantidad == 0:
                continue

            # Usar el costo pre-calculado del modelo (solo costos fijos)
            valor_unitario = vehiculo_data.get('costo_mensual_calculado', 0)

            # Crear rubro
            rubro = RubroVehiculo(
                id=f"vehiculo_{tipo_vehiculo}_renting_{marca.marca_id}",
                nombre=nombre_vehiculo,
                categoria='logistico',
                tipo='vehiculo',
                tipo_asignacion=TipoAsignacion(asignacion_str),
                marca_id=marca.marca_id if asignacion_str == 'individual' else None,
                cantidad=cantidad,
                tipo_vehiculo=tipo_vehiculo,
                esquema='renting',
                valor_unitario=valor_unitario
            )

            if rubro.es_individual():
                marca.agregar_rubro_individual(rubro)
            else:
                criterio_str = vehiculo_data.get('criterio_prorrateo', 'volumen')
                rubro.criterio_prorrateo = CriterioProrrateo(criterio_str)
                rubro.porcentaje_dedicacion = vehiculo_data.get('porcentaje_uso')
                self.rubros_compartidos.append(rubro)

        # Tradicional (Propio)
        for vehiculo_data in vehiculos_config.get('tradicional', []):
            tipo_vehiculo = vehiculo_data.get('tipo')
            cantidad = vehiculo_data.get('cantidad', 0)
            asignacion_str = vehiculo_data.get('asignacion', 'individual')
            nombre_vehiculo = vehiculo_data.get('nombre', f"Vehículo {tipo_vehiculo.upper()} (Propio)")

            if cantidad == 0:
                continue

            # Usar el costo pre-calculado del modelo (solo costos fijos)
            valor_unitario = vehiculo_data.get('costo_mensual_calculado', 0)

            rubro = RubroVehiculo(
                id=f"vehiculo_{tipo_vehiculo}_tradicional_{marca.marca_id}",
                nombre=nombre_vehiculo,
                categoria='logistico',
                tipo='vehiculo',
                tipo_asignacion=TipoAsignacion(asignacion_str),
                marca_id=marca.marca_id if asignacion_str == 'individual' else None,
                cantidad=cantidad,
                tipo_vehiculo=tipo_vehiculo,
                esquema='tradicional',
                valor_unitario=valor_unitario
            )

            if rubro.es_individual():
                marca.agregar_rubro_individual(rubro)
            else:
                criterio_str = vehiculo_data.get('criterio_prorrateo', 'volumen')
                rubro.criterio_prorrateo = CriterioProrrateo(criterio_str)
                self.rubros_compartidos.append(rubro)

        # Tercero (Flete con terceros)
        # NOTA: El costo del flete base ahora viene de los Recorridos Logísticos
        # Aquí solo se registran costos fijos adicionales del vehículo tercero
        for vehiculo_data in vehiculos_config.get('tercero', []):
            tipo_vehiculo = vehiculo_data.get('tipo')
            cantidad = vehiculo_data.get('cantidad', 0)
            asignacion_str = vehiculo_data.get('asignacion', 'individual')
            nombre_vehiculo = vehiculo_data.get('nombre', f"Vehículo {tipo_vehiculo.upper()} (Tercero)")

            if cantidad == 0:
                continue

            # Para terceros, el costo fijo es solo monitoreo + seguro mercancía
            # El flete base viene de los Recorridos Logísticos
            valor_unitario = vehiculo_data.get('costo_mensual_calculado', 0)

            rubro = RubroVehiculo(
                id=f"vehiculo_{tipo_vehiculo}_tercero_{marca.marca_id}",
                nombre=nombre_vehiculo,
                categoria='logistico',
                tipo='vehiculo',
                tipo_asignacion=TipoAsignacion(asignacion_str),
                marca_id=marca.marca_id if asignacion_str == 'individual' else None,
                cantidad=cantidad,
                tipo_vehiculo=tipo_vehiculo,
                esquema='tercero',
                valor_unitario=valor_unitario
            )

            if rubro.es_individual():
                marca.agregar_rubro_individual(rubro)
            else:
                criterio_str = vehiculo_data.get('criterio_prorrateo', 'volumen')
                rubro.criterio_prorrateo = CriterioProrrateo(criterio_str)
                rubro.porcentaje_dedicacion = vehiculo_data.get('porcentaje_uso')
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
                    nombre=empleado_data.get('nombre', tipo_personal.replace('_', ' ').title()),
                    categoria='logistico',
                    tipo='personal',
                    tipo_asignacion=TipoAsignacion(asignacion_str),
                    marca_id=marca.marca_id if asignacion_str == 'individual' else None,
                    cantidad=cantidad,
                    salario_base=salario_base,
                    prestaciones=costo.prestaciones,
                    subsidio_transporte=costo.subsidio_transporte,
                    factor_prestacional=0.402 if perfil == 'logistico' else 0.378,
                    auxilios_no_prestacionales=empleado_data.get('auxilios_no_prestacionales', {})
                )

                if rubro.es_individual():
                    marca.agregar_rubro_individual(rubro)
                    marca.empleados_logisticos += cantidad
                else:
                    criterio_str = empleado_data.get('criterio_prorrateo', 'volumen')
                    rubro.criterio_prorrateo = CriterioProrrateo(criterio_str)
                    rubro.porcentaje_dedicacion = empleado_data.get('porcentaje_dedicacion')
                    self.rubros_compartidos.append(rubro)

        # Procesar gastos logísticos
        gastos = datos_logistica.get('gastos_logisticos', [])

        for gasto_data in gastos:
            valor_mensual = gasto_data.get('valor_mensual', 0)
            if valor_mensual == 0:
                continue

            asignacion_str = gasto_data.get('asignacion', 'individual')

            # Crear rubro de gasto
            rubro = Rubro(
                id=f"gasto_log_{gasto_data.get('tipo')}_{marca.marca_id}",
                nombre=gasto_data.get('nombre', gasto_data.get('tipo', 'Gasto')),
                categoria='logistico',
                tipo='gasto',
                tipo_asignacion=TipoAsignacion(asignacion_str),
                marca_id=marca.marca_id if asignacion_str == 'individual' else None,
                valor_unitario=valor_mensual,
                cantidad=1
            )

            if rubro.es_individual():
                marca.agregar_rubro_individual(rubro)
            else:
                criterio_str = gasto_data.get('criterio_prorrateo', 'volumen')
                rubro.criterio_prorrateo = CriterioProrrateo(criterio_str)
                self.rubros_compartidos.append(rubro)

        logger.debug(f"Rubros logísticos procesados para {marca.nombre}")

    def _procesar_rubros_administrativos(
        self,
        marca: Marca,
        datos_administrativo: Dict[str, Any]
    ):
        """
        Procesa y agrega rubros administrativos a una marca.

        Args:
            marca: Marca a la que agregar rubros
            datos_administrativo: Datos administrativos de la marca
        """
        # Procesar personal administrativo
        personal_list = datos_administrativo.get('personal', [])

        for empleado_data in personal_list:
            cantidad = empleado_data.get('cantidad', 0)
            if cantidad == 0:
                continue

            tipo_contrato = empleado_data.get('tipo_contrato', 'nomina')
            asignacion_str = empleado_data.get('asignacion', 'individual')

            # Diferenciar entre honorarios y nómina
            if tipo_contrato == 'honorarios':
                # Honorarios: usar directamente el valor sin calcular prestaciones
                honorarios = empleado_data.get('honorarios_mensuales', 0)

                # Crear rubro simple (sin desglose de prestaciones)
                rubro = Rubro(
                    id=f"admin_{empleado_data.get('tipo')}_{marca.marca_id}",
                    nombre=empleado_data.get('nombre', empleado_data.get('tipo', 'Personal Admin')),
                    categoria='administrativo',
                    tipo='personal',
                    tipo_asignacion=TipoAsignacion(asignacion_str),
                    marca_id=marca.marca_id if asignacion_str == 'individual' else None,
                    valor_unitario=honorarios,
                    cantidad=cantidad
                )
            else:
                # Nómina: calcular con prestaciones
                salario_base = empleado_data.get('salario_base', 0)
                perfil = empleado_data.get('perfil_prestacional', 'administrativo')

                # Calcular costo con la calculadora para obtener desglose
                costo = self.calc_nomina.calcular_costo_empleado(
                    salario_base=salario_base,
                    perfil=perfil
                )

                # Crear rubro de personal con desglose completo
                rubro = RubroPersonal(
                    id=f"admin_{empleado_data.get('tipo')}_{marca.marca_id}",
                    nombre=empleado_data.get('nombre', empleado_data.get('tipo', 'Personal Admin')),
                    categoria='administrativo',
                    tipo='personal',
                    tipo_asignacion=TipoAsignacion(asignacion_str),
                    marca_id=marca.marca_id if asignacion_str == 'individual' else None,
                    cantidad=cantidad,
                    salario_base=salario_base,
                    prestaciones=costo.prestaciones,
                    subsidio_transporte=costo.subsidio_transporte,
                    factor_prestacional=0.378 if perfil == 'administrativo' else 0.49 if perfil == 'aprendiz_sena' else 0.378,
                    auxilios_no_prestacionales=empleado_data.get('auxilios_no_prestacionales', {})
                )

            if rubro.es_individual():
                marca.agregar_rubro_individual(rubro)
            else:
                criterio_str = empleado_data.get('criterio_prorrateo', 'ventas')
                rubro.criterio_prorrateo = CriterioProrrateo(criterio_str)
                # Personal administrativo no usa porcentaje_dedicacion
                self.rubros_compartidos.append(rubro)

        # Procesar gastos administrativos
        gastos = datos_administrativo.get('gastos', [])
        for gasto_data in gastos:
            valor_mensual = gasto_data.get('valor_mensual', 0)
            if valor_mensual == 0:
                continue

            asignacion_str = gasto_data.get('asignacion', 'individual')

            # Crear rubro de gasto
            rubro = Rubro(
                id=f"gasto_admin_{gasto_data.get('tipo')}_{marca.marca_id}",
                nombre=gasto_data.get('nombre', gasto_data.get('tipo', 'Gasto')),
                categoria='administrativo',
                tipo='gasto',
                tipo_asignacion=TipoAsignacion(asignacion_str),
                marca_id=marca.marca_id if asignacion_str == 'individual' else None,
                valor_unitario=valor_mensual,
                cantidad=1
            )

            if rubro.es_individual():
                marca.agregar_rubro_individual(rubro)
            else:
                criterio_str = gasto_data.get('criterio_prorrateo', 'ventas')
                rubro.criterio_prorrateo = CriterioProrrateo(criterio_str)
                self.rubros_compartidos.append(rubro)

        logger.debug(f"Rubros administrativos procesados para {marca.nombre}")

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

            salario_base = config.get('salario_base', 0)
            perfil = config.get('perfil_prestacional', 'administrativo')

            # Calcular costo con la calculadora para obtener desglose
            costo = self.calc_nomina.calcular_costo_empleado(
                salario_base=salario_base,
                perfil=perfil
            )

            # Crear rubro compartido con desglose completo
            criterio_str = config.get('criterio_prorrateo', 'ventas')

            rubro = RubroPersonal(
                id=f"admin_{puesto}",
                nombre=config.get('nombre', config.get('descripcion', puesto.replace('_', ' ').title())),
                categoria='administrativo',
                tipo='personal',
                tipo_asignacion=TipoAsignacion.COMPARTIDO,
                criterio_prorrateo=CriterioProrrateo(criterio_str),
                cantidad=cantidad,
                salario_base=salario_base,
                prestaciones=costo.prestaciones,
                subsidio_transporte=costo.subsidio_transporte,
                factor_prestacional=0.378 if perfil == 'administrativo' else 0.49 if perfil == 'aprendiz_sena' else 0.378,
                auxilios_no_prestacionales=config.get('auxilios_no_prestacionales', {})
            )

            self.rubros_compartidos.append(rubro)

        # Procesar gastos administrativos compartidos
        gastos = datos_admin.get('gastos_administrativos', [])
        for gasto_data in gastos:
            valor_mensual = gasto_data.get('valor_mensual', 0)
            if valor_mensual == 0:
                continue

            criterio_str = gasto_data.get('criterio_prorrateo', 'ventas')

            # Crear rubro de gasto
            rubro = Rubro(
                id=f"gasto_admin_{gasto_data.get('tipo')}",
                nombre=gasto_data.get('nombre', gasto_data.get('tipo', 'Gasto')),
                categoria='administrativo',
                tipo='gasto',
                tipo_asignacion=TipoAsignacion.COMPARTIDO,
                criterio_prorrateo=CriterioProrrateo(criterio_str),
                valor_unitario=valor_mensual,
                cantidad=1
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

        errores_carga = []
        for marca_id in marcas_ids:
            try:
                # Cargar datos completos de la marca
                datos_marca = self.loader.cargar_marca_completa(marca_id)

                # Crear marca
                marca = self._crear_marca_desde_datos(datos_marca)

                # Procesar rubros individuales
                self._procesar_rubros_comerciales(marca, datos_marca.get('comercial', {}))
                self._procesar_rubros_logisticos(marca, datos_marca.get('logistica', {}))
                self._procesar_rubros_administrativos(marca, datos_marca.get('administrativo', {}))

                self.marcas.append(marca)

            except Exception as e:
                import traceback
                error_detalle = f"Error cargando marca '{marca_id}': {e}\n{traceback.format_exc()}"
                logger.error(error_detalle)
                errores_carga.append(error_detalle)

        # Procesar rubros compartidos administrativos
        self._procesar_rubros_compartidos_admin()

        # Cargar configuraciones de descuentos
        try:
            self.calc_descuentos.cargar_configuraciones(marcas_ids)
            logger.info("Configuraciones de descuentos cargadas")
        except Exception as e:
            logger.warning(f"No se pudieron cargar descuentos: {e}")

        # Guardar errores para referencia
        self._errores_carga = errores_carga

        logger.info(
            f"Cargadas {len(self.marcas)} marcas y "
            f"{len(self.rubros_compartidos)} rubros compartidos"
        )
        if errores_carga:
            logger.warning(f"Hubo {len(errores_carga)} errores al cargar marcas")

    def ejecutar_simulacion(self) -> ResultadoSimulacion:
        """
        Ejecuta la simulación completa.

        Returns:
            ResultadoSimulacion con todos los resultados
        """
        logger.info("Iniciando simulación...")

        # Validar que haya marcas cargadas
        if not self.marcas:
            errores = getattr(self, '_errores_carga', [])
            if errores:
                raise ValueError(f"No hay marcas cargadas. Errores:\n" + "\n".join(errores))
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

        # Aplicar descuentos a cada marca
        for marca in self.marcas:
            try:
                resultado_descuentos = self.calc_descuentos.calcular_descuentos(
                    marca.marca_id,
                    marca.ventas_mensuales
                )

                marca.aplicar_descuentos(
                    descuento_pie_factura=resultado_descuentos.descuento_pie_factura,
                    rebate=resultado_descuentos.rebate,
                    descuento_financiero=resultado_descuentos.descuento_financiero,
                    ventas_netas=resultado_descuentos.ventas_netas,
                    porcentaje_descuento_total=resultado_descuentos.porcentaje_descuento_total
                )

                if resultado_descuentos.porcentaje_descuento_total > 0:
                    logger.info(
                        f"Descuentos aplicados a {marca.nombre}: "
                        f"{resultado_descuentos.porcentaje_descuento_total:.2f}% "
                        f"(${resultado_descuentos.ventas_brutas - resultado_descuentos.ventas_netas:,.0f})"
                    )
            except Exception as e:
                logger.warning(f"Error aplicando descuentos a {marca.nombre}: {e}")

        # Calcular lejanías (gastos variables por ruta)
        self._calcular_lejanias()

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
        total_ventas_brutas = sum(m.ventas_mensuales for m in self.marcas)
        total_ventas_netas = sum(
            m.ventas_netas_mensuales if m.ventas_netas_mensuales > 0 else m.ventas_mensuales
            for m in self.marcas
        )
        total_descuentos = sum(
            m.descuento_pie_factura + m.rebate + m.descuento_financiero
            for m in self.marcas
        )
        total_costos = sum(m.costo_total for m in self.marcas)

        return {
            'total_ventas_brutas_mensuales': total_ventas_brutas,
            'total_ventas_netas_mensuales': total_ventas_netas,
            'total_descuentos_mensuales': total_descuentos,
            'total_ventas_anuales': total_ventas_netas * 12,
            'total_costos_mensuales': total_costos,
            'total_costos_anuales': total_costos * 12,
            'margen_consolidado': (total_ventas_netas - total_costos) / total_ventas_netas if total_ventas_netas > 0 else 0,
            'costo_comercial_total': sum(m.costo_comercial for m in self.marcas),
            'costo_logistico_total': sum(m.costo_logistico for m in self.marcas),
            'costo_administrativo_total': sum(m.costo_administrativo for m in self.marcas),
            'total_empleados': sum(m.total_empleados for m in self.marcas),
            'porcentaje_descuento_promedio': (total_descuentos / total_ventas_brutas * 100) if total_ventas_brutas > 0 else 0
        }

    def _calcular_lejanias(self):
        """
        Calcula lejanías (gastos variables por ruta) para todas las marcas.
        Requiere que las marcas tengan zonas configuradas con municipios.
        """
        try:
            # Obtener escenario del loader
            escenario = getattr(self.loader, 'escenario', None)
            if not escenario:
                logger.warning("No hay escenario disponible, saltando cálculo de lejanías")
                return

            # Inicializar calculadora con escenario
            self.calc_lejanias = CalculadoraLejanias(escenario)

            # Calcular para cada marca
            for marca in self.marcas:
                try:
                    # Obtener el objeto Marca de Django
                    from core.models import Marca as MarcaDjango
                    marca_django = MarcaDjango.objects.get(marca_id=marca.marca_id)

                    resultado = self.calc_lejanias.calcular_lejanias_marca(marca_django)

                    # Asignar a la marca (dataclass)
                    marca.lejania_comercial = float(resultado['comercial']['total_mensual'])
                    marca.lejania_logistica = float(resultado['logistica']['total_mensual'])

                    # Agregar costos del comité comercial (ya calculados en signals.py y persistidos en GastoComercial)
                    from core.models import GastoComercial
                    from django.db.models import Sum
                    comite_total = GastoComercial.objects.filter(
                        escenario=escenario,
                        marca=marca_django,
                        nombre__startswith='Comité Comercial'
                    ).aggregate(total=Sum('valor_mensual'))['total'] or 0
                    marca.lejania_comercial += float(comite_total)

                    # Agregar a costos totales
                    marca.costo_comercial += marca.lejania_comercial
                    marca.costo_logistico += marca.lejania_logistica
                    marca.costo_total = (
                        marca.costo_comercial +
                        marca.costo_logistico +
                        marca.costo_administrativo
                    )

                    logger.info(
                        f"Lejanías calculadas para {marca.nombre}: "
                        f"Comercial=${marca.lejania_comercial:,.0f} (incl. comité=${comite_total:,.0f}), "
                        f"Logística=${marca.lejania_logistica:,.0f}"
                    )
                except Exception as e:
                    logger.warning(f"Error calculando lejanías para {marca.nombre}: {e}")
        except Exception as e:
            logger.warning(f"No se pudieron calcular lejanías: {e}")


# Función de conveniencia
def simular_modelo_completo(
    marcas_ids: Optional[List[str]] = None,
    escenario_id: Optional[int] = None
) -> ResultadoSimulacion:
    """
    Función de conveniencia para ejecutar una simulación completa.

    Args:
        marcas_ids: IDs de marcas a simular. Si es None, simula todas.
        escenario_id: ID del escenario a simular.

    Returns:
        ResultadoSimulacion
    """
    # Intentar usar loader de BD por defecto si está disponible
    try:
        from utils.loaders_db import get_loader_db
        loader = get_loader_db(escenario_id=escenario_id)
    except (ImportError, Exception) as e:
        logger.warning(f"No se pudo cargar DataLoaderDB, usando YAML: {e}")
        loader = DataLoader()

    simulator = Simulator(loader=loader)
    simulator.cargar_marcas(marcas_ids)
    return simulator.ejecutar_simulacion()
