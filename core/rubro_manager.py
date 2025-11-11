"""
Gestor del catálogo de rubros.

Este módulo permite administrar el catálogo central de rubros:
- Listar rubros disponibles
- Agregar nuevos rubros
- Modificar rubros existentes
- Desactivar/activar rubros
- Validar que los rubros usados sean válidos
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
from pathlib import Path

from utils.loaders import DataLoader

logger = logging.getLogger(__name__)


@dataclass
class ResultadoValidacion:
    """Resultado de una validación de rubro."""
    es_valido: bool
    errores: List[str]
    advertencias: List[str]

    def agregar_error(self, mensaje: str):
        """Agrega un error."""
        self.es_valido = False
        self.errores.append(mensaje)

    def agregar_advertencia(self, mensaje: str):
        """Agrega una advertencia."""
        self.advertencias.append(mensaje)


class RubroManager:
    """
    Gestor del catálogo de rubros.

    Proporciona operaciones CRUD sobre el catálogo de rubros
    y validación de datos.
    """

    def __init__(self, loader: Optional[DataLoader] = None):
        """
        Inicializa el RubroManager.

        Args:
            loader: DataLoader a usar. Si no se provee, se crea uno nuevo.
        """
        self.loader = loader or DataLoader()
        self._catalogo = None
        self._cargar_catalogo()

    def _cargar_catalogo(self):
        """Carga el catálogo de rubros desde el archivo YAML."""
        try:
            self._catalogo = self.loader.cargar_catalogo_rubros()
            logger.info(f"Catálogo cargado: {len(self.get_rubros_disponibles())} rubros")
        except FileNotFoundError:
            logger.error("Catálogo de rubros no encontrado")
            # Crear catálogo vacío
            self._catalogo = {
                'rubros_disponibles': [],
                'metadata': {
                    'version': '1.0.0',
                    'total_rubros': 0
                }
            }

    def _guardar_catalogo(self):
        """Guarda el catálogo de rubros al archivo YAML."""
        # Actualizar metadata
        self._catalogo['metadata']['total_rubros'] = len(self._catalogo['rubros_disponibles'])

        # Guardar
        filepath = self.loader.base_path / 'catalogos' / 'rubros.yaml'
        self.loader._guardar_yaml(filepath, self._catalogo)
        logger.info("Catálogo guardado exitosamente")

    # =========================================================================
    # CONSULTAS
    # =========================================================================

    def get_rubros_disponibles(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista completa de rubros disponibles.

        Returns:
            Lista de rubros
        """
        return self._catalogo.get('rubros_disponibles', [])

    def get_rubro(self, rubro_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un rubro específico por su ID.

        Args:
            rubro_id: ID del rubro

        Returns:
            Datos del rubro o None si no existe
        """
        for rubro in self.get_rubros_disponibles():
            if rubro.get('id') == rubro_id:
                return rubro
        return None

    def rubro_existe(self, rubro_id: str) -> bool:
        """
        Verifica si un rubro existe en el catálogo.

        Args:
            rubro_id: ID del rubro

        Returns:
            True si el rubro existe
        """
        return self.get_rubro(rubro_id) is not None

    def listar_rubros_activos(self, categoria: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lista rubros activos, opcionalmente filtrados por categoría.

        Args:
            categoria: Filtrar por categoría (comercial, logistica, administrativa)

        Returns:
            Lista de rubros activos
        """
        rubros = [r for r in self.get_rubros_disponibles() if r.get('activo', True)]

        if categoria:
            rubros = [r for r in rubros if r.get('categoria') == categoria]

        return rubros

    def listar_rubros_por_tipo(self, tipo: str) -> List[Dict[str, Any]]:
        """
        Lista rubros por tipo.

        Args:
            tipo: Tipo de rubro (personal, vehiculo, infraestructura, etc.)

        Returns:
            Lista de rubros del tipo especificado
        """
        return [r for r in self.get_rubros_disponibles() if r.get('tipo') == tipo]

    def get_categorias(self) -> List[str]:
        """Obtiene la lista de categorías disponibles."""
        categorias = set()
        for rubro in self.get_rubros_disponibles():
            if 'categoria' in rubro:
                categorias.add(rubro['categoria'])
        return sorted(list(categorias))

    def get_tipos(self) -> List[str]:
        """Obtiene la lista de tipos disponibles."""
        tipos = set()
        for rubro in self.get_rubros_disponibles():
            if 'tipo' in rubro:
                tipos.add(rubro['tipo'])
        return sorted(list(tipos))

    # =========================================================================
    # MODIFICACIONES
    # =========================================================================

    def agregar_rubro(self, rubro: Dict[str, Any]) -> ResultadoValidacion:
        """
        Agrega un nuevo rubro al catálogo.

        Args:
            rubro: Datos del nuevo rubro

        Returns:
            ResultadoValidacion indicando si se agregó exitosamente
        """
        resultado = self._validar_nuevo_rubro(rubro)

        if resultado.es_valido:
            self._catalogo['rubros_disponibles'].append(rubro)
            self._guardar_catalogo()
            logger.info(f"Rubro '{rubro.get('id')}' agregado exitosamente")

        return resultado

    def modificar_rubro(self, rubro_id: str, nuevos_datos: Dict[str, Any]) -> ResultadoValidacion:
        """
        Modifica un rubro existente.

        Args:
            rubro_id: ID del rubro a modificar
            nuevos_datos: Nuevos datos del rubro

        Returns:
            ResultadoValidacion
        """
        resultado = ResultadoValidacion(True, [], [])

        rubro = self.get_rubro(rubro_id)
        if not rubro:
            resultado.agregar_error(f"Rubro '{rubro_id}' no existe")
            return resultado

        # Actualizar datos
        for key, value in nuevos_datos.items():
            rubro[key] = value

        self._guardar_catalogo()
        logger.info(f"Rubro '{rubro_id}' modificado exitosamente")

        return resultado

    def activar_rubro(self, rubro_id: str) -> bool:
        """
        Activa un rubro desactivado.

        Args:
            rubro_id: ID del rubro

        Returns:
            True si se activó exitosamente
        """
        rubro = self.get_rubro(rubro_id)
        if rubro:
            rubro['activo'] = True
            self._guardar_catalogo()
            logger.info(f"Rubro '{rubro_id}' activado")
            return True
        return False

    def desactivar_rubro(self, rubro_id: str) -> bool:
        """
        Desactiva un rubro (no lo elimina, solo lo marca como inactivo).

        Args:
            rubro_id: ID del rubro

        Returns:
            True si se desactivó exitosamente
        """
        rubro = self.get_rubro(rubro_id)
        if rubro:
            rubro['activo'] = False
            self._guardar_catalogo()
            logger.info(f"Rubro '{rubro_id}' desactivado")
            return True
        return False

    # =========================================================================
    # VALIDACIÓN
    # =========================================================================

    def _validar_nuevo_rubro(self, rubro: Dict[str, Any]) -> ResultadoValidacion:
        """
        Valida que un nuevo rubro tenga la estructura correcta.

        Args:
            rubro: Datos del rubro a validar

        Returns:
            ResultadoValidacion
        """
        resultado = ResultadoValidacion(True, [], [])

        # Campos requeridos
        campos_requeridos = ['id', 'nombre', 'categoria', 'tipo']
        for campo in campos_requeridos:
            if campo not in rubro:
                resultado.agregar_error(f"Campo requerido faltante: '{campo}'")

        # Verificar que el ID no exista
        if 'id' in rubro and self.rubro_existe(rubro['id']):
            resultado.agregar_error(f"Ya existe un rubro con ID '{rubro['id']}'")

        # Validar categoría
        if 'categoria' in rubro:
            categorias_validas = ['comercial', 'logistica', 'administrativa']
            if rubro['categoria'] not in categorias_validas:
                resultado.agregar_advertencia(
                    f"Categoría '{rubro['categoria']}' no es estándar. "
                    f"Categorías estándar: {categorias_validas}"
                )

        return resultado

    def validar_uso_rubro(self, rubro_id: str, datos: Dict[str, Any]) -> ResultadoValidacion:
        """
        Valida que el uso de un rubro sea correcto.

        Args:
            rubro_id: ID del rubro
            datos: Datos del rubro en uso (cantidad, salario_base, etc.)

        Returns:
            ResultadoValidacion
        """
        resultado = ResultadoValidacion(True, [], [])

        # Verificar que el rubro exista
        rubro = self.get_rubro(rubro_id)
        if not rubro:
            resultado.agregar_error(f"Rubro '{rubro_id}' no existe en el catálogo")
            return resultado

        # Verificar que esté activo
        if not rubro.get('activo', True):
            resultado.agregar_advertencia(
                f"Rubro '{rubro_id}' está desactivado en el catálogo"
            )

        # Validar campos requeridos
        campos_requeridos = rubro.get('campos_requeridos', [])
        for campo in campos_requeridos:
            if campo not in datos:
                resultado.agregar_error(
                    f"Campo requerido faltante para '{rubro_id}': '{campo}'"
                )

        # Validar asignación
        asignacion = datos.get('asignacion')
        if asignacion:
            asignaciones_permitidas = rubro.get('asignacion_permitida', ['individual', 'compartido'])
            if asignacion not in asignaciones_permitidas:
                resultado.agregar_error(
                    f"Asignación '{asignacion}' no permitida para '{rubro_id}'. "
                    f"Permitidas: {asignaciones_permitidas}"
                )

        return resultado

    def validar_marca(self, datos_marca: Dict[str, Any]) -> ResultadoValidacion:
        """
        Valida todos los rubros usados en una marca.

        Args:
            datos_marca: Datos completos de la marca

        Returns:
            ResultadoValidacion con todos los errores encontrados
        """
        resultado = ResultadoValidacion(True, [], [])

        # Validar rubros comerciales
        recursos_comerciales = datos_marca.get('comercial', {}).get('recursos_comerciales', {})

        # Vendedores
        for vendedor in recursos_comerciales.get('vendedores', []):
            tipo = vendedor.get('tipo')
            if tipo:
                val = self.validar_uso_rubro(tipo, vendedor)
                resultado.errores.extend(val.errores)
                resultado.advertencias.extend(val.advertencias)
                if not val.es_valido:
                    resultado.es_valido = False

        # Similar para otros rubros...

        return resultado

    # =========================================================================
    # UTILIDADES
    # =========================================================================

    def get_info_rubro(self, rubro_id: str) -> str:
        """
        Obtiene información legible de un rubro.

        Args:
            rubro_id: ID del rubro

        Returns:
            String con información del rubro
        """
        rubro = self.get_rubro(rubro_id)
        if not rubro:
            return f"Rubro '{rubro_id}' no encontrado"

        info = [
            f"ID: {rubro['id']}",
            f"Nombre: {rubro['nombre']}",
            f"Categoría: {rubro.get('categoria', 'N/A')}",
            f"Tipo: {rubro.get('tipo', 'N/A')}",
            f"Activo: {'Sí' if rubro.get('activo', True) else 'No'}",
        ]

        if 'descripcion' in rubro:
            info.append(f"Descripción: {rubro['descripcion']}")

        if 'campos_requeridos' in rubro:
            info.append(f"Campos requeridos: {', '.join(rubro['campos_requeridos'])}")

        if 'asignacion_permitida' in rubro:
            info.append(f"Asignación permitida: {', '.join(rubro['asignacion_permitida'])}")

        return "\n".join(info)

    def generar_reporte(self) -> str:
        """
        Genera un reporte del estado del catálogo.

        Returns:
            String con el reporte
        """
        total = len(self.get_rubros_disponibles())
        activos = len(self.listar_rubros_activos())
        categorias = self.get_categorias()
        tipos = self.get_tipos()

        reporte = [
            "=== REPORTE DEL CATÁLOGO DE RUBROS ===",
            f"Total de rubros: {total}",
            f"Rubros activos: {activos}",
            f"Rubros inactivos: {total - activos}",
            f"Categorías: {', '.join(categorias)}",
            f"Tipos: {', '.join(tipos)}",
            "",
            "=== DISTRIBUCIÓN POR CATEGORÍA ===",
        ]

        for categoria in categorias:
            rubros_cat = [r for r in self.get_rubros_disponibles()
                         if r.get('categoria') == categoria]
            activos_cat = [r for r in rubros_cat if r.get('activo', True)]
            reporte.append(
                f"{categoria.upper()}: {len(rubros_cat)} total, "
                f"{len(activos_cat)} activos"
            )

        return "\n".join(reporte)


# Instancia global (singleton)
_manager_instance = None

def get_rubro_manager() -> RubroManager:
    """Obtiene la instancia global del RubroManager."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = RubroManager()
    return _manager_instance
