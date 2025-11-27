"""
Calculadora de Lejanías (Gastos Variables por Ruta)

Calcula gastos de:
- Combustible (según distancia y rendimiento)
- Peajes (solo logística)
- Pernocta (alojamiento, alimentación, parqueadero)

Para:
- Comerciales: Por Zona Comercial (vendedor visita municipios)
- Logísticos: Por Ruta Logística (vehículo/tercero entrega a municipios)
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

    # =========================================================================
    # LEJANÍAS COMERCIALES (Por Zona Comercial - Vendedores)
    # =========================================================================

    def calcular_lejania_comercial_zona(self, zona) -> Dict:
        """
        Calcula lejanía comercial mensual para una zona

        Args:
            zona: Instancia de Zona (comercial)

        Returns:
            {
                'combustible_mensual': Decimal,
                'pernocta_mensual': Decimal,
                'total_mensual': Decimal,
                'detalle': {...}
            }
        """
        if not self.config or not self.params_macro:
            return self._resultado_vacio_comercial()

        from core.models import MatrizDesplazamiento

        combustible_total = Decimal('0')
        pernocta_total = Decimal('0')
        detalle_municipios = []

        # Base del vendedor (desde donde parte)
        base_vendedor = zona.municipio_base_vendedor or self.config.municipio_bodega
        if not base_vendedor:
            logger.warning(f"Zona {zona} no tiene base de vendedor ni bodega configurada")
            return self._resultado_vacio_comercial()

        # Consumo según tipo de vehículo
        if zona.tipo_vehiculo_comercial == 'MOTO':
            consumo_km_galon = self.config.consumo_galon_km_moto
        else:  # AUTOMOVIL
            consumo_km_galon = self.config.consumo_galon_km_automovil

        # Precio gasolina (comerciales usan gasolina)
        precio_galon = self.params_macro.precio_galon_gasolina

        # Calcular para cada municipio de la zona (usando related_name 'municipios')
        for zona_mun in zona.municipios.all():
            municipio = zona_mun.municipio

            # Buscar ruta en matriz (por ID para evitar problemas de comparación de objetos)
            try:
                matriz = MatrizDesplazamiento.objects.get(
                    origen_id=base_vendedor.id,
                    destino_id=municipio.id
                )
            except MatrizDesplazamiento.DoesNotExist:
                logger.warning(f"No existe ruta {base_vendedor.nombre} (ID:{base_vendedor.id}) → {municipio.nombre} (ID:{municipio.id})")
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

            detalle_municipios.append({
                'municipio': municipio.nombre,
                'municipio_id': municipio.id,
                'distancia_km': float(matriz.distancia_km),
                'visitas_mensuales': float(visitas_mensuales),
                'combustible_mensual': float(combustible_municipio),
            })

        # Pernocta se calcula a nivel de ZONA (una vez por viaje, no por municipio)
        if zona.requiere_pernocta and zona.noches_pernocta > 0:
            gasto_por_noche = (
                self.config.desayuno_comercial +
                self.config.almuerzo_comercial +
                self.config.cena_comercial +
                self.config.alojamiento_comercial
            )
            # Pernocta = noches × gasto_por_noche × viajes_por_mes
            periodos_mes = zona.periodos_por_mes()
            pernocta_total = gasto_por_noche * zona.noches_pernocta * periodos_mes

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

    def calcular_lejanias_comerciales_marca(self, marca) -> Dict:
        """
        Calcula todas las lejanías comerciales para una marca

        Returns:
            {
                'total_combustible_mensual': Decimal,
                'total_pernocta_mensual': Decimal,
                'total_mensual': Decimal,
                'total_anual': Decimal,
                'zonas': [...]
            }
        """
        from core.models import Zona

        zonas = Zona.objects.filter(
            marca=marca,
            escenario=self.escenario,
            activo=True
        ).prefetch_related('municipios__municipio').select_related('vendedor', 'municipio_base_vendedor')

        total_combustible = Decimal('0')
        total_pernocta = Decimal('0')
        detalle_zonas = []

        for zona in zonas:
            resultado = self.calcular_lejania_comercial_zona(zona)
            total_combustible += resultado['combustible_mensual']
            total_pernocta += resultado['pernocta_mensual']

            detalle_zonas.append({
                'zona_id': zona.id,
                'zona_nombre': zona.nombre,
                'vendedor': zona.vendedor.nombre if zona.vendedor else None,
                'tipo_vehiculo': zona.tipo_vehiculo_comercial,
                'frecuencia': zona.frecuencia,
                'requiere_pernocta': zona.requiere_pernocta,
                'noches_pernocta': zona.noches_pernocta,
                'combustible_mensual': float(resultado['combustible_mensual']),
                'pernocta_mensual': float(resultado['pernocta_mensual']),
                'total_mensual': float(resultado['total_mensual']),
                'detalle': resultado['detalle'],
            })

        total_mensual = total_combustible + total_pernocta

        return {
            'total_combustible_mensual': total_combustible,
            'total_pernocta_mensual': total_pernocta,
            'total_mensual': total_mensual,
            'total_anual': total_mensual * 12,
            'zonas': detalle_zonas,
        }

    # =========================================================================
    # LEJANÍAS LOGÍSTICAS (Por Ruta Logística - Vehículos/Terceros)
    # =========================================================================

    def calcular_lejania_logistica_ruta(self, ruta) -> Dict:
        """
        Calcula lejanía logística mensual para una ruta

        Args:
            ruta: Instancia de RutaLogistica

        Returns:
            {
                'flete_base_mensual': Decimal,
                'combustible_mensual': Decimal,
                'peaje_mensual': Decimal,
                'pernocta_mensual': Decimal,
                'total_mensual': Decimal,
                'detalle': {...}
            }
        """
        if not self.config or not self.params_macro:
            return self._resultado_vacio_logistica()

        from core.models import MatrizDesplazamiento

        flete_base_total = Decimal('0')
        combustible_total = Decimal('0')
        peaje_total = Decimal('0')
        pernocta_total = Decimal('0')
        detalle_municipios = []

        # Bodega (desde donde parten los vehículos)
        bodega = self.config.municipio_bodega
        if not bodega:
            logger.warning(f"No hay bodega configurada para el escenario {self.escenario}")
            return self._resultado_vacio_logistica()

        # Vehículo de la ruta
        vehiculo = ruta.vehiculo
        if not vehiculo:
            logger.warning(f"Ruta {ruta} no tiene vehículo asignado")
            return self._resultado_vacio_logistica()

        # Consumo y precio según vehículo
        consumo_km_galon = vehiculo.consumo_galon_km or Decimal('30')
        if vehiculo.tipo_combustible == 'gasolina':
            precio_galon = self.params_macro.precio_galon_gasolina
        else:  # acpm
            precio_galon = self.params_macro.precio_galon_acpm
        tipo_combustible = vehiculo.tipo_combustible
        esquema_vehiculo = vehiculo.esquema

        # Calcular para cada municipio de la ruta (usando related_name 'municipios')
        for ruta_mun in ruta.municipios.all():
            municipio = ruta_mun.municipio

            # Buscar ruta en matriz (por ID para evitar problemas de comparación de objetos)
            try:
                matriz = MatrizDesplazamiento.objects.get(
                    origen_id=bodega.id,
                    destino_id=municipio.id
                )
            except MatrizDesplazamiento.DoesNotExist:
                logger.warning(f"No existe ruta {bodega.nombre} (ID:{bodega.id}) → {municipio.nombre} (ID:{municipio.id})")
                continue

            # Aplicar umbral
            if matriz.distancia_km < self.config.umbral_lejania_logistica_km:
                continue  # No aplica lejanía

            # Entregas mensuales
            entregas_mensuales = ruta_mun.entregas_mensuales()

            # Flete base (para terceros principalmente)
            flete_base_municipio = ruta_mun.flete_base or Decimal('0')
            flete_base_total += flete_base_municipio * entregas_mensuales

            # Combustible (aplica para propios y renting, no para terceros)
            combustible_municipio = Decimal('0')
            if esquema_vehiculo in ['tradicional', 'renting']:
                distancia_ida_vuelta = matriz.distancia_km * 2
                galones_por_entrega = distancia_ida_vuelta / consumo_km_galon
                costo_combustible_entrega = galones_por_entrega * precio_galon
                combustible_municipio = costo_combustible_entrega * entregas_mensuales
                combustible_total += combustible_municipio

            # Peajes (aplica para propios y renting)
            peaje_municipio = Decimal('0')
            if esquema_vehiculo in ['tradicional', 'renting']:
                peaje_por_entrega = (matriz.peaje_ida or Decimal('0')) + (matriz.peaje_vuelta or Decimal('0'))
                peaje_municipio = peaje_por_entrega * entregas_mensuales
                peaje_total += peaje_municipio

            # Pernocta (si la ruta lo requiere o es muy larga)
            pernocta_municipio = Decimal('0')
            requiere_pernocta_mun = ruta.requiere_pernocta or matriz.distancia_km > 150 or matriz.tiempo_minutos > 240

            if requiere_pernocta_mun:
                noches = ruta.noches_pernocta if ruta.noches_pernocta > 0 else 1
                gasto_por_noche = (
                    self.config.desayuno_logistica +
                    self.config.almuerzo_logistica +
                    self.config.cena_logistica +
                    self.config.alojamiento_logistica +
                    self.config.parqueadero_logistica
                )
                pernocta_municipio = gasto_por_noche * noches * entregas_mensuales
                pernocta_total += pernocta_municipio

            detalle_municipios.append({
                'municipio': municipio.nombre,
                'municipio_id': municipio.id,
                'distancia_km': float(matriz.distancia_km),
                'tiempo_minutos': matriz.tiempo_minutos,
                'entregas_mensuales': float(entregas_mensuales),
                'flete_base': float(flete_base_municipio),
                'combustible_mensual': float(combustible_municipio),
                'peaje_mensual': float(peaje_municipio),
                'pernocta_mensual': float(pernocta_municipio),
                'requiere_pernocta': requiere_pernocta_mun,
            })

        total = flete_base_total + combustible_total + peaje_total + pernocta_total

        return {
            'flete_base_mensual': flete_base_total,
            'combustible_mensual': combustible_total,
            'peaje_mensual': peaje_total,
            'pernocta_mensual': pernocta_total,
            'total_mensual': total,
            'detalle': {
                'bodega': bodega.nombre,
                'vehiculo': str(vehiculo),
                'vehiculo_id': vehiculo.id,
                'esquema': esquema_vehiculo,
                'tipo_vehiculo': vehiculo.tipo_vehiculo,
                'tipo_combustible': tipo_combustible,
                'consumo_km_galon': float(consumo_km_galon),
                'precio_galon': float(precio_galon),
                'umbral_km': self.config.umbral_lejania_logistica_km,
                'municipios': detalle_municipios,
                'es_constitutiva_salario': self.config.es_constitutiva_salario_logistica,
            }
        }

    def calcular_lejanias_logisticas_marca(self, marca) -> Dict:
        """
        Calcula todas las lejanías logísticas para una marca (por ruta/vehículo)

        Returns:
            {
                'total_flete_base_mensual': Decimal,
                'total_combustible_mensual': Decimal,
                'total_peaje_mensual': Decimal,
                'total_pernocta_mensual': Decimal,
                'total_mensual': Decimal,
                'total_anual': Decimal,
                'rutas': [...]
            }
        """
        from core.models import RutaLogistica

        rutas = RutaLogistica.objects.filter(
            marca=marca,
            escenario=self.escenario,
            activo=True
        ).prefetch_related('municipios__municipio').select_related('vehiculo')

        total_flete_base = Decimal('0')
        total_combustible = Decimal('0')
        total_peaje = Decimal('0')
        total_pernocta = Decimal('0')
        detalle_rutas = []

        for ruta in rutas:
            resultado = self.calcular_lejania_logistica_ruta(ruta)
            total_flete_base += resultado['flete_base_mensual']
            total_combustible += resultado['combustible_mensual']
            total_peaje += resultado['peaje_mensual']
            total_pernocta += resultado['pernocta_mensual']

            detalle_rutas.append({
                'ruta_id': ruta.id,
                'ruta_nombre': ruta.nombre,
                'vehiculo': str(ruta.vehiculo) if ruta.vehiculo else None,
                'vehiculo_id': ruta.vehiculo.id if ruta.vehiculo else None,
                'esquema': ruta.vehiculo.esquema if ruta.vehiculo else None,
                'tipo_vehiculo': ruta.vehiculo.tipo_vehiculo if ruta.vehiculo else None,
                'frecuencia': ruta.frecuencia,
                'requiere_pernocta': ruta.requiere_pernocta,
                'noches_pernocta': ruta.noches_pernocta,
                'flete_base_mensual': float(resultado['flete_base_mensual']),
                'combustible_mensual': float(resultado['combustible_mensual']),
                'peaje_mensual': float(resultado['peaje_mensual']),
                'pernocta_mensual': float(resultado['pernocta_mensual']),
                'total_mensual': float(resultado['total_mensual']),
                'detalle': resultado['detalle'],
            })

        total_mensual = total_flete_base + total_combustible + total_peaje + total_pernocta

        return {
            'total_flete_base_mensual': total_flete_base,
            'total_combustible_mensual': total_combustible,
            'total_peaje_mensual': total_peaje,
            'total_pernocta_mensual': total_pernocta,
            'total_mensual': total_mensual,
            'total_anual': total_mensual * 12,
            'rutas': detalle_rutas,
        }

    # =========================================================================
    # MÉTODO COMBINADO (Para el simulador)
    # =========================================================================

    def calcular_lejanias_marca(self, marca) -> Dict:
        """
        Calcula todas las lejanías (comerciales + logísticas) para una marca

        Returns:
            {
                'comercial': {...},
                'logistica': {...},
                'total_mensual': Decimal,
                'total_anual': Decimal
            }
        """
        comercial = self.calcular_lejanias_comerciales_marca(marca)
        logistica = self.calcular_lejanias_logisticas_marca(marca)

        total_mensual = comercial['total_mensual'] + logistica['total_mensual']

        return {
            'comercial': comercial,
            'logistica': logistica,
            'total_mensual': total_mensual,
            'total_anual': total_mensual * 12,
        }

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _resultado_vacio_comercial(self) -> Dict:
        """Retorna resultado vacío para lejanías comerciales"""
        return {
            'combustible_mensual': Decimal('0'),
            'pernocta_mensual': Decimal('0'),
            'total_mensual': Decimal('0'),
            'detalle': {}
        }

    def _resultado_vacio_logistica(self) -> Dict:
        """Retorna resultado vacío para lejanías logísticas"""
        return {
            'flete_base_mensual': Decimal('0'),
            'combustible_mensual': Decimal('0'),
            'peaje_mensual': Decimal('0'),
            'pernocta_mensual': Decimal('0'),
            'total_mensual': Decimal('0'),
            'detalle': {}
        }

    # Mantener compatibilidad con código existente
    def calcular_lejania_logistica_zona(self, zona, vehiculo=None) -> Dict:
        """
        DEPRECATED: Usar calcular_lejania_logistica_ruta() en su lugar.
        Mantiene compatibilidad temporal.
        """
        logger.warning("calcular_lejania_logistica_zona está deprecado. Usar calcular_lejania_logistica_ruta()")
        return self._resultado_vacio_logistica()
