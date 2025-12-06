"""
DataLoader que usa PostgreSQL a través de Django ORM
"""
from typing import Dict, List, Any, Optional
import logging

# Inicializar Django antes de importar modelos (reorganiza sys.path)
from . import django_init

# Importar modelos de Django (ahora core.models será de /app/admin_panel/core/)
from core.models import (
    Marca, PersonalComercial, PersonalLogistico, PersonalAdministrativo,
    Vehiculo, ProyeccionVentasConfig,
    ParametrosMacro, FactorPrestacional, Escenario,
    GastoComercial, GastoLogistico, GastoAdministrativo
)

logger = logging.getLogger(__name__)


class DataLoaderDB:
    """
    Carga datos desde PostgreSQL usando Django ORM.

    Esta clase tiene la misma interfaz que el DataLoader original
    pero lee desde la base de datos en lugar de YAMLs.
    """

    def __init__(self, escenario_id: Optional[int] = None):
        logger.info(f"DataLoaderDB inicializado (PostgreSQL) - Escenario ID: {escenario_id}")
        self.escenario_id = escenario_id
        self._escenario_cache = None

    def _get_escenario(self):
        """Obtiene el escenario activo o el solicitado"""
        if self._escenario_cache:
            return self._escenario_cache
            
        if self.escenario_id:
            try:
                self._escenario_cache = Escenario.objects.get(pk=self.escenario_id)
            except Escenario.DoesNotExist:
                logger.warning(f"Escenario {self.escenario_id} no encontrado, buscando activo")
                self._escenario_cache = Escenario.objects.filter(activo=True).first()
        else:
            self._escenario_cache = Escenario.objects.filter(activo=True).first()
            
        if not self._escenario_cache:
            # Fallback al último creado si no hay activos
            self._escenario_cache = Escenario.objects.order_by('-id').first()
            
        return self._escenario_cache

    @property
    def escenario(self):
        """Propiedad para acceder al escenario (compatible con CalculadoraLejanias)"""
        return self._get_escenario()

    def _get_filter_kwargs(self):
        """Retorna los kwargs para filtrar por escenario"""
        escenario = self._get_escenario()
        if escenario:
            return {'escenario': escenario}
        return {}

    # =========================================================================
    # CONFIGURACIÓN
    # =========================================================================

    def cargar_parametros_macro(self) -> Dict[str, Any]:
        """Carga los parámetros macroeconómicos activos (o del año del escenario)"""
        try:
            escenario = self._get_escenario()
            if escenario:
                # Intentar cargar macros del año del escenario
                params = ParametrosMacro.objects.filter(anio=escenario.anio).first()
            else:
                params = ParametrosMacro.objects.filter(activo=True).first()
                
            if not params:
                # Fallback a cualquier activo
                params = ParametrosMacro.objects.filter(activo=True).first()
                
            if not params:
                raise ValueError("No hay parámetros macro activos")

            return {
                'parametros': {
                    'anio': params.anio,
                    'ipc': float(params.ipc),
                    'ipt': float(params.ipt),
                    'salario_minimo_legal_2025': float(params.salario_minimo_legal),
                    'subsidio_transporte_2025': float(params.subsidio_transporte),
                    'incremento_salarios': float(params.incremento_salarios),
                }
            }
        except Exception as e:
            logger.error(f"Error cargando parámetros macro: {e}")
            raise

    def cargar_factores_prestacionales(self) -> Dict[str, Any]:
        """
        Carga los factores prestacionales.

        Los valores en BD están en formato 0-100 (ej: 8.5 para 8.5%).
        Se convierten a decimal (0.085) para usar en cálculos.
        """
        try:
            factores = FactorPrestacional.objects.all()
            result = {}

            for factor in factores:
                # Convertir de porcentaje (0-100) a decimal (0-1) para cálculos
                result[factor.perfil] = {
                    'salud': float(factor.salud) / 100,
                    'pension': float(factor.pension) / 100,
                    'arl': float(factor.arl) / 100,
                    'caja_compensacion': float(factor.caja_compensacion) / 100,
                    'icbf': float(factor.icbf) / 100,
                    'sena': float(factor.sena) / 100,
                    'cesantias': float(factor.cesantias) / 100,
                    'intereses_cesantias': float(factor.intereses_cesantias) / 100,
                    'prima': float(factor.prima) / 100,
                    'vacaciones': float(factor.vacaciones) / 100,
                    'factor_total': float(factor.factor_total),  # Ya viene en decimal del property
                }

            return result
        except Exception as e:
            logger.error(f"Error cargando factores prestacionales: {e}")
            raise

    def cargar_config_marcas(self) -> Dict[str, Any]:
        """Carga la configuración de marcas"""
        try:
            marcas = Marca.objects.filter(activa=True)

            return {
                'marcas': [
                    {
                        'id': m.marca_id,
                        'nombre': m.nombre,
                        'descripcion': m.descripcion,
                        'activa': m.activa,
                        'color': m.color,
                    }
                    for m in marcas
                ],
                'configuracion': {
                    'permitir_recursos_compartidos': True,
                    'criterio_prorrateo_default': 'ventas',
                    'calcular_margenes_consolidados': True,
                }
            }
        except Exception as e:
            logger.error(f"Error cargando config de marcas: {e}")
            raise

    def cargar_catalogo_rubros(self) -> Dict[str, Any]:
        """Carga el catálogo de rubros (mantiene compatibilidad con YAML)"""
        # Por ahora, cargar desde YAML original
        from .loaders import DataLoader
        yaml_loader = DataLoader()
        return yaml_loader.cargar_catalogo_rubros()

    def cargar_catalogo_vehiculos(self) -> Dict[str, Any]:
        """Carga el catálogo de vehículos (mantiene compatibilidad con YAML)"""
        # Por ahora, cargar desde YAML original
        from .loaders import DataLoader
        yaml_loader = DataLoader()
        return yaml_loader.cargar_catalogo_vehiculos()

    # =========================================================================
    # DATOS POR MARCA
    # =========================================================================

    def cargar_marca_comercial(self, marca_id: str) -> Dict[str, Any]:
        """Carga los datos comerciales de una marca desde PostgreSQL"""
        try:
            marca = Marca.objects.get(marca_id=marca_id)

            # IMPORTANTE: Forzar recarga desde DB (evitar caché de Django ORM)
            personal = PersonalComercial.objects.filter(marca=marca, **self._get_filter_kwargs()).all()

            # DEBUG: Log para verificar qué se está leyendo
            logger.info(f"[DEBUG] Cargando personal comercial de {marca_id}")
            logger.info(f"[DEBUG] Total registros: {personal.count()}")
            for p in personal:
                logger.info(f"[DEBUG] - Tipo: {p.tipo}, Cantidad: {p.cantidad}, ID: {p.id}")

            # Cargar proyección de ventas desde ProyeccionVentasConfig
            total_ventas_anuales = 0
            escenario = self._get_escenario()
            if escenario:
                try:
                    config = ProyeccionVentasConfig.objects.get(
                        marca=marca,
                        escenario=escenario,
                        anio=escenario.anio
                    )
                    total_ventas_anuales = config.get_venta_anual()
                except ProyeccionVentasConfig.DoesNotExist:
                    logger.warning(f"No hay ProyeccionVentasConfig para {marca_id} en escenario {escenario.nombre}")

            # Agrupar personal por tipo
            recursos_comerciales = {}

            for p in personal:
                tipo_key = p.tipo

                if tipo_key not in recursos_comerciales:
                    recursos_comerciales[tipo_key] = []

                data = {
                    'tipo': p.tipo,
                    'nombre': p.nombre if hasattr(p, 'nombre') else '',  # ⭐ NUEVO campo
                    'cantidad': p.cantidad,
                    'salario_base': float(p.salario_base),
                    'perfil_prestacional': p.perfil_prestacional,
                    'asignacion': p.asignacion,
                    'auxilio_adicional': float(p.auxilio_adicional) if p.auxilio_adicional else 0,
                    'porcentaje_dedicacion': float(p.porcentaje_dedicacion) if p.porcentaje_dedicacion else None,
                    'criterio_prorrateo': p.criterio_prorrateo,
                    'costo_mensual_calculado': float(p.calcular_costo_mensual()),  # ⭐ USAR método del modelo
                }

                logger.info(f"[DEBUG] Agregando {p.tipo}: cantidad={p.cantidad}")
                recursos_comerciales[tipo_key].append(data)

            # Cargar gastos comerciales
            # IMPORTANTE: Excluir gastos de lejanías porque se calculan dinámicamente
            # mediante CalculadoraLejanias y se agregan en marca.lejania_comercial
            gastos_comerciales = []
            gastos_qs = GastoComercial.objects.filter(marca=marca, **self._get_filter_kwargs())

            for gasto in gastos_qs:
                # Filtrar gastos de lejanías (mismo criterio que pyg_service.py)
                nombre = gasto.nombre or ''
                if nombre.startswith('Combustible Lejanía') or nombre.startswith('Viáticos Pernocta'):
                    logger.debug(f"[DEBUG] Excluyendo gasto de lejanía: {nombre}")
                    continue

                gastos_comerciales.append({
                    'tipo': gasto.tipo,
                    'nombre': gasto.nombre,
                    'valor_mensual': float(gasto.valor_mensual),
                    'asignacion': gasto.asignacion,
                    'criterio_prorrateo': gasto.criterio_prorrateo if gasto.asignacion == 'compartido' else None,
                })

            logger.info(f"[DEBUG] Gastos comerciales cargados: {len(gastos_comerciales)}")

            return {
                'marca_id': marca.marca_id,
                'nombre': marca.nombre,
                'proyeccion_ventas': {
                    'resumen_anual': {
                        'total_ventas_anuales': float(total_ventas_anuales)
                    },
                    'proyeccion_mensual': {
                        # Esto podría detallarse más si se necesita
                    }
                },
                'recursos_comerciales': recursos_comerciales,
                'gastos_comerciales': gastos_comerciales,
            }

        except Marca.DoesNotExist:
            logger.error(f"Marca no encontrada: {marca_id}")
            raise FileNotFoundError(f"Marca no encontrada: {marca_id}")
        except Exception as e:
            logger.error(f"Error cargando datos comerciales de {marca_id}: {e}")
            raise

    def cargar_marca_logistica(self, marca_id: str) -> Dict[str, Any]:
        """Carga los datos logísticos de una marca desde PostgreSQL"""
        try:
            marca = Marca.objects.get(marca_id=marca_id)

            # Cargar vehículos
            vehiculos_qs = Vehiculo.objects.filter(marca=marca, **self._get_filter_kwargs())
            vehiculos_dict = {'tercero': [], 'renting': [], 'tradicional': []}  # ⭐ Agregar esquema tercero

            for v in vehiculos_qs:
                vehiculo_data = {
                    'id': v.id,
                    'nombre': v.nombre or f"{v.get_tipo_vehiculo_display()} #{v.id}",
                    'tipo': v.tipo_vehiculo,
                    'cantidad': v.cantidad,
                    'asignacion': v.asignacion,
                    'porcentaje_uso': float(v.porcentaje_uso) if v.porcentaje_uso else None,
                    'criterio_prorrateo': v.criterio_prorrateo,
                    'costo_mensual_calculado': float(v.calcular_costo_mensual()),
                    # Campos adicionales para referencia
                    'costo_seguro_mercancia_mensual': float(v.costo_seguro_mercancia_mensual) if v.costo_seguro_mercancia_mensual else 0,
                    'costo_monitoreo_mensual': float(v.costo_monitoreo_mensual) if v.costo_monitoreo_mensual else 0,
                    # Campos para cálculo de combustible en recorridos
                    'tipo_combustible': v.tipo_combustible,
                    'consumo_galon_km': float(v.consumo_galon_km) if v.consumo_galon_km else 0,
                    'esquema': v.esquema,
                }
                vehiculos_dict[v.esquema].append(vehiculo_data)

            # Cargar personal logístico
            personal_qs = PersonalLogistico.objects.filter(marca=marca, **self._get_filter_kwargs())
            personal_dict = {}

            for p in personal_qs:
                tipo_key = p.tipo if not p.tipo.endswith('s') else p.tipo + 'es'

                if tipo_key not in personal_dict:
                    personal_dict[tipo_key] = []

                personal_dict[tipo_key].append({
                    'nombre': p.nombre if hasattr(p, 'nombre') else '',  # ⭐ NUEVO campo
                    'cantidad': p.cantidad,
                    'salario_base': float(p.salario_base),
                    'perfil_prestacional': p.perfil_prestacional,
                    'asignacion': p.asignacion,
                    'auxilio_adicional': float(p.auxilio_adicional) if p.auxilio_adicional else 0,
                    'porcentaje_dedicacion': float(p.porcentaje_dedicacion) if p.porcentaje_dedicacion else None,
                    'criterio_prorrateo': p.criterio_prorrateo,
                    'costo_mensual_calculado': float(p.calcular_costo_mensual()),  # ⭐ USAR método del modelo
                })

            # Cargar gastos logísticos
            # IMPORTANTE: Excluir gastos de lejanías logísticas porque se calculan dinámicamente
            # mediante CalculadoraLejanias y se agregan en marca.lejania_logistica
            gastos_logisticos = []
            gastos_qs = GastoLogistico.objects.filter(marca=marca, **self._get_filter_kwargs())

            for gasto in gastos_qs:
                # Filtrar gastos de lejanías logísticas (mismo criterio que pyg_service.py)
                nombre = gasto.nombre or ''
                if (nombre.startswith('Combustible - ') or
                    nombre.startswith('Peaje - ') or
                    nombre.startswith('Viáticos Conductor - ') or
                    nombre.startswith('Viáticos Auxiliar - ') or
                    nombre.startswith('Flete Base Tercero - ') or
                    nombre == 'Flete Transporte (Tercero)'):
                    logger.debug(f"[DEBUG] Excluyendo gasto de lejanía logística: {nombre}")
                    continue

                gastos_logisticos.append({
                    'tipo': gasto.tipo,
                    'nombre': gasto.nombre,
                    'valor_mensual': float(gasto.valor_mensual),
                    'asignacion': gasto.asignacion,
                    'criterio_prorrateo': gasto.criterio_prorrateo if gasto.asignacion == 'compartido' else None,
                })

            logger.info(f"[DEBUG] Gastos logísticos cargados: {len(gastos_logisticos)}")

            return {
                'marca_id': marca.marca_id,
                'vehiculos': vehiculos_dict,
                'personal': personal_dict,
                'gastos_logisticos': gastos_logisticos,
            }

        except Marca.DoesNotExist:
            logger.error(f"Marca no encontrada: {marca_id}")
            raise FileNotFoundError(f"Marca no encontrada: {marca_id}")
        except Exception as e:
            logger.error(f"Error cargando datos logísticos de {marca_id}: {e}")
            raise

    def cargar_marca_ventas(self, marca_id: str) -> Dict[str, Any]:
        """Carga las proyecciones de ventas de una marca desde PostgreSQL"""
        try:
            marca = Marca.objects.get(marca_id=marca_id)
            escenario = self._get_escenario()

            ventas_mensuales = {}
            total_anual = 0

            if escenario:
                try:
                    config = ProyeccionVentasConfig.objects.get(
                        marca=marca,
                        escenario=escenario,
                        anio=escenario.anio
                    )
                    ventas_mensuales = config.calcular_ventas_mensuales()
                    total_anual = sum(ventas_mensuales.values())
                except ProyeccionVentasConfig.DoesNotExist:
                    logger.warning(f"No hay ProyeccionVentasConfig para {marca_id}")

            promedio = total_anual / 12 if total_anual > 0 else 0

            return {
                'marca_id': marca.marca_id,
                'ventas_mensuales': ventas_mensuales,
                'resumen_anual': {
                    'total_ventas_anuales': total_anual,
                    'promedio_mensual': promedio,
                }
            }

        except Marca.DoesNotExist:
            logger.error(f"Marca no encontrada: {marca_id}")
            raise FileNotFoundError(f"Marca no encontrada: {marca_id}")
        except Exception as e:
            logger.error(f"Error cargando datos de ventas de {marca_id}: {e}")
            raise

    def cargar_marca_administrativo(self, marca_id: str) -> Dict[str, Any]:
        """Carga los datos administrativos de una marca desde PostgreSQL"""
        try:
            marca = Marca.objects.get(marca_id=marca_id)

            # Cargar personal administrativo
            personal_dict = []
            try:
                personal_qs = PersonalAdministrativo.objects.filter(marca=marca, **self._get_filter_kwargs())

                for p in personal_qs:
                    try:
                        personal_dict.append({
                            'tipo': p.tipo,
                            'nombre': p.nombre if p.nombre else '',
                            'cantidad': p.cantidad,
                            'salario_base': float(p.salario_base) if p.salario_base else 0,
                            'perfil_prestacional': p.perfil_prestacional,
                            'tipo_contrato': p.tipo_contrato,
                            'honorarios_mensuales': float(p.honorarios_mensuales) if p.honorarios_mensuales else 0,
                            'auxilio_adicional': float(p.auxilio_adicional) if p.auxilio_adicional else 0,
                            'asignacion': p.asignacion,
                            'criterio_prorrateo': p.criterio_prorrateo,
                            'costo_mensual_calculado': float(p.calcular_costo_mensual()),
                        })
                    except Exception as e:
                        logger.warning(f"Error procesando personal administrativo {p.id}: {e}")
                        continue
            except Exception as e:
                logger.warning(f"Error cargando personal administrativo de {marca_id}: {e}")

            # Cargar gastos administrativos
            gastos_dict = []
            try:
                gastos_qs = GastoAdministrativo.objects.filter(marca=marca, **self._get_filter_kwargs())

                for gasto in gastos_qs:
                    try:
                        gastos_dict.append({
                            'tipo': gasto.tipo,
                            'nombre': gasto.nombre,
                            'valor_mensual': float(gasto.valor_mensual),
                            'asignacion': gasto.asignacion,
                            'criterio_prorrateo': gasto.criterio_prorrateo if gasto.asignacion == 'compartido' else None,
                        })
                    except Exception as e:
                        logger.warning(f"Error procesando gasto administrativo {gasto.id}: {e}")
                        continue
            except Exception as e:
                logger.warning(f"Error cargando gastos administrativos de {marca_id}: {e}")

            logger.info(f"[DEBUG] Personal administrativo de {marca_id}: {len(personal_dict)}")
            logger.info(f"[DEBUG] Gastos administrativos de {marca_id}: {len(gastos_dict)}")

            return {
                'marca_id': marca.marca_id,
                'personal': personal_dict,
                'gastos': gastos_dict,
            }

        except Marca.DoesNotExist:
            logger.warning(f"Marca no encontrada: {marca_id}, retornando datos vacíos")
            return {
                'marca_id': marca_id,
                'personal': [],
                'gastos': [],
            }
        except Exception as e:
            logger.error(f"Error cargando datos administrativos de {marca_id}: {e}")
            # No romper la simulación, retornar estructura vacía
            return {
                'marca_id': marca_id,
                'personal': [],
                'gastos': [],
            }

    def cargar_marca_completa(self, marca_id: str) -> Dict[str, Any]:
        """Carga todos los datos de una marca"""
        return {
            'marca_id': marca_id,
            'comercial': self.cargar_marca_comercial(marca_id),
            'logistica': self.cargar_marca_logistica(marca_id),
            'administrativo': self.cargar_marca_administrativo(marca_id),
            'ventas': self.cargar_marca_ventas(marca_id)
        }

    def listar_marcas(self) -> List[str]:
        """Lista todas las marcas activas"""
        return list(Marca.objects.filter(activa=True).values_list('marca_id', flat=True))

    def listar_escenarios(self) -> List[Dict[str, Any]]:
        """Lista todos los escenarios disponibles"""
        escenarios = Escenario.objects.all().order_by('-anio', '-id')
        return [
            {
                'id': e.id,
                'nombre': e.nombre,
                'anio': e.anio,
                'tipo': e.tipo,
                'activo': e.activo,
                'periodo': f"{e.periodo_tipo} {e.periodo_numero or ''}".strip()
            }
            for e in escenarios
        ]

    # =========================================================================
    # DATOS COMPARTIDOS
    # =========================================================================

    def cargar_compartidos_administrativo(self) -> Dict[str, Any]:
        """Carga recursos administrativos compartidos desde PostgreSQL"""
        try:
            # Cargar personal administrativo compartido (asignacion='compartido')
            personal_qs = PersonalAdministrativo.objects.filter(asignacion='compartido', **self._get_filter_kwargs())

            personal_administrativo = {}
            for p in personal_qs:
                # Usar el nombre o tipo como key
                key = p.nombre if p.nombre else p.tipo
                personal_administrativo[key] = {
                    'tipo': p.tipo,
                    'nombre': p.nombre,
                    'cantidad': p.cantidad,
                    'salario_base': float(p.salario_base) if p.salario_base else 0,
                    'perfil_prestacional': p.perfil_prestacional,
                    'tipo_contrato': p.tipo_contrato,
                    'honorarios_mensuales': float(p.honorarios_mensuales) if p.honorarios_mensuales else 0,
                    'criterio_prorrateo': p.criterio_prorrateo,
                    'costo_mensual_calculado': float(p.calcular_costo_mensual()),
                }

            # Cargar gastos administrativos compartidos
            gastos_qs = GastoAdministrativo.objects.filter(asignacion='compartido', **self._get_filter_kwargs())

            gastos_administrativos = []
            for gasto in gastos_qs:
                gastos_administrativos.append({
                    'tipo': gasto.tipo,
                    'nombre': gasto.nombre,
                    'valor_mensual': float(gasto.valor_mensual),
                    'asignacion': gasto.asignacion,
                    'criterio_prorrateo': gasto.criterio_prorrateo,
                })

            logger.info(f"[DEBUG] Personal administrativo compartido: {len(personal_administrativo)}")
            logger.info(f"[DEBUG] Gastos administrativos compartidos: {len(gastos_administrativos)}")

            return {
                'personal_administrativo': personal_administrativo,
                'gastos_administrativos': gastos_administrativos,
            }

        except Exception as e:
            logger.error(f"Error cargando datos administrativos compartidos: {e}")
            # Fallback a estructura vacía
            return {
                'personal_administrativo': {},
                'gastos_administrativos': [],
            }

    def cargar_compartidos_logistica(self) -> Dict[str, Any]:
        """Carga recursos logísticos compartidos (mantiene compatibilidad)"""
        # Por ahora, cargar desde YAML original
        from .loaders import DataLoader
        yaml_loader = DataLoader()
        try:
            return yaml_loader.cargar_compartidos_logistica()
        except FileNotFoundError:
            return {}


def get_loader_db(escenario_id: Optional[int] = None):
    """Factory function para obtener el loader de base de datos"""
    return DataLoaderDB(escenario_id=escenario_id)
