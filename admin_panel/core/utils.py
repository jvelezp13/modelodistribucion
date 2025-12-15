"""
Utilidades genéricas para el sistema DxV
"""
from django.db import models, transaction
from typing import Dict, Any, List, Optional, Set


def copiar_instancia(
    instancia: models.Model,
    override: Optional[Dict[str, Any]] = None,
    excluir_campos: Optional[Set[str]] = None,
    campos_monetarios: Optional[Set[str]] = None,
    factor_incremento: float = 0,
    sufijo_nombre: str = " (Copia)"
) -> models.Model:
    """
    Crea una copia de cualquier instancia de modelo Django.

    Args:
        instancia: La instancia del modelo a copiar
        override: Diccionario con campos a sobrescribir en la copia
        excluir_campos: Campos adicionales a excluir (además de id, pk, fecha_*)
        campos_monetarios: Campos a los que aplicar factor_incremento
        factor_incremento: Factor de incremento para campos monetarios (0 = sin cambio)
        sufijo_nombre: Sufijo a agregar a campos únicos de texto (nombre, perfil, etc.)

    Returns:
        Nueva instancia creada (ya guardada en BD)

    Example:
        # Copia simple
        nuevo_vendedor = copiar_instancia(vendedor_original)

        # Copia con cambios
        nuevo_vendedor = copiar_instancia(
            vendedor_original,
            override={'marca': otra_marca, 'nombre': 'Vendedor Sur'},
        )

        # Copia con incremento en salarios
        nuevo_personal = copiar_instancia(
            personal_original,
            campos_monetarios={'salario_base', 'auxilio_adicional'},
            factor_incremento=0.05  # 5% de incremento
        )
    """
    override = override or {}
    excluir_campos = excluir_campos or set()
    campos_monetarios = campos_monetarios or set()

    # Campos que siempre se excluyen
    campos_excluir_siempre = {
        'id', 'pk',
        'fecha_creacion', 'fecha_modificacion',
        'created_at', 'updated_at',
    }
    campos_excluir = campos_excluir_siempre | excluir_campos

    # Identificar campos de texto que necesitan sufijo
    # Incluye campos únicos Y el campo 'nombre' (común en modelos)
    campos_con_sufijo = set()
    for field in instancia._meta.fields:
        if isinstance(field, (models.CharField, models.TextField)):
            if field.unique or field.name == 'nombre':
                campos_con_sufijo.add(field.name)

    # Construir diccionario con los valores de la instancia original
    data = {}
    for field in instancia._meta.fields:
        nombre_campo = field.name

        # Saltar campos excluidos
        if nombre_campo in campos_excluir:
            continue

        # Si está en override, usar el valor de override
        if nombre_campo in override:
            data[nombre_campo] = override[nombre_campo]
            continue

        # Obtener valor original
        valor = getattr(instancia, nombre_campo)

        # Aplicar incremento a campos monetarios
        if nombre_campo in campos_monetarios and valor is not None and factor_incremento != 0:
            valor = float(valor) * (1 + factor_incremento)

        # Agregar sufijo a campos de texto (nombre, perfil, etc.)
        if nombre_campo in campos_con_sufijo and sufijo_nombre and nombre_campo not in override:
            if valor:
                valor = f"{valor}{sufijo_nombre}"

        data[nombre_campo] = valor

    # Agregar cualquier override adicional que no sea un campo del modelo
    # (esto permite agregar campos de relaciones como 'escenario=nuevo_escenario')
    for key, value in override.items():
        if key not in data:
            data[key] = value

    # Crear nueva instancia
    modelo_class = instancia.__class__
    nueva_instancia = modelo_class.objects.create(**data)

    return nueva_instancia


def copiar_instancia_con_hijos(
    instancia: models.Model,
    relaciones_hijos: Dict[str, Dict[str, Any]],
    override: Optional[Dict[str, Any]] = None,
    excluir_campos: Optional[Set[str]] = None,
    campos_monetarios: Optional[Set[str]] = None,
    factor_incremento: float = 0,
    sufijo_nombre: str = " (Copia)"
) -> models.Model:
    """
    Copia una instancia junto con sus registros hijos relacionados.

    Args:
        instancia: La instancia del modelo padre a copiar
        relaciones_hijos: Diccionario con configuración de relaciones a copiar
            {
                'related_name': {
                    'campo_padre': 'nombre_del_fk',  # Campo FK en el hijo que apunta al padre
                    'campos_monetarios': {'campo1', 'campo2'},  # Opcional
                    'factor_incremento': 0.05,  # Opcional, default usa el del padre
                }
            }
        override: Campos a sobrescribir en el padre
        excluir_campos: Campos a excluir del padre
        campos_monetarios: Campos monetarios del padre
        factor_incremento: Factor de incremento para campos monetarios
        sufijo_nombre: Sufijo para el nombre

    Returns:
        Nueva instancia padre con sus hijos copiados

    Example:
        nueva_zona = copiar_instancia_con_hijos(
            zona_original,
            relaciones_hijos={
                'municipios': {  # related_name en ZonaMunicipio
                    'campo_padre': 'zona',
                }
            },
            override={'escenario': nuevo_escenario}
        )
    """
    override = override or {}

    with transaction.atomic():
        # 1. Copiar el padre
        nuevo_padre = copiar_instancia(
            instancia,
            override=override,
            excluir_campos=excluir_campos,
            campos_monetarios=campos_monetarios,
            factor_incremento=factor_incremento,
            sufijo_nombre=sufijo_nombre
        )

        # 2. Copiar cada relación de hijos
        for related_name, config in relaciones_hijos.items():
            campo_padre = config.get('campo_padre', related_name.rstrip('s'))
            campos_mon_hijo = config.get('campos_monetarios', set())
            factor_hijo = config.get('factor_incremento', factor_incremento)

            # Obtener los hijos originales
            try:
                hijos_originales = getattr(instancia, related_name).all()
            except AttributeError:
                # Intentar con el manager por defecto
                continue

            # Copiar cada hijo
            for hijo in hijos_originales:
                copiar_instancia(
                    hijo,
                    override={campo_padre: nuevo_padre},
                    campos_monetarios=campos_mon_hijo,
                    factor_incremento=factor_hijo,
                    sufijo_nombre=""  # Los hijos no necesitan sufijo
                )

        return nuevo_padre


# ==============================================
# Configuración de campos monetarios por modelo
# ==============================================
# Esto permite saber qué campos deben incrementarse en proyecciones

CAMPOS_MONETARIOS_POR_MODELO = {
    'PersonalComercial': {'salario_base', 'auxilio_adicional'},
    'PersonalLogistico': {'salario_base'},
    'PersonalAdministrativo': {'salario_base', 'honorarios_mensuales'},
    'GastoComercial': {'valor_mensual'},
    'GastoLogistico': {'valor_mensual'},
    'GastoAdministrativo': {'valor_mensual'},
    'RutaMunicipio': {'flete_base'},
    'ProyeccionManual': {
        'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
        'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
    },
}


def get_campos_monetarios(modelo: models.Model) -> Set[str]:
    """Obtiene los campos monetarios configurados para un modelo"""
    nombre_modelo = modelo.__class__.__name__
    return CAMPOS_MONETARIOS_POR_MODELO.get(nombre_modelo, set())
