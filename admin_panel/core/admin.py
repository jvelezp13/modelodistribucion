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
    Escenario, PoliticaRecursosHumanos,
    # Módulo de Lejanías
    Municipio, MatrizDesplazamiento, ConfiguracionLejania,
    Zona, ZonaMunicipio
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
    change_list_template = 'admin/core/change_list_with_total.html'
    list_display = ('marca', 'nombre', 'escenario', 'tipo', 'cantidad', 'salario_base', 'costo_total_estimado', 'asignacion', 'perfil_prestacional')
    list_filter = ('escenario', 'marca', 'tipo', 'asignacion', 'perfil_prestacional')
    search_fields = ('marca__nombre', 'nombre')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('marca', 'escenario', 'nombre', 'tipo', 'cantidad', 'salario_base', 'perfil_prestacional')
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


@admin.register(PersonalLogistico)
class PersonalLogisticoAdmin(admin.ModelAdmin):
    change_list_template = 'admin/core/change_list_with_total.html'
    list_display = ('marca', 'nombre', 'escenario', 'tipo', 'cantidad', 'salario_base', 'costo_total_estimado', 'asignacion', 'perfil_prestacional')
    list_filter = ('escenario', 'marca', 'tipo', 'asignacion', 'perfil_prestacional')
    search_fields = ('marca__nombre', 'nombre')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('marca', 'escenario', 'nombre', 'tipo', 'cantidad', 'salario_base', 'perfil_prestacional')
        }),
        ('Asignación', {
            'fields': ('asignacion', 'porcentaje_dedicacion', 'criterio_prorrateo')
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


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    change_list_template = 'admin/core/change_list_with_total.html'
    list_display = ('marca', 'escenario', 'tipo_vehiculo', 'esquema', 'cantidad', 'costo_mensual_estimado_formateado')
    list_filter = ('escenario', 'marca', 'tipo_vehiculo', 'esquema', 'asignacion')
    search_fields = ('marca__nombre',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('marca', 'escenario', 'tipo_vehiculo', 'esquema', 'cantidad', 'kilometraje_promedio_mensual')
        }),
        ('Esquema: Tercero', {
            'fields': ('valor_flete_mensual',),
            'description': '⚠️ IMPORTANTE: Para vehículos de terceros (fletes externos), registrar AQUÍ en lugar de usar Gastos Logísticos "flete_tercero". Diligenciar solo si el esquema es "Tercero".',
            'classes': ('collapse',)
        }),
        ('Información del Propietario (Terceros)', {
            'fields': ('placa', 'propietario', 'tipo_documento', 'numero_documento', 'conductor'),
            'description': 'Información del propietario y conductor para vehículos de terceros',
            'classes': ('collapse',)
        }),
        ('Información Bancaria (Pagos a Terceros)', {
            'fields': ('banco', 'tipo_cuenta', 'numero_cuenta'),
            'description': 'Datos bancarios para liquidación y pago a terceros',
            'classes': ('collapse',)
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
        ('Consumo de Combustible (Propio/Renting)', {
            'fields': ('tipo_combustible', 'consumo_galon_km'),
            'description': 'Diligenciar para esquemas Propio y Renting',
            'classes': ('collapse',)
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
        ('Asignación y Proyecciones', {
            'fields': ('asignacion', 'porcentaje_uso', 'criterio_prorrateo', 'indice_incremento'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

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
    change_list_template = 'admin/core/change_list_with_total.html'
    list_display = ('nombre', 'marca', 'escenario', 'tipo', 'cantidad', 'asignacion', 'tipo_contrato', 'valor_mensual', 'costo_total_estimado')
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


@admin.register(GastoAdministrativo)
class GastoAdministrativoAdmin(admin.ModelAdmin):
    change_list_template = 'admin/core/change_list_with_total.html'
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


@admin.register(GastoComercial)
class GastoComercialAdmin(admin.ModelAdmin):
    change_list_template = 'admin/core/change_list_with_total.html'
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


@admin.register(GastoLogistico)
class GastoLogisticoAdmin(admin.ModelAdmin):
    change_list_template = 'admin/core/change_list_with_total.html'
    list_display = ('marca', 'escenario', 'nombre', 'tipo', 'valor_mensual_formateado', 'fecha_modificacion')
    list_filter = ('escenario', 'marca', 'tipo')
    search_fields = ('nombre', 'notas')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('marca', 'escenario', 'nombre', 'tipo', 'valor_mensual'),
            'description': '⚠️ IMPORTANTE: Para fletes de terceros (transportadoras externas), usar la tabla VEHÍCULOS con esquema="Tercero" en lugar de gastos logísticos. La opción "flete_tercero" ha sido deprecada.'
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
        'costo_examen_ingreso_comercial_formateado',
        'costo_examen_ingreso_operativo_formateado',
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
        ('EPP (Comercial)', {
            'fields': ('valor_epp_anual_comercial', 'frecuencia_epp_anual'),
            'description': 'Configuración para EPP específico de personal comercial'
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


# ============================================================================
# ADMINS PARA MÓDULO DE LEJANÍAS
# ============================================================================

@admin.register(Municipio)
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


@admin.register(MatrizDesplazamiento)
class MatrizDesplazamientoAdmin(admin.ModelAdmin):
    list_display = ('origen', 'destino', 'distancia_km', 'tiempo_minutos', 'tiempo_horas', 'peaje_ida', 'peaje_vuelta')
    list_filter = ('origen__departamento',)
    search_fields = ('origen__nombre', 'destino__nombre')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    autocomplete_fields = ['origen', 'destino']

    fieldsets = (
        ('Ruta', {
            'fields': ('origen', 'destino')
        }),
        ('Distancia y Tiempo', {
            'fields': ('distancia_km', 'tiempo_minutos')
        }),
        ('Peajes (Solo para Logística)', {
            'fields': ('peaje_ida', 'peaje_vuelta'),
            'description': 'Costos de peajes en la ruta. Solo aplica para vehículos logísticos (no para motos comerciales).'
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

    def tiempo_horas(self, obj):
        return f"{obj.tiempo_minutos / 60:.1f}h"
    tiempo_horas.short_description = 'Tiempo (hrs)'


@admin.register(ConfiguracionLejania)
class ConfiguracionLejaniaAdmin(admin.ModelAdmin):
    list_display = ('escenario', 'municipio_bodega', 'umbral_logistica', 'umbral_comercial')
    list_filter = ('escenario__anio',)
    search_fields = ('escenario__nombre',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    autocomplete_fields = ['municipio_bodega']

    fieldsets = (
        ('Escenario y Bodega', {
            'fields': ('escenario', 'municipio_bodega')
        }),
        ('Umbrales de Lejanía', {
            'fields': ('umbral_lejania_logistica_km', 'umbral_lejania_comercial_km'),
            'description': 'Distancia mínima en km para aplicar cálculo de lejanía'
        }),
        ('Consumo Combustible Comercial', {
            'fields': ('consumo_galon_km_moto', 'consumo_galon_km_automovil'),
            'description': 'Rendimiento en km por galón de gasolina'
        }),
        ('Gastos Pernocta Logística', {
            'fields': (
                ('desayuno_logistica', 'almuerzo_logistica', 'cena_logistica'),
                ('alojamiento_logistica', 'parqueadero_logistica'),
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
    model = ZonaMunicipio
    extra = 1
    autocomplete_fields = ['municipio', 'vehiculo_logistica']
    fields = ('municipio', 'visitas_por_periodo', 'entregas_por_periodo', 'vehiculo_logistica', 'flete_base')


@admin.register(Zona)
class ZonaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'marca', 'vendedor', 'tipo_vehiculo_comercial', 'frecuencia', 'requiere_pernocta', 'activo')
    list_filter = ('marca', 'frecuencia', 'requiere_pernocta', 'tipo_vehiculo_comercial', 'activo')
    search_fields = ('nombre', 'codigo', 'descripcion')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    autocomplete_fields = ['vendedor', 'municipio_base_vendedor']
    inlines = [ZonaMunicipioInline]

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'codigo', 'descripcion', 'activo')
        }),
        ('Asignación', {
            'fields': ('marca', 'escenario', 'vendedor', 'municipio_base_vendedor')
        }),
        ('Configuración Comercial', {
            'fields': ('tipo_vehiculo_comercial', 'frecuencia')
        }),
        ('Pernocta', {
            'fields': ('requiere_pernocta', 'noches_pernocta'),
            'description': 'Si la zona requiere que el personal pernocte fuera de casa'
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('marca', 'vendedor', 'municipio_base_vendedor')


@admin.register(ZonaMunicipio)
class ZonaMunicipioAdmin(admin.ModelAdmin):
    list_display = ('zona', 'municipio', 'visitas_por_periodo', 'entregas_por_periodo', 'visitas_mensuales_calc', 'entregas_mensuales_calc')
    list_filter = ('zona__marca', 'zona__frecuencia')
    search_fields = ('zona__nombre', 'municipio__nombre')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    autocomplete_fields = ['zona', 'municipio']

    fieldsets = (
        ('Relación', {
            'fields': ('zona', 'municipio')
        }),
        ('Frecuencias por Periodo', {
            'fields': ('visitas_por_periodo', 'entregas_por_periodo'),
            'description': 'Frecuencia según el periodo de la zona (semanal/quincenal/mensual)'
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def visitas_mensuales_calc(self, obj):
        return obj.visitas_mensuales()
    visitas_mensuales_calc.short_description = 'Visitas/Mes'

    def entregas_mensuales_calc(self, obj):
        return obj.entregas_mensuales()
    entregas_mensuales_calc.short_description = 'Entregas/Mes'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('zona', 'municipio')

