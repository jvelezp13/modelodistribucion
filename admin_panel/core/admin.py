"""
Configuración del Django Admin para los modelos DxV
"""
from django import forms
from django.contrib import admin
from django.contrib import messages
from django.db.models import Sum, Count
from .utils import copiar_instancia
from .models import (
    Marca, PersonalComercial, PersonalLogistico,
    Vehiculo, ParametrosMacro, FactorPrestacional,
    PersonalAdministrativo, GastoAdministrativo,
    GastoComercial, GastoLogistico, Impuesto,
    ConfiguracionDescuentos, TramoDescuentoFactura,
    Escenario, PoliticaRecursosHumanos,
    # Módulo de Lejanías Comerciales
    Municipio, MatrizDesplazamiento, ConfiguracionLejania,
    Zona, ZonaMunicipio,
    # Módulo de Rutas Logísticas
    RutaLogistica, RutaMunicipio,
    # Módulo de Proyección de Ventas
    CanalVenta, CategoriaProducto, Producto, PlantillaEstacional,
    DefinicionMercado, ProyeccionVentasConfig, ProyeccionManual,
    ProyeccionCrecimiento, ProyeccionProducto, ProyeccionCanal,
    ProyeccionPenetracion
)
from .admin_site import dxv_admin_site


# =============================================================================
# MIXIN PARA ACCIÓN DUPLICAR
# =============================================================================

class DuplicarMixin:
    """
    Mixin que agrega la acción 'Duplicar' a cualquier ModelAdmin.
    Permite duplicar uno o varios registros seleccionados.
    """

    def duplicar_registros(self, request, queryset):
        """Duplica los registros seleccionados"""
        duplicados = 0
        errores = []

        for obj in queryset:
            try:
                copiar_instancia(obj)
                duplicados += 1
            except Exception as e:
                errores.append(f"{obj}: {str(e)}")

        if duplicados:
            self.message_user(
                request,
                f"Se duplicaron {duplicados} registro(s) exitosamente.",
                level=messages.SUCCESS
            )

        if errores:
            self.message_user(
                request,
                f"Errores al duplicar: {'; '.join(errores)}",
                level=messages.ERROR
            )

    duplicar_registros.short_description = "Duplicar registro(s) seleccionado(s)"


@admin.register(Escenario, site=dxv_admin_site)
class EscenarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'anio', 'periodo_display', 'activo', 'fecha_modificacion')
    list_filter = ('tipo', 'anio', 'activo')
    search_fields = ('nombre', 'notas')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'tipo', 'anio', 'activo')
        }),
        ('Periodo', {
            'fields': ('periodo_tipo', 'periodo_numero')
        }),
        ('Detalles', {
            'fields': ('notas',)
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def periodo_display(self, obj):
        if obj.periodo_tipo == 'anual':
            return "Anual"
        elif obj.periodo_tipo == 'trimestral':
            return f"Trimestral (Q{obj.periodo_numero})"
        elif obj.periodo_tipo == 'mensual':
            meses = ['', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
            mes_nombre = meses[obj.periodo_numero] if obj.periodo_numero else '?'
            return f"Mensual ({mes_nombre})"
        return obj.periodo_tipo
    periodo_display.short_description = 'Periodo'

    actions = ['duplicar_escenario', 'proyectar_escenario']

    def duplicar_escenario(self, request, queryset):
        """Crea una copia exacta del escenario seleccionado"""
        from .services import EscenarioService
        from django.contrib import messages

        if queryset.count() != 1:
            self.message_user(
                request,
                "Por favor selecciona solo un escenario para duplicar.",
                level=messages.WARNING
            )
            return

        escenario_base = queryset.first()

        try:
            nuevo_escenario = EscenarioService.duplicar_escenario(escenario_base.pk)
            self.message_user(
                request,
                f"Escenario duplicado exitosamente: {nuevo_escenario.nombre}",
                level=messages.SUCCESS
            )
        except Exception as e:
            self.message_user(
                request,
                f"Error al duplicar escenario: {str(e)}",
                level=messages.ERROR
            )

    duplicar_escenario.short_description = "Duplicar Escenario (copia exacta)"

    def proyectar_escenario(self, request, queryset):
        """Crea un nuevo escenario proyectado al siguiente año"""
        from .services import EscenarioService
        from django.contrib import messages

        if queryset.count() != 1:
            self.message_user(
                request,
                "Por favor selecciona solo un escenario para proyectar.",
                level=messages.WARNING
            )
            return

        escenario_base = queryset.first()
        nuevo_anio = escenario_base.anio + 1

        try:
            nuevo_escenario = EscenarioService.proyectar_escenario(escenario_base.pk, nuevo_anio)
            self.message_user(
                request,
                f"Escenario proyectado exitosamente: {nuevo_escenario.nombre}",
                level=messages.SUCCESS
            )
        except Exception as e:
            self.message_user(
                request,
                f"Error al proyectar escenario: {str(e)}",
                level=messages.ERROR
            )

    proyectar_escenario.short_description = "Proyectar al Siguiente Año"


@admin.register(Marca, site=dxv_admin_site)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'marca_id', 'activa', 'total_empleados', 'total_vehiculos', 'fecha_modificacion')
    list_filter = ('activa',)
    search_fields = ('nombre', 'marca_id', 'descripcion')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('marca_id', 'nombre', 'descripcion', 'activa', 'color')
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def total_empleados(self, obj):
        comercial = obj.personal_comercial.aggregate(total=Sum('cantidad'))['total'] or 0
        logistico = obj.personal_logistico.aggregate(total=Sum('cantidad'))['total'] or 0
        return comercial + logistico
    total_empleados.short_description = 'Total Empleados'

    def total_vehiculos(self, obj):
        return obj.vehiculos.aggregate(total=Sum('cantidad'))['total'] or 0
    total_vehiculos.short_description = 'Total Vehículos'


@admin.register(PersonalComercial, site=dxv_admin_site)
class PersonalComercialAdmin(DuplicarMixin, admin.ModelAdmin):
    change_list_template = 'admin/core/change_list_with_total.html'
    list_display = ('marca', 'nombre', 'escenario', 'tipo', 'cantidad', 'salario_base', 'costo_total_estimado', 'asignacion', 'perfil_prestacional')
    list_filter = ('escenario', 'marca', 'tipo', 'asignacion', 'perfil_prestacional')
    search_fields = ('marca__nombre', 'nombre')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    actions = ['duplicar_registros']

    fieldsets = (
        ('Información Básica', {
            'fields': ('marca', 'escenario', 'nombre', 'tipo', 'cantidad', 'salario_base', 'perfil_prestacional')
        }),
        ('Asignación por Marca', {
            'fields': ('asignacion', 'porcentaje_dedicacion', 'criterio_prorrateo')
        }),
        ('Asignación Geográfica (P&G por Zona)', {
            'fields': ('tipo_asignacion_geo', 'zona'),
            'description': 'Cómo se distribuye este costo entre las zonas comerciales'
        }),
        ('Adicionales', {
            'fields': ('auxilio_adicional',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Hacer campos condicionales según asignación
        if obj and obj.asignacion == 'individual':
            form.base_fields['porcentaje_dedicacion'].required = False
            form.base_fields['criterio_prorrateo'].required = False
        return form

    def costo_total_estimado(self, obj):
        if not obj.salario_base:
            return "-"
        try:
            factor = FactorPrestacional.objects.get(perfil=obj.perfil_prestacional)
            total = obj.salario_base * (1 + factor.factor_total)

            # Sumar auxilio de transporte si aplica (<= 2 SMLV)
            if obj.escenario:
                try:
                    macro = ParametrosMacro.objects.get(anio=obj.escenario.anio, activo=True)
                    if obj.salario_base <= (macro.salario_minimo_legal * 2):
                        total += macro.subsidio_transporte
                except ParametrosMacro.DoesNotExist:
                    pass

            return f"${total:,.0f}"
        except FactorPrestacional.DoesNotExist:
            return f"${obj.salario_base:,.0f} (Sin Factor)"
    costo_total_estimado.short_description = 'Costo Total (Est.)'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data['cl'].queryset
            total_general = sum(obj.calcular_costo_mensual() for obj in qs)
            total_registros = qs.count()
            promedio = total_general / total_registros if total_registros > 0 else 0

            response.context_data['total_valor_mensual'] = total_general
            response.context_data['total_registros'] = total_registros
            response.context_data['promedio_registro'] = promedio
        except (AttributeError, KeyError):
            pass
        return response


@admin.register(PersonalLogistico, site=dxv_admin_site)
class PersonalLogisticoAdmin(DuplicarMixin, admin.ModelAdmin):
    change_list_template = 'admin/core/change_list_with_total.html'
    list_display = ('marca', 'nombre', 'escenario', 'tipo', 'cantidad', 'salario_base', 'costo_total_estimado', 'asignacion', 'perfil_prestacional')
    list_filter = ('escenario', 'marca', 'tipo', 'asignacion', 'perfil_prestacional')
    search_fields = ('marca__nombre', 'nombre')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    actions = ['duplicar_registros']

    fieldsets = (
        ('Información Básica', {
            'fields': ('marca', 'escenario', 'nombre', 'tipo', 'cantidad', 'salario_base', 'perfil_prestacional')
        }),
        ('Asignación por Marca', {
            'fields': ('asignacion', 'porcentaje_dedicacion', 'criterio_prorrateo')
        }),
        ('Asignación Geográfica (P&G por Zona)', {
            'fields': ('tipo_asignacion_geo', 'zona'),
            'description': 'Cómo se distribuye este costo entre las zonas comerciales'
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def costo_total_estimado(self, obj):
        if not obj.salario_base:
            return "-"
        try:
            factor = FactorPrestacional.objects.get(perfil=obj.perfil_prestacional)
            total = obj.salario_base * (1 + factor.factor_total)

            # Sumar auxilio de transporte si aplica (<= 2 SMLV)
            if obj.escenario:
                try:
                    macro = ParametrosMacro.objects.get(anio=obj.escenario.anio, activo=True)
                    if obj.salario_base <= (macro.salario_minimo_legal * 2):
                        total += macro.subsidio_transporte
                except ParametrosMacro.DoesNotExist:
                    pass

            return f"${total:,.0f}"
        except FactorPrestacional.DoesNotExist:
            return f"${obj.salario_base:,.0f} (Sin Factor)"
    costo_total_estimado.short_description = 'Costo Total (Est.)'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data['cl'].queryset
            total_general = sum(obj.calcular_costo_mensual() for obj in qs)
            total_registros = qs.count()
            promedio = total_general / total_registros if total_registros > 0 else 0

            response.context_data['total_valor_mensual'] = total_general
            response.context_data['total_registros'] = total_registros
            response.context_data['promedio_registro'] = promedio
        except (AttributeError, KeyError):
            pass
        return response


@admin.register(Vehiculo, site=dxv_admin_site)
class VehiculoAdmin(DuplicarMixin, admin.ModelAdmin):
    change_list_template = 'admin/core/change_list_with_total.html'
    list_display = ('nombre_display', 'marca', 'escenario', 'tipo_vehiculo', 'esquema', 'cantidad', 'costo_mensual_estimado_formateado')
    list_filter = ('escenario', 'marca', 'tipo_vehiculo', 'esquema', 'asignacion')
    search_fields = ['nombre', 'marca__nombre', 'tipo_vehiculo', 'esquema']
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    actions = ['duplicar_registros']

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'marca', 'escenario', 'tipo_vehiculo', 'esquema', 'cantidad'),
            'description': 'El campo "Nombre" permite identificar el vehículo de forma única (ej: "Turbo 01", "NKR Zona Norte")'
        }),
        ('Esquema: Renting', {
            'fields': ('canon_renting',),
            'description': 'Diligenciar solo si el esquema es "Renting"',
            'classes': ('collapse',)
        }),
        ('Esquema: Propio', {
            'fields': ('costo_compra', 'vida_util_anios', 'valor_residual', 'costo_mantenimiento_mensual', 'costo_seguro_mensual'),
            'description': 'Diligenciar solo si el esquema es "Tradicional (Propio)"',
            'classes': ('collapse',)
        }),
        ('Consumo de Combustible (Todos los Esquemas)', {
            'fields': ('tipo_combustible', 'consumo_galon_km'),
            'description': 'Requerido para calcular combustible en Recorridos Logísticos. Aplica a Propio, Renting y Tercero.',
        }),
        ('Otros Costos Operativos (Propio/Renting)', {
            'fields': ('costo_lavado_mensual', 'costo_parqueadero_mensual'),
            'description': 'Aseo y Parqueadero',
            'classes': ('collapse',)
        }),
        ('Otros Costos (Todos los Esquemas)', {
            'fields': ('costo_monitoreo_mensual', 'costo_seguro_mercancia_mensual'),
            'description': 'Monitoreo Satelital (GPS) y Seguro de Mercancía',
            'classes': ('collapse',)
        }),
        ('Personal del Vehículo', {
            'fields': ('cantidad_auxiliares',),
            'description': 'Auxiliares de entrega fijos asignados a este vehículo (normalmente 1)'
        }),
        ('Asignación y Proyecciones', {
            'fields': ('asignacion', 'porcentaje_uso', 'criterio_prorrateo', 'indice_incremento'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def nombre_display(self, obj):
        if obj.nombre:
            return obj.nombre
        return f"{obj.get_tipo_vehiculo_display()} #{obj.id}"
    nombre_display.short_description = 'Nombre'

    def costo_mensual_estimado_formateado(self, obj):
        costo = obj.calcular_costo_mensual()
        return f"${costo:,.0f}"
    costo_mensual_estimado_formateado.short_description = 'Costo Mensual (Est.)'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data['cl'].queryset
            total_general = sum(obj.calcular_costo_mensual() for obj in qs)
            total_registros = qs.count()
            promedio = total_general / total_registros if total_registros > 0 else 0

            response.context_data['total_valor_mensual'] = total_general
            response.context_data['total_registros'] = total_registros
            response.context_data['promedio_registro'] = promedio
        except (AttributeError, KeyError):
            pass
        return response


@admin.register(ParametrosMacro, site=dxv_admin_site)
class ParametrosMacroAdmin(admin.ModelAdmin):
    list_display = (
        'anio',
        'ipc_percent',
        'salario_minimo_formateado',
        'subsidio_transporte_formateado',
        'activo',
        'fecha_modificacion'
    )
    list_filter = ('activo', 'anio')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Año', {
            'fields': ('anio', 'activo')
        }),
        ('Índices Generales', {
            'fields': ('ipc', 'ipt')
        }),
        ('Salarios y Subsidios', {
            'fields': ('salario_minimo_legal', 'subsidio_transporte')
        }),
        ('Índices de Incremento para Proyecciones', {
            'fields': (
                'incremento_salarios',
                'incremento_salario_minimo',
                'incremento_combustible',
                'incremento_arriendos',
            ),
            'description': 'Índices a usar para proyectar valores de años futuros'
        }),
        ('Índices Personalizados', {
            'fields': (
                ('nombre_personalizado_1', 'incremento_personalizado_1'),
                ('nombre_personalizado_2', 'incremento_personalizado_2'),
            ),
            'classes': ('collapse',),
            'description': 'Índices configurables para casos específicos'
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def ipc_percent(self, obj):
        return f"{obj.ipc:.2f}%"
    ipc_percent.short_description = 'IPC'
    ipc_percent.admin_order_field = 'ipc'

    def salario_minimo_formateado(self, obj):
        return f"${obj.salario_minimo_legal:,.0f}"
    salario_minimo_formateado.short_description = 'Salario Mínimo'
    salario_minimo_formateado.admin_order_field = 'salario_minimo_legal'

    def subsidio_transporte_formateado(self, obj):
        return f"${obj.subsidio_transporte:,.0f}"
    subsidio_transporte_formateado.short_description = 'Subsidio Transporte'
    subsidio_transporte_formateado.admin_order_field = 'subsidio_transporte'


@admin.register(FactorPrestacional, site=dxv_admin_site)
class FactorPrestacionalAdmin(DuplicarMixin, admin.ModelAdmin):
    list_display = ('perfil', 'arl_percent', 'factor_total_percent', 'salud_percent', 'pension_percent', 'fecha_modificacion')
    list_filter = ('perfil',)
    readonly_fields = ('factor_total_display', 'guia_arl_display', 'fecha_creacion', 'fecha_modificacion')
    actions = ['duplicar_registros']

    fieldsets = (
        ('Perfil', {
            'fields': ('perfil',),
            'description': '''
            <strong>Guía de Selección:</strong><br>
            • <b>Administrativo (Riesgo I)</b>: Oficina, contabilidad, sistemas<br>
            • <b>Comercial (Riesgo II)</b>: Vendedores externos, preventa, TAT, mercaderistas<br>
            • <b>Logístico Bodega (Riesgo III)</b>: Operarios de bodega, empaque, picking<br>
            • <b>Logístico Calle (Riesgo IV)</b>: Conductores, auxiliares de entrega<br>
            • <b>Aprendiz SENA</b>: Etapa productiva (Ley 2466/2025: 100% SMLV)
            '''
        }),
        ('Referencia ARL por Clase de Riesgo', {
            'fields': ('guia_arl_display',),
            'description': 'Use esta tabla como referencia para el campo ARL según el perfil seleccionado.'
        }),
        ('Seguridad Social (Base: solo salario)', {
            'fields': ('salud', 'pension', 'arl'),
            'description': 'Salud EXONERADO (0%) por Ley 1607/2012 para empleados < 10 SMLV. Pensión y ARL siempre aplican.'
        }),
        ('Parafiscales (Base: solo salario)', {
            'fields': ('caja_compensacion', 'icbf', 'sena'),
            'description': 'ICBF y SENA EXONERADOS (0%) por Ley 1607/2012 para empleados < 10 SMLV. Caja siempre aplica.'
        }),
        ('Prestaciones Sociales', {
            'fields': ('cesantias', 'intereses_cesantias', 'prima', 'vacaciones'),
            'description': 'Cesantías, Int. Cesantías y Prima: base = salario + subsidio. Vacaciones: base = solo salario.'
        }),
        ('Total Calculado', {
            'fields': ('factor_total_display',),
            'description': 'Suma de todos los componentes. Para empleados con exoneración Ley 1607: poner 0 en Salud, ICBF y SENA.'
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def guia_arl_display(self, obj):
        """Muestra tabla de referencia ARL por clase de riesgo"""
        from django.utils.html import format_html
        return format_html('''
            <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
                <tr style="background: #f0f0f0;">
                    <th style="border: 1px solid #ccc; padding: 8px; text-align: left;">Clase</th>
                    <th style="border: 1px solid #ccc; padding: 8px; text-align: left;">ARL %</th>
                    <th style="border: 1px solid #ccc; padding: 8px; text-align: left;">Tipo de Actividad</th>
                </tr>
                <tr>
                    <td style="border: 1px solid #ccc; padding: 8px;"><b>I</b></td>
                    <td style="border: 1px solid #ccc; padding: 8px;">0.522</td>
                    <td style="border: 1px solid #ccc; padding: 8px;">Oficina, administrativo, sistemas</td>
                </tr>
                <tr style="background: #f9f9f9;">
                    <td style="border: 1px solid #ccc; padding: 8px;"><b>II</b></td>
                    <td style="border: 1px solid #ccc; padding: 8px;">1.044</td>
                    <td style="border: 1px solid #ccc; padding: 8px;">Vendedores externos, TAT, preventa, mercaderistas</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ccc; padding: 8px;"><b>III</b></td>
                    <td style="border: 1px solid #ccc; padding: 8px;">2.436</td>
                    <td style="border: 1px solid #ccc; padding: 8px;">Bodega, empaque, picking, manufactura ligera</td>
                </tr>
                <tr style="background: #f9f9f9;">
                    <td style="border: 1px solid #ccc; padding: 8px;"><b>IV</b></td>
                    <td style="border: 1px solid #ccc; padding: 8px;">4.350</td>
                    <td style="border: 1px solid #ccc; padding: 8px;">Conductores, auxiliares de entrega, montacargas</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ccc; padding: 8px;"><b>V</b></td>
                    <td style="border: 1px solid #ccc; padding: 8px;">6.960</td>
                    <td style="border: 1px solid #ccc; padding: 8px;">Minería, construcción (raro en distribución)</td>
                </tr>
            </table>
        ''')
    guia_arl_display.short_description = 'Tabla de Referencia ARL'

    def factor_total_display(self, obj):
        """Muestra el factor total calculado (solo para objetos guardados)"""
        if obj and obj.pk:
            return f"{obj.factor_total_porcentaje:.2f}%"
        return "Se calculará al guardar"
    factor_total_display.short_description = 'Factor Total'

    def factor_total_percent(self, obj):
        return f"{obj.factor_total_porcentaje:.2f}%"
    factor_total_percent.short_description = 'Factor Total'

    def arl_percent(self, obj):
        return f"{obj.arl:.3f}%"
    arl_percent.short_description = 'ARL'
    arl_percent.admin_order_field = 'arl'

    def pension_percent(self, obj):
        return f"{obj.pension:.2f}%"
    pension_percent.short_description = 'Pensión'
    pension_percent.admin_order_field = 'pension'

    def salud_percent(self, obj):
        return f"{obj.salud:.2f}%"
    salud_percent.short_description = 'Salud'
    salud_percent.admin_order_field = 'salud'


@admin.register(PersonalAdministrativo, site=dxv_admin_site)
class PersonalAdministrativoAdmin(DuplicarMixin, admin.ModelAdmin):
    change_list_template = 'admin/core/change_list_with_total.html'
    list_display = ('nombre', 'marca', 'escenario', 'tipo', 'cantidad', 'asignacion', 'tipo_contrato', 'valor_mensual', 'costo_total_estimado')
    list_filter = ('escenario', 'marca', 'tipo', 'asignacion', 'tipo_contrato')
    search_fields = ('nombre',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    actions = ['duplicar_registros']

    fieldsets = (
        ('Asignación', {
            'fields': ('marca', 'escenario', 'asignacion'),
            'description': 'Si asignas a una marca específica, será individual. Si dejas marca vacía, será compartido.'
        }),
        ('Información Básica', {
            'fields': ('nombre', 'tipo', 'cantidad', 'tipo_contrato')
        }),
        ('Nómina', {
            'fields': ('salario_base', 'perfil_prestacional'),
            'classes': ('collapse',)
        }),
        ('Honorarios', {
            'fields': ('honorarios_mensuales',),
            'classes': ('collapse',)
        }),
        ('Prorrateo (Solo Compartidos)', {
            'fields': ('criterio_prorrateo',),
            'description': 'Solo aplica si no tiene marca asignada'
        }),
        ('Asignación Geográfica (P&G por Zona)', {
            'fields': ('tipo_asignacion_geo',),
            'description': 'Cómo se distribuye este costo entre las zonas (típicamente compartido/equitativo)'
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def valor_mensual(self, obj):
        if obj.tipo_contrato == 'nomina' and obj.salario_base:
            return f"${obj.salario_base:,.0f}"
        elif obj.tipo_contrato == 'honorarios' and obj.honorarios_mensuales:
            return f"${obj.honorarios_mensuales:,.0f}"
        return "-"
    valor_mensual.short_description = 'Valor Mensual'

    def costo_total_estimado(self, obj):
        if obj.tipo_contrato == 'honorarios':
            return f"${obj.honorarios_mensuales:,.0f}" if obj.honorarios_mensuales else "-"

        if not obj.salario_base:
            return "-"

        try:
            factor = FactorPrestacional.objects.get(perfil=obj.perfil_prestacional)
            total = obj.salario_base * (1 + factor.factor_total)

            # Sumar auxilio de transporte si aplica (<= 2 SMLV)
            if obj.escenario:
                try:
                    macro = ParametrosMacro.objects.get(anio=obj.escenario.anio, activo=True)
                    if obj.salario_base <= (macro.salario_minimo_legal * 2):
                        total += macro.subsidio_transporte
                except ParametrosMacro.DoesNotExist:
                    pass

            return f"${total:,.0f}"
        except FactorPrestacional.DoesNotExist:
            return f"${obj.salario_base:,.0f} (Sin Factor)"
    costo_total_estimado.short_description = 'Costo Total (Est.)'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data['cl'].queryset
            total_general = sum(obj.calcular_costo_mensual() for obj in qs)
            total_registros = qs.count()
            promedio = total_general / total_registros if total_registros > 0 else 0

            response.context_data['total_valor_mensual'] = total_general
            response.context_data['total_registros'] = total_registros
            response.context_data['promedio_registro'] = promedio
        except (AttributeError, KeyError):
            pass
        return response


@admin.register(GastoAdministrativo, site=dxv_admin_site)
class GastoAdministrativoAdmin(DuplicarMixin, admin.ModelAdmin):
    change_list_template = 'admin/core/change_list_with_total.html'
    list_display = ('nombre', 'marca', 'escenario', 'tipo', 'asignacion', 'valor_mensual_formateado', 'criterio_prorrateo')
    list_filter = ('escenario', 'marca', 'tipo', 'asignacion', 'criterio_prorrateo')
    search_fields = ('nombre', 'notas')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    actions = ['duplicar_registros']

    fieldsets = (
        ('Asignación', {
            'fields': ('marca', 'escenario', 'asignacion'),
            'description': 'Si asignas a una marca específica, será individual. Si dejas marca vacía, será compartido.'
        }),
        ('Información Básica', {
            'fields': ('nombre', 'tipo', 'valor_mensual')
        }),
        ('Prorrateo (Solo Compartidos)', {
            'fields': ('criterio_prorrateo',),
            'description': 'Solo aplica si no tiene marca asignada'
        }),
        ('Asignación Geográfica (P&G por Zona)', {
            'fields': ('tipo_asignacion_geo',),
            'description': 'Cómo se distribuye este gasto entre las zonas (típicamente compartido/equitativo)'
        }),
        ('Notas', {
            'fields': ('notas',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def valor_mensual_formateado(self, obj):
        return f"${obj.valor_mensual:,.0f}"
    valor_mensual_formateado.short_description = 'Valor Mensual'
    valor_mensual_formateado.admin_order_field = 'valor_mensual'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data['cl'].queryset
            total = qs.aggregate(total=Sum('valor_mensual'))['total'] or 0
            total_registros = qs.count()
            promedio = total / total_registros if total_registros > 0 else 0

            response.context_data['total_valor_mensual'] = total
            response.context_data['total_registros'] = total_registros
            response.context_data['promedio_registro'] = promedio
        except (AttributeError, KeyError):
            pass
        return response


@admin.register(GastoComercial, site=dxv_admin_site)
class GastoComercialAdmin(DuplicarMixin, admin.ModelAdmin):
    change_list_template = 'admin/core/change_list_with_total.html'
    list_display = ('marca', 'escenario', 'nombre', 'tipo', 'valor_mensual_formateado', 'fecha_modificacion')
    list_filter = ('escenario', 'marca', 'tipo')
    search_fields = ('nombre', 'notas')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    actions = ['duplicar_registros']

    fieldsets = (
        ('Información Básica', {
            'fields': ('marca', 'escenario', 'nombre', 'tipo', 'valor_mensual')
        }),
        ('Asignación Geográfica (P&G por Zona)', {
            'fields': ('tipo_asignacion_geo', 'zona'),
            'description': 'Cómo se distribuye este gasto entre las zonas comerciales'
        }),
        ('Notas', {
            'fields': ('notas',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def valor_mensual_formateado(self, obj):
        return f"${obj.valor_mensual:,.0f}"
    valor_mensual_formateado.short_description = 'Valor Mensual'
    valor_mensual_formateado.admin_order_field = 'valor_mensual'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data['cl'].queryset
            total = qs.aggregate(total=Sum('valor_mensual'))['total'] or 0
            total_registros = qs.count()
            promedio = total / total_registros if total_registros > 0 else 0

            response.context_data['total_valor_mensual'] = total
            response.context_data['total_registros'] = total_registros
            response.context_data['promedio_registro'] = promedio
        except (AttributeError, KeyError):
            pass
        return response


@admin.register(GastoLogistico, site=dxv_admin_site)
class GastoLogisticoAdmin(DuplicarMixin, admin.ModelAdmin):
    change_list_template = 'admin/core/change_list_with_total.html'
    list_display = ('marca', 'escenario', 'nombre', 'tipo', 'valor_mensual_formateado', 'fecha_modificacion')
    list_filter = ('escenario', 'marca', 'tipo')
    search_fields = ('nombre', 'notas')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    actions = ['duplicar_registros']

    fieldsets = (
        ('Información Básica', {
            'fields': ('marca', 'escenario', 'nombre', 'tipo', 'valor_mensual'),
            'description': '⚠️ IMPORTANTE: Para fletes de terceros (transportadoras externas), usar la tabla VEHÍCULOS con esquema="Tercero" en lugar de gastos logísticos. La opción "flete_tercero" ha sido deprecada.'
        }),
        ('Asignación Geográfica (P&G por Zona)', {
            'fields': ('tipo_asignacion_geo', 'zona'),
            'description': 'Cómo se distribuye este gasto entre las zonas comerciales'
        }),
        ('Notas', {
            'fields': ('notas',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def valor_mensual_formateado(self, obj):
        return f"${obj.valor_mensual:,.0f}"
    valor_mensual_formateado.short_description = 'Valor Mensual'
    valor_mensual_formateado.admin_order_field = 'valor_mensual'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data['cl'].queryset
            total = qs.aggregate(total=Sum('valor_mensual'))['total'] or 0
            total_registros = qs.count()
            promedio = total / total_registros if total_registros > 0 else 0

            response.context_data['total_valor_mensual'] = total
            response.context_data['total_registros'] = total_registros
            response.context_data['promedio_registro'] = promedio
        except (AttributeError, KeyError):
            pass
        return response


@admin.register(Impuesto, site=dxv_admin_site)
class ImpuestoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'aplicacion', 'valor_display', 'periodicidad', 'activo')
    list_filter = ('tipo', 'aplicacion', 'periodicidad', 'activo')
    search_fields = ('nombre', 'notas')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'tipo', 'aplicacion', 'periodicidad', 'activo')
        }),
        ('Configuración', {
            'fields': ('porcentaje', 'valor_fijo'),
            'description': 'Completa el porcentaje (para impuestos sobre ventas/utilidad) o el valor fijo'
        }),
        ('Notas', {
            'fields': ('notas',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def valor_display(self, obj):
        if obj.porcentaje:
            return f"{obj.porcentaje:.2f}%"
        elif obj.valor_fijo:
            return f"${obj.valor_fijo:,.0f}"
        return "-"
    valor_display.short_description = 'Valor'


class TramoDescuentoFacturaInline(admin.TabularInline):
    """Inline para tramos de descuento"""
    model = TramoDescuentoFactura
    extra = 1
    fields = ('orden', 'porcentaje_ventas', 'porcentaje_descuento')
    ordering = ('orden',)


@admin.register(ConfiguracionDescuentos, site=dxv_admin_site)
class ConfiguracionDescuentosAdmin(admin.ModelAdmin):
    list_display = (
        'marca',
        'porcentaje_rebate_display',
        'descuento_financiero_display',
        'total_tramos_display',
        'activa',
        'fecha_modificacion'
    )
    list_filter = ('activa', 'aplica_descuento_financiero')
    search_fields = ('marca__nombre',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion', 'total_tramos_porcentaje')
    inlines = [TramoDescuentoFacturaInline]

    fieldsets = (
        ('Marca', {
            'fields': ('marca', 'activa')
        }),
        ('Descuento a Pie de Factura', {
            'fields': ('total_tramos_porcentaje',),
            'description': 'Los tramos de descuento se configuran en la tabla inferior. La suma de los porcentajes de ventas debe ser 100%.'
        }),
        ('Rebate / RxP', {
            'fields': ('porcentaje_rebate',),
            'description': 'Porcentaje de rebate sobre las ventas netas (después de descuentos a pie de factura)'
        }),
        ('Descuento Financiero', {
            'fields': ('aplica_descuento_financiero', 'porcentaje_descuento_financiero'),
            'description': 'Descuento por pronto pago'
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def porcentaje_rebate_display(self, obj):
        return f"{obj.porcentaje_rebate:.2f}%"
    porcentaje_rebate_display.short_description = 'Rebate'
    porcentaje_rebate_display.admin_order_field = 'porcentaje_rebate'

    def descuento_financiero_display(self, obj):
        if obj.aplica_descuento_financiero:
            return f"SÍ - {obj.porcentaje_descuento_financiero:.2f}%"
        return "NO"
    descuento_financiero_display.short_description = 'Desc. Financiero'

    def total_tramos_display(self, obj):
        from django.utils.html import format_html
        total = obj.total_tramos_porcentaje()
        if abs(total - 100) < 0.01:
            color = "green"
            status = "✓"
        elif total == 0:
            color = "gray"
            status = "⚠"
        else:
            color = "red"
            status = "✗"
        return format_html('<span style="color: {}; font-weight: bold;">{} {}%</span>', color, status, f'{total:.2f}')
    total_tramos_display.short_description = 'Total Tramos'

    def save_model(self, request, obj, form, change):
        """Valida antes de guardar"""
        from django.contrib import messages
        super().save_model(request, obj, form, change)

        # Validar que los tramos sumen 100% después de guardar
        if obj.tramos.exists():
            total = obj.total_tramos_porcentaje()
            if abs(total - 100) > 0.01:
                messages.warning(
                    request,
                    f"Advertencia: Los tramos de descuento suman {total:.2f}% en lugar de 100%"
                )


@admin.register(PoliticaRecursosHumanos, site=dxv_admin_site)
class PoliticaRecursosHumanosAdmin(DuplicarMixin, admin.ModelAdmin):
    list_display = (
        'anio',
        'valor_dotacion_formateado',
        'frecuencia_dotacion_display',
        'frecuencia_epp_display',
        'tasa_rotacion_percent',
        'indice_incremento',
        'activo'
    )
    list_filter = ('activo', 'anio', 'indice_incremento')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    actions = ['duplicar_registros']

    fieldsets = (
        ('Año y Proyección', {
            'fields': ('anio', 'indice_incremento', 'activo'),
            'description': 'El índice de incremento se usa al proyectar valores monetarios al siguiente año'
        }),
        ('Dotación', {
            'fields': ('valor_dotacion_completa', 'frecuencia_dotacion_meses', 'tope_smlv_dotacion'),
            'description': 'Frecuencia en meses: 4 = cada 4 meses (3 veces/año), 6 = cada 6 meses (2 veces/año)'
        }),
        ('EPP (Comercial)', {
            'fields': ('valor_epp_anual_comercial', 'frecuencia_epp_meses'),
            'description': 'Frecuencia en meses: 12 = cada año, 24 = cada 2 años'
        }),
        ('Exámenes Médicos', {
            'fields': (
                ('costo_examen_ingreso_comercial', 'costo_examen_ingreso_operativo'),
                ('costo_examen_periodico_comercial', 'costo_examen_periodico_operativo'),
                'tasa_rotacion_anual'
            ),
            'description': 'Configuración para cálculo de exámenes según rotación y planta'
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def valor_dotacion_formateado(self, obj):
        return f"${obj.valor_dotacion_completa:,.0f}"
    valor_dotacion_formateado.short_description = 'Valor Dotación'

    def costo_examen_ingreso_comercial_formateado(self, obj):
        return f"${obj.costo_examen_ingreso_comercial:,.0f}"
    costo_examen_ingreso_comercial_formateado.short_description = 'Ex. Ingreso (Com)'

    def costo_examen_ingreso_operativo_formateado(self, obj):
        return f"${obj.costo_examen_ingreso_operativo:,.0f}"
    costo_examen_ingreso_operativo_formateado.short_description = 'Ex. Ingreso (Otros)'

    def tasa_rotacion_percent(self, obj):
        return f"{obj.tasa_rotacion_anual:.1f}%"
    tasa_rotacion_percent.short_description = 'Rotación'

    def frecuencia_dotacion_display(self, obj):
        meses = obj.frecuencia_dotacion_meses
        veces_anio = 12 / meses
        if veces_anio == int(veces_anio):
            return f"c/{meses}m ({int(veces_anio)}x/año)"
        return f"c/{meses}m ({veces_anio:.1f}x/año)"
    frecuencia_dotacion_display.short_description = 'Frec. Dotación'

    def frecuencia_epp_display(self, obj):
        meses = obj.frecuencia_epp_meses
        if meses >= 12:
            anios = meses / 12
            if anios == int(anios):
                return f"c/{int(anios)} año(s)"
            return f"c/{anios:.1f} años"
        return f"c/{meses} meses"
    frecuencia_epp_display.short_description = 'Frec. EPP'


# ============================================================================
# ADMINS PARA MÓDULO DE LEJANÍAS
# ============================================================================

@admin.register(Municipio, site=dxv_admin_site)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'departamento', 'codigo_dane', 'activo')
    list_filter = ('departamento', 'activo')
    search_fields = ['nombre', 'codigo_dane', 'departamento']  # Para autocomplete
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'departamento', 'codigo_dane', 'activo')
        }),
        ('Geolocalización (Opcional)', {
            'fields': ('latitud', 'longitud'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MatrizDesplazamiento, site=dxv_admin_site)
class MatrizDesplazamientoAdmin(admin.ModelAdmin):
    list_display = ('origen', 'destino', 'distancia_km', 'tiempo_minutos', 'tiempo_horas', 'peaje_formateado')
    list_filter = ('origen__departamento',)
    search_fields = ('origen__nombre', 'destino__nombre')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    autocomplete_fields = ['origen', 'destino']

    fieldsets = (
        ('Ruta', {
            'fields': ('origen', 'destino'),
            'description': 'Cada tramo es unidireccional. Ej: Amagá→Medellín es diferente de Medellín→Amagá'
        }),
        ('Distancia y Tiempo', {
            'fields': ('distancia_km', 'tiempo_minutos')
        }),
        ('Peajes (Solo para Logística)', {
            'fields': ('peaje_ida',),
            'description': 'Costo de peajes en este tramo. Solo aplica para vehículos logísticos (no para motos comerciales).'
        }),
        ('Notas', {
            'fields': ('notas',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def peaje_formateado(self, obj):
        if obj.peaje_ida:
            return f"${obj.peaje_ida:,.0f}"
        return "-"
    peaje_formateado.short_description = 'Peaje'

    def tiempo_horas(self, obj):
        return f"{obj.tiempo_minutos / 60:.1f}h"
    tiempo_horas.short_description = 'Tiempo (hrs)'


@admin.register(ConfiguracionLejania, site=dxv_admin_site)
class ConfiguracionLejaniaAdmin(admin.ModelAdmin):
    list_display = ('escenario', 'municipio_bodega', 'umbral_logistica', 'umbral_comercial')
    list_filter = ('escenario__anio',)
    search_fields = ('escenario__nombre',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    autocomplete_fields = ['municipio_bodega', 'municipio_comite']

    fieldsets = (
        ('Escenario y Bodega', {
            'fields': ('escenario', 'municipio_bodega')
        }),
        ('Umbrales de Lejanía', {
            'fields': ('umbral_lejania_logistica_km', 'umbral_lejania_comercial_km'),
            'description': 'Distancia mínima en km para aplicar cálculo de lejanía'
        }),
        ('Precios de Combustible', {
            'fields': ('precio_galon_gasolina', 'precio_galon_acpm'),
            'description': 'Precios usados para calcular combustible en Recorridos Logísticos y Zonas Comerciales'
        }),
        ('Consumo Combustible Comercial', {
            'fields': ('consumo_galon_km_moto', 'consumo_galon_km_automovil'),
            'description': 'Rendimiento en km por galón (solo para vehículos comerciales). Los logísticos usan el consumo del vehículo.'
        }),
        ('Pernocta Logística - Conductor', {
            'fields': (
                ('desayuno_conductor', 'almuerzo_conductor', 'cena_conductor'),
                'alojamiento_conductor',
            ),
            'description': 'Gastos del conductor. En esquema Tercero, estos van incluidos en el pago al tercero.'
        }),
        ('Pernocta Logística - Auxiliar', {
            'fields': (
                ('desayuno_auxiliar', 'almuerzo_auxiliar', 'cena_auxiliar'),
                'alojamiento_auxiliar',
            ),
            'description': 'Gastos del auxiliar. Siempre los paga la empresa (convenios, etc.)'
        }),
        ('Gastos Vehículo Logística', {
            'fields': (
                'parqueadero_logistica',
                'es_constitutiva_salario_logistica'
            )
        }),
        ('Gastos Pernocta Comercial', {
            'fields': (
                ('desayuno_comercial', 'almuerzo_comercial', 'cena_comercial'),
                'alojamiento_comercial',
                'es_constitutiva_salario_comercial'
            )
        }),
        ('Comité Comercial', {
            'fields': (
                'tiene_comite_comercial',
                ('municipio_comite', 'frecuencia_comite'),
            ),
            'description': 'Reunión periódica de vendedores. El costo de lejanía se suma a todos los vendedores de este escenario.'
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def umbral_logistica(self, obj):
        return f"{obj.umbral_lejania_logistica_km} km"
    umbral_logistica.short_description = 'Umbral Log.'

    def umbral_comercial(self, obj):
        return f"{obj.umbral_lejania_comercial_km} km"
    umbral_comercial.short_description = 'Umbral Com.'


class ZonaMunicipioInline(admin.TabularInline):
    """Inline para municipios de una zona comercial"""
    model = ZonaMunicipio
    extra = 1
    autocomplete_fields = ['municipio']
    fields = ('municipio', 'visitas_por_periodo')


@admin.register(Zona, site=dxv_admin_site)
class ZonaAdmin(DuplicarMixin, admin.ModelAdmin):
    """Admin para Zonas Comerciales (vendedores)"""
    list_display = ('nombre', 'marca', 'vendedor', 'venta_proyectada_fmt', 'participacion_ventas_fmt', 'tipo_vehiculo_comercial', 'frecuencia', 'requiere_pernocta', 'activo')
    list_filter = ('marca', 'escenario', 'frecuencia', 'requiere_pernocta', 'tipo_vehiculo_comercial', 'activo')
    search_fields = ['nombre', 'vendedor__nombre', 'marca__nombre']
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    autocomplete_fields = ['vendedor', 'municipio_base_vendedor']
    inlines = [ZonaMunicipioInline]
    actions = ['duplicar_registros']

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'activo')
        }),
        ('Asignación', {
            'fields': ('marca', 'escenario', 'vendedor', 'municipio_base_vendedor')
        }),
        ('Configuración Comercial', {
            'fields': ('tipo_vehiculo_comercial', 'frecuencia'),
            'description': 'Tipo de vehículo que usa el vendedor y frecuencia de visitas'
        }),
        ('Pernocta Comercial', {
            'fields': ('requiere_pernocta', 'noches_pernocta'),
            'description': 'Si el vendedor requiere pernoctar fuera de casa'
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def venta_proyectada_fmt(self, obj):
        return f"${obj.venta_proyectada:,.0f}"
    venta_proyectada_fmt.short_description = 'Venta Proy.'
    venta_proyectada_fmt.admin_order_field = 'venta_proyectada'

    def participacion_ventas_fmt(self, obj):
        return f"{obj.participacion_ventas:.2f}%"
    participacion_ventas_fmt.short_description = 'Part. %'
    participacion_ventas_fmt.admin_order_field = 'participacion_ventas'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('marca', 'vendedor', 'municipio_base_vendedor')


@admin.register(ZonaMunicipio, site=dxv_admin_site)
class ZonaMunicipioAdmin(admin.ModelAdmin):
    """Admin para relación Zona-Municipio (comercial)"""
    list_display = ('zona', 'municipio', 'venta_proyectada_fmt', 'participacion_ventas_fmt', 'visitas_por_periodo', 'visitas_mensuales_calc')
    list_filter = ('zona__marca', 'zona__frecuencia')
    search_fields = ('zona__nombre', 'municipio__nombre')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    autocomplete_fields = ['zona', 'municipio']

    fieldsets = (
        ('Relación', {
            'fields': ('zona', 'municipio')
        }),
        ('Visitas Comerciales', {
            'fields': ('visitas_por_periodo',),
            'description': 'Cantidad de visitas por periodo según la frecuencia de la zona'
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def venta_proyectada_fmt(self, obj):
        return f"${obj.venta_proyectada:,.0f}"
    venta_proyectada_fmt.short_description = 'Venta Proy.'
    venta_proyectada_fmt.admin_order_field = 'venta_proyectada'

    def participacion_ventas_fmt(self, obj):
        return f"{obj.participacion_ventas:.2f}%"
    participacion_ventas_fmt.short_description = 'Part. %'
    participacion_ventas_fmt.admin_order_field = 'participacion_ventas'

    def visitas_mensuales_calc(self, obj):
        return obj.visitas_mensuales()
    visitas_mensuales_calc.short_description = 'Visitas/Mes'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('zona', 'municipio')


# ============================================================================
# ADMINS PARA RECORRIDOS LOGÍSTICOS
# ============================================================================

class RecorridoMunicipioInline(admin.TabularInline):
    """Inline para municipios de un recorrido logístico"""
    model = RutaMunicipio
    extra = 1
    autocomplete_fields = ['municipio']
    fields = ('orden_visita', 'municipio', 'flete_base')
    ordering = ['orden_visita']


@admin.register(RutaLogistica, site=dxv_admin_site)
class RecorridoLogisticoAdmin(DuplicarMixin, admin.ModelAdmin):
    """Admin para Recorridos Logísticos (circuitos que hace un vehículo)"""
    list_display = ('nombre', 'marca', 'vehiculo', 'esquema_vehiculo', 'frecuencia', 'viajes_por_periodo', 'requiere_pernocta', 'activo')
    list_filter = ('marca', 'escenario', 'vehiculo__esquema', 'frecuencia', 'requiere_pernocta', 'activo')
    search_fields = ['nombre', 'vehiculo__tipo_vehiculo']
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    autocomplete_fields = ['vehiculo']
    inlines = [RecorridoMunicipioInline]
    actions = ['duplicar_registros']

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'activo')
        }),
        ('Asignación', {
            'fields': ('marca', 'escenario', 'vehiculo'),
            'description': 'El vehículo puede ser propio, renting o tercero'
        }),
        ('Frecuencia', {
            'fields': ('frecuencia', 'viajes_por_periodo'),
            'description': 'Cuántas veces por periodo (semana/quincena/mes) se hace este recorrido completo'
        }),
        ('Personal de Ruta', {
            'fields': ('cantidad_auxiliares',),
            'description': 'Cantidad de auxiliares de entrega que van en este recorrido (0, 1 o 2)'
        }),
        ('Pernocta', {
            'fields': ('requiere_pernocta', 'noches_pernocta'),
            'description': 'Si el recorrido completo requiere que el conductor pase la noche fuera'
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def esquema_vehiculo(self, obj):
        return obj.vehiculo.get_esquema_display() if obj.vehiculo else '-'
    esquema_vehiculo.short_description = 'Esquema'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('marca', 'vehiculo', 'escenario')


@admin.register(RutaMunicipio, site=dxv_admin_site)
class RecorridoMunicipioAdmin(admin.ModelAdmin):
    """Admin para Municipios de un Recorrido (logística)"""
    list_display = ('ruta', 'orden_visita', 'municipio', 'flete_base_formateado')
    list_filter = ('ruta__marca', 'ruta__vehiculo__esquema', 'ruta__frecuencia')
    search_fields = ('ruta__nombre', 'municipio__nombre')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    autocomplete_fields = ['ruta', 'municipio']
    ordering = ['ruta', 'orden_visita']

    fieldsets = (
        ('Recorrido', {
            'fields': ('ruta', 'orden_visita', 'municipio'),
            'description': 'El orden de visita define la secuencia del circuito'
        }),
        ('Flete (Solo Terceros)', {
            'fields': ('flete_base',),
            'description': 'Valor base del flete para este municipio. Solo aplica si el vehículo es tercero.'
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def flete_base_formateado(self, obj):
        if obj.flete_base:
            return f"${obj.flete_base:,.0f}"
        return "-"
    flete_base_formateado.short_description = 'Flete Base'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ruta', 'ruta__vehiculo', 'municipio')


# =============================================================================
# MÓDULO DE PROYECCIÓN DE VENTAS
# =============================================================================

@admin.register(CanalVenta, site=dxv_admin_site)
class CanalVentaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo', 'fecha_modificacion')
    list_filter = ('activo',)
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        (None, {
            'fields': ('nombre', 'descripcion', 'activo')
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CategoriaProducto, site=dxv_admin_site)
class CategoriaProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'marca', 'precio_promedio_fmt', 'activo')
    list_filter = ('marca', 'activo')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        (None, {
            'fields': ('nombre', 'descripcion', 'marca', 'precio_promedio', 'activo')
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def precio_promedio_fmt(self, obj):
        return f"${obj.precio_promedio:,.0f}"
    precio_promedio_fmt.short_description = 'Precio Promedio'


@admin.register(Producto, site=dxv_admin_site)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('sku', 'nombre', 'marca', 'categoria', 'precio_unitario_fmt', 'activo')
    list_filter = ('marca', 'categoria', 'activo')
    search_fields = ('sku', 'nombre')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        (None, {
            'fields': ('sku', 'nombre', 'marca', 'categoria', 'precio_unitario', 'activo')
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def precio_unitario_fmt(self, obj):
        return f"${obj.precio_unitario:,.0f}"
    precio_unitario_fmt.short_description = 'Precio Unitario'


class PlantillaEstacionalForm(forms.ModelForm):
    """Form que valida que los porcentajes sumen 100%"""
    class Meta:
        model = PlantillaEstacional
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
        total = sum(cleaned_data.get(mes, 0) or 0 for mes in meses)
        if abs(float(total) - 100) > 0.5:
            raise forms.ValidationError(
                f"Los porcentajes deben sumar 100%. Suma actual: {total:.2f}%"
            )
        return cleaned_data


@admin.register(PlantillaEstacional, site=dxv_admin_site)
class PlantillaEstacionalAdmin(DuplicarMixin, admin.ModelAdmin):
    form = PlantillaEstacionalForm
    list_display = ('nombre', 'marca', 'total_porcentaje_fmt')
    list_filter = ('marca',)
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    actions = ['duplicar_registros']

    fieldsets = (
        ('Información General', {
            'fields': ('nombre', 'descripcion', 'marca')
        }),
        ('Distribución Mensual (%)', {
            'fields': (
                ('enero', 'febrero', 'marzo'),
                ('abril', 'mayo', 'junio'),
                ('julio', 'agosto', 'septiembre'),
                ('octubre', 'noviembre', 'diciembre'),
            ),
            'description': 'Los porcentajes deben sumar 100%'
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def total_porcentaje_fmt(self, obj):
        total = obj.total_porcentaje()
        return f"{total:.2f}%"
    total_porcentaje_fmt.short_description = 'Total %'


@admin.register(DefinicionMercado, site=dxv_admin_site)
class DefinicionMercadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'tamano_mercado_fmt', 'crecimiento_anual', 'activo')
    list_filter = ('tipo', 'activo')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información General', {
            'fields': ('nombre', 'tipo', 'descripcion', 'activo')
        }),
        ('Tamaño del Mercado', {
            'fields': ('tamano_mercado', 'crecimiento_anual')
        }),
        ('Para Tipo "Clientes"', {
            'fields': ('numero_clientes_potenciales', 'ticket_promedio'),
            'classes': ('collapse',),
            'description': 'Solo aplica si el tipo de mercado es "Base de Clientes"'
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def tamano_mercado_fmt(self, obj):
        return f"${obj.tamano_mercado:,.0f}"
    tamano_mercado_fmt.short_description = 'Tamaño Mercado'


# Inlines para ProyeccionVentasConfig
class ProyeccionManualInline(admin.StackedInline):
    model = ProyeccionManual
    extra = 0
    max_num = 1
    fieldsets = (
        ('Ventas Mensuales', {
            'fields': (
                ('enero', 'febrero', 'marzo'),
                ('abril', 'mayo', 'junio'),
                ('julio', 'agosto', 'septiembre'),
                ('octubre', 'noviembre', 'diciembre'),
            )
        }),
    )


class ProyeccionCrecimientoInline(admin.StackedInline):
    model = ProyeccionCrecimiento
    extra = 0
    max_num = 1
    fieldsets = (
        ('Configuración de Crecimiento', {
            'fields': ('anio_base', 'ventas_base_anual', 'factor_crecimiento')
        }),
    )


class ProyeccionProductoInline(admin.TabularInline):
    model = ProyeccionProducto
    extra = 1
    fields = ('tipo', 'producto', 'categoria', 'precio_unitario',
              'unidades_enero', 'unidades_febrero', 'unidades_marzo',
              'unidades_abril', 'unidades_mayo', 'unidades_junio',
              'unidades_julio', 'unidades_agosto', 'unidades_septiembre',
              'unidades_octubre', 'unidades_noviembre', 'unidades_diciembre')


class ProyeccionCanalInline(admin.TabularInline):
    model = ProyeccionCanal
    extra = 1
    fields = ('canal', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
              'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre')


class ProyeccionPenetracionInline(admin.StackedInline):
    model = ProyeccionPenetracion
    extra = 0
    max_num = 1
    fieldsets = (
        ('Configuración de Penetración', {
            'fields': ('mercado', 'penetracion_inicial', 'penetracion_final')
        }),
    )


@admin.register(ProyeccionVentasConfig, site=dxv_admin_site)
class ProyeccionVentasConfigAdmin(DuplicarMixin, admin.ModelAdmin):
    list_display = ('marca', 'escenario', 'anio', 'metodo', 'venta_anual_fmt', 'fecha_modificacion')
    list_filter = ('marca', 'escenario', 'anio', 'metodo')
    search_fields = ('marca__nombre', 'escenario__nombre', 'notas')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion', 'venta_anual_calculada')
    actions = ['duplicar_registros']

    fieldsets = (
        ('Configuración', {
            'fields': ('marca', 'escenario', 'anio', 'metodo')
        }),
        ('Estacionalidad', {
            'fields': ('plantilla_estacional',),
            'description': 'Selecciona una plantilla para distribuir las ventas mensualmente (aplica para métodos Crecimiento y Penetración)'
        }),
        ('Resultado', {
            'fields': ('venta_anual_calculada',),
            'description': 'Venta anual calculada según el método seleccionado'
        }),
        ('Notas', {
            'fields': ('notas',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    inlines = [
        ProyeccionManualInline,
        ProyeccionCrecimientoInline,
        ProyeccionProductoInline,
        ProyeccionCanalInline,
        ProyeccionPenetracionInline,
    ]

    def venta_anual_fmt(self, obj):
        try:
            venta = obj.get_venta_anual()
            return f"${venta:,.0f}"
        except Exception:
            return "-"
    venta_anual_fmt.short_description = 'Venta Anual'

    def venta_anual_calculada(self, obj):
        try:
            venta = obj.get_venta_anual()
            return f"${venta:,.0f}"
        except Exception:
            return "No calculable - complete los datos del método seleccionado"
    venta_anual_calculada.short_description = 'Venta Anual Calculada'


# Admin independientes para los modelos de detalle (por si se quieren ver/editar directamente)
@admin.register(ProyeccionManual, site=dxv_admin_site)
class ProyeccionManualAdmin(admin.ModelAdmin):
    list_display = ('config', 'total_anual_fmt')
    search_fields = ('config__marca__nombre',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Configuración', {
            'fields': ('config',)
        }),
        ('Ventas Mensuales', {
            'fields': (
                ('enero', 'febrero', 'marzo'),
                ('abril', 'mayo', 'junio'),
                ('julio', 'agosto', 'septiembre'),
                ('octubre', 'noviembre', 'diciembre'),
            )
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def total_anual_fmt(self, obj):
        return f"${obj.get_total_anual():,.0f}"
    total_anual_fmt.short_description = 'Total Anual'


@admin.register(ProyeccionCrecimiento, site=dxv_admin_site)
class ProyeccionCrecimientoAdmin(admin.ModelAdmin):
    list_display = ('config', 'anio_base', 'ventas_base_fmt', 'factor_crecimiento', 'venta_proyectada_fmt')
    search_fields = ('config__marca__nombre',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Configuración', {
            'fields': ('config',)
        }),
        ('Parámetros de Crecimiento', {
            'fields': ('anio_base', 'ventas_base_anual', 'factor_crecimiento')
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def ventas_base_fmt(self, obj):
        return f"${obj.ventas_base_anual:,.0f}"
    ventas_base_fmt.short_description = 'Ventas Base'

    def venta_proyectada_fmt(self, obj):
        return f"${obj.get_venta_anual_proyectada():,.0f}"
    venta_proyectada_fmt.short_description = 'Venta Proyectada'


@admin.register(ProyeccionProducto, site=dxv_admin_site)
class ProyeccionProductoAdmin(admin.ModelAdmin):
    list_display = ('config', 'tipo', 'producto', 'categoria', 'precio_unitario_fmt', 'total_unidades', 'total_ventas_fmt')
    list_filter = ('config__marca', 'tipo')
    search_fields = ('config__marca__nombre', 'producto__nombre', 'categoria__nombre')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Configuración', {
            'fields': ('config', 'tipo', 'producto', 'categoria', 'precio_unitario')
        }),
        ('Unidades por Mes', {
            'fields': (
                ('unidades_enero', 'unidades_febrero', 'unidades_marzo'),
                ('unidades_abril', 'unidades_mayo', 'unidades_junio'),
                ('unidades_julio', 'unidades_agosto', 'unidades_septiembre'),
                ('unidades_octubre', 'unidades_noviembre', 'unidades_diciembre'),
            )
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def precio_unitario_fmt(self, obj):
        return f"${obj.precio_unitario:,.0f}"
    precio_unitario_fmt.short_description = 'Precio Unit.'

    def total_unidades(self, obj):
        return f"{obj.get_total_unidades():,}"
    total_unidades.short_description = 'Total Unid.'

    def total_ventas_fmt(self, obj):
        return f"${obj.get_total_ventas():,.0f}"
    total_ventas_fmt.short_description = 'Total Ventas'


@admin.register(ProyeccionCanal, site=dxv_admin_site)
class ProyeccionCanalAdmin(admin.ModelAdmin):
    list_display = ('config', 'canal', 'total_anual_fmt')
    list_filter = ('config__marca', 'canal')
    search_fields = ('config__marca__nombre', 'canal__nombre')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Configuración', {
            'fields': ('config', 'canal')
        }),
        ('Ventas Mensuales', {
            'fields': (
                ('enero', 'febrero', 'marzo'),
                ('abril', 'mayo', 'junio'),
                ('julio', 'agosto', 'septiembre'),
                ('octubre', 'noviembre', 'diciembre'),
            )
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def total_anual_fmt(self, obj):
        return f"${obj.get_total_anual():,.0f}"
    total_anual_fmt.short_description = 'Total Anual'


@admin.register(ProyeccionPenetracion, site=dxv_admin_site)
class ProyeccionPenetracionAdmin(admin.ModelAdmin):
    list_display = ('config', 'mercado', 'penetracion_inicial', 'penetracion_final', 'venta_proyectada_fmt')
    list_filter = ('config__marca', 'mercado')
    search_fields = ('config__marca__nombre', 'mercado__nombre')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Configuración', {
            'fields': ('config', 'mercado')
        }),
        ('Penetración', {
            'fields': ('penetracion_inicial', 'penetracion_final'),
            'description': 'Porcentaje del mercado a capturar al inicio y final del año'
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def venta_proyectada_fmt(self, obj):
        return f"${obj.get_venta_anual_proyectada():,.0f}"
    venta_proyectada_fmt.short_description = 'Venta Proyectada'

