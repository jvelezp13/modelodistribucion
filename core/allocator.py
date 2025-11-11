"""
Asignador de Gastos Compartidos (Allocator).

Este módulo implementa la lógica de prorrateo de gastos compartidos
entre múltiples marcas según diferentes criterios:
- Por ventas
- Por volumen
- Por headcount (cantidad de empleados)
- Equitativo (partes iguales)
- Por uso real
"""

from typing import List, Dict, Any, Optional
from models.marca import Marca
from models.rubro import Rubro, CriterioProrrateo
import logging

logger = logging.getLogger(__name__)


class Allocator:
    """
    Asignador de gastos compartidos entre marcas.

    Toma rubros compartidos y los distribuye entre las marcas
    según el criterio de prorrateo configurado.
    """

    def __init__(self, marcas: List[Marca]):
        """
        Inicializa el allocator.

        Args:
            marcas: Lista de marcas activas
        """
        self.marcas = marcas
        self.marcas_activas = [m for m in marcas if m.activa]

        if not self.marcas_activas:
            raise ValueError("Debe haber al menos una marca activa")

        logger.info(f"Allocator inicializado con {len(self.marcas_activas)} marcas activas")

    def calcular_factor_prorrateo_ventas(
        self,
        marca: Marca,
        rubro: Rubro
    ) -> float:
        """
        Calcula el factor de prorrateo basado en ventas.

        El factor es: ventas_marca / ventas_totales

        Args:
            marca: Marca para la cual calcular el factor
            rubro: Rubro a prorratear

        Returns:
            Factor de prorrateo (0.0 - 1.0)
        """
        total_ventas = sum(m.ventas_mensuales for m in self.marcas_activas)

        if total_ventas == 0:
            logger.warning("Ventas totales son 0, distribuyendo equitativamente")
            return 1.0 / len(self.marcas_activas)

        factor = marca.ventas_mensuales / total_ventas

        logger.debug(
            f"Factor ventas para {marca.nombre}: "
            f"{factor:.2%} (${marca.ventas_mensuales:,.0f} / ${total_ventas:,.0f})"
        )

        return factor

    def calcular_factor_prorrateo_volumen(
        self,
        marca: Marca,
        rubro: Rubro
    ) -> float:
        """
        Calcula el factor de prorrateo basado en volumen (m³).

        Args:
            marca: Marca para la cual calcular el factor
            rubro: Rubro a prorratear

        Returns:
            Factor de prorrateo (0.0 - 1.0)
        """
        total_volumen = sum(m.volumen_m3_mensual for m in self.marcas_activas)

        if total_volumen == 0:
            logger.warning("Volumen total es 0, distribuyendo equitativamente")
            return 1.0 / len(self.marcas_activas)

        factor = marca.volumen_m3_mensual / total_volumen

        logger.debug(
            f"Factor volumen para {marca.nombre}: "
            f"{factor:.2%} ({marca.volumen_m3_mensual:.0f} m³ / {total_volumen:.0f} m³)"
        )

        return factor

    def calcular_factor_prorrateo_headcount(
        self,
        marca: Marca,
        rubro: Rubro
    ) -> float:
        """
        Calcula el factor de prorrateo basado en cantidad de empleados.

        Args:
            marca: Marca para la cual calcular el factor
            rubro: Rubro a prorratear

        Returns:
            Factor de prorrateo (0.0 - 1.0)
        """
        total_empleados = sum(m.total_empleados for m in self.marcas_activas)

        if total_empleados == 0:
            logger.warning("Total empleados es 0, distribuyendo equitativamente")
            return 1.0 / len(self.marcas_activas)

        factor = marca.total_empleados / total_empleados

        logger.debug(
            f"Factor headcount para {marca.nombre}: "
            f"{factor:.2%} ({marca.total_empleados} / {total_empleados})"
        )

        return factor

    def calcular_factor_prorrateo_equitativo(
        self,
        marca: Marca,
        rubro: Rubro
    ) -> float:
        """
        Calcula el factor de prorrateo equitativo (partes iguales).

        Args:
            marca: Marca
            rubro: Rubro

        Returns:
            Factor de prorrateo (1 / cantidad de marcas)
        """
        factor = 1.0 / len(self.marcas_activas)

        logger.debug(
            f"Factor equitativo para {marca.nombre}: "
            f"{factor:.2%} (1 / {len(self.marcas_activas)})"
        )

        return factor

    def calcular_factor_prorrateo(
        self,
        marca: Marca,
        rubro: Rubro
    ) -> float:
        """
        Calcula el factor de prorrateo según el criterio del rubro.

        Args:
            marca: Marca para la cual calcular
            rubro: Rubro compartido

        Returns:
            Factor de prorrateo (0.0 - 1.0)
        """
        if not rubro.criterio_prorrateo:
            logger.warning(f"Rubro '{rubro.id}' sin criterio de prorrateo, usando ventas")
            criterio = CriterioProrrateo.VENTAS
        else:
            criterio = rubro.criterio_prorrateo

        if criterio == CriterioProrrateo.VENTAS:
            return self.calcular_factor_prorrateo_ventas(marca, rubro)

        elif criterio == CriterioProrrateo.VOLUMEN:
            return self.calcular_factor_prorrateo_volumen(marca, rubro)

        elif criterio == CriterioProrrateo.HEADCOUNT:
            return self.calcular_factor_prorrateo_headcount(marca, rubro)

        elif criterio == CriterioProrrateo.EQUITATIVO:
            return self.calcular_factor_prorrateo_equitativo(marca, rubro)

        elif criterio == CriterioProrrateo.USO_REAL:
            # Para uso real, se debe especificar el porcentaje_dedicacion
            if rubro.porcentaje_dedicacion is not None:
                return rubro.porcentaje_dedicacion
            else:
                logger.warning(
                    f"Rubro '{rubro.id}' con uso_real pero sin porcentaje_dedicacion, "
                    "usando equitativo"
                )
                return self.calcular_factor_prorrateo_equitativo(marca, rubro)

        else:
            logger.error(f"Criterio de prorrateo desconocido: {criterio}")
            return 0.0

    def asignar_rubro_compartido(
        self,
        rubro: Rubro
    ) -> Dict[str, float]:
        """
        Asigna un rubro compartido a todas las marcas.

        Args:
            rubro: Rubro compartido a asignar

        Returns:
            Dict con marca_id -> monto asignado
        """
        if not rubro.es_compartido():
            raise ValueError(f"Rubro '{rubro.id}' no es compartido")

        asignaciones = {}

        for marca in self.marcas_activas:
            factor = self.calcular_factor_prorrateo(marca, rubro)
            monto_asignado = rubro.valor_total * factor
            asignaciones[marca.marca_id] = monto_asignado

            logger.debug(
                f"Asignado {rubro.id} a {marca.nombre}: "
                f"${monto_asignado:,.0f} ({factor:.2%})"
            )

        # Validar que la suma sea correcta (puede haber diferencias por redondeo)
        total_asignado = sum(asignaciones.values())
        diferencia = abs(total_asignado - rubro.valor_total)

        if diferencia > 1:  # Tolerancia de $1 por redondeo
            logger.warning(
                f"Diferencia en asignación de '{rubro.id}': "
                f"${diferencia:,.2f} (asignado: ${total_asignado:,.0f}, "
                f"original: ${rubro.valor_total:,.0f})"
            )

        return asignaciones

    def asignar_rubros_compartidos(
        self,
        rubros_compartidos: List[Rubro]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Asigna una lista de rubros compartidos a todas las marcas.

        Args:
            rubros_compartidos: Lista de rubros compartidos

        Returns:
            Dict con marca_id -> lista de rubros asignados con montos
        """
        # Inicializar estructura
        asignaciones_por_marca = {
            marca.marca_id: [] for marca in self.marcas_activas
        }

        # Asignar cada rubro
        for rubro in rubros_compartidos:
            if not rubro.es_compartido():
                logger.warning(f"Rubro '{rubro.id}' no es compartido, ignorando")
                continue

            asignaciones = self.asignar_rubro_compartido(rubro)

            # Agregar a cada marca
            for marca_id, monto in asignaciones.items():
                asignaciones_por_marca[marca_id].append({
                    'rubro_id': rubro.id,
                    'rubro_nombre': rubro.nombre,
                    'categoria': rubro.categoria,
                    'criterio_prorrateo': rubro.criterio_prorrateo.value if rubro.criterio_prorrateo else 'ventas',
                    'valor_original': rubro.valor_total,
                    'valor_asignado': monto
                })

        return asignaciones_por_marca

    def generar_reporte_prorrateo(
        self,
        rubros_compartidos: List[Rubro]
    ) -> str:
        """
        Genera un reporte legible del prorrateo.

        Args:
            rubros_compartidos: Lista de rubros compartidos

        Returns:
            String con el reporte
        """
        asignaciones = self.asignar_rubros_compartidos(rubros_compartidos)

        lineas = [
            "=" * 80,
            "REPORTE DE PRORRATEO DE GASTOS COMPARTIDOS",
            "=" * 80,
            f"\nMarcas activas: {len(self.marcas_activas)}",
            f"Rubros compartidos: {len(rubros_compartidos)}",
        ]

        # Total compartido
        total_compartido = sum(r.valor_total for r in rubros_compartidos)
        lineas.append(f"Total gastos compartidos: ${total_compartido:,.0f}\n")

        # Por cada marca
        for marca in self.marcas_activas:
            marca_id = marca.marca_id
            rubros_marca = asignaciones[marca_id]

            total_asignado = sum(r['valor_asignado'] for r in rubros_marca)

            lineas.append(f"\n{'=' * 70}")
            lineas.append(f"MARCA: {marca.nombre}")
            lineas.append(f"{'=' * 70}")
            lineas.append(f"Total asignado: ${total_asignado:,.0f}")
            lineas.append(f"% del total: {(total_asignado / total_compartido * 100):.1f}%\n")

            lineas.append("Detalle:")
            for rubro in rubros_marca:
                porcentaje = (rubro['valor_asignado'] / rubro['valor_original']) * 100
                lineas.append(
                    f"  • {rubro['rubro_nombre']:30s} "
                    f"${rubro['valor_asignado']:>12,.0f} "
                    f"({porcentaje:>5.1f}%) "
                    f"[{rubro['criterio_prorrateo']}]"
                )

        lineas.append("\n" + "=" * 80)

        return "\n".join(lineas)

    def validar_prorrateo(
        self,
        rubros_compartidos: List[Rubro]
    ) -> Dict[str, Any]:
        """
        Valida que el prorrateo se haga correctamente.

        Args:
            rubros_compartidos: Lista de rubros compartidos

        Returns:
            Dict con resultado de validación
        """
        errores = []
        advertencias = []

        # Validar que las marcas tengan datos necesarios
        for marca in self.marcas_activas:
            # Ventas
            if marca.ventas_mensuales == 0:
                advertencias.append(
                    f"Marca '{marca.nombre}' tiene ventas en 0, "
                    "prorrateos por ventas pueden fallar"
                )

        # Validar rubros
        for rubro in rubros_compartidos:
            if not rubro.criterio_prorrateo:
                advertencias.append(
                    f"Rubro '{rubro.id}' sin criterio de prorrateo definido"
                )

        # Hacer asignación de prueba
        try:
            asignaciones = self.asignar_rubros_compartidos(rubros_compartidos)

            # Validar sumas
            for rubro in rubros_compartidos:
                total_asignado = sum(
                    r['valor_asignado']
                    for marca_rubros in asignaciones.values()
                    for r in marca_rubros
                    if r['rubro_id'] == rubro.id
                )

                diferencia = abs(total_asignado - rubro.valor_total)
                if diferencia > 10:  # Tolerancia de $10
                    errores.append(
                        f"Rubro '{rubro.id}': diferencia de ${diferencia:,.2f} "
                        f"entre asignado y original"
                    )

        except Exception as e:
            errores.append(f"Error en asignación: {str(e)}")

        return {
            'es_valido': len(errores) == 0,
            'errores': errores,
            'advertencias': advertencias
        }
