"""
Configuración del Django Admin para los modelos DxV
"""
from django.contrib import admin
from django.db.models import Sum, Count
from .models import (
    Marca, PersonalComercial, PersonalLogistico,
    Vehiculo, ProyeccionVentas, VolumenOperacion,
    ParametrosMacro, FactorPrestacional,
    PersonalAdministrativo, GastoAdministrativo,
    GastoComercial, GastoLogistico, Impuesto,
    ConfiguracionDescuentos, TramoDescuentoFactura,
    Escenario, PoliticaRecursosHumanos
)


@admin.register(Escenario)
class EscenarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'anio', 'periodo_display', 'activo', 'aprobado', 'fecha_modificacion')
    list_filter = ('tipo', 'anio', 'activo', 'aprobado')
    search_fields = ('nombre', 'notas')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'tipo', 'anio', 'activo', 'aprobado')
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

    actions = ['proyectar_escenario']

    def proyectar_escenario(self, request, queryset):
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


@admin.register(Marca)
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


@admin.register(PersonalComercial)
class PersonalComercialAdmin(admin.ModelAdmin):
    list_display = ('marca', 'escenario', 'tipo', 'cantidad', 'salario_base', 'asignacion', 'perfil_prestacional')
    list_filter = ('escenario', 'marca', 'tipo', 'asignacion', 'perfil_prestacional')
    search_fields = ('marca__nombre',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('marca', 'escenario', 'tipo', 'cantidad', 'salario_base', 'perfil_prestacional')
        }),
        ('Asignación', {
            'fields': ('asignacion', 'porcentaje_dedicacion', 'criterio_prorrateo')
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


@admin.register(PersonalLogistico)
class PersonalLogisticoAdmin(admin.ModelAdmin):
    list_display = ('marca', 'escenario', 'tipo', 'cantidad', 'salario_base', 'asignacion', 'perfil_prestacional')
    list_filter = ('escenario', 'marca', 'tipo', 'asignacion', 'perfil_prestacional')
    search_fields = ('marca__nombre',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('marca', 'escenario', 'tipo', 'cantidad', 'salario_base', 'perfil_prestacional')
        }),
        ('Asignación', {
            'fields': ('asignacion', 'porcentaje_dedicacion', 'criterio_prorrateo')
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('marca', 'escenario', 'tipo_vehiculo', 'esquema', 'cantidad', 'kilometraje_promedio_mensual', 'asignacion')
    list_filter = ('escenario', 'marca', 'tipo_vehiculo', 'esquema', 'asignacion')
    search_fields = ('marca__nombre',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('marca', 'escenario', 'tipo_vehiculo', 'esquema', 'cantidad', 'kilometraje_promedio_mensual')
        }),
        ('Asignación', {
            'fields': ('asignacion', 'porcentaje_uso', 'criterio_prorrateo')
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )


class ProyeccionVentasInline(admin.TabularInline):
    model = ProyeccionVentas
    extra = 12
    max_num = 12


@admin.register(ProyeccionVentas)
class ProyeccionVentasAdmin(admin.ModelAdmin):
    list_display = ('marca', 'escenario', 'anio', 'mes', 'ventas_formateadas', 'fecha_modificacion')
    list_filter = ('escenario', 'marca', 'anio', 'mes')
    search_fields = ('marca__nombre',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('marca', 'escenario', 'anio', 'mes', 'ventas')
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def ventas_formateadas(self, obj):
        return f"${obj.ventas:,.0f}"
    ventas_formateadas.short_description = 'Ventas'
    ventas_formateadas.admin_order_field = 'ventas'


@admin.register(VolumenOperacion)
class VolumenOperacionAdmin(admin.ModelAdmin):
    list_display = (
        'marca',
        'pallets_mensuales',
        'toneladas_mensuales',
        'entregas_mensuales',
        'rutas_activas'
    )
    list_filter = ('marca',)
    search_fields = ('marca__nombre',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Marca', {
            'fields': ('marca',)
        }),
        ('Volumen', {
            'fields': (
                'pallets_mensuales',
                'metros_cubicos_mensuales',
                'toneladas_mensuales',
                'entregas_mensuales'
            )
        }),
        ('Cobertura', {
            'fields': ('rutas_activas', 'zonas_cobertura')
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ParametrosMacro)
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
        return f"{obj.ipc * 100:.2f}%"
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


@admin.register(FactorPrestacional)
class FactorPrestacionalAdmin(admin.ModelAdmin):
    list_display = ('perfil', 'factor_total_percent', 'pension_percent', 'salud_percent', 'fecha_modificacion')
    list_filter = ('perfil',)
    readonly_fields = ('factor_total_display', 'fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Perfil', {
            'fields': ('perfil',)
        }),
        ('Seguridad Social', {
            'fields': ('salud', 'pension', 'arl', 'caja_compensacion', 'icbf', 'sena')
        }),
        ('Prestaciones', {
            'fields': ('cesantias', 'intereses_cesantias', 'prima', 'vacaciones')
        }),
        ('Total Calculado', {
            'fields': ('factor_total_display',),
            'description': 'El factor total se calcula automáticamente sumando todos los componentes'
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def factor_total_display(self, obj):
        """Muestra el factor total calculado (solo para objetos guardados)"""
        if obj and obj.pk:
            return f"{obj.factor_total * 100:.2f}%"
        return "Se calculará al guardar"
    factor_total_display.short_description = 'Factor Total'

    def factor_total_percent(self, obj):
        return f"{obj.factor_total * 100:.2f}%"
    factor_total_percent.short_description = 'Factor Total'

    def pension_percent(self, obj):
        return f"{obj.pension * 100:.2f}%"
    pension_percent.short_description = 'Pensión'
    pension_percent.admin_order_field = 'pension'

    def salud_percent(self, obj):
        return f"{obj.salud * 100:.2f}%"
    salud_percent.short_description = 'Salud'
    salud_percent.admin_order_field = 'salud'


@admin.register(PersonalAdministrativo)
class PersonalAdministrativoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'marca', 'escenario', 'tipo', 'cantidad', 'asignacion', 'tipo_contrato', 'valor_mensual')
    list_filter = ('escenario', 'marca', 'tipo', 'asignacion', 'tipo_contrato')
    search_fields = ('nombre',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

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


@admin.register(GastoAdministrativo)
class GastoAdministrativoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'marca', 'escenario', 'tipo', 'asignacion', 'valor_mensual_formateado', 'criterio_prorrateo')
    list_filter = ('escenario', 'marca', 'tipo', 'asignacion', 'criterio_prorrateo')
    search_fields = ('nombre', 'notas')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

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


@admin.register(GastoComercial)
class GastoComercialAdmin(admin.ModelAdmin):
    list_display = ('marca', 'escenario', 'nombre', 'tipo', 'valor_mensual_formateado', 'fecha_modificacion')
    list_filter = ('escenario', 'marca', 'tipo')
    search_fields = ('nombre', 'notas')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('marca', 'escenario', 'nombre', 'tipo', 'valor_mensual')
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


@admin.register(GastoLogistico)
class GastoLogisticoAdmin(admin.ModelAdmin):
    list_display = ('marca', 'escenario', 'nombre', 'tipo', 'valor_mensual_formateado', 'fecha_modificacion')
    list_filter = ('escenario', 'marca', 'tipo')
    search_fields = ('nombre', 'notas')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('marca', 'escenario', 'nombre', 'tipo', 'valor_mensual')
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


@admin.register(Impuesto)
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
            return f"{obj.porcentaje * 100:.2f}%"
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


@admin.register(ConfiguracionDescuentos)
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
        return f'<span style="color: {color}; font-weight: bold;">{status} {total:.2f}%</span>'
    total_tramos_display.short_description = 'Total Tramos'
    total_tramos_display.allow_tags = True

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


@admin.register(TramoDescuentoFactura)
class TramoDescuentoFacturaAdmin(admin.ModelAdmin):
    list_display = (
        'configuracion',
        'orden',
        'porcentaje_ventas_display',
        'porcentaje_descuento_display',
        'fecha_modificacion'
    )
    list_filter = ('configuracion__marca',)
    search_fields = ('configuracion__marca__nombre',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    ordering = ('configuracion', 'orden')

    fieldsets = (
        ('Configuración', {
            'fields': ('configuracion', 'orden')
        }),
        ('Tramo', {
            'fields': ('porcentaje_ventas', 'porcentaje_descuento'),
            'description': 'Define qué porcentaje de las ventas totales se aplica este descuento'
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def porcentaje_ventas_display(self, obj):
        return f"{obj.porcentaje_ventas:.2f}%"
    porcentaje_ventas_display.short_description = '% Ventas'
    porcentaje_ventas_display.admin_order_field = 'porcentaje_ventas'

    def porcentaje_descuento_display(self, obj):
        return f"{obj.porcentaje_descuento:.2f}%"
    porcentaje_descuento_display.short_description = '% Descuento'
    porcentaje_descuento_display.admin_order_field = 'porcentaje_descuento'


@admin.register(PoliticaRecursosHumanos)
class PoliticaRecursosHumanosAdmin(admin.ModelAdmin):
    list_display = (
        'anio', 
        'valor_dotacion_formateado', 
        'frecuencia_dotacion_anual', 
        'costo_examen_ingreso_formateado',
        'tasa_rotacion_percent',
        'activo'
    )
    list_filter = ('activo', 'anio')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Año', {
            'fields': ('anio', 'activo')
        }),
        ('Dotación', {
            'fields': ('valor_dotacion_completa', 'frecuencia_dotacion_anual', 'tope_smlv_dotacion'),
            'description': 'Configuración para cálculo automático de dotación'
        }),
        ('Exámenes Médicos', {
            'fields': ('costo_examen_ingreso', 'costo_examen_periodico', 'tasa_rotacion_anual'),
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

    def costo_examen_ingreso_formateado(self, obj):
        return f"${obj.costo_examen_ingreso:,.0f}"
    costo_examen_ingreso_formateado.short_description = 'Costo Ex. Ingreso'

    def tasa_rotacion_percent(self, obj):
        return f"{obj.tasa_rotacion_anual:.1f}%"
    tasa_rotacion_percent.short_description = 'Rotación'

