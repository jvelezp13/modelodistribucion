"""
Calculadora de Nómina.

Calcula el costo total de personal incluyendo:
- Salario base
- Prestaciones sociales (salud, pensión, ARL, cesantías, prima, vacaciones)
- Subsidio de transporte
- Otros costos (uniformes, plan de datos, etc.)
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

from utils.loaders import DataLoader

logger = logging.getLogger(__name__)


@dataclass
class CostoEmpleado:
    """Resultado del cálculo de costo de un empleado."""
    salario_base: float
    prestaciones: float
    subsidio_transporte: float
    otros_costos: float
    costo_mensual: float
    costo_anual: float

    # Desglose seguridad social (base: solo salario)
    salud: float = 0.0
    pension: float = 0.0
    arl: float = 0.0

    # Desglose parafiscales (base: solo salario)
    caja_compensacion: float = 0.0
    icbf: float = 0.0
    sena: float = 0.0

    # Desglose prestaciones sociales (base: salario + subsidio para cesantías, prima, int. cesantías)
    cesantias: float = 0.0
    intereses_cesantias: float = 0.0
    prima: float = 0.0
    vacaciones: float = 0.0  # Base: solo salario

    def to_dict(self) -> Dict[str, float]:
        """Convierte a diccionario."""
        return {
            'salario_base': self.salario_base,
            'prestaciones': self.prestaciones,
            'subsidio_transporte': self.subsidio_transporte,
            'otros_costos': self.otros_costos,
            'costo_mensual': self.costo_mensual,
            'costo_anual': self.costo_anual,
            'desglose_prestaciones': {
                'salud': self.salud,
                'pension': self.pension,
                'arl': self.arl,
                'caja_compensacion': self.caja_compensacion,
                'icbf': self.icbf,
                'sena': self.sena,
                'cesantias': self.cesantias,
                'intereses_cesantias': self.intereses_cesantias,
                'prima': self.prima,
                'vacaciones': self.vacaciones
            }
        }


class CalculadoraNomina:
    """
    Calculadora de costos de nómina.

    Utiliza los factores prestacionales configurados para calcular
    el costo total de empleados según su perfil.
    """

    def __init__(self, loader: Optional[DataLoader] = None):
        """
        Inicializa la calculadora.

        Args:
            loader: DataLoader para cargar configuración
        """
        self.loader = loader or DataLoader()
        self._factores_prestacionales = None
        self._parametros_macro = None
        self._cargar_configuracion()

    def _cargar_configuracion(self):
        """Carga la configuración necesaria."""
        self._factores_prestacionales = self.loader.cargar_factores_prestacionales()
        self._parametros_macro = self.loader.cargar_parametros_macro()
        logger.info("Configuración de nómina cargada")

    def get_salario_minimo(self) -> float:
        """Obtiene el salario mínimo legal vigente."""
        return self._parametros_macro['parametros']['salario_minimo_legal_2025']

    def get_subsidio_transporte(self) -> float:
        """Obtiene el valor del subsidio de transporte."""
        return self._parametros_macro['parametros']['subsidio_transporte_2025']

    def aplica_subsidio_transporte(self, salario_base: float) -> bool:
        """
        Determina si un salario aplica para subsidio de transporte.

        El subsidio de transporte aplica para salarios menores o iguales a 2 SMLV.

        Args:
            salario_base: Salario base del empleado

        Returns:
            True si aplica subsidio
        """
        salario_minimo = self.get_salario_minimo()
        limite = salario_minimo * 2
        return salario_base <= limite

    def calcular_costo_empleado(
        self,
        salario_base: float,
        perfil: str,
        incluir_subsidio_transporte: bool = True,
        otros_costos: float = 0.0,
        calcular_desglose: bool = False
    ) -> CostoEmpleado:
        """
        Calcula el costo total de un empleado.

        Args:
            salario_base: Salario base mensual
            perfil: Perfil prestacional (comercial, administrativo, logistico, aprendiz_sena)
            incluir_subsidio_transporte: Si se incluye subsidio de transporte
            otros_costos: Otros costos adicionales (uniformes, plan datos, etc.)
            calcular_desglose: Si se calcula el desglose detallado de prestaciones

        Returns:
            CostoEmpleado con el cálculo completo
        """
        # Validar perfil
        if perfil not in self._factores_prestacionales:
            raise ValueError(
                f"Perfil '{perfil}' no válido. "
                f"Perfiles disponibles: {list(self._factores_prestacionales.keys())}"
            )

        factores = self._factores_prestacionales[perfil]

        # Determinar subsidio de transporte primero (se necesita para algunas prestaciones)
        subsidio = 0.0
        if incluir_subsidio_transporte and self.aplica_subsidio_transporte(salario_base):
            subsidio = self.get_subsidio_transporte()

        # Base para prestaciones según normativa colombiana:
        # - Seguridad social (salud, pensión, ARL, parafiscales): solo salario
        # - Cesantías, intereses cesantías, prima: salario + subsidio transporte
        # - Vacaciones: solo salario
        base_seguridad_social = salario_base
        base_prestaciones_sociales = salario_base + subsidio  # Cesantías, prima, int. cesantías

        # Calcular prestaciones
        if calcular_desglose:
            # Aportes patronales (sobre salario base únicamente)
            salud = base_seguridad_social * factores.get('salud', 0.0)
            pension = base_seguridad_social * factores.get('pension', 0.0)
            arl = base_seguridad_social * factores.get('arl', 0.0)
            caja_compensacion = base_seguridad_social * factores.get('caja_compensacion', 0.0)
            icbf = base_seguridad_social * factores.get('icbf', 0.0)
            sena = base_seguridad_social * factores.get('sena', 0.0)

            # Prestaciones sociales (cesantías, prima e intereses incluyen subsidio)
            cesantias = base_prestaciones_sociales * factores.get('cesantias', 0.0)
            intereses_cesantias = base_prestaciones_sociales * factores.get('intereses_cesantias', 0.0)
            prima = base_prestaciones_sociales * factores.get('prima', 0.0)

            # Vacaciones (solo salario base, no incluye subsidio)
            vacaciones = base_seguridad_social * factores.get('vacaciones', 0.0)

            prestaciones_total = (
                salud + pension + arl + caja_compensacion + icbf + sena +
                cesantias + intereses_cesantias + prima + vacaciones
            )
        else:
            # Cálculo simplificado usando factor_total
            # Nota: factor_total asume cálculo sobre salario base, ajustamos por subsidio
            factor_total = factores.get('factor_total', 0.0)

            # Factores que aplican sobre salario + subsidio
            factor_con_subsidio = (
                factores.get('cesantias', 0.0) +
                factores.get('intereses_cesantias', 0.0) +
                factores.get('prima', 0.0)
            )
            # Factores que aplican solo sobre salario
            factor_sin_subsidio = factor_total - factor_con_subsidio

            prestaciones_total = (
                base_seguridad_social * factor_sin_subsidio +
                base_prestaciones_sociales * factor_con_subsidio
            )

            # Desglose vacío
            salud = pension = arl = cesantias = 0.0
            intereses_cesantias = prima = vacaciones = 0.0
            caja_compensacion = icbf = sena = 0.0

        # Costo mensual
        costo_mensual = salario_base + prestaciones_total + subsidio + otros_costos

        # Costo anual (12 meses)
        costo_anual = costo_mensual * 12

        return CostoEmpleado(
            salario_base=salario_base,
            prestaciones=prestaciones_total,
            subsidio_transporte=subsidio,
            otros_costos=otros_costos,
            costo_mensual=costo_mensual,
            costo_anual=costo_anual,
            salud=salud,
            pension=pension,
            arl=arl,
            caja_compensacion=caja_compensacion,
            icbf=icbf,
            sena=sena,
            cesantias=cesantias,
            intereses_cesantias=intereses_cesantias,
            prima=prima,
            vacaciones=vacaciones
        )

    def calcular_costo_grupo(
        self,
        cantidad: int,
        salario_base: float,
        perfil: str,
        incluir_subsidio_transporte: bool = True,
        otros_costos_por_persona: float = 0.0
    ) -> Dict[str, Any]:
        """
        Calcula el costo de un grupo de empleados idénticos.

        Args:
            cantidad: Número de empleados
            salario_base: Salario base de cada uno
            perfil: Perfil prestacional
            incluir_subsidio_transporte: Si incluye subsidio
            otros_costos_por_persona: Otros costos por persona

        Returns:
            Dict con costo individual y total
        """
        costo_individual = self.calcular_costo_empleado(
            salario_base=salario_base,
            perfil=perfil,
            incluir_subsidio_transporte=incluir_subsidio_transporte,
            otros_costos=otros_costos_por_persona,
            calcular_desglose=True
        )

        costo_mensual_total = costo_individual.costo_mensual * cantidad
        costo_anual_total = costo_individual.costo_anual * cantidad

        return {
            'cantidad': cantidad,
            'costo_individual': costo_individual.to_dict(),
            'costo_mensual_total': costo_mensual_total,
            'costo_anual_total': costo_anual_total
        }

    def comparar_perfiles(self, salario_base: float) -> Dict[str, CostoEmpleado]:
        """
        Compara el costo de un mismo salario en diferentes perfiles.

        Útil para ver el impacto de los factores prestacionales.

        Args:
            salario_base: Salario base a comparar

        Returns:
            Dict con el costo para cada perfil
        """
        resultados = {}

        for perfil in self._factores_prestacionales.keys():
            resultados[perfil] = self.calcular_costo_empleado(
                salario_base=salario_base,
                perfil=perfil,
                calcular_desglose=True
            )

        return resultados

    def calcular_incremento_salarial(
        self,
        salario_actual: float,
        perfil: str,
        porcentaje_incremento: float
    ) -> Dict[str, Any]:
        """
        Calcula el impacto de un incremento salarial.

        Args:
            salario_actual: Salario base actual
            perfil: Perfil prestacional
            porcentaje_incremento: Incremento como decimal (ej: 0.05 = 5%)

        Returns:
            Dict con salario nuevo, costo anterior y nuevo
        """
        salario_nuevo = salario_actual * (1 + porcentaje_incremento)

        costo_anterior = self.calcular_costo_empleado(salario_actual, perfil)
        costo_nuevo = self.calcular_costo_empleado(salario_nuevo, perfil)

        incremento_costo = costo_nuevo.costo_mensual - costo_anterior.costo_mensual
        incremento_porcentaje = (incremento_costo / costo_anterior.costo_mensual) * 100

        return {
            'salario_anterior': salario_actual,
            'salario_nuevo': salario_nuevo,
            'incremento_salarial_porcentaje': porcentaje_incremento * 100,
            'costo_anterior': costo_anterior.costo_mensual,
            'costo_nuevo': costo_nuevo.costo_mensual,
            'incremento_costo': incremento_costo,
            'incremento_costo_porcentaje': incremento_porcentaje
        }

    def generar_tabla_salarial(
        self,
        perfil: str,
        salario_min: float = None,
        salario_max: float = None,
        step: float = 100000
    ) -> list:
        """
        Genera una tabla de costos para diferentes salarios.

        Args:
            perfil: Perfil prestacional
            salario_min: Salario mínimo (por defecto SMLV)
            salario_max: Salario máximo (por defecto 10 SMLV)
            step: Incremento entre filas

        Returns:
            Lista de dicts con salario y costo
        """
        if salario_min is None:
            salario_min = self.get_salario_minimo()

        if salario_max is None:
            salario_max = self.get_salario_minimo() * 10

        tabla = []
        salario = salario_min

        while salario <= salario_max:
            costo = self.calcular_costo_empleado(salario, perfil)
            tabla.append({
                'salario_base': salario,
                'costo_mensual': costo.costo_mensual,
                'costo_anual': costo.costo_anual
            })
            salario += step

        return tabla


# Instancia global (singleton)
_calculadora_instance = None

def get_calculadora_nomina() -> CalculadoraNomina:
    """Obtiene la instancia global de la calculadora de nómina."""
    global _calculadora_instance
    if _calculadora_instance is None:
        _calculadora_instance = CalculadoraNomina()
    return _calculadora_instance
