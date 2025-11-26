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
    Vehiculo, ProyeccionVentas, VolumenOperacion,
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
        """Carga los factores prestacionales"""
        try:
            factores = FactorPrestacional.objects.all()
            result = {}

            for factor in factores:
                result[factor.perfil] = {
                    'salud': float(factor.salud),
                    'pension': float(factor.pension),
                    'arl': float(factor.arl),
                    'caja_compensacion': float(factor.caja_compensacion),
                    'icbf': float(factor.icbf),
                    'sena': float(factor.sena),
                    'cesantias': float(factor.cesantias),
                    'intereses_cesantias': float(factor.intereses_cesantias),
                    'prima': float(factor.prima),
                    'vacaciones': float(factor.vacaciones),
                    'factor_total': float(factor.factor_total),
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

            # Cargar proyección de ventas
            # Nota: ProyeccionVentas también tiene escenario ahora
            proyecciones = ProyeccionVentas.objects.filter(marca=marca, **self._get_filter_kwargs())
            
            total_ventas_anuales = 0
            if proyecciones.exists():
                total_ventas_anuales = sum(p.ventas for p in proyecciones)
            else:
                # Fallback a lógica anterior si no hay proyecciones por escenario (aunque deberían haber)
                # Si no hay proyecciones específicas del escenario, buscar cualquiera del año
                escenario = self._get_escenario()
                if escenario:
                    proyecciones = ProyeccionVentas.objects.filter(marca=marca, anio=escenario.anio)
                    total_ventas_anuales = sum(p.ventas for p in proyecciones)

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
            gastos_comerciales = []
            gastos_qs = GastoComercial.objects.filter(marca=marca, **self._get_filter_kwargs())

            for gasto in gastos_qs:
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
                    'tipo': v.tipo_vehiculo,
                    'cantidad': v.cantidad,
                    'asignacion': v.asignacion,
                    'kilometraje_promedio_mensual': v.kilometraje_promedio_mensual,
                    'porcentaje_uso': float(v.porcentaje_uso) if v.porcentaje_uso else None,
                    'criterio_prorrateo': v.criterio_prorrateo,
                    'costo_mensual_calculado': float(v.calcular_costo_mensual()),  # ⭐ USAR método del modelo (incluye seguro mercancía)
                    # Campos adicionales para referencia
                    'costo_seguro_mercancia_mensual': float(v.costo_seguro_mercancia_mensual) if v.costo_seguro_mercancia_mensual else 0,
                    'costo_monitoreo_mensual': float(v.costo_monitoreo_mensual) if v.costo_monitoreo_mensual else 0,
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
                    'porcentaje_dedicacion': float(p.porcentaje_dedicacion) if p.porcentaje_dedicacion else None,
                    'criterio_prorrateo': p.criterio_prorrateo,
                    'costo_mensual_calculado': float(p.calcular_costo_mensual()),  # ⭐ USAR método del modelo
                })

            # Cargar volumen de operación
            try:
                volumen = VolumenOperacion.objects.get(marca=marca)
                proyeccion_volumen = {
                    'pallets_mensuales': volumen.pallets_mensuales,
                    'metros_cubicos_mensuales': float(volumen.metros_cubicos_mensuales),
                    'toneladas_mensuales': float(volumen.toneladas_mensuales),
                    'entregas_mensuales': volumen.entregas_mensuales,
                }
            except VolumenOperacion.DoesNotExist:
                proyeccion_volumen = {}

            # Cargar gastos logísticos
            gastos_logisticos = []
            gastos_qs = GastoLogistico.objects.filter(marca=marca, **self._get_filter_kwargs())

            for gasto in gastos_qs:
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
                'proyeccion_volumen': proyeccion_volumen,
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
            proyecciones = ProyeccionVentas.objects.filter(marca=marca, **self._get_filter_kwargs()).order_by('mes')
            
            if not proyecciones.exists():
                 # Fallback
                escenario = self._get_escenario()
                if escenario:
                     proyecciones = ProyeccionVentas.objects.filter(marca=marca, anio=escenario.anio).order_by('mes')

            ventas_mensuales = {}
            for p in proyecciones:
                ventas_mensuales[p.mes] = float(p.ventas)

            total_anual = sum(ventas_mensuales.values())
            promedio = total_anual / len(ventas_mensuales) if ventas_mensuales else 0

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
                            'salario_base': float(p.salario_base),
                            'perfil_prestacional': p.perfil_prestacional,
                            'asignacion': p.asignacion,
                            'porcentaje_dedicacion': float(p.porcentaje_dedicacion) if p.porcentaje_dedicacion else None,
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
                    'salario_base': float(p.salario_base),
                    'perfil_prestacional': p.perfil_prestacional,
                    'tipo_contrato': 'nomina',  # Puede ser 'honorarios' o 'nomina'
                    'criterio_prorrateo': p.criterio_prorrateo,
                    'porcentaje_dedicacion': float(p.porcentaje_dedicacion) if p.porcentaje_dedicacion else None,
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
