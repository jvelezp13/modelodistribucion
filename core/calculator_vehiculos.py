"""
Calculadora de Vehículos.

Calcula el costo total de vehículos en dos esquemas:
- Renting: Cánon + combustible + lavada + reposición
- Tradicional: Depreciación + mantenimiento + seguro + combustible + impuestos
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

from utils.loaders import DataLoader

logger = logging.getLogger(__name__)


@dataclass
class CostoVehiculo:
    """Resultado del cálculo de costo de un vehículo."""
    tipo_vehiculo: str
    esquema: str  # renting o tradicional
    cantidad: int

    # Costos mensuales unitarios
    costo_unitario_mensual: float

    # Costos totales
    costo_mensual_total: float
    costo_anual_total: float

    # Desglose según esquema
    desglose: Dict[str, float]

    # Metadata
    capacidad_ton: float = 0.0
    capacidad_m3: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'tipo_vehiculo': self.tipo_vehiculo,
            'esquema': self.esquema,
            'cantidad': self.cantidad,
            'costo_unitario_mensual': self.costo_unitario_mensual,
            'costo_mensual_total': self.costo_mensual_total,
            'costo_anual_total': self.costo_anual_total,
            'desglose': self.desglose,
            'capacidad_ton': self.capacidad_ton,
            'capacidad_m3': self.capacidad_m3
        }


class CalculadoraVehiculos:
    """
    Calculadora de costos de vehículos.

    Soporta dos esquemas:
    - Renting: Vehículo arrendado
    - Tradicional: Vehículo propio
    """

    def __init__(self, loader: Optional[DataLoader] = None):
        """
        Inicializa la calculadora.

        Args:
            loader: DataLoader para cargar configuración
        """
        self.loader = loader or DataLoader()
        self._catalogo_vehiculos = None
        self._cargar_catalogo()

    def _cargar_catalogo(self):
        """Carga el catálogo de vehículos."""
        self._catalogo_vehiculos = self.loader.cargar_catalogo_vehiculos()
        logger.info(f"Catálogo de vehículos cargado: {len(self._catalogo_vehiculos['vehiculos'])} tipos")

    def get_tipos_vehiculos(self) -> list:
        """Obtiene la lista de tipos de vehículos disponibles."""
        return [v['id'] for v in self._catalogo_vehiculos['vehiculos']]

    def get_info_vehiculo(self, tipo_vehiculo: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene la información de un tipo de vehículo.

        Args:
            tipo_vehiculo: ID del tipo de vehículo

        Returns:
            Información del vehículo o None si no existe
        """
        for vehiculo in self._catalogo_vehiculos['vehiculos']:
            if vehiculo['id'] == tipo_vehiculo:
                return vehiculo
        return None

    def calcular_costo_renting(
        self,
        tipo_vehiculo: str,
        cantidad: int = 1,
        kilometraje_mensual: Optional[float] = None
    ) -> CostoVehiculo:
        """
        Calcula el costo de vehículo(s) en esquema renting.

        Args:
            tipo_vehiculo: Tipo de vehículo (nhr, pickup, etc.)
            cantidad: Cantidad de vehículos
            kilometraje_mensual: Km mensuales (si se quiere ajustar combustible)

        Returns:
            CostoVehiculo con el cálculo completo
        """
        info = self.get_info_vehiculo(tipo_vehiculo)
        if not info:
            raise ValueError(f"Tipo de vehículo '{tipo_vehiculo}' no encontrado")

        if 'renting' not in info.get('esquemas_disponibles', []):
            raise ValueError(f"Vehículo '{tipo_vehiculo}' no disponible en renting")

        costos_renting = info['costos']['renting']

        # Componentes del costo
        canon = costos_renting['canon_mensual']
        combustible = costos_renting['combustible_promedio_mensual']
        lavada = costos_renting['lavada_mensual']
        reposicion = costos_renting['reposicion_mensual']

        # Costo unitario mensual
        costo_unitario = canon + combustible + lavada + reposicion

        # Totales
        costo_mensual_total = costo_unitario * cantidad
        costo_anual_total = costo_mensual_total * 12

        return CostoVehiculo(
            tipo_vehiculo=tipo_vehiculo,
            esquema='renting',
            cantidad=cantidad,
            costo_unitario_mensual=costo_unitario,
            costo_mensual_total=costo_mensual_total,
            costo_anual_total=costo_anual_total,
            desglose={
                'canon': canon,
                'combustible': combustible,
                'lavada': lavada,
                'reposicion': reposicion
            },
            capacidad_ton=info.get('capacidad_ton', 0.0),
            capacidad_m3=info.get('capacidad_m3', 0.0)
        )

    def calcular_costo_tradicional(
        self,
        tipo_vehiculo: str,
        cantidad: int = 1,
        kilometraje_mensual: Optional[float] = None
    ) -> CostoVehiculo:
        """
        Calcula el costo de vehículo(s) en esquema tradicional (propio).

        Args:
            tipo_vehiculo: Tipo de vehículo
            cantidad: Cantidad de vehículos
            kilometraje_mensual: Km mensuales

        Returns:
            CostoVehiculo con el cálculo completo
        """
        info = self.get_info_vehiculo(tipo_vehiculo)
        if not info:
            raise ValueError(f"Tipo de vehículo '{tipo_vehiculo}' no encontrado")

        if 'tradicional' not in info.get('esquemas_disponibles', []):
            raise ValueError(f"Vehículo '{tipo_vehiculo}' no disponible en tradicional")

        costos_tradicional = info['costos']['tradicional']

        # Componentes del costo
        depreciacion = costos_tradicional['depreciacion_mensual']
        mantenimiento = costos_tradicional['mantenimiento_mensual']
        seguro = costos_tradicional['seguro_mensual']
        combustible = costos_tradicional['combustible_promedio_mensual']
        impuestos_mensual = costos_tradicional['impuestos_anuales'] / 12

        # Costo unitario mensual
        costo_unitario = (
            depreciacion + mantenimiento + seguro +
            combustible + impuestos_mensual
        )

        # Totales
        costo_mensual_total = costo_unitario * cantidad
        costo_anual_total = costo_mensual_total * 12

        return CostoVehiculo(
            tipo_vehiculo=tipo_vehiculo,
            esquema='tradicional',
            cantidad=cantidad,
            costo_unitario_mensual=costo_unitario,
            costo_mensual_total=costo_mensual_total,
            costo_anual_total=costo_anual_total,
            desglose={
                'depreciacion': depreciacion,
                'mantenimiento': mantenimiento,
                'seguro': seguro,
                'combustible': combustible,
                'impuestos_mensual': impuestos_mensual
            },
            capacidad_ton=info.get('capacidad_ton', 0.0),
            capacidad_m3=info.get('capacidad_m3', 0.0)
        )

    def calcular_costo_vehiculo(
        self,
        tipo_vehiculo: str,
        esquema: str,
        cantidad: int = 1,
        kilometraje_mensual: Optional[float] = None
    ) -> CostoVehiculo:
        """
        Calcula el costo de vehículo(s) según el esquema especificado.

        Args:
            tipo_vehiculo: Tipo de vehículo
            esquema: 'renting' o 'tradicional'
            cantidad: Cantidad de vehículos
            kilometraje_mensual: Km mensuales

        Returns:
            CostoVehiculo
        """
        if esquema == 'renting':
            return self.calcular_costo_renting(
                tipo_vehiculo, cantidad, kilometraje_mensual
            )
        elif esquema == 'tradicional':
            return self.calcular_costo_tradicional(
                tipo_vehiculo, cantidad, kilometraje_mensual
            )
        else:
            raise ValueError(f"Esquema '{esquema}' no válido. Use 'renting' o 'tradicional'")

    def comparar_esquemas(
        self,
        tipo_vehiculo: str,
        cantidad: int = 1
    ) -> Dict[str, CostoVehiculo]:
        """
        Compara el costo de un vehículo en ambos esquemas.

        Args:
            tipo_vehiculo: Tipo de vehículo
            cantidad: Cantidad de vehículos

        Returns:
            Dict con costos en renting y tradicional
        """
        info = self.get_info_vehiculo(tipo_vehiculo)
        if not info:
            raise ValueError(f"Tipo de vehículo '{tipo_vehiculo}' no encontrado")

        esquemas_disponibles = info.get('esquemas_disponibles', [])
        resultados = {}

        if 'renting' in esquemas_disponibles:
            resultados['renting'] = self.calcular_costo_renting(tipo_vehiculo, cantidad)

        if 'tradicional' in esquemas_disponibles:
            resultados['tradicional'] = self.calcular_costo_tradicional(tipo_vehiculo, cantidad)

        return resultados

    def calcular_flota(self, configuracion_flota: list) -> Dict[str, Any]:
        """
        Calcula el costo de una flota completa.

        Args:
            configuracion_flota: Lista de dicts con tipo_vehiculo, esquema, cantidad

        Returns:
            Dict con costo total y desglose por vehículo
        """
        vehiculos_calculados = []
        costo_total_mensual = 0.0
        costo_total_anual = 0.0

        for config in configuracion_flota:
            costo = self.calcular_costo_vehiculo(
                tipo_vehiculo=config['tipo_vehiculo'],
                esquema=config['esquema'],
                cantidad=config.get('cantidad', 1),
                kilometraje_mensual=config.get('kilometraje_mensual')
            )

            vehiculos_calculados.append(costo)
            costo_total_mensual += costo.costo_mensual_total
            costo_total_anual += costo.costo_anual_total

        return {
            'vehiculos': [v.to_dict() for v in vehiculos_calculados],
            'total_vehiculos': sum(v.cantidad for v in vehiculos_calculados),
            'costo_mensual_total': costo_total_mensual,
            'costo_anual_total': costo_total_anual,
            'costo_promedio_por_vehiculo': costo_total_mensual / sum(v.cantidad for v in vehiculos_calculados) if vehiculos_calculados else 0
        }

    def optimizar_esquema(
        self,
        tipo_vehiculo: str,
        meses_uso: int = 60
    ) -> Dict[str, Any]:
        """
        Analiza qué esquema es más conveniente según los meses de uso.

        Args:
            tipo_vehiculo: Tipo de vehículo
            meses_uso: Cantidad de meses que se usará el vehículo

        Returns:
            Dict con recomendación y análisis
        """
        comparacion = self.comparar_esquemas(tipo_vehiculo, 1)

        if len(comparacion) < 2:
            return {
                'recomendacion': list(comparacion.keys())[0] if comparacion else None,
                'razon': 'Solo un esquema disponible',
                'analisis': comparacion
            }

        costo_renting_total = comparacion['renting'].costo_mensual_total * meses_uso
        costo_tradicional_total = comparacion['tradicional'].costo_mensual_total * meses_uso

        ahorro = abs(costo_renting_total - costo_tradicional_total)
        ahorro_porcentaje = (ahorro / max(costo_renting_total, costo_tradicional_total)) * 100

        if costo_renting_total < costo_tradicional_total:
            recomendacion = 'renting'
            razon = f'Ahorro de ${ahorro:,.0f} ({ahorro_porcentaje:.1f}%) en {meses_uso} meses'
        else:
            recomendacion = 'tradicional'
            razon = f'Ahorro de ${ahorro:,.0f} ({ahorro_porcentaje:.1f}%) en {meses_uso} meses'

        return {
            'recomendacion': recomendacion,
            'razon': razon,
            'analisis': {
                'meses_uso': meses_uso,
                'costo_renting_total': costo_renting_total,
                'costo_tradicional_total': costo_tradicional_total,
                'ahorro': ahorro,
                'ahorro_porcentaje': ahorro_porcentaje
            },
            'comparacion_mensual': {
                'renting': comparacion['renting'].to_dict(),
                'tradicional': comparacion['tradicional'].to_dict()
            }
        }

    def generar_reporte_flota(self, configuracion_flota: list) -> str:
        """
        Genera un reporte legible de la flota.

        Args:
            configuracion_flota: Configuración de la flota

        Returns:
            String con el reporte
        """
        calculo = self.calcular_flota(configuracion_flota)

        lineas = [
            "=== REPORTE DE FLOTA ===",
            f"Total de vehículos: {calculo['total_vehiculos']}",
            f"Costo mensual total: ${calculo['costo_mensual_total']:,.0f}",
            f"Costo anual total: ${calculo['costo_anual_total']:,.0f}",
            f"Costo promedio por vehículo: ${calculo['costo_promedio_por_vehiculo']:,.0f}",
            "",
            "=== DETALLE POR VEHÍCULO ==="
        ]

        for vehiculo in calculo['vehiculos']:
            lineas.append(
                f"\n{vehiculo['tipo_vehiculo'].upper()} ({vehiculo['esquema']}) x {vehiculo['cantidad']}:"
            )
            lineas.append(f"  Costo unitario: ${vehiculo['costo_unitario_mensual']:,.0f}/mes")
            lineas.append(f"  Costo total: ${vehiculo['costo_mensual_total']:,.0f}/mes")

            lineas.append("  Desglose:")
            for concepto, valor in vehiculo['desglose'].items():
                lineas.append(f"    - {concepto}: ${valor:,.0f}")

        return "\n".join(lineas)


# Instancia global (singleton)
_calculadora_vehiculos_instance = None

def get_calculadora_vehiculos() -> CalculadoraVehiculos:
    """Obtiene la instancia global de la calculadora de vehículos."""
    global _calculadora_vehiculos_instance
    if _calculadora_vehiculos_instance is None:
        _calculadora_vehiculos_instance = CalculadoraVehiculos()
    return _calculadora_vehiculos_instance
