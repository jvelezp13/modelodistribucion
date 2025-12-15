"""
Importador de Lista de Precios desde CSV/JSON.

Permite cargar masivamente productos con precios y demanda proyectada
desde archivos procesados externamente (ej: con AI).
"""
import csv
import json
import io
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ResultadoImportacion:
    """Resultado de una importación de lista de precios."""
    total_procesados: int = 0
    productos_creados: int = 0
    productos_actualizados: int = 0
    demandas_creadas: int = 0
    errores: List[str] = None

    def __post_init__(self):
        if self.errores is None:
            self.errores = []

    @property
    def exitoso(self) -> bool:
        return len(self.errores) == 0 or self.productos_creados > 0 or self.productos_actualizados > 0


MESES = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
]


def validar_fila_csv(fila: Dict[str, str], num_fila: int) -> Tuple[bool, Optional[str]]:
    """
    Valida una fila del CSV.

    Returns:
        (es_valida, mensaje_error)
    """
    # SKU es obligatorio
    if not fila.get('sku', '').strip():
        return False, f"Fila {num_fila}: SKU es obligatorio"

    # Validar método de captura (si se especifica)
    metodo = fila.get('metodo_captura', '').strip().lower()
    if metodo and metodo not in ('directo', 'descuento_sobre_venta', 'margen_sobre_compra'):
        return False, f"Fila {num_fila}: metodo_captura inválido '{metodo}'"

    # Validación flexible: solo advertir si no hay precios, pero permitir continuar
    # Los precios se pueden completar después manualmente
    return True, None


def parse_decimal(valor: str, default: Optional[Decimal] = None) -> Optional[Decimal]:
    """Convierte string a Decimal de forma segura."""
    if not valor or not valor.strip():
        return default
    try:
        # Limpiar el valor (remover comas de miles, espacios)
        valor_limpio = valor.strip().replace(',', '').replace('$', '')
        return Decimal(valor_limpio)
    except (InvalidOperation, ValueError):
        return default


def parse_int(valor: str, default: int = 0) -> int:
    """Convierte string a int de forma segura."""
    if not valor or not valor.strip():
        return default
    try:
        valor_limpio = valor.strip().replace(',', '').replace('.', '')
        return int(valor_limpio)
    except ValueError:
        return default


def importar_lista_precios_csv(
    config,  # ProyeccionVentasConfig
    archivo_csv,
    actualizar_existentes: bool = True,
    crear_productos_faltantes: bool = False
) -> ResultadoImportacion:
    """
    Importa lista de precios desde archivo CSV.

    Formato esperado del CSV:
    sku,nombre,precio_compra,precio_venta,metodo_captura,porcentaje_descuento,porcentaje_margen,unidades_enero,...,unidades_diciembre

    Args:
        config: ProyeccionVentasConfig de destino
        archivo_csv: Archivo CSV (FileField o similar)
        actualizar_existentes: Si True, actualiza productos existentes
        crear_productos_faltantes: Si True, crea Productos que no existen

    Returns:
        ResultadoImportacion con estadísticas
    """
    from core.models import Producto, ListaPreciosProducto, ProyeccionDemandaProducto

    resultado = ResultadoImportacion()

    try:
        # Leer contenido del archivo
        if hasattr(archivo_csv, 'read'):
            contenido = archivo_csv.read()
            if isinstance(contenido, bytes):
                contenido = contenido.decode('utf-8-sig')  # utf-8 con BOM
        else:
            contenido = str(archivo_csv)

        # Parsear CSV
        reader = csv.DictReader(io.StringIO(contenido))

        for num_fila, fila in enumerate(reader, start=2):  # start=2 porque fila 1 es header
            resultado.total_procesados += 1

            # Validar fila
            es_valida, error = validar_fila_csv(fila, num_fila)
            if not es_valida:
                resultado.errores.append(error)
                continue

            sku = fila['sku'].strip()
            nombre = fila.get('nombre', '').strip() or sku

            # Preparar precio para el producto (se necesita para crear Producto)
            precio_venta_valor = parse_decimal(fila.get('precio_venta'))
            precio_compra_valor = parse_decimal(fila.get('precio_compra'))
            precio_unitario = precio_venta_valor or precio_compra_valor or Decimal('0')

            # Buscar o crear Producto
            try:
                producto = Producto.objects.get(sku=sku, marca=config.marca)
            except Producto.DoesNotExist:
                if crear_productos_faltantes:
                    producto = Producto.objects.create(
                        sku=sku,
                        nombre=nombre,
                        marca=config.marca,
                        precio_unitario=precio_unitario,
                        activo=True
                    )
                    logger.info(f"Producto creado: {sku}")
                else:
                    resultado.errores.append(f"Fila {num_fila}: Producto con SKU '{sku}' no existe")
                    continue

            # Preparar datos de precio para ListaPreciosProducto
            metodo = fila.get('metodo_captura', '').strip().lower() or 'directo'
            porcentaje_descuento = parse_decimal(fila.get('porcentaje_descuento'))
            porcentaje_margen = parse_decimal(fila.get('porcentaje_margen'))

            # Buscar o crear ListaPreciosProducto
            lista_precio, creado = ListaPreciosProducto.objects.get_or_create(
                config=config,
                producto=producto,
                defaults={
                    'metodo_captura': metodo,
                    'precio_compra': precio_compra_valor,
                    'precio_venta': precio_venta_valor,
                    'porcentaje_descuento': porcentaje_descuento,
                    'porcentaje_margen': porcentaje_margen,
                    'activo': True
                }
            )

            if creado:
                resultado.productos_creados += 1
            elif actualizar_existentes:
                lista_precio.metodo_captura = metodo
                lista_precio.precio_compra = precio_compra_valor
                lista_precio.precio_venta = precio_venta_valor
                lista_precio.porcentaje_descuento = porcentaje_descuento
                lista_precio.porcentaje_margen = porcentaje_margen
                lista_precio.activo = True
                lista_precio.save()
                resultado.productos_actualizados += 1

            # Procesar unidades mensuales si existen
            tiene_unidades = any(
                fila.get(f'unidades_{mes}') for mes in MESES
            )

            if tiene_unidades:
                # Crear o actualizar ProyeccionDemandaProducto
                demanda, demanda_creada = ProyeccionDemandaProducto.objects.get_or_create(
                    lista_precio=lista_precio,
                    defaults={'metodo_demanda': 'precio_unidades'}
                )

                # Asignar unidades por mes
                for mes in MESES:
                    valor = parse_int(fila.get(f'unidades_{mes}', '0'))
                    setattr(demanda, f'unidades_{mes}', valor)

                demanda.metodo_demanda = 'precio_unidades'
                demanda.save()

                if demanda_creada:
                    resultado.demandas_creadas += 1

        logger.info(
            f"Importación completada: {resultado.productos_creados} creados, "
            f"{resultado.productos_actualizados} actualizados, "
            f"{len(resultado.errores)} errores"
        )

    except Exception as e:
        logger.error(f"Error en importación: {e}")
        resultado.errores.append(f"Error general: {str(e)}")

    return resultado


def importar_lista_precios_json(
    config,  # ProyeccionVentasConfig
    archivo_json,
    actualizar_existentes: bool = True,
    crear_productos_faltantes: bool = False
) -> ResultadoImportacion:
    """
    Importa lista de precios desde archivo JSON.

    Formato esperado:
    {
        "productos": [
            {
                "sku": "SKU001",
                "nombre": "Producto A",
                "metodo_captura": "directo",
                "precio_compra": 8500,
                "precio_venta": 10000,
                "unidades": {
                    "enero": 100, "febrero": 120, ...
                }
            }
        ]
    }
    """
    from core.models import Producto, ListaPreciosProducto, ProyeccionDemandaProducto

    resultado = ResultadoImportacion()

    try:
        # Leer contenido
        if hasattr(archivo_json, 'read'):
            contenido = archivo_json.read()
            if isinstance(contenido, bytes):
                contenido = contenido.decode('utf-8')
        else:
            contenido = str(archivo_json)

        data = json.loads(contenido)
        productos_data = data.get('productos', [])

        for idx, prod in enumerate(productos_data, start=1):
            resultado.total_procesados += 1

            sku = prod.get('sku', '').strip()
            if not sku:
                resultado.errores.append(f"Producto {idx}: SKU es obligatorio")
                continue

            nombre = prod.get('nombre', sku)

            # Buscar o crear Producto
            try:
                producto = Producto.objects.get(sku=sku, marca=config.marca)
            except Producto.DoesNotExist:
                if crear_productos_faltantes:
                    producto = Producto.objects.create(
                        sku=sku,
                        nombre=nombre,
                        marca=config.marca,
                        activo=True
                    )
                else:
                    resultado.errores.append(f"Producto {idx}: SKU '{sku}' no existe")
                    continue

            # Datos de precio
            metodo = prod.get('metodo_captura', 'directo')
            precio_compra = Decimal(str(prod.get('precio_compra', 0))) if prod.get('precio_compra') else None
            precio_venta = Decimal(str(prod.get('precio_venta', 0))) if prod.get('precio_venta') else None
            porcentaje_descuento = Decimal(str(prod.get('porcentaje_descuento', 0))) if prod.get('porcentaje_descuento') else None
            porcentaje_margen = Decimal(str(prod.get('porcentaje_margen', 0))) if prod.get('porcentaje_margen') else None

            # Crear o actualizar ListaPreciosProducto
            lista_precio, creado = ListaPreciosProducto.objects.get_or_create(
                config=config,
                producto=producto,
                defaults={
                    'metodo_captura': metodo,
                    'precio_compra': precio_compra,
                    'precio_venta': precio_venta,
                    'porcentaje_descuento': porcentaje_descuento,
                    'porcentaje_margen': porcentaje_margen,
                    'activo': True
                }
            )

            if creado:
                resultado.productos_creados += 1
            elif actualizar_existentes:
                lista_precio.metodo_captura = metodo
                lista_precio.precio_compra = precio_compra
                lista_precio.precio_venta = precio_venta
                lista_precio.porcentaje_descuento = porcentaje_descuento
                lista_precio.porcentaje_margen = porcentaje_margen
                lista_precio.save()
                resultado.productos_actualizados += 1

            # Unidades
            unidades = prod.get('unidades', {})
            if unidades:
                demanda, demanda_creada = ProyeccionDemandaProducto.objects.get_or_create(
                    lista_precio=lista_precio,
                    defaults={'metodo_demanda': 'precio_unidades'}
                )

                for mes in MESES:
                    valor = int(unidades.get(mes, 0))
                    setattr(demanda, f'unidades_{mes}', valor)

                demanda.metodo_demanda = 'precio_unidades'
                demanda.save()

                if demanda_creada:
                    resultado.demandas_creadas += 1

    except json.JSONDecodeError as e:
        resultado.errores.append(f"Error parseando JSON: {e}")
    except Exception as e:
        logger.error(f"Error en importación JSON: {e}")
        resultado.errores.append(f"Error general: {str(e)}")

    return resultado


def generar_plantilla_csv() -> str:
    """
    Genera una plantilla CSV de ejemplo.

    Returns:
        String con contenido CSV
    """
    header = [
        'sku', 'nombre', 'metodo_captura',
        'precio_compra', 'precio_venta',
        'porcentaje_descuento', 'porcentaje_margen'
    ] + [f'unidades_{mes}' for mes in MESES]

    filas = [
        # Ejemplo método directo
        ['SKU001', 'Producto Ejemplo A', 'directo', '8500', '10000', '', ''] +
        ['100', '120', '110', '130', '140', '150', '160', '150', '140', '130', '200', '250'],
        # Ejemplo descuento sobre venta
        ['SKU002', 'Producto Ejemplo B', 'descuento_sobre_venta', '', '12000', '15', ''] +
        ['80', '90', '85', '95', '100', '110', '120', '115', '105', '95', '150', '180'],
        # Ejemplo margen sobre compra
        ['SKU003', 'Producto Ejemplo C', 'margen_sobre_compra', '7000', '', '', '25'] +
        ['60', '70', '65', '75', '80', '90', '100', '95', '85', '75', '120', '150'],
    ]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(header)
    writer.writerows(filas)

    return output.getvalue()
