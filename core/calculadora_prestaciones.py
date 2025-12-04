"""
Calculadora de Prestaciones Sociales - Fuente única de verdad.

Este módulo centraliza el cálculo de costos de nómina según la normativa
laboral colombiana. Debe ser usado tanto por los modelos Django como por
el simulador para garantizar consistencia.

Normativa aplicada:
- Ley 1ª de 1963: Cesantías incluyen subsidio de transporte
- CST Art. 306: Prima de servicios incluye subsidio de transporte
- Ley 52 de 1975: Intereses sobre cesantías
- Ley 1607 de 2012: Exoneración de aportes (salud, ICBF, SENA) para < 10 SMLV
"""

from decimal import Decimal
from typing import Dict, Union, NamedTuple
from dataclasses import dataclass


@dataclass
class FactoresPrestacionales:
    """
    Factores prestacionales por perfil.
    Todos los valores en decimal (ej: 0.12 = 12%)
    """
    # Sobre solo salario
    salud: Decimal = Decimal('0')
    pension: Decimal = Decimal('0.12')
    arl: Decimal = Decimal('0.01044')  # Riesgo II por defecto
    caja_compensacion: Decimal = Decimal('0.04')
    icbf: Decimal = Decimal('0')  # Exonerado < 10 SMLV
    sena: Decimal = Decimal('0')  # Exonerado < 10 SMLV
    vacaciones: Decimal = Decimal('0')  # 0 si se maneja con supernumerarios

    # Sobre salario + subsidio de transporte
    cesantias: Decimal = Decimal('0.0833')
    intereses_cesantias: Decimal = Decimal('0.01')
    prima: Decimal = Decimal('0.0833')

    @property
    def factor_solo_salario(self) -> Decimal:
        """Suma de factores que aplican solo sobre salario."""
        return (
            self.salud + self.pension + self.arl +
            self.caja_compensacion + self.icbf + self.sena +
            self.vacaciones
        )

    @property
    def factor_con_subsidio(self) -> Decimal:
        """Suma de factores que aplican sobre salario + subsidio."""
        return self.cesantias + self.intereses_cesantias + self.prima

    @property
    def factor_total_aproximado(self) -> Decimal:
        """
        Factor total aproximado (asume subsidio = 0).
        Usar solo como referencia, no para cálculos precisos.
        """
        return self.factor_solo_salario + self.factor_con_subsidio


@dataclass
class ResultadoCostoNomina:
    """Resultado del cálculo de costo de nómina."""
    salario_base: Decimal
    subsidio_transporte: Decimal
    prestaciones_sobre_salario: Decimal
    prestaciones_sobre_salario_subsidio: Decimal
    auxilio_adicional: Decimal
    costo_unitario: Decimal
    cantidad: int
    costo_total: Decimal

    def to_dict(self) -> Dict:
        """Convierte a diccionario para serialización."""
        return {
            'salario_base': float(self.salario_base),
            'subsidio_transporte': float(self.subsidio_transporte),
            'prestaciones_sobre_salario': float(self.prestaciones_sobre_salario),
            'prestaciones_sobre_salario_subsidio': float(self.prestaciones_sobre_salario_subsidio),
            'auxilio_adicional': float(self.auxilio_adicional),
            'costo_unitario': float(self.costo_unitario),
            'cantidad': self.cantidad,
            'costo_total': float(self.costo_total),
        }


def calcular_costo_nomina(
    salario_base: Union[Decimal, float, int],
    factores: FactoresPrestacionales,
    subsidio_transporte: Union[Decimal, float, int] = 0,
    auxilio_adicional: Union[Decimal, float, int] = 0,
    cantidad: int = 1,
) -> ResultadoCostoNomina:
    """
    Calcula el costo total de nómina según normativa laboral colombiana.

    Args:
        salario_base: Salario base mensual
        factores: Factores prestacionales del perfil
        subsidio_transporte: Subsidio de transporte (si aplica, <= 2 SMLV)
        auxilio_adicional: Auxilios adicionales (rodamiento, etc.)
        cantidad: Número de empleados con este mismo perfil/salario

    Returns:
        ResultadoCostoNomina con el desglose completo

    Ejemplo:
        >>> factores = FactoresPrestacionales(pension=Decimal('0.12'), ...)
        >>> resultado = calcular_costo_nomina(
        ...     salario_base=2300000,
        ...     factores=factores,
        ...     subsidio_transporte=200000,
        ...     cantidad=1
        ... )
        >>> print(resultado.costo_total)
        3333420.00
    """
    # Convertir a Decimal para precisión
    salario = Decimal(str(salario_base))
    subsidio = Decimal(str(subsidio_transporte))
    auxilio = Decimal(str(auxilio_adicional))

    # Calcular prestaciones según base legal
    # 1. Prestaciones sobre solo salario (seguridad social, parafiscales, vacaciones)
    prestaciones_salario = salario * factores.factor_solo_salario

    # 2. Prestaciones sobre salario + subsidio (cesantías, intereses, prima)
    base_con_subsidio = salario + subsidio
    prestaciones_con_subsidio = base_con_subsidio * factores.factor_con_subsidio

    # Costo unitario
    costo_unitario = (
        salario +
        prestaciones_salario +
        prestaciones_con_subsidio +
        subsidio +
        auxilio
    )

    # Costo total
    costo_total = costo_unitario * cantidad

    return ResultadoCostoNomina(
        salario_base=salario,
        subsidio_transporte=subsidio,
        prestaciones_sobre_salario=prestaciones_salario,
        prestaciones_sobre_salario_subsidio=prestaciones_con_subsidio,
        auxilio_adicional=auxilio,
        costo_unitario=costo_unitario,
        cantidad=cantidad,
        costo_total=costo_total,
    )


def aplica_subsidio_transporte(
    salario_base: Union[Decimal, float, int],
    salario_minimo: Union[Decimal, float, int],
    limite_smlv: int = 2
) -> bool:
    """
    Determina si un salario aplica para subsidio de transporte.

    El subsidio de transporte aplica para salarios menores o iguales
    a 2 SMLV (por defecto).

    Args:
        salario_base: Salario base del empleado
        salario_minimo: Salario mínimo legal vigente
        limite_smlv: Número de SMLV como límite (default: 2)

    Returns:
        True si aplica subsidio de transporte
    """
    salario = Decimal(str(salario_base))
    smlv = Decimal(str(salario_minimo))
    limite = smlv * limite_smlv
    return salario <= limite


def crear_factores_desde_dict(datos: Dict) -> FactoresPrestacionales:
    """
    Crea FactoresPrestacionales desde un diccionario.

    Útil para convertir desde el modelo Django FactorPrestacional
    o desde configuración JSON.

    Args:
        datos: Diccionario con los factores (valores en porcentaje 0-100 o decimal 0-1)

    Returns:
        FactoresPrestacionales con valores en decimal
    """
    def a_decimal(valor, es_porcentaje=True):
        """Convierte a Decimal, dividiendo por 100 si es porcentaje."""
        if valor is None:
            return Decimal('0')
        d = Decimal(str(valor))
        # Si el valor es > 1, asumimos que es porcentaje (ej: 12 = 12%)
        if es_porcentaje and d > 1:
            return d / Decimal('100')
        return d

    return FactoresPrestacionales(
        salud=a_decimal(datos.get('salud', 0)),
        pension=a_decimal(datos.get('pension', 12)),
        arl=a_decimal(datos.get('arl', 1.044)),
        caja_compensacion=a_decimal(datos.get('caja_compensacion', 4)),
        icbf=a_decimal(datos.get('icbf', 0)),
        sena=a_decimal(datos.get('sena', 0)),
        vacaciones=a_decimal(datos.get('vacaciones', 0)),
        cesantias=a_decimal(datos.get('cesantias', 8.33)),
        intereses_cesantias=a_decimal(datos.get('intereses_cesantias', 1)),
        prima=a_decimal(datos.get('prima', 8.33)),
    )


def crear_factores_desde_modelo_django(factor_prestacional) -> FactoresPrestacionales:
    """
    Crea FactoresPrestacionales desde un modelo Django FactorPrestacional.

    Args:
        factor_prestacional: Instancia de FactorPrestacional de Django

    Returns:
        FactoresPrestacionales con valores en decimal
    """
    return FactoresPrestacionales(
        salud=factor_prestacional.salud / Decimal('100'),
        pension=factor_prestacional.pension / Decimal('100'),
        arl=factor_prestacional.arl / Decimal('100'),
        caja_compensacion=factor_prestacional.caja_compensacion / Decimal('100'),
        icbf=factor_prestacional.icbf / Decimal('100'),
        sena=factor_prestacional.sena / Decimal('100'),
        vacaciones=factor_prestacional.vacaciones / Decimal('100'),
        cesantias=factor_prestacional.cesantias / Decimal('100'),
        intereses_cesantias=factor_prestacional.intereses_cesantias / Decimal('100'),
        prima=factor_prestacional.prima / Decimal('100'),
    )
