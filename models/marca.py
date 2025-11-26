"""
Modelo de Marca.

Representa una marca en el sistema multimarcas.
Contiene todos los recursos, costos y métricas asociadas a una marca.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from models.rubro import Rubro


@dataclass
class Marca:
    """
    Representa una marca en el sistema.

    Una marca tiene:
    - Recursos comerciales (vendedores, supervisores, etc.)
    - Recursos logísticos (vehículos, personal logístico, etc.)
    - Proyección de ventas
    - Costos asignados (individuales + compartidos prorrateados)
    """

    # Identificación
    marca_id: str
    nombre: str

    # Ventas
    ventas_mensuales: float = 0.0  # Ventas brutas
    ventas_anuales: float = 0.0     # Ventas brutas anuales

    # Descuentos e Incentivos
    descuento_pie_factura: float = 0.0
    rebate: float = 0.0
    descuento_financiero: float = 0.0
    ventas_netas_mensuales: float = 0.0  # Ventas después de todos los descuentos
    porcentaje_descuento_total: float = 0.0

    # Volumen (para prorrateos)
    volumen_m3_mensual: float = 0.0
    volumen_ton_mensual: float = 0.0
    pallets_mensuales: int = 0

    # Headcount (para prorrateos)
    empleados_comerciales: int = 0
    empleados_logisticos: int = 0
    empleados_administrativos: int = 0

    # Rubros asignados
    rubros_individuales: List[Rubro] = field(default_factory=list)
    rubros_compartidos_asignados: List[Rubro] = field(default_factory=list)

    # Costos calculados
    costo_comercial: float = 0.0
    costo_logistico: float = 0.0
    costo_administrativo: float = 0.0
    costo_total: float = 0.0

    # Lejanías (gastos variables por ruta)
    lejania_comercial: float = 0.0
    lejania_logistica: float = 0.0

    # Metadata
    activa: bool = True
    color: str = "#4ECDC4"  # Para visualizaciones
    descripcion: Optional[str] = None

    @property
    def total_empleados(self) -> int:
        """Total de empleados de la marca."""
        return (self.empleados_comerciales +
                self.empleados_logisticos +
                self.empleados_administrativos)

    @property
    def margen(self) -> float:
        """
        Calcula el margen de la marca usando ventas netas.

        Returns:
            Margen como decimal (0.0 - 1.0)
        """
        ventas_base = self.ventas_mensuales
        if ventas_base == 0:
            return 0.0
            
        # Ingresos del distribuidor = Descuentos totales
        # (Pie de factura + Rebate + Financiero)
        ingresos_distribuidor = (
            self.descuento_pie_factura + 
            self.rebate + 
            self.descuento_financiero
        )
        
        # Utilidad = Ingresos - Costos Operativos
        utilidad = ingresos_distribuidor - self.costo_total
        
        # Margen = Utilidad / Ventas (Sell Out)
        return utilidad / ventas_base

    @property
    def margen_porcentaje(self) -> float:
        """Margen como porcentaje (0-100)."""
        return self.margen * 100

    @property
    def costo_como_porcentaje_ventas(self) -> float:
        """Costo total como porcentaje de ventas."""
        if self.ventas_mensuales == 0:
            return 0.0
        return (self.costo_total / self.ventas_mensuales) * 100

    def agregar_rubro_individual(self, rubro: Rubro):
        """
        Agrega un rubro individual a la marca.

        Args:
            rubro: Rubro a agregar
        """
        if rubro.es_individual():
            self.rubros_individuales.append(rubro)
            self._actualizar_costos()
        else:
            raise ValueError(f"Rubro '{rubro.id}' no es individual")

    def agregar_rubro_compartido(self, rubro: Rubro):
        """
        Agrega un rubro compartido (ya prorrateado) a la marca.

        Args:
            rubro: Rubro compartido con valor ya prorrateado
        """
        if rubro.es_compartido():
            self.rubros_compartidos_asignados.append(rubro)
            self._actualizar_costos()
        else:
            raise ValueError(f"Rubro '{rubro.id}' no es compartido")

    def _actualizar_costos(self):
        """Recalcula todos los costos de la marca."""
        # Reset
        self.costo_comercial = 0.0
        self.costo_logistico = 0.0
        self.costo_administrativo = 0.0

        # Sumar rubros individuales
        for rubro in self.rubros_individuales:
            self._agregar_costo_por_categoria(rubro)

        # Sumar rubros compartidos
        for rubro in self.rubros_compartidos_asignados:
            self._agregar_costo_por_categoria(rubro)

        # Calcular total
        self.costo_total = (
            self.costo_comercial +
            self.costo_logistico +
            self.costo_administrativo
        )

    def _agregar_costo_por_categoria(self, rubro: Rubro):
        """Agrega el costo de un rubro a la categoría correspondiente."""
        if rubro.categoria == 'comercial':
            self.costo_comercial += rubro.valor_total
        elif rubro.categoria == 'logistico':
            self.costo_logistico += rubro.valor_total
        elif rubro.categoria == 'administrativo':
            self.costo_administrativo += rubro.valor_total

    def aplicar_descuentos(
        self,
        descuento_pie_factura: float,
        rebate: float,
        descuento_financiero: float,
        ventas_netas: float,
        porcentaje_descuento_total: float
    ):
        """
        Aplica los descuentos calculados a la marca.

        Args:
            descuento_pie_factura: Monto de descuento a pie de factura
            rebate: Monto de rebate/RxP
            descuento_financiero: Monto de descuento financiero
            ventas_netas: Ventas netas después de todos los descuentos
            porcentaje_descuento_total: Porcentaje total de descuento
        """
        self.descuento_pie_factura = descuento_pie_factura
        self.rebate = rebate
        self.descuento_financiero = descuento_financiero
        self.ventas_netas_mensuales = ventas_netas
        self.porcentaje_descuento_total = porcentaje_descuento_total

    def get_rubros_por_categoria(self, categoria: str) -> List[Rubro]:
        """
        Obtiene todos los rubros de una categoría específica.

        Args:
            categoria: comercial, logistica, administrativa

        Returns:
            Lista de rubros de esa categoría
        """
        todos_rubros = self.rubros_individuales + self.rubros_compartidos_asignados
        return [r for r in todos_rubros if r.categoria == categoria]

    def calcular_factor_prorrateo(self, criterio: str, total_global: float) -> float:
        """
        Calcula el factor de prorrateo para esta marca según un criterio.

        Args:
            criterio: ventas, volumen, headcount, equitativo
            total_global: Total consolidado de todas las marcas

        Returns:
            Factor de prorrateo (0.0 - 1.0)
        """
        if total_global == 0:
            return 0.0

        if criterio == 'ventas':
            return self.ventas_mensuales / total_global

        elif criterio == 'volumen':
            return self.volumen_m3_mensual / total_global

        elif criterio == 'headcount':
            return self.total_empleados / total_global

        elif criterio == 'equitativo':
            # Se divide en partes iguales entre todas las marcas
            # Este factor se calcula fuera, aquí solo retornamos
            return 1.0  # El allocator lo dividirá entre todas las marcas

        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la marca a diccionario."""
        return {
            'marca_id': self.marca_id,
            'nombre': self.nombre,
            'ventas_mensuales': self.ventas_mensuales,
            'ventas_anuales': self.ventas_anuales,
            'descuento_pie_factura': self.descuento_pie_factura,
            'rebate': self.rebate,
            'descuento_financiero': self.descuento_financiero,
            'ventas_netas_mensuales': self.ventas_netas_mensuales,
            'porcentaje_descuento_total': self.porcentaje_descuento_total,
            'volumen_m3_mensual': self.volumen_m3_mensual,
            'volumen_ton_mensual': self.volumen_ton_mensual,
            'pallets_mensuales': self.pallets_mensuales,
            'empleados_comerciales': self.empleados_comerciales,
            'empleados_logisticos': self.empleados_logisticos,
            'empleados_administrativos': self.empleados_administrativos,
            'total_empleados': self.total_empleados,
            'costo_comercial': self.costo_comercial,
            'costo_logistico': self.costo_logistico,
            'costo_administrativo': self.costo_administrativo,
            'costo_total': self.costo_total,
            'lejania_comercial': self.lejania_comercial,
            'lejania_logistica': self.lejania_logistica,
            'margen': self.margen,
            'margen_porcentaje': self.margen_porcentaje,
            'costo_como_porcentaje_ventas': self.costo_como_porcentaje_ventas,
            'activa': self.activa,
            'color': self.color,
            'descripcion': self.descripcion,
            'rubros_individuales': [r.to_dict() for r in self.rubros_individuales],
            'rubros_compartidos': [r.to_dict() for r in self.rubros_compartidos_asignados]
        }

    def generar_resumen(self) -> str:
        """
        Genera un resumen legible de la marca.

        Returns:
            String con el resumen
        """
        lineas = [
            f"=== MARCA: {self.nombre} ===",
            f"Ventas Mensuales: ${self.ventas_mensuales:,.0f}",
            f"Ventas Anuales: ${self.ventas_anuales:,.0f}",
            "",
            "=== COSTOS ===",
            f"Comercial: ${self.costo_comercial:,.0f}",
            f"Logístico: ${self.costo_logistico:,.0f}",
            f"Administrativo: ${self.costo_administrativo:,.0f}",
            f"TOTAL: ${self.costo_total:,.0f}",
            "",
            "=== MÉTRICAS ===",
            f"Margen: {self.margen_porcentaje:.2f}%",
            f"Costo / Ventas: {self.costo_como_porcentaje_ventas:.2f}%",
            f"Empleados: {self.total_empleados}",
            "",
            "=== RECURSOS ===",
            f"Rubros Individuales: {len(self.rubros_individuales)}",
            f"Rubros Compartidos: {len(self.rubros_compartidos_asignados)}"
        ]

        return "\n".join(lineas)

    def __repr__(self) -> str:
        """Representación string de la marca."""
        return (f"Marca(id='{self.marca_id}', nombre='{self.nombre}', "
                f"ventas={self.ventas_mensuales:,.0f}, "
                f"margen={self.margen_porcentaje:.1f}%)")
