"""
DataLoader que usa PostgreSQL a través de Django ORM
"""
from typing import Dict, List, Any, Optional
import logging

# Inicializar Django antes de importar modelos (reorganiza sys.path)
from . import django_init

# Importar modelos de Django (ahora core.models será de /app/admin_panel/core/)
from core.models import (
    Marca, PersonalComercial, PersonalLogistico,
    Vehiculo, ProyeccionVentas, VolumenOperacion,
    ParametrosMacro, FactorPrestacional
)

logger = logging.getLogger(__name__)


class DataLoaderDB:
    """
    Carga datos desde PostgreSQL usando Django ORM.

    Esta clase tiene la misma interfaz que el DataLoader original
    pero lee desde la base de datos en lugar de YAMLs.
    """

    def __init__(self):
        logger.info("DataLoaderDB inicializado (PostgreSQL)")

    # =========================================================================
    # CONFIGURACIÓN
    # =========================================================================

    def cargar_parametros_macro(self) -> Dict[str, Any]:
        """Carga los parámetros macroeconómicos activos"""
        try:
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
            personal = PersonalComercial.objects.filter(marca=marca).all()

            # DEBUG: Log para verificar qué se está leyendo
            logger.info(f"[DEBUG] Cargando personal comercial de {marca_id}")
            logger.info(f"[DEBUG] Total registros: {personal.count()}")
            for p in personal:
                logger.info(f"[DEBUG] - Tipo: {p.tipo}, Cantidad: {p.cantidad}, ID: {p.id}")

            # Calcular proyección de ventas mensual promedio
            proyecciones = ProyeccionVentas.objects.filter(marca=marca)
            if proyecciones.exists():
                ventas_promedio = sum(p.ventas for p in proyecciones) / proyecciones.count()
            else:
                ventas_promedio = 0

            # Agrupar personal por tipo
            recursos_comerciales = {}

            for p in personal:
                tipo_key = p.tipo

                if tipo_key not in recursos_comerciales:
                    recursos_comerciales[tipo_key] = []

                data = {
                    'tipo': p.tipo,
                    'cantidad': p.cantidad,
                    'salario_base': float(p.salario_base),
                    'perfil_prestacional': p.perfil_prestacional,
                    'asignacion': p.asignacion,
                    'auxilio_adicional': float(p.auxilio_adicional) if p.auxilio_adicional else 0,
                    'porcentaje_dedicacion': float(p.porcentaje_dedicacion) if p.porcentaje_dedicacion else None,
                    'criterio_prorrateo': p.criterio_prorrateo,
                }

                logger.info(f"[DEBUG] Agregando {p.tipo}: cantidad={p.cantidad}")
                recursos_comerciales[tipo_key].append(data)

            return {
                'marca_id': marca.marca_id,
                'nombre': marca.nombre,
                'proyeccion_ventas_mensual': float(ventas_promedio),
                'recursos_comerciales': recursos_comerciales,
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
            vehiculos = Vehiculo.objects.filter(marca=marca)
            vehiculos_dict = {'renting': [], 'tradicional': []}

            for v in vehiculos:
                vehiculo_data = {
                    'tipo': v.tipo_vehiculo,
                    'cantidad': v.cantidad,
                    'asignacion': v.asignacion,
                    'kilometraje_promedio_mensual': v.kilometraje_promedio_mensual,
                    'porcentaje_uso': float(v.porcentaje_uso) if v.porcentaje_uso else None,
                    'criterio_prorrateo': v.criterio_prorrateo,
                }
                vehiculos_dict[v.esquema].append(vehiculo_data)

            # Cargar personal logístico
            personal = PersonalLogistico.objects.filter(marca=marca)
            personal_dict = {}

            for p in personal:
                tipo_key = p.tipo if not p.tipo.endswith('s') else p.tipo + 'es'

                if tipo_key not in personal_dict:
                    personal_dict[tipo_key] = []

                personal_dict[tipo_key].append({
                    'cantidad': p.cantidad,
                    'salario_base': float(p.salario_base),
                    'perfil_prestacional': p.perfil_prestacional,
                    'asignacion': p.asignacion,
                    'porcentaje_dedicacion': float(p.porcentaje_dedicacion) if p.porcentaje_dedicacion else None,
                    'criterio_prorrateo': p.criterio_prorrateo,
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

            return {
                'marca_id': marca.marca_id,
                'vehiculos': vehiculos_dict,
                'personal': personal_dict,
                'proyeccion_volumen': proyeccion_volumen,
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
            proyecciones = ProyeccionVentas.objects.filter(marca=marca).order_by('mes')

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

    def cargar_marca_completa(self, marca_id: str) -> Dict[str, Any]:
        """Carga todos los datos de una marca"""
        return {
            'marca_id': marca_id,
            'comercial': self.cargar_marca_comercial(marca_id),
            'logistica': self.cargar_marca_logistica(marca_id),
            'ventas': self.cargar_marca_ventas(marca_id)
        }

    def listar_marcas(self) -> List[str]:
        """Lista todas las marcas activas"""
        return list(Marca.objects.filter(activa=True).values_list('marca_id', flat=True))

    # =========================================================================
    # DATOS COMPARTIDOS
    # =========================================================================

    def cargar_compartidos_administrativo(self) -> Dict[str, Any]:
        """Carga recursos administrativos compartidos (mantiene compatibilidad)"""
        # Por ahora, cargar desde YAML original
        from .loaders import DataLoader
        yaml_loader = DataLoader()
        return yaml_loader.cargar_compartidos_administrativo()

    def cargar_compartidos_logistica(self) -> Dict[str, Any]:
        """Carga recursos logísticos compartidos (mantiene compatibilidad)"""
        # Por ahora, cargar desde YAML original
        from .loaders import DataLoader
        yaml_loader = DataLoader()
        try:
            return yaml_loader.cargar_compartidos_logistica()
        except FileNotFoundError:
            return {}


def get_loader_db():
    """Factory function para obtener el loader de base de datos"""
    return DataLoaderDB()
