"""
Utilidades para cargar datos desde archivos YAML.

Este módulo centraliza toda la lógica de carga de datos,
facilitando la futura migración a base de datos.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataLoader:
    """
    Carga datos desde archivos YAML.

    Esta clase es el punto central de carga de datos. En el futuro,
    puede modificarse para cargar desde base de datos sin cambiar
    el código que la usa.
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Inicializa el DataLoader.

        Args:
            base_path: Ruta base del proyecto. Si no se provee, se usa la ruta actual.
        """
        if base_path is None:
            # Asume que estamos en la raíz del proyecto
            self.base_path = Path(__file__).parent.parent
        else:
            self.base_path = Path(base_path)

        logger.info(f"DataLoader inicializado con base_path: {self.base_path}")

    def _cargar_yaml(self, filepath: Path) -> Dict[str, Any]:
        """
        Carga un archivo YAML.

        Args:
            filepath: Ruta al archivo YAML

        Returns:
            Diccionario con los datos cargados

        Raises:
            FileNotFoundError: Si el archivo no existe
            yaml.YAMLError: Si hay error al parsear el YAML
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {filepath}")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            logger.debug(f"Archivo cargado exitosamente: {filepath}")
            return data
        except yaml.YAMLError as e:
            logger.error(f"Error al parsear YAML {filepath}: {e}")
            raise

    def _guardar_yaml(self, filepath: Path, data: Dict[str, Any]) -> None:
        """
        Guarda datos en un archivo YAML.

        Args:
            filepath: Ruta al archivo YAML
            data: Datos a guardar
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False,
                         allow_unicode=True, sort_keys=False)
            logger.info(f"Archivo guardado exitosamente: {filepath}")
        except Exception as e:
            logger.error(f"Error al guardar YAML {filepath}: {e}")
            raise

    # =========================================================================
    # CONFIGURACIÓN
    # =========================================================================

    def cargar_parametros_macro(self) -> Dict[str, Any]:
        """Carga los parámetros macroeconómicos."""
        filepath = self.base_path / 'config' / 'parametros_macro.yaml'
        return self._cargar_yaml(filepath)

    def cargar_factores_prestacionales(self) -> Dict[str, Any]:
        """Carga los factores prestacionales."""
        filepath = self.base_path / 'config' / 'factores_prestacionales.yaml'
        return self._cargar_yaml(filepath)

    def cargar_config_marcas(self) -> Dict[str, Any]:
        """Carga la configuración de marcas."""
        filepath = self.base_path / 'config' / 'marcas.yaml'
        return self._cargar_yaml(filepath)

    def cargar_config_empresa(self) -> Dict[str, Any]:
        """Carga la configuración de la empresa."""
        filepath = self.base_path / 'config' / 'empresa.yaml'
        return self._cargar_yaml(filepath)

    # =========================================================================
    # CATÁLOGOS
    # =========================================================================

    def cargar_catalogo_rubros(self) -> Dict[str, Any]:
        """Carga el catálogo de rubros disponibles."""
        filepath = self.base_path / 'catalogos' / 'rubros.yaml'
        return self._cargar_yaml(filepath)

    def cargar_catalogo_vehiculos(self) -> Dict[str, Any]:
        """Carga el catálogo de tipos de vehículos."""
        filepath = self.base_path / 'catalogos' / 'tipos_vehiculos.yaml'
        return self._cargar_yaml(filepath)

    # =========================================================================
    # DATOS POR MARCA
    # =========================================================================

    def cargar_marca_comercial(self, marca_id: str) -> Dict[str, Any]:
        """
        Carga los datos comerciales de una marca.

        Args:
            marca_id: ID de la marca

        Returns:
            Datos comerciales de la marca
        """
        filepath = self.base_path / 'data' / 'marcas' / marca_id / 'comercial.yaml'
        return self._cargar_yaml(filepath)

    def cargar_marca_logistica(self, marca_id: str) -> Dict[str, Any]:
        """Carga los datos logísticos de una marca."""
        filepath = self.base_path / 'data' / 'marcas' / marca_id / 'logistica.yaml'
        return self._cargar_yaml(filepath)

    def cargar_marca_ventas(self, marca_id: str) -> Dict[str, Any]:
        """Carga las proyecciones de ventas de una marca."""
        filepath = self.base_path / 'data' / 'marcas' / marca_id / 'ventas.yaml'
        return self._cargar_yaml(filepath)

    def cargar_marca_completa(self, marca_id: str) -> Dict[str, Any]:
        """
        Carga todos los datos de una marca.

        Args:
            marca_id: ID de la marca

        Returns:
            Diccionario con comercial, logistica y ventas
        """
        return {
            'marca_id': marca_id,
            'comercial': self.cargar_marca_comercial(marca_id),
            'logistica': self.cargar_marca_logistica(marca_id),
            'ventas': self.cargar_marca_ventas(marca_id)
        }

    def guardar_marca_comercial(self, marca_id: str, data: Dict[str, Any]) -> None:
        """Guarda los datos comerciales de una marca."""
        filepath = self.base_path / 'data' / 'marcas' / marca_id / 'comercial.yaml'
        self._guardar_yaml(filepath, data)

    def guardar_marca_logistica(self, marca_id: str, data: Dict[str, Any]) -> None:
        """Guarda los datos logísticos de una marca."""
        filepath = self.base_path / 'data' / 'marcas' / marca_id / 'logistica.yaml'
        self._guardar_yaml(filepath, data)

    def guardar_marca_ventas(self, marca_id: str, data: Dict[str, Any]) -> None:
        """Guarda las proyecciones de ventas de una marca."""
        filepath = self.base_path / 'data' / 'marcas' / marca_id / 'ventas.yaml'
        self._guardar_yaml(filepath, data)

    # =========================================================================
    # DATOS COMPARTIDOS
    # =========================================================================

    def cargar_compartidos_administrativo(self) -> Dict[str, Any]:
        """Carga los recursos administrativos compartidos."""
        filepath = self.base_path / 'data' / 'compartidos' / 'administrativo.yaml'
        return self._cargar_yaml(filepath)

    def cargar_compartidos_logistica(self) -> Dict[str, Any]:
        """Carga los recursos logísticos compartidos."""
        filepath = self.base_path / 'data' / 'compartidos' / 'logistica.yaml'
        return self._cargar_yaml(filepath)

    def guardar_compartidos_administrativo(self, data: Dict[str, Any]) -> None:
        """Guarda los recursos administrativos compartidos."""
        filepath = self.base_path / 'data' / 'compartidos' / 'administrativo.yaml'
        self._guardar_yaml(filepath, data)

    # =========================================================================
    # UTILIDADES
    # =========================================================================

    def listar_marcas(self) -> List[str]:
        """
        Lista todas las marcas disponibles.

        Returns:
            Lista de IDs de marcas
        """
        marcas_path = self.base_path / 'data' / 'marcas'
        if not marcas_path.exists():
            return []

        marcas = [
            d.name for d in marcas_path.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        ]

        logger.info(f"Marcas encontradas: {marcas}")
        return marcas

    def marca_existe(self, marca_id: str) -> bool:
        """
        Verifica si una marca existe.

        Args:
            marca_id: ID de la marca

        Returns:
            True si la marca existe
        """
        marca_path = self.base_path / 'data' / 'marcas' / marca_id
        return marca_path.exists() and marca_path.is_dir()

    def crear_marca(self, marca_id: str, nombre: str) -> None:
        """
        Crea la estructura de carpetas para una nueva marca.

        Args:
            marca_id: ID de la marca
            nombre: Nombre de la marca
        """
        marca_path = self.base_path / 'data' / 'marcas' / marca_id
        marca_path.mkdir(parents=True, exist_ok=True)

        # Crear archivos base vacíos
        comercial_template = {
            'marca_id': marca_id,
            'nombre': nombre,
            'proyeccion_ventas_mensual': 0,
            'recursos_comerciales': {
                'vendedores': [],
                'supervisores': [],
            },
            'costos_adicionales': {}
        }

        logistica_template = {
            'marca_id': marca_id,
            'vehiculos': {
                'renting': [],
                'tradicional': []
            },
            'personal': {}
        }

        ventas_template = {
            'marca_id': marca_id,
            'ventas_mensuales': {},
            'resumen_anual': {}
        }

        self.guardar_marca_comercial(marca_id, comercial_template)
        self.guardar_marca_logistica(marca_id, logistica_template)
        self.guardar_marca_ventas(marca_id, ventas_template)

        logger.info(f"Marca '{marca_id}' creada exitosamente")


# Instancia global del loader (singleton pattern)
_loader_instance = None

def get_loader() -> DataLoader:
    """
    Obtiene la instancia global del DataLoader.

    Returns:
        Instancia de DataLoader
    """
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = DataLoader()
    return _loader_instance


# Funciones de conveniencia
def cargar_catalogo_rubros() -> Dict[str, Any]:
    """Función de conveniencia para cargar el catálogo de rubros."""
    return get_loader().cargar_catalogo_rubros()


def cargar_marca(marca_id: str) -> Dict[str, Any]:
    """Función de conveniencia para cargar todos los datos de una marca."""
    return get_loader().cargar_marca_completa(marca_id)


def listar_marcas() -> List[str]:
    """Función de conveniencia para listar todas las marcas."""
    return get_loader().listar_marcas()
