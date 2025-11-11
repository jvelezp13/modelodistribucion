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
    GastoComercial, GastoLogistico, Impuesto
)


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
    list_display = ('marca', 'tipo', 'cantidad', 'salario_base', 'asignacion', 'perfil_prestacional')
    list_filter = ('marca', 'tipo', 'asignacion', 'perfil_prestacional')
    search_fields = ('marca__nombre',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('marca', 'tipo', 'cantidad', 'salario_base', 'perfil_prestacional')
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
    list_display = ('marca', 'tipo', 'cantidad', 'salario_base', 'asignacion', 'perfil_prestacional')
    list_filter = ('marca', 'tipo', 'asignacion', 'perfil_prestacional')
    search_fields = ('marca__nombre',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('marca', 'tipo', 'cantidad', 'salario_base', 'perfil_prestacional')
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
    list_display = ('marca', 'tipo_vehiculo', 'esquema', 'cantidad', 'kilometraje_promedio_mensual', 'asignacion')
    list_filter = ('marca', 'tipo_vehiculo', 'esquema', 'asignacion')
    search_fields = ('marca__nombre',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('marca', 'tipo_vehiculo', 'esquema', 'cantidad', 'kilometraje_promedio_mensual')
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
    list_display = ('marca', 'anio', 'mes', 'ventas_formateadas', 'fecha_modificacion')
    list_filter = ('marca', 'anio', 'mes')
    search_fields = ('marca__nombre',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('marca', 'anio', 'mes', 'ventas')
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
        ('Índices', {
            'fields': ('ipc', 'ipt', 'incremento_salarios')
        }),
        ('Salarios y Subsidios', {
            'fields': ('salario_minimo_legal', 'subsidio_transporte')
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
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

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
        ('Total', {
            'fields': ('factor_total',)
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def factor_total_percent(self, obj):
        return f"{obj.factor_total * 100:.2f}%"
    factor_total_percent.short_description = 'Factor Total'
    factor_total_percent.admin_order_field = 'factor_total'

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
    list_display = ('tipo', 'cantidad', 'tipo_contrato', 'valor_mensual', 'criterio_prorrateo')
    list_filter = ('tipo', 'tipo_contrato', 'criterio_prorrateo')
    search_fields = ('nombre',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
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
        ('Prorrateo', {
            'fields': ('asignacion', 'criterio_prorrateo')
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
    list_display = ('nombre', 'tipo', 'valor_mensual_formateado', 'criterio_prorrateo')
    list_filter = ('tipo', 'criterio_prorrateo')
    search_fields = ('nombre', 'notas')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'tipo', 'valor_mensual')
        }),
        ('Prorrateo', {
            'fields': ('criterio_prorrateo',)
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
    list_display = ('marca', 'nombre', 'tipo', 'valor_mensual_formateado', 'fecha_modificacion')
    list_filter = ('marca', 'tipo')
    search_fields = ('nombre', 'notas')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('marca', 'nombre', 'tipo', 'valor_mensual')
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
    list_display = ('marca', 'nombre', 'tipo', 'valor_mensual_formateado', 'fecha_modificacion')
    list_filter = ('marca', 'tipo')
    search_fields = ('nombre', 'notas')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('marca', 'nombre', 'tipo', 'valor_mensual')
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
