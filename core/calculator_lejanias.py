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
        precio_galon = self.config.precio_galon_gasolina

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

            # Visitas mensuales
            visitas_mensuales = zona_mun.visitas_mensuales()

            # Calcular distancia efectiva para lejanía (km después del umbral)
            umbral = self.config.umbral_lejania_comercial_km
            distancia_efectiva = max(Decimal('0'), matriz.distancia_km - umbral)

            # Calcular combustible (solo km después del umbral)
            combustible_municipio = Decimal('0')
            if distancia_efectiva > 0:
                distancia_ida_vuelta = distancia_efectiva * 2
                galones_por_visita = distancia_ida_vuelta / consumo_km_galon
                costo_combustible_visita = galones_por_visita * precio_galon
                combustible_municipio = costo_combustible_visita * visitas_mensuales
                combustible_total += combustible_municipio

            detalle_municipios.append({
                'municipio': municipio.nombre,
                'municipio_id': municipio.id,
                'distancia_km': float(matriz.distancia_km),
                'distancia_efectiva_km': float(distancia_efectiva),
                'visitas_por_periodo': zona_mun.visitas_por_periodo,
                'visitas_mensuales': float(visitas_mensuales),
                'combustible_mensual': float(combustible_municipio),
            })

        # Pernocta se calcula a nivel de ZONA (una vez por viaje, no por municipio)
        detalle_pernocta = None
        if zona.requiere_pernocta and zona.noches_pernocta > 0:
            desayuno = self.config.desayuno_comercial
            almuerzo = self.config.almuerzo_comercial
            cena = self.config.cena_comercial
            alojamiento = self.config.alojamiento_comercial
            gasto_por_noche = desayuno + almuerzo + cena + alojamiento

            # Pernocta = noches × gasto_por_noche × viajes_por_mes
            periodos_mes = zona.periodos_por_mes()
            pernocta_total = gasto_por_noche * zona.noches_pernocta * periodos_mes

            detalle_pernocta = {
                'noches': zona.noches_pernocta,
                'desayuno': float(desayuno),
                'almuerzo': float(almuerzo),
                'cena': float(cena),
                'alojamiento': float(alojamiento),
                'gasto_por_noche': float(gasto_por_noche),
                'periodos_mes': float(periodos_mes),
                'total_mensual': float(pernocta_total),
            }

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
                'pernocta': detalle_pernocta,
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
        Calcula lejanía logística mensual para un recorrido (circuito)

        El cálculo usa el orden de visita para calcular distancias reales:
        Bodega → Municipio1 → Municipio2 → ... → Bodega

        Args:
            ruta: Instancia de RutaLogistica (recorrido)

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
        detalle_municipios = []
        detalle_tramos = []

        # Bodega (desde donde parten los vehículos)
        bodega = self.config.municipio_bodega
        if not bodega:
            logger.warning(f"No hay bodega configurada para el escenario {self.escenario}")
            return self._resultado_vacio_logistica()

        # Vehículo del recorrido
        vehiculo = ruta.vehiculo
        if not vehiculo:
            logger.warning(f"Recorrido {ruta} no tiene vehículo asignado")
            return self._resultado_vacio_logistica()

        # Consumo y precio según vehículo
        consumo_km_galon = vehiculo.consumo_galon_km or Decimal('30')
        if vehiculo.tipo_combustible == 'gasolina':
            precio_galon = self.config.precio_galon_gasolina
        else:  # acpm
            precio_galon = self.config.precio_galon_acpm
        tipo_combustible = vehiculo.tipo_combustible
        esquema_vehiculo = vehiculo.esquema

        # Recorridos mensuales (cuántas veces se hace el circuito completo por mes)
        recorridos_mensuales = ruta.recorridos_mensuales()

        # Obtener municipios ordenados por orden_visita
        municipios_ordenados = list(ruta.municipios.all().order_by('orden_visita'))

        if not municipios_ordenados:
            return self._resultado_vacio_logistica()

        # Calcular flete base por municipio (se suma por cada recorrido)
        for ruta_mun in municipios_ordenados:
            flete_base_municipio = ruta_mun.flete_base or Decimal('0')
            # Multiplicar por recorridos mensuales para obtener flete mensual
            flete_base_total += flete_base_municipio * recorridos_mensuales

            detalle_municipios.append({
                'orden': ruta_mun.orden_visita,
                'municipio': ruta_mun.municipio.nombre,
                'municipio_id': ruta_mun.municipio.id,
                'flete_base': float(flete_base_municipio),
            })

        # Calcular circuito: Bodega → Mun1 → Mun2 → ... → MunN → Bodega
        # Construir lista de puntos del circuito
        puntos_circuito = [bodega] + [rm.municipio for rm in municipios_ordenados] + [bodega]

        distancia_total_circuito = Decimal('0')
        peaje_total_circuito = Decimal('0')
        umbral = self.config.umbral_lejania_logistica_km

        # Calcular cada tramo del circuito
        for i in range(len(puntos_circuito) - 1):
            origen = puntos_circuito[i]
            destino = puntos_circuito[i + 1]

            try:
                matriz = MatrizDesplazamiento.objects.get(
                    origen_id=origen.id,
                    destino_id=destino.id
                )
                distancia_tramo = matriz.distancia_km
                peaje_tramo = matriz.peaje_ida or Decimal('0')
            except MatrizDesplazamiento.DoesNotExist:
                logger.warning(f"No existe tramo {origen.nombre} → {destino.nombre} en matriz")
                distancia_tramo = Decimal('0')
                peaje_tramo = Decimal('0')

            distancia_total_circuito += distancia_tramo
            peaje_total_circuito += peaje_tramo

            detalle_tramos.append({
                'origen': origen.nombre,
                'destino': destino.nombre,
                'distancia_km': float(distancia_tramo),
                'peaje': float(peaje_tramo),
            })

        # Aplicar umbral a la distancia total del circuito
        distancia_efectiva = max(Decimal('0'), distancia_total_circuito - umbral)

        # Combustible del circuito (solo km después del umbral)
        if distancia_efectiva > 0:
            galones_por_circuito = distancia_efectiva / consumo_km_galon
            costo_combustible_circuito = galones_por_circuito * precio_galon
            combustible_total = costo_combustible_circuito * recorridos_mensuales

        # Peajes del circuito
        peaje_total = peaje_total_circuito * recorridos_mensuales

        # Pernocta del recorrido (a nivel de recorrido, no municipio)
        # Se separa en conductor y auxiliar para diferenciar pagos
        pernocta_conductor_total = Decimal('0')
        pernocta_auxiliar_total = Decimal('0')
        parqueadero_total = Decimal('0')
        detalle_pernocta = None

        if ruta.requiere_pernocta and ruta.noches_pernocta > 0:
            # Gastos del conductor (en tercero, van al pago del tercero)
            desayuno_conductor = self.config.desayuno_conductor
            almuerzo_conductor = self.config.almuerzo_conductor
            cena_conductor = self.config.cena_conductor
            alojamiento_conductor = self.config.alojamiento_conductor
            gasto_conductor_noche = desayuno_conductor + almuerzo_conductor + cena_conductor + alojamiento_conductor

            # Gastos del auxiliar (siempre los paga la empresa)
            desayuno_auxiliar = self.config.desayuno_auxiliar
            almuerzo_auxiliar = self.config.almuerzo_auxiliar
            cena_auxiliar = self.config.cena_auxiliar
            alojamiento_auxiliar = self.config.alojamiento_auxiliar
            gasto_auxiliar_noche = desayuno_auxiliar + almuerzo_auxiliar + cena_auxiliar + alojamiento_auxiliar

            # Parqueadero (del vehículo)
            parqueadero = self.config.parqueadero_logistica

            pernocta_conductor_total = gasto_conductor_noche * ruta.noches_pernocta * recorridos_mensuales
            pernocta_auxiliar_total = gasto_auxiliar_noche * ruta.noches_pernocta * recorridos_mensuales
            parqueadero_total = parqueadero * ruta.noches_pernocta * recorridos_mensuales

            detalle_pernocta = {
                'noches': ruta.noches_pernocta,
                'conductor': {
                    'desayuno': float(desayuno_conductor),
                    'almuerzo': float(almuerzo_conductor),
                    'cena': float(cena_conductor),
                    'alojamiento': float(alojamiento_conductor),
                    'gasto_por_noche': float(gasto_conductor_noche),
                    'total_mensual': float(pernocta_conductor_total),
                },
                'auxiliar': {
                    'desayuno': float(desayuno_auxiliar),
                    'almuerzo': float(almuerzo_auxiliar),
                    'cena': float(cena_auxiliar),
                    'alojamiento': float(alojamiento_auxiliar),
                    'gasto_por_noche': float(gasto_auxiliar_noche),
                    'total_mensual': float(pernocta_auxiliar_total),
                },
                'parqueadero': float(parqueadero),
                'parqueadero_mensual': float(parqueadero_total),
            }

        pernocta_total = pernocta_conductor_total + pernocta_auxiliar_total + parqueadero_total
        total = flete_base_total + combustible_total + peaje_total + pernocta_total

        return {
            'flete_base_mensual': flete_base_total,
            'combustible_mensual': combustible_total,
            'peaje_mensual': peaje_total,
            'pernocta_conductor_mensual': pernocta_conductor_total,
            'pernocta_auxiliar_mensual': pernocta_auxiliar_total,
            'parqueadero_mensual': parqueadero_total,
            'pernocta_mensual': pernocta_total,  # Total para compatibilidad
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
                'recorridos_por_periodo': ruta.viajes_por_periodo,
                'recorridos_mensuales': float(recorridos_mensuales),
                'distancia_circuito_km': float(distancia_total_circuito),
                'distancia_efectiva_km': float(distancia_efectiva),
                'municipios': detalle_municipios,
                'tramos': detalle_tramos,
                'pernocta': detalle_pernocta,
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
                'total_pernocta_conductor_mensual': Decimal,
                'total_pernocta_auxiliar_mensual': Decimal,
                'total_parqueadero_mensual': Decimal,
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
        total_pernocta_conductor = Decimal('0')
        total_pernocta_auxiliar = Decimal('0')
        total_parqueadero = Decimal('0')
        total_pernocta = Decimal('0')
        detalle_rutas = []

        for ruta in rutas:
            resultado = self.calcular_lejania_logistica_ruta(ruta)
            total_flete_base += resultado['flete_base_mensual']
            total_combustible += resultado['combustible_mensual']
            total_peaje += resultado['peaje_mensual']
            total_pernocta_conductor += resultado['pernocta_conductor_mensual']
            total_pernocta_auxiliar += resultado['pernocta_auxiliar_mensual']
            total_parqueadero += resultado['parqueadero_mensual']
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
                'pernocta_conductor_mensual': float(resultado['pernocta_conductor_mensual']),
                'pernocta_auxiliar_mensual': float(resultado['pernocta_auxiliar_mensual']),
                'parqueadero_mensual': float(resultado['parqueadero_mensual']),
                'pernocta_mensual': float(resultado['pernocta_mensual']),
                'total_mensual': float(resultado['total_mensual']),
                'detalle': resultado['detalle'],
            })

        total_mensual = total_flete_base + total_combustible + total_peaje + total_pernocta

        return {
            'total_flete_base_mensual': total_flete_base,
            'total_combustible_mensual': total_combustible,
            'total_peaje_mensual': total_peaje,
            'total_pernocta_conductor_mensual': total_pernocta_conductor,
            'total_pernocta_auxiliar_mensual': total_pernocta_auxiliar,
            'total_parqueadero_mensual': total_parqueadero,
            'total_pernocta_mensual': total_pernocta,  # Total combinado para compatibilidad
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

    # =========================================================================
    # DISTRIBUCIÓN DE COSTOS LOGÍSTICOS A ZONAS COMERCIALES
    # =========================================================================

    def calcular_costos_logisticos_por_municipio(self, marca) -> Dict[int, Dict]:
        """
        Calcula el costo logístico total por municipio (flete + lejanías).

        Suma los costos de TODAS las rutas que visitan cada municipio.

        Returns:
            Dict con municipio_id como key y:
            {
                'municipio_nombre': str,
                'flete_total': Decimal,
                'combustible_total': Decimal,
                'peaje_total': Decimal,
                'pernocta_total': Decimal,
                'costo_total': Decimal,
                'rutas': [lista de rutas que lo visitan]
            }
        """
        from core.models import RutaLogistica, RutaMunicipio, MatrizDesplazamiento

        costos_por_municipio = {}

        # Obtener todas las rutas de la marca
        rutas = RutaLogistica.objects.filter(
            marca=marca,
            escenario=self.escenario,
            activo=True
        ).prefetch_related('municipios__municipio').select_related('vehiculo')

        if not self.config:
            return costos_por_municipio

        bodega = self.config.municipio_bodega
        if not bodega:
            return costos_por_municipio

        for ruta in rutas:
            vehiculo = ruta.vehiculo
            if not vehiculo:
                continue

            # Configuración del vehículo
            consumo_km_galon = vehiculo.consumo_galon_km or Decimal('30')
            if vehiculo.tipo_combustible == 'gasolina':
                precio_galon = self.config.precio_galon_gasolina
            else:
                precio_galon = self.config.precio_galon_acpm

            recorridos_mensuales = ruta.recorridos_mensuales()
            umbral = self.config.umbral_lejania_logistica_km

            # Obtener municipios ordenados
            municipios_ruta = list(ruta.municipios.all().order_by('orden_visita'))
            if not municipios_ruta:
                continue

            # Calcular el circuito completo para obtener distancia total
            puntos_circuito = [bodega] + [rm.municipio for rm in municipios_ruta] + [bodega]

            # Calcular distancia y peaje total del circuito
            distancia_total_circuito = Decimal('0')
            peaje_total_circuito = Decimal('0')

            for i in range(len(puntos_circuito) - 1):
                origen = puntos_circuito[i]
                destino = puntos_circuito[i + 1]
                try:
                    matriz = MatrizDesplazamiento.objects.get(
                        origen_id=origen.id,
                        destino_id=destino.id
                    )
                    distancia_total_circuito += matriz.distancia_km
                    peaje_total_circuito += matriz.peaje_ida or Decimal('0')
                except MatrizDesplazamiento.DoesNotExist:
                    pass

            # Calcular combustible del circuito
            distancia_efectiva = max(Decimal('0'), distancia_total_circuito - umbral)
            if distancia_efectiva > 0:
                galones_por_circuito = distancia_efectiva / consumo_km_galon
                combustible_circuito = galones_por_circuito * precio_galon * recorridos_mensuales
            else:
                combustible_circuito = Decimal('0')

            peaje_circuito = peaje_total_circuito * recorridos_mensuales

            # Calcular pernocta del circuito
            pernocta_circuito = Decimal('0')
            if ruta.requiere_pernocta and ruta.noches_pernocta > 0:
                gasto_conductor = (
                    self.config.desayuno_conductor +
                    self.config.almuerzo_conductor +
                    self.config.cena_conductor +
                    self.config.alojamiento_conductor
                )
                gasto_auxiliar = (
                    self.config.desayuno_auxiliar +
                    self.config.almuerzo_auxiliar +
                    self.config.cena_auxiliar +
                    self.config.alojamiento_auxiliar
                )
                parqueadero = self.config.parqueadero_logistica
                pernocta_circuito = (gasto_conductor + gasto_auxiliar + parqueadero) * ruta.noches_pernocta * recorridos_mensuales

            # Distribuir costos del circuito entre los municipios de la ruta
            # Usamos el flete_base como peso para distribuir
            total_flete_ruta = sum(rm.flete_base or Decimal('0') for rm in municipios_ruta)

            for ruta_mun in municipios_ruta:
                mun_id = ruta_mun.municipio.id
                flete_municipio = (ruta_mun.flete_base or Decimal('0')) * recorridos_mensuales

                # Proporción de este municipio en la ruta (por flete)
                if total_flete_ruta > 0:
                    proporcion = (ruta_mun.flete_base or Decimal('0')) / total_flete_ruta
                else:
                    # Si no hay fletes, distribuir equitativamente
                    proporcion = Decimal('1') / len(municipios_ruta)

                # Distribuir costos del circuito proporcionalmente
                combustible_municipio = combustible_circuito * proporcion
                peaje_municipio = peaje_circuito * proporcion
                pernocta_municipio = pernocta_circuito * proporcion

                costo_total_municipio = flete_municipio + combustible_municipio + peaje_municipio + pernocta_municipio

                # Acumular en el diccionario
                if mun_id not in costos_por_municipio:
                    costos_por_municipio[mun_id] = {
                        'municipio_nombre': ruta_mun.municipio.nombre,
                        'flete_total': Decimal('0'),
                        'combustible_total': Decimal('0'),
                        'peaje_total': Decimal('0'),
                        'pernocta_total': Decimal('0'),
                        'costo_total': Decimal('0'),
                        'rutas': []
                    }

                costos_por_municipio[mun_id]['flete_total'] += flete_municipio
                costos_por_municipio[mun_id]['combustible_total'] += combustible_municipio
                costos_por_municipio[mun_id]['peaje_total'] += peaje_municipio
                costos_por_municipio[mun_id]['pernocta_total'] += pernocta_municipio
                costos_por_municipio[mun_id]['costo_total'] += costo_total_municipio
                costos_por_municipio[mun_id]['rutas'].append({
                    'ruta_id': ruta.id,
                    'ruta_nombre': ruta.nombre,
                    'flete': float(flete_municipio),
                    'combustible': float(combustible_municipio),
                    'peaje': float(peaje_municipio),
                    'pernocta': float(pernocta_municipio),
                })

        return costos_por_municipio

    def distribuir_costos_logisticos_a_zonas(self, marca) -> Dict[int, Dict]:
        """
        Distribuye los costos logísticos a las zonas comerciales según:
        1. Qué municipios atiende cada zona
        2. La venta proyectada de cada zona en ese municipio

        Returns:
            Dict con zona_id como key y:
            {
                'zona_nombre': str,
                'costo_logistico_total': Decimal,
                'detalle_municipios': [...]
            }
        """
        from core.models import ZonaMunicipio, Zona

        # Paso 1: Calcular costo por municipio
        costos_por_municipio = self.calcular_costos_logisticos_por_municipio(marca)

        # Paso 2: Obtener todas las zonas de la marca y sus municipios
        zonas = Zona.objects.filter(
            marca=marca,
            escenario=self.escenario,
            activo=True
        )

        costos_por_zona = {}

        # Inicializar todas las zonas
        for zona in zonas:
            costos_por_zona[zona.id] = {
                'zona_nombre': zona.nombre,
                'costo_logistico_total': Decimal('0'),
                'detalle_municipios': []
            }

        # Paso 3: Para cada municipio con costo logístico
        for mun_id, costo_mun in costos_por_municipio.items():
            # Encontrar todas las zonas que atienden este municipio
            zonas_municipio = ZonaMunicipio.objects.filter(
                municipio_id=mun_id,
                zona__marca=marca,
                zona__escenario=self.escenario,
                zona__activo=True
            ).select_related('zona')

            if not zonas_municipio.exists():
                # Ninguna zona atiende este municipio, el costo no se asigna
                logger.warning(f"Municipio {costo_mun['municipio_nombre']} (id={mun_id}) tiene costo logístico pero ninguna zona lo atiende")
                continue

            # Calcular venta total de todas las zonas en este municipio
            venta_total_municipio = sum(
                zm.venta_proyectada or Decimal('0')
                for zm in zonas_municipio
            )

            # Distribuir el costo entre las zonas
            for zona_mun in zonas_municipio:
                zona_id = zona_mun.zona.id

                if venta_total_municipio > 0:
                    # Proporcional a la venta proyectada
                    proporcion = (zona_mun.venta_proyectada or Decimal('0')) / venta_total_municipio
                else:
                    # Si no hay ventas, distribuir equitativamente
                    proporcion = Decimal('1') / zonas_municipio.count()

                costo_zona_municipio = costo_mun['costo_total'] * proporcion

                costos_por_zona[zona_id]['costo_logistico_total'] += costo_zona_municipio
                costos_por_zona[zona_id]['detalle_municipios'].append({
                    'municipio_id': mun_id,
                    'municipio_nombre': costo_mun['municipio_nombre'],
                    'costo_total_municipio': float(costo_mun['costo_total']),
                    'venta_zona': float(zona_mun.venta_proyectada or 0),
                    'venta_total': float(venta_total_municipio),
                    'proporcion': float(proporcion),
                    'costo_asignado': float(costo_zona_municipio),
                })

        return costos_por_zona

    def distribuir_flota_a_zonas(self, marca) -> Dict[int, Dict]:
        """
        Distribuye los costos fijos de vehículos (flota) a las zonas comerciales
        según las rutas que atiende cada vehículo.

        Lógica:
        1. Para cada vehículo, identificar qué rutas lo usan
        2. Para cada ruta, identificar qué municipios visita
        3. Distribuir el costo del vehículo a las zonas que atienden esos municipios
           (proporcional a la venta proyectada)

        Returns:
            Dict con zona_id como key y:
            {
                'zona_nombre': str,
                'costo_flota_total': Decimal,
                'detalle_vehiculos': [...]
            }
        """
        from core.models import Vehiculo, RutaLogistica, ZonaMunicipio, Zona
        from django.db.models import Q

        zonas = Zona.objects.filter(
            marca=marca,
            escenario=self.escenario,
            activo=True
        )

        costos_por_zona = {}

        # Inicializar todas las zonas
        for zona in zonas:
            costos_por_zona[zona.id] = {
                'zona_nombre': zona.nombre,
                'costo_flota_total': Decimal('0'),
                'detalle_vehiculos': []
            }

        # Obtener todos los vehículos de la marca
        vehiculos = Vehiculo.objects.filter(
            escenario=self.escenario,
            activo=True
        ).filter(
            # Vehículos individuales de la marca o compartidos
            Q(marca=marca, asignacion='individual') |
            Q(asignacion='compartido')
        )

        for vehiculo in vehiculos:
            # Calcular costo fijo mensual del vehículo
            costo_fijo = vehiculo.costo_fijo_total_mensual()

            # Si es compartido, obtener solo la proporción de esta marca
            if vehiculo.asignacion == 'compartido':
                # Buscar el prorrateo para esta marca
                from core.models import VehiculoProrrateo
                prorrateo = VehiculoProrrateo.objects.filter(
                    vehiculo=vehiculo,
                    marca=marca
                ).first()
                if prorrateo:
                    costo_fijo = costo_fijo * (prorrateo.porcentaje / 100)
                else:
                    continue  # No tiene prorrateo para esta marca

            # Encontrar las rutas que usan este vehículo
            rutas = RutaLogistica.objects.filter(
                vehiculo=vehiculo,
                marca=marca,
                escenario=self.escenario,
                activo=True
            ).prefetch_related('municipios__municipio')

            if not rutas.exists():
                # Vehículo sin rutas asignadas - distribuir proporcionalmente
                # (fallback al comportamiento anterior)
                for zona in zonas:
                    participacion = (zona.participacion_ventas or Decimal('0')) / 100
                    costo_zona = costo_fijo * participacion
                    costos_por_zona[zona.id]['costo_flota_total'] += costo_zona
                    costos_por_zona[zona.id]['detalle_vehiculos'].append({
                        'vehiculo_id': vehiculo.id,
                        'vehiculo_nombre': str(vehiculo),
                        'costo_vehiculo': float(costo_fijo),
                        'metodo': 'proporcional',
                        'costo_asignado': float(costo_zona)
                    })
                continue

            # Recopilar todos los municipios de todas las rutas del vehículo
            municipios_vehiculo = set()
            for ruta in rutas:
                for rm in ruta.municipios.all():
                    municipios_vehiculo.add(rm.municipio.id)

            if not municipios_vehiculo:
                continue

            # Encontrar todas las zonas que atienden estos municipios
            zonas_municipios = ZonaMunicipio.objects.filter(
                municipio_id__in=municipios_vehiculo,
                zona__marca=marca,
                zona__escenario=self.escenario,
                zona__activo=True
            ).select_related('zona')

            # Calcular venta total de todas las zonas en los municipios del vehículo
            venta_total = sum(
                zm.venta_proyectada or Decimal('0')
                for zm in zonas_municipios
            )

            # Agrupar por zona y sumar ventas
            venta_por_zona = {}
            for zm in zonas_municipios:
                zona_id = zm.zona.id
                if zona_id not in venta_por_zona:
                    venta_por_zona[zona_id] = Decimal('0')
                venta_por_zona[zona_id] += zm.venta_proyectada or Decimal('0')

            # Distribuir el costo del vehículo entre las zonas
            for zona_id, venta_zona in venta_por_zona.items():
                if venta_total > 0:
                    proporcion = venta_zona / venta_total
                else:
                    proporcion = Decimal('1') / len(venta_por_zona)

                costo_zona = costo_fijo * proporcion

                costos_por_zona[zona_id]['costo_flota_total'] += costo_zona
                costos_por_zona[zona_id]['detalle_vehiculos'].append({
                    'vehiculo_id': vehiculo.id,
                    'vehiculo_nombre': str(vehiculo),
                    'costo_vehiculo': float(costo_fijo),
                    'metodo': 'por_rutas',
                    'venta_zona': float(venta_zona),
                    'venta_total': float(venta_total),
                    'proporcion': float(proporcion),
                    'costo_asignado': float(costo_zona)
                })

        return costos_por_zona
