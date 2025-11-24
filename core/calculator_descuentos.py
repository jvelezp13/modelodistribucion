"""
Calculadora de Descuentos e Incentivos.

Calcula los 3 tipos de descuentos configurados por marca:
1. Descuento a pie de factura (por tramos)
2. Rebate / RxP
3. Descuento financiero
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from decimal import Decimal
import logging
import os

logger = logging.getLogger(__name__)


@dataclass
class TramoDescuento:
    """Representa un tramo de descuento a pie de factura."""
    orden: int
    porcentaje_ventas: Decimal
    porcentaje_descuento: Decimal


@dataclass
class ConfigDescuentos:
    """Configuración de descuentos para una marca."""
    marca_id: str
    tramos: List[TramoDescuento]
    porcentaje_rebate: Decimal
    aplica_descuento_financiero: bool
    porcentaje_descuento_financiero: Decimal
    activa: bool = True


@dataclass
class ResultadoDescuentos:
    """Resultado del cálculo de descuentos."""
    ventas_brutas: float
    descuento_pie_factura: float
    ventas_post_descuento: float
    rebate: float
    ventas_post_rebate: float
    descuento_financiero: float
    ventas_netas: float
    porcentaje_descuento_total: float

    def to_dict(self) -> Dict[str, float]:
        """Convierte a diccionario."""
        return {
            'ventas_brutas': self.ventas_brutas,
            'descuento_pie_factura': self.descuento_pie_factura,
            'ventas_post_descuento': self.ventas_post_descuento,
            'rebate': self.rebate,
            'ventas_post_rebate': self.ventas_post_rebate,
            'descuento_financiero': self.descuento_financiero,
            'ventas_netas': self.ventas_netas,
            'porcentaje_descuento_total': self.porcentaje_descuento_total
        }


class CalculadoraDescuentos:
    """
    Calculadora de descuentos e incentivos por marca.

    Carga configuraciones desde Django y calcula el impacto
    de los descuentos en las ventas.
    """

    def __init__(self):
        """Inicializa la calculadora."""
        self._configuraciones: Dict[str, ConfigDescuentos] = {}
        self._django_inicializado = False

    def _inicializar_django(self):
        """Inicializa Django para acceder a los modelos."""
        if self._django_inicializado:
            return

        try:
            # Usar el mismo método que loaders_db.py
            from utils import django_init

            self._django_inicializado = True
            logger.info("Django inicializado para calculadora de descuentos")

        except Exception as e:
            logger.error(f"Error inicializando Django: {e}")
            raise

    def cargar_configuraciones(self, marcas_ids: Optional[List[str]] = None):
        """
        Carga configuraciones de descuentos desde Django.

        Args:
            marcas_ids: Lista de IDs de marcas. Si es None, carga todas.
        """
        self._inicializar_django()

        try:
            # Importar DESPUÉS de inicializar Django
            from core.models import ConfiguracionDescuentos

            # Construir query
            query = ConfiguracionDescuentos.objects.filter(activa=True)

            if marcas_ids:
                query = query.filter(marca__marca_id__in=marcas_ids)

            query = query.select_related('marca').prefetch_related('tramos')

            # Cargar configuraciones
            for config in query:
                tramos = [
                    TramoDescuento(
                        orden=t.orden,
                        porcentaje_ventas=t.porcentaje_ventas,
                        porcentaje_descuento=t.porcentaje_descuento
                    )
                    for t in config.tramos.all().order_by('orden')
                ]

                self._configuraciones[config.marca.marca_id] = ConfigDescuentos(
                    marca_id=config.marca.marca_id,
                    tramos=tramos,
                    porcentaje_rebate=config.porcentaje_rebate,
                    aplica_descuento_financiero=config.aplica_descuento_financiero,
                    porcentaje_descuento_financiero=config.porcentaje_descuento_financiero,
                    activa=config.activa
                )

            logger.info(f"Configuraciones de descuentos cargadas para {len(self._configuraciones)} marcas")

        except Exception as e:
            logger.error(f"Error cargando configuraciones de descuentos: {e}")
            # No fallar si no hay descuentos configurados
            pass

    def calcular_descuentos(self, marca_id: str, ventas_brutas: float) -> ResultadoDescuentos:
        """
        Calcula todos los descuentos para una marca.

        Args:
            marca_id: ID de la marca
            ventas_brutas: Ventas brutas mensuales

        Returns:
            ResultadoDescuentos con todos los cálculos
        """
        # Si no hay configuración, retornar ventas sin descuentos
        if marca_id not in self._configuraciones:
            return ResultadoDescuentos(
                ventas_brutas=ventas_brutas,
                descuento_pie_factura=0.0,
                ventas_post_descuento=ventas_brutas,
                rebate=0.0,
                ventas_post_rebate=ventas_brutas,
                descuento_financiero=0.0,
                ventas_netas=ventas_brutas,
                porcentaje_descuento_total=0.0
            )

        config = self._configuraciones[marca_id]

        # 1. Calcular descuento a pie de factura (sobre Ventas Brutas / Sell In teórico)
        descuento_pie_factura = self._calcular_descuento_pie_factura(
            ventas_brutas, config.tramos
        )
        
        # Base para financiero: Lo que se paga en factura (Ventas - Pie de Factura)
        monto_factura = ventas_brutas - descuento_pie_factura

        # 2. Calcular descuento financiero (sobre monto factura)
        descuento_financiero = 0.0
        if config.aplica_descuento_financiero:
            descuento_financiero = monto_factura * (
                float(config.porcentaje_descuento_financiero) / 100.0
            )

        # 3. Calcular rebate / RxP (sobre Sell Out / Ventas Brutas)
        # "RxP aplica sobre el Sell Out"
        rebate = ventas_brutas * (float(config.porcentaje_rebate) / 100.0)

        # Ventas Netas ahora es igual a Ventas Brutas (Sell Out)
        # Los descuentos son ingresos, no reducciones de venta
        ventas_netas = ventas_brutas
        
        # Variables auxiliares para compatibilidad (aunque ya no se restan en cascada)
        ventas_post_descuento = ventas_brutas  
        ventas_post_rebate = ventas_brutas

        # Calcular porcentaje total de descuento (Ingreso total / Venta)
        total_descuentos = descuento_pie_factura + rebate + descuento_financiero
        porcentaje_descuento_total = (
            (total_descuentos / ventas_brutas * 100.0) if ventas_brutas > 0 else 0.0
        )

        return ResultadoDescuentos(
            ventas_brutas=ventas_brutas,
            descuento_pie_factura=descuento_pie_factura,
            ventas_post_descuento=ventas_post_descuento,
            rebate=rebate,
            ventas_post_rebate=ventas_post_rebate,
            descuento_financiero=descuento_financiero,
            ventas_netas=ventas_netas,
            porcentaje_descuento_total=porcentaje_descuento_total
        )

    def _calcular_descuento_pie_factura(
        self,
        ventas_brutas: float,
        tramos: List[TramoDescuento]
    ) -> float:
        """
        Calcula el descuento a pie de factura aplicando los tramos.

        Args:
            ventas_brutas: Ventas brutas
            tramos: Lista de tramos de descuento

        Returns:
            Monto total de descuento
        """
        if not tramos:
            return 0.0

        descuento_total = 0.0

        for tramo in tramos:
            # Calcular porción de ventas que corresponde a este tramo
            porcion_ventas = ventas_brutas * (float(tramo.porcentaje_ventas) / 100.0)

            # Aplicar descuento a esta porción
            descuento_tramo = porcion_ventas * (float(tramo.porcentaje_descuento) / 100.0)

            descuento_total += descuento_tramo

        return descuento_total

    def tiene_configuracion(self, marca_id: str) -> bool:
        """Verifica si una marca tiene configuración de descuentos."""
        return marca_id in self._configuraciones

    def get_configuracion(self, marca_id: str) -> Optional[ConfigDescuentos]:
        """Obtiene la configuración de descuentos de una marca."""
        return self._configuraciones.get(marca_id)
