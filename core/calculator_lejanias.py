"""
Calculadora de Lejanías (Gastos Variables por Ruta)

Calcula gastos de:
- Combustible (según distancia y rendimiento)
- Pernocta (alojamiento, alimentación, parqueadero)

Para:
- Comerciales (desde base del vendedor)
- Logísticos (desde bodega)
"""
from decimal import Decimal
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class CalculadoraLejanias:
    """
    Calcula gastos de lejanías comerciales y logísticas
    """

    def __init__(self, escenario):
        """
        Args:
            escenario: Instancia de Escenario con configuración y parámetros macro
        """
        self.escenario = escenario

        # Cargar configuración de lejanías
        try:
            from core.models import ConfiguracionLejania, ParametrosMacro
            self.config = ConfiguracionLejania.objects.get(escenario=escenario)
            self.params_macro = ParametrosMacro.objects.get(anio=escenario.anio, activo=True)
        except Exception as e:
            logger.warning(f"No se pudo cargar configuración de lejanías para {escenario}: {e}")
            self.config = None
            self.params_macro = None

    def calcular_lejania_comercial_zona(self, zona) -> Dict[str, Decimal]:
        """
        Calcula lejanía comercial mensual para una zona

        Args:
            zona: Instancia de Zona

        Returns:
            {
                'combustible_mensual': Decimal,
                'pernocta_mensual': Decimal,
                'total_mensual': Decimal,
                'detalle': {...}
            }
        """
        if not self.config or not self.params_macro:
            return self._resultado_vacio()

        from core.models import MatrizDesplazamiento

        combustible_total = Decimal('0')
        pernocta_total = Decimal('0')
        detalle_municipios = []

        # Base del vendedor (desde donde parte)
        base_vendedor = zona.municipio_base_vendedor or self.config.municipio_bodega
        if not base_vendedor:
            logger.warning(f"Zona {zona} no tiene base de vendedor ni bodega configurada")
            return self._resultado_vacio()

        # Consumo según tipo de vehículo
        if zona.tipo_vehiculo_comercial == 'MOTO':
            consumo_km_galon = self.config.consumo_galon_km_moto
        else:  # AUTOMOVIL
            consumo_km_galon = self.config.consumo_galon_km_automovil

        # Precio gasolina (comerciales usan gasolina)
        precio_galon = self.params_macro.precio_galon_gasolina

        # Calcular para cada municipio de la zona
        for zona_mun in zona.zonamunicipio_set.all():
            municipio = zona_mun.municipio

            # Buscar ruta en matriz
            try:
                matriz = MatrizDesplazamiento.objects.get(
                    origen=base_vendedor,
                    destino=municipio
                )
            except MatrizDesplazamiento.DoesNotExist:
                logger.warning(f"No existe ruta {base_vendedor} → {municipio}")
                continue

            # Aplicar umbral
            if matriz.distancia_km < self.config.umbral_lejania_comercial_km:
                continue  # No aplica lejanía

            # Calcular combustible por visita (ida y vuelta)
            distancia_ida_vuelta = matriz.distancia_km * 2
            galones_por_visita = distancia_ida_vuelta / consumo_km_galon
            costo_combustible_visita = galones_por_visita * precio_galon

            # Visitas mensuales
            visitas_mensuales = zona_mun.visitas_mensuales()
            combustible_municipio = costo_combustible_visita * visitas_mensuales

            combustible_total += combustible_municipio

            # Pernocta (si aplica)
            pernocta_municipio = Decimal('0')
            if zona.requiere_pernocta and zona.noches_pernocta > 0:
                # Gastos por noche
                gasto_por_noche = (
                    self.config.desayuno_comercial +
                    self.config.almuerzo_comercial +
                    self.config.cena_comercial +
                    self.config.alojamiento_comercial
                )

                # Calcular según frecuencia de zona
                periodos_mes = zona.periodos_por_mes()
                pernocta_municipio = gasto_por_noche * zona.noches_pernocta * periodos_mes
                pernocta_total += pernocta_municipio

            detalle_municipios.append({
                'municipio': municipio.nombre,
                'distancia_km': float(matriz.distancia_km),
                'visitas_mensuales': visitas_mensuales,
                'combustible_mensual': float(combustible_municipio),
                'pernocta_mensual': float(pernocta_municipio),
            })

        total = combustible_total + pernocta_total

        return {
            'combustible_mensual': combustible_total,
            'pernocta_mensual': pernocta_total,
            'total_mensual': total,
            'detalle': {
                'base': base_vendedor.nombre,
                'tipo_vehiculo': zona.tipo_vehiculo_comercial,
                'consumo_km_galon': float(consumo_km_galon),
                'precio_galon': float(precio_galon),
                'umbral_km': self.config.umbral_lejania_comercial_km,
                'municipios': detalle_municipios,
                'es_constitutiva_salario': self.config.es_constitutiva_salario_comercial,
            }
        }

    def calcular_lejania_logistica_zona(self, zona, vehiculo=None) -> Dict[str, Decimal]:
        """
        Calcula lejanía logística mensual para una zona

        Args:
            zona: Instancia de Zona
            vehiculo: Instancia opcional de Vehiculo (para usar su consumo específico)

        Returns:
            {
                'combustible_mensual': Decimal,
                'pernocta_mensual': Decimal,
                'total_mensual': Decimal,
                'detalle': {...}
            }
        """
        if not self.config or not self.params_macro:
            return self._resultado_vacio()

        from core.models import MatrizDesplazamiento

        combustible_total = Decimal('0')
        pernocta_total = Decimal('0')
        detalle_municipios = []

        # Bodega (desde donde parten los vehículos)
        bodega = self.config.municipio_bodega
        if not bodega:
            logger.warning(f"No hay bodega configurada para el escenario {self.escenario}")
            return self._resultado_vacio()

        # Consumo y precio según vehículo
        if vehiculo:
            consumo_km_galon = vehiculo.consumo_galon_km
            # Precio según tipo de combustible del vehículo
            if vehiculo.tipo_combustible == 'gasolina':
                precio_galon = self.params_macro.precio_galon_gasolina
            else:  # acpm
                precio_galon = self.params_macro.precio_galon_acpm
            tipo_combustible = vehiculo.tipo_combustible
        else:
            # Usar defaults (NHR típico)
            consumo_km_galon = Decimal('35')  # NHR ~35 km/gal ACPM
            precio_galon = self.params_macro.precio_galon_acpm
            tipo_combustible = 'acpm'

        # Calcular para cada municipio de la zona
        for zona_mun in zona.zonamunicipio_set.all():
            municipio = zona_mun.municipio

            # Buscar ruta en matriz
            try:
                matriz = MatrizDesplazamiento.objects.get(
                    origen=bodega,
                    destino=municipio
                )
            except MatrizDesplazamiento.DoesNotExist:
                logger.warning(f"No existe ruta {bodega} → {municipio}")
                continue

            # Aplicar umbral
            if matriz.distancia_km < self.config.umbral_lejania_logistica_km:
                continue  # No aplica lejanía

            # Calcular combustible por entrega (ida y vuelta)
            distancia_ida_vuelta = matriz.distancia_km * 2
            galones_por_entrega = distancia_ida_vuelta / consumo_km_galon
            costo_combustible_entrega = galones_por_entrega * precio_galon

            # Entregas mensuales
            entregas_mensuales = zona_mun.entregas_mensuales()
            combustible_municipio = costo_combustible_entrega * entregas_mensuales

            combustible_total += combustible_municipio

            # Pernocta (si la ruta es larga y requiere pernocta)
            pernocta_municipio = Decimal('0')
            # Asumimos pernocta si distancia > 150 km o tiempo > 4 horas
            if matriz.distancia_km > 150 or matriz.tiempo_minutos > 240:
                # Gastos por noche (incluye parqueadero para logística)
                gasto_por_noche = (
                    self.config.desayuno_logistica +
                    self.config.almuerzo_logistica +
                    self.config.cena_logistica +
                    self.config.alojamiento_logistica +
                    self.config.parqueadero_logistica
                )

                # 1 noche por entrega que requiere pernocta
                pernocta_municipio = gasto_por_noche * entregas_mensuales
                pernocta_total += pernocta_municipio

            detalle_municipios.append({
                'municipio': municipio.nombre,
                'distancia_km': float(matriz.distancia_km),
                'entregas_mensuales': entregas_mensuales,
                'combustible_mensual': float(combustible_municipio),
                'pernocta_mensual': float(pernocta_municipio),
                'requiere_pernocta': matriz.distancia_km > 150,
            })

        total = combustible_total + pernocta_total

        return {
            'combustible_mensual': combustible_total,
            'pernocta_mensual': pernocta_total,
            'total_mensual': total,
            'detalle': {
                'bodega': bodega.nombre,
                'tipo_combustible': tipo_combustible,
                'consumo_km_galon': float(consumo_km_galon),
                'precio_galon': float(precio_galon),
                'umbral_km': self.config.umbral_lejania_logistica_km,
                'municipios': detalle_municipios,
                'es_constitutiva_salario': self.config.es_constitutiva_salario_logistica,
            }
        }

    def calcular_lejanias_marca(self, marca) -> Dict[str, Dict]:
        """
        Calcula todas las lejanías para una marca

        Returns:
            {
                'comercial': {...},
                'logistica': {...},
                'total_mensual': Decimal
            }
        """
        from core.models import Zona

        # Obtener zonas de la marca para este escenario
        zonas = Zona.objects.filter(
            marca=marca,
            escenario=self.escenario,
            activo=True
        ).prefetch_related('zonamunicipio_set__municipio')

        comercial_total = Decimal('0')
        logistica_total = Decimal('0')
        detalle_zonas = []

        for zona in zonas:
            # Calcular comercial
            resultado_com = self.calcular_lejania_comercial_zona(zona)
            comercial_total += resultado_com['total_mensual']

            # Calcular logística
            resultado_log = self.calcular_lejania_logistica_zona(zona)
            logistica_total += resultado_log['total_mensual']

            detalle_zonas.append({
                'zona': zona.nombre,
                'comercial_mensual': float(resultado_com['total_mensual']),
                'logistica_mensual': float(resultado_log['total_mensual']),
            })

        return {
            'comercial': {
                'total_mensual': comercial_total,
                'total_anual': comercial_total * 12,
            },
            'logistica': {
                'total_mensual': logistica_total,
                'total_anual': logistica_total * 12,
            },
            'total_mensual': comercial_total + logistica_total,
            'total_anual': (comercial_total + logistica_total) * 12,
            'zonas': detalle_zonas,
        }

    def _resultado_vacio(self) -> Dict:
        """Retorna resultado vacío cuando no hay configuración"""
        return {
            'combustible_mensual': Decimal('0'),
            'pernocta_mensual': Decimal('0'),
            'total_mensual': Decimal('0'),
            'detalle': {}
        }
