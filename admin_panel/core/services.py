from django.db import transaction
from .models import (
    Escenario, ParametrosMacro, PersonalComercial, PersonalLogistico,
    PersonalAdministrativo, Vehiculo, GastoComercial, GastoLogistico,
    GastoAdministrativo, Zona, ZonaMunicipio, RutaLogistica, RutaMunicipio,
    ProyeccionVentasConfig, ProyeccionManual, ProyeccionCrecimiento,
    ProyeccionProducto, ProyeccionCanal, ProyeccionPenetracion
)

class EscenarioService:
    @staticmethod
    def get_incremento_valor(indice_nombre, macros):
        """
        Obtiene el valor decimal del incremento basado en el nombre del índice
        y los parámetros macroeconómicos del año destino.
        """
        if not macros:
            return 0

        if indice_nombre == 'fijo':
            return 0

        mapping = {
            'salarios': macros.incremento_salarios,
            'salario_minimo': macros.incremento_salario_minimo,
            'ipc': macros.ipc,
            'ipt': macros.ipt,
            'combustible': macros.incremento_combustible,
            'arriendos': macros.incremento_arriendos,
            'personalizado_1': macros.incremento_personalizado_1,
            'personalizado_2': macros.incremento_personalizado_2,
        }

        return mapping.get(indice_nombre, 0)

    @classmethod
    def duplicar_escenario(cls, escenario_id, nuevo_nombre=None):
        """
        Crea una copia exacta de un escenario (mismo año, mismos valores).
        Útil para crear variantes de un escenario base.
        """
        source = Escenario.objects.get(pk=escenario_id)

        if not nuevo_nombre:
            nuevo_nombre = f"{source.nombre} (Copia)"

        with transaction.atomic():
            # 1. Crear nuevo escenario
            new_scenario = Escenario.objects.create(
                nombre=nuevo_nombre,
                tipo=source.tipo,
                anio=source.anio,
                periodo_tipo=source.periodo_tipo,
                periodo_numero=source.periodo_numero,
                activo=False,
                notas=f"Duplicado desde: {source.nombre}"
            )

            # 2. Copiar todos los datos relacionados
            cls._copiar_datos_escenario(source, new_scenario, factor_incremento=0)

            return new_scenario

    @classmethod
    def proyectar_escenario(cls, escenario_id, nuevo_anio, nuevo_nombre=None):
        """
        Crea un nuevo escenario basado en uno existente, proyectando los valores
        según los índices macroeconómicos del año destino.
        """
        source = Escenario.objects.get(pk=escenario_id)

        if not nuevo_nombre:
            nuevo_nombre = f"{source.nombre} (Proyección {nuevo_anio})"

        # Obtener macros del año destino
        try:
            macros = ParametrosMacro.objects.get(anio=nuevo_anio)
        except ParametrosMacro.DoesNotExist:
            macros = None

        with transaction.atomic():
            # 1. Crear nuevo escenario
            new_scenario = Escenario.objects.create(
                nombre=nuevo_nombre,
                tipo='planeado',
                anio=nuevo_anio,
                periodo_tipo=source.periodo_tipo,
                periodo_numero=source.periodo_numero,
                activo=False,
                notas=f"Proyectado desde: {source.nombre} ({source.anio})"
            )

            # 2. Copiar y proyectar datos
            cls._copiar_datos_escenario(source, new_scenario, macros=macros, nuevo_anio=nuevo_anio)

            return new_scenario

    @classmethod
    def _copiar_datos_escenario(cls, source, target, macros=None, nuevo_anio=None, factor_incremento=None):
        """
        Copia todos los datos de un escenario a otro.
        Si macros está presente, aplica incrementos según índices.
        Si factor_incremento=0, copia valores exactos.
        """

        def get_factor(indice_nombre):
            if factor_incremento is not None:
                return factor_incremento
            return cls.get_incremento_valor(indice_nombre, macros)

        # =====================
        # PERSONAL COMERCIAL
        # =====================
        for item in PersonalComercial.objects.filter(escenario=source):
            incremento = get_factor(getattr(item, 'indice_incremento', 'salarios'))
            PersonalComercial.objects.create(
                escenario=target,
                marca=item.marca,
                tipo=item.tipo,
                cantidad=item.cantidad,
                salario_base=float(item.salario_base) * (1 + incremento),
                perfil_prestacional=item.perfil_prestacional,
                asignacion=item.asignacion,
                auxilio_adicional=float(item.auxilio_adicional or 0) * (1 + incremento) if item.auxilio_adicional else None,
                porcentaje_dedicacion=item.porcentaje_dedicacion,
                criterio_prorrateo=item.criterio_prorrateo,
            )

        # =====================
        # PERSONAL LOGÍSTICO
        # =====================
        for item in PersonalLogistico.objects.filter(escenario=source):
            incremento = get_factor(getattr(item, 'indice_incremento', 'salarios'))
            PersonalLogistico.objects.create(
                escenario=target,
                marca=item.marca,
                tipo=item.tipo,
                cantidad=item.cantidad,
                salario_base=float(item.salario_base) * (1 + incremento),
                perfil_prestacional=item.perfil_prestacional,
                asignacion=item.asignacion,
                porcentaje_dedicacion=item.porcentaje_dedicacion,
                criterio_prorrateo=item.criterio_prorrateo,
            )

        # =====================
        # PERSONAL ADMINISTRATIVO
        # =====================
        for item in PersonalAdministrativo.objects.filter(escenario=source):
            incremento = get_factor(getattr(item, 'indice_incremento', 'salarios'))
            PersonalAdministrativo.objects.create(
                escenario=target,
                marca=item.marca,
                tipo=item.tipo,
                cantidad=item.cantidad,
                salario_base=float(item.salario_base or 0) * (1 + incremento) if item.salario_base else None,
                honorarios_mensuales=float(item.honorarios_mensuales or 0) * (1 + incremento) if item.honorarios_mensuales else None,
                perfil_prestacional=item.perfil_prestacional,
                asignacion=item.asignacion,
                porcentaje_dedicacion=item.porcentaje_dedicacion,
                criterio_prorrateo=item.criterio_prorrateo,
            )

        # =====================
        # VEHÍCULOS
        # =====================
        vehiculos_map = {}  # Mapeo de vehículo viejo -> nuevo (para rutas)
        for item in Vehiculo.objects.filter(escenario=source):
            nuevo_vehiculo = Vehiculo.objects.create(
                escenario=target,
                marca=item.marca,
                tipo_vehiculo=item.tipo_vehiculo,
                esquema=item.esquema,
                cantidad=item.cantidad,
                asignacion=item.asignacion,
                kilometraje_promedio_mensual=item.kilometraje_promedio_mensual,
                porcentaje_uso=item.porcentaje_uso,
                criterio_prorrateo=item.criterio_prorrateo,
            )
            vehiculos_map[item.pk] = nuevo_vehiculo

        # =====================
        # GASTOS COMERCIALES
        # =====================
        for item in GastoComercial.objects.filter(escenario=source):
            incremento = get_factor(getattr(item, 'indice_incremento', 'ipc'))
            GastoComercial.objects.create(
                escenario=target,
                marca=item.marca,
                tipo=item.tipo,
                descripcion=item.descripcion,
                valor_mensual=float(item.valor_mensual) * (1 + incremento),
                asignacion=item.asignacion,
                porcentaje_dedicacion=item.porcentaje_dedicacion,
                criterio_prorrateo=item.criterio_prorrateo,
            )

        # =====================
        # GASTOS LOGÍSTICOS
        # =====================
        for item in GastoLogistico.objects.filter(escenario=source):
            incremento = get_factor(getattr(item, 'indice_incremento', 'ipc'))
            GastoLogistico.objects.create(
                escenario=target,
                marca=item.marca,
                tipo=item.tipo,
                descripcion=item.descripcion,
                valor_mensual=float(item.valor_mensual) * (1 + incremento),
                asignacion=item.asignacion,
                porcentaje_dedicacion=item.porcentaje_dedicacion,
                criterio_prorrateo=item.criterio_prorrateo,
            )

        # =====================
        # GASTOS ADMINISTRATIVOS
        # =====================
        for item in GastoAdministrativo.objects.filter(escenario=source):
            incremento = get_factor(getattr(item, 'indice_incremento', 'ipc'))
            GastoAdministrativo.objects.create(
                escenario=target,
                marca=item.marca,
                tipo=item.tipo,
                descripcion=item.descripcion,
                valor_mensual=float(item.valor_mensual) * (1 + incremento),
                asignacion=item.asignacion,
                porcentaje_dedicacion=item.porcentaje_dedicacion,
                criterio_prorrateo=item.criterio_prorrateo,
            )

        # =====================
        # ZONAS COMERCIALES
        # =====================
        for zona in Zona.objects.filter(escenario=source):
            nueva_zona = Zona.objects.create(
                escenario=target,
                marca=zona.marca,
                nombre=zona.nombre,
                vendedor=zona.vendedor,
                frecuencia=zona.frecuencia,
                tipo_vehiculo_comercial=zona.tipo_vehiculo_comercial,
                municipio_base_vendedor=zona.municipio_base_vendedor,
                requiere_pernocta=zona.requiere_pernocta,
                noches_pernocta=zona.noches_pernocta,
                activo=zona.activo,
            )
            # Copiar municipios de la zona
            for zm in ZonaMunicipio.objects.filter(zona=zona):
                ZonaMunicipio.objects.create(
                    zona=nueva_zona,
                    municipio=zm.municipio,
                    visitas_por_periodo=zm.visitas_por_periodo,
                )

        # =====================
        # RUTAS LOGÍSTICAS
        # =====================
        for ruta in RutaLogistica.objects.filter(escenario=source):
            nuevo_vehiculo = vehiculos_map.get(ruta.vehiculo_id) if ruta.vehiculo_id else None
            nueva_ruta = RutaLogistica.objects.create(
                escenario=target,
                marca=ruta.marca,
                nombre=ruta.nombre,
                vehiculo=nuevo_vehiculo,
                frecuencia=ruta.frecuencia,
                viajes_por_periodo=ruta.viajes_por_periodo,
                requiere_pernocta=ruta.requiere_pernocta,
                noches_pernocta=ruta.noches_pernocta,
                activo=ruta.activo,
            )
            # Copiar municipios de la ruta
            incremento_flete = get_factor('ipc')
            for rm in RutaMunicipio.objects.filter(ruta=ruta):
                RutaMunicipio.objects.create(
                    ruta=nueva_ruta,
                    municipio=rm.municipio,
                    orden_visita=rm.orden_visita,
                    flete_base=float(rm.flete_base or 0) * (1 + incremento_flete) if rm.flete_base else None,
                )

        # =====================
        # PROYECCIÓN DE VENTAS
        # =====================
        anio_destino = nuevo_anio or source.anio
        incremento_ventas = get_factor('ipc')

        for config in ProyeccionVentasConfig.objects.filter(escenario=source):
            nueva_config = ProyeccionVentasConfig.objects.create(
                marca=config.marca,
                escenario=target,
                anio=anio_destino,
                metodo=config.metodo,
                plantilla_estacional=config.plantilla_estacional,
            )

            # Copiar datos según el método
            if config.metodo == 'manual':
                try:
                    manual = ProyeccionManual.objects.get(config=config)
                    ProyeccionManual.objects.create(
                        config=nueva_config,
                        enero=float(manual.enero) * (1 + incremento_ventas),
                        febrero=float(manual.febrero) * (1 + incremento_ventas),
                        marzo=float(manual.marzo) * (1 + incremento_ventas),
                        abril=float(manual.abril) * (1 + incremento_ventas),
                        mayo=float(manual.mayo) * (1 + incremento_ventas),
                        junio=float(manual.junio) * (1 + incremento_ventas),
                        julio=float(manual.julio) * (1 + incremento_ventas),
                        agosto=float(manual.agosto) * (1 + incremento_ventas),
                        septiembre=float(manual.septiembre) * (1 + incremento_ventas),
                        octubre=float(manual.octubre) * (1 + incremento_ventas),
                        noviembre=float(manual.noviembre) * (1 + incremento_ventas),
                        diciembre=float(manual.diciembre) * (1 + incremento_ventas),
                    )
                except ProyeccionManual.DoesNotExist:
                    pass

            elif config.metodo == 'crecimiento':
                try:
                    crec = ProyeccionCrecimiento.objects.get(config=config)
                    ProyeccionCrecimiento.objects.create(
                        config=nueva_config,
                        anio_base=crec.anio_base,
                        ventas_base_anual=float(crec.ventas_base_anual) * (1 + incremento_ventas),
                        factor_crecimiento=crec.factor_crecimiento,
                    )
                except ProyeccionCrecimiento.DoesNotExist:
                    pass

            elif config.metodo == 'precio_unidades':
                for prod in ProyeccionProducto.objects.filter(config=config):
                    ProyeccionProducto.objects.create(
                        config=nueva_config,
                        tipo=prod.tipo,
                        producto=prod.producto,
                        categoria=prod.categoria,
                        precio_unitario=float(prod.precio_unitario) * (1 + incremento_ventas),
                        unidades_enero=prod.unidades_enero,
                        unidades_febrero=prod.unidades_febrero,
                        unidades_marzo=prod.unidades_marzo,
                        unidades_abril=prod.unidades_abril,
                        unidades_mayo=prod.unidades_mayo,
                        unidades_junio=prod.unidades_junio,
                        unidades_julio=prod.unidades_julio,
                        unidades_agosto=prod.unidades_agosto,
                        unidades_septiembre=prod.unidades_septiembre,
                        unidades_octubre=prod.unidades_octubre,
                        unidades_noviembre=prod.unidades_noviembre,
                        unidades_diciembre=prod.unidades_diciembre,
                    )

            elif config.metodo == 'canal':
                for canal in ProyeccionCanal.objects.filter(config=config):
                    ProyeccionCanal.objects.create(
                        config=nueva_config,
                        canal=canal.canal,
                        enero=float(canal.enero) * (1 + incremento_ventas),
                        febrero=float(canal.febrero) * (1 + incremento_ventas),
                        marzo=float(canal.marzo) * (1 + incremento_ventas),
                        abril=float(canal.abril) * (1 + incremento_ventas),
                        mayo=float(canal.mayo) * (1 + incremento_ventas),
                        junio=float(canal.junio) * (1 + incremento_ventas),
                        julio=float(canal.julio) * (1 + incremento_ventas),
                        agosto=float(canal.agosto) * (1 + incremento_ventas),
                        septiembre=float(canal.septiembre) * (1 + incremento_ventas),
                        octubre=float(canal.octubre) * (1 + incremento_ventas),
                        noviembre=float(canal.noviembre) * (1 + incremento_ventas),
                        diciembre=float(canal.diciembre) * (1 + incremento_ventas),
                    )

            elif config.metodo == 'penetracion':
                try:
                    pen = ProyeccionPenetracion.objects.get(config=config)
                    ProyeccionPenetracion.objects.create(
                        config=nueva_config,
                        mercado=pen.mercado,
                        penetracion_inicial=pen.penetracion_inicial,
                        penetracion_final=pen.penetracion_final,
                    )
                except ProyeccionPenetracion.DoesNotExist:
                    pass
