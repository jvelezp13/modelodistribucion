"""
Modelo de Rubro.

Un rubro representa un ítem de costo en el sistema (personal, vehículo, servicio, etc.).
Puede ser individual (asignado 100% a una marca) o compartido (prorrateado entre marcas).
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class TipoAsignacion(Enum):
    """Tipo de asignación de un rubro."""
    INDIVIDUAL = "individual"  # 100% dedicado a una marca
    COMPARTIDO = "compartido"  # Compartido entre marcas


class CriterioProrrateo(Enum):
    """Criterio de prorrateo para rubros compartidos."""
    VENTAS = "ventas"  # Proporcional a las ventas
    VOLUMEN = "volumen"  # Proporcional al volumen (m3, ton, pallets)
    HEADCOUNT = "headcount"  # Proporcional a cantidad de empleados
    USO_REAL = "uso_real"  # Según uso medido real
    EQUITATIVO = "equitativo"  # Todas las marcas pagan por igual


@dataclass
class Rubro:
    """
    Representa un rubro de costo.

    Un rubro puede ser:
    - Personal (vendedor, conductor, contador, etc.)
    - Vehículo (NHR, pickup, motocarro, etc.)
    - Infraestructura (bodega, oficina, etc.)
    - Servicio (internet, seguridad, etc.)
    """

    # Identificación
    id: str
    nombre: str
    categoria: str  # comercial, logistica, administrativa
    tipo: str  # personal, vehiculo, infraestructura, servicio

    # Asignación
    tipo_asignacion: TipoAsignacion
    marca_id: Optional[str] = None  # Si es individual, a qué marca pertenece

    # Prorrateo (solo para rubros compartidos)
    criterio_prorrateo: Optional[CriterioProrrateo] = None
    porcentaje_dedicacion: Optional[float] = None  # Si es compartido parcial (0.0 - 1.0)

    # Valores
    cantidad: int = 1
    valor_unitario: float = 0.0  # Costo unitario mensual
    valor_total: float = 0.0  # cantidad × valor_unitario

    # Metadata
    descripcion: Optional[str] = None
    activo: bool = True
    datos_adicionales: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calcula valores derivados después de la inicialización."""
        if self.valor_total == 0.0:
            self.valor_total = self.cantidad * self.valor_unitario

        # Validaciones
        if self.tipo_asignacion == TipoAsignacion.INDIVIDUAL and not self.marca_id:
            raise ValueError("Rubros individuales deben tener marca_id")

        if self.tipo_asignacion == TipoAsignacion.COMPARTIDO and not self.criterio_prorrateo:
            # Criterio por defecto
            self.criterio_prorrateo = CriterioProrrateo.VENTAS

    def es_individual(self) -> bool:
        """Verifica si el rubro es individual."""
        return self.tipo_asignacion == TipoAsignacion.INDIVIDUAL

    def es_compartido(self) -> bool:
        """Verifica si el rubro es compartido."""
        return self.tipo_asignacion == TipoAsignacion.COMPARTIDO

    def calcular_asignacion_marca(self, marca_id: str, factor_prorrateo: float = 1.0) -> float:
        """
        Calcula cuánto de este rubro le corresponde a una marca específica.

        Args:
            marca_id: ID de la marca
            factor_prorrateo: Factor de prorrateo calculado (0.0 - 1.0)

        Returns:
            Valor asignado a la marca
        """
        if self.es_individual():
            # Si es individual y pertenece a esta marca, se asigna el 100%
            if self.marca_id == marca_id:
                return self.valor_total
            else:
                return 0.0

        elif self.es_compartido():
            # Si tiene porcentaje de dedicación específico
            if self.porcentaje_dedicacion is not None:
                return self.valor_total * self.porcentaje_dedicacion

            # Si no, se usa el factor de prorrateo
            return self.valor_total * factor_prorrateo

        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el rubro a diccionario."""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'categoria': self.categoria,
            'tipo': self.tipo,
            'tipo_asignacion': self.tipo_asignacion.value,
            'marca_id': self.marca_id,
            'criterio_prorrateo': self.criterio_prorrateo.value if self.criterio_prorrateo else None,
            'porcentaje_dedicacion': self.porcentaje_dedicacion,
            'cantidad': self.cantidad,
            'valor_unitario': self.valor_unitario,
            'valor_total': self.valor_total,
            'descripcion': self.descripcion,
            'activo': self.activo,
            'datos_adicionales': self.datos_adicionales
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rubro':
        """Crea un Rubro desde un diccionario."""
        # Convertir strings a enums
        tipo_asignacion = TipoAsignacion(data.get('tipo_asignacion', 'individual'))

        criterio_prorrateo = None
        if data.get('criterio_prorrateo'):
            criterio_prorrateo = CriterioProrrateo(data['criterio_prorrateo'])

        return cls(
            id=data['id'],
            nombre=data['nombre'],
            categoria=data['categoria'],
            tipo=data['tipo'],
            tipo_asignacion=tipo_asignacion,
            marca_id=data.get('marca_id'),
            criterio_prorrateo=criterio_prorrateo,
            porcentaje_dedicacion=data.get('porcentaje_dedicacion'),
            cantidad=data.get('cantidad', 1),
            valor_unitario=data.get('valor_unitario', 0.0),
            valor_total=data.get('valor_total', 0.0),
            descripcion=data.get('descripcion'),
            activo=data.get('activo', True),
            datos_adicionales=data.get('datos_adicionales', {})
        )

    def __repr__(self) -> str:
        """Representación string del rubro."""
        return (f"Rubro(id='{self.id}', nombre='{self.nombre}', "
                f"categoria='{self.categoria}', tipo_asignacion={self.tipo_asignacion.value}, "
                f"valor_total={self.valor_total:,.0f})")


@dataclass
class RubroPersonal(Rubro):
    """Rubro especializado para personal (vendedor, conductor, etc.)."""

    salario_base: float = 0.0
    prestaciones: float = 0.0
    subsidio_transporte: float = 0.0
    factor_prestacional: float = 0.0

    def __post_init__(self):
        """Calcula el costo total del personal."""
        # Calcular prestaciones si no están definidas
        if self.prestaciones == 0.0 and self.factor_prestacional > 0.0:
            self.prestaciones = self.salario_base * self.factor_prestacional

        # Calcular valor unitario
        self.valor_unitario = self.salario_base + self.prestaciones + self.subsidio_transporte

        # Llamar al __post_init__ del padre
        super().__post_init__()

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el rubro de personal a diccionario con campos adicionales."""
        base_dict = super().to_dict()
        base_dict.update({
            'salario_base': self.salario_base,
            'prestaciones': self.prestaciones,
            'subsidio_transporte': self.subsidio_transporte,
            'factor_prestacional': self.factor_prestacional,
        })
        return base_dict


@dataclass
class RubroVehiculo(Rubro):
    """Rubro especializado para vehículos."""

    tipo_vehiculo: str = ""  # nhr, pickup, motocarro, etc.
    esquema: str = "renting"  # renting, tradicional, tercero

    # Costos según esquema
    # Renting
    canon_mensual: float = 0.0
    combustible: float = 0.0
    mantenimiento: float = 0.0
    lavada: float = 0.0
    reposicion: float = 0.0

    # Tradicional
    depreciacion: float = 0.0
    seguro: float = 0.0
    impuestos: float = 0.0

    # Tercero
    valor_flete_mensual: float = 0.0

    def __post_init__(self):
        """Calcula el costo total del vehículo."""
        if self.esquema == "renting":
            self.valor_unitario = (
                self.canon_mensual + self.combustible +
                self.lavada + self.reposicion
            )
        else:  # tradicional
            self.valor_unitario = (
                self.depreciacion + self.mantenimiento +
                self.seguro + self.combustible +
                self.impuestos / 12  # Impuestos anuales a mensual
            )

        super().__post_init__()

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el rubro de vehículo a diccionario con campos adicionales."""
        base_dict = super().to_dict()
        base_dict.update({
            'tipo_vehiculo': self.tipo_vehiculo,
            'esquema': self.esquema,
            'canon_mensual': self.canon_mensual,
            'combustible': self.combustible,
            'mantenimiento': self.mantenimiento,
            'lavada': self.lavada,
            'reposicion': self.reposicion,
            'depreciacion': self.depreciacion,
            'seguro': self.seguro,
            'impuestos': self.impuestos,
            'valor_flete_mensual': self.valor_flete_mensual,
        })
        return base_dict
