"""
Configuración del Django Admin para los modelos DxV
"""
from django import forms
from django.contrib import admin
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils.html import format_html
from .utils import copiar_instancia
from .models import (
    Marca, PersonalComercial, PersonalLogistico,
    Vehiculo, ParametrosMacro, FactorPrestacional,
    PersonalAdministrativo, GastoAdministrativo,
    GastoComercial, GastoLogistico, Impuesto,
    ConfiguracionDescuentos, TramoDescuentoFactura,
    Escenario, PoliticaRecursosHumanos,
    # Módulo de Operaciones (Centros de Costos)
    Operacion, MarcaOperacion,
    # Módulo de Lejanías Comerciales
    Municipio, MatrizDesplazamiento, ConfiguracionLejania,
    Zona, ZonaMunicipio,
    # Módulo de Rutas Logísticas
    RutaLogistica, RutaMunicipio,
    # Módulo de Proyección de Ventas
    CanalVenta, CategoriaProducto, Producto,
    ProyeccionVentasConfig, ProyeccionManual,
    TipologiaProyeccion,
    # Modelos de asignación multi-marca
    PersonalComercialMarca, PersonalLogisticoMarca, PersonalAdministrativoMarca,
    GastoComercialMarca, GastoLogisticoMarca, GastoAdministrativoMarca,
    ZonaMarca,
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


# =============================================================================
# MIXIN PARA FILTRO GLOBAL POR ESCENARIO/MARCA
# =============================================================================

class GlobalFilterMixin:
    """
    Mixin que filtra automáticamente el queryset por el escenario y marca
    seleccionados globalmente en la sesión.

    Requisitos del modelo:
    - Campo 'escenario' (ForeignKey a Escenario)
    - Campo 'marca' opcional (ForeignKey a Marca)
    """

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Obtener filtros globales de sesión
        escenario_id = request.session.get('global_escenario_id')
        marca_id = request.session.get('global_marca_id')

        # Filtrar por escenario si el modelo tiene el campo
        if escenario_id and hasattr(qs.model, 'escenario'):
            qs = qs.filter(escenario_id=escenario_id)

        # Filtrar por marca si está seleccionada y el modelo tiene el campo
        if marca_id and hasattr(qs.model, 'marca'):
            qs = qs.filter(marca_id=marca_id)

        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Pre-filtra los campos ForeignKey de escenario y marca en formularios"""
        escenario_id = request.session.get('global_escenario_id')
        marca_id = request.session.get('global_marca_id')

        # Pre-seleccionar escenario en formularios
        if db_field.name == 'escenario' and escenario_id:
            kwargs['initial'] = escenario_id
            kwargs['queryset'] = Escenario.objects.filter(pk=escenario_id)

        # Pre-seleccionar marca en formularios (si hay una seleccionada)
        if db_field.name == 'marca' and marca_id:
            kwargs['initial'] = marca_id

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# =============================================================================
# INLINES PARA ASIGNACIÓN MULTI-MARCA
# =============================================================================

class PersonalComercialMarcaInline(admin.TabularInline):
    """Inline para asignar marcas con porcentajes a Personal Comercial"""
    model = PersonalComercialMarca
    extra = 1
    min_num = 1
    autocomplete_fields = ['marca']
    fields = ['marca', 'porcentaje']
    verbose_name = "Marca Asignada"
    verbose_name_plural = "Marcas Asignadas (debe sumar 100%)"


class PersonalLogisticoMarcaInline(admin.TabularInline):
    """Inline para asignar marcas con porcentajes a Personal Logístico"""
    model = PersonalLogisticoMarca
    extra = 1
    min_num = 1
    autocomplete_fields = ['marca']
    fields = ['marca', 'porcentaje']
    verbose_name = "Marca Asignada"
    verbose_name_plural = "Marcas Asignadas (debe sumar 100%)"


class PersonalAdministrativoMarcaInline(admin.TabularInline):
    """Inline para asignar marcas con porcentajes a Personal Administrativo"""
    model = PersonalAdministrativoMarca
    extra = 1
    min_num = 1
    autocomplete_fields = ['marca']
    fields = ['marca', 'porcentaje']
    verbose_name = "Marca Asignada"
    verbose_name_plural = "Marcas Asignadas (debe sumar 100%)"


class GastoComercialMarcaInline(admin.TabularInline):
    """Inline para asignar marcas con porcentajes a Gasto Comercial"""
    model = GastoComercialMarca
    extra = 1
    min_num = 1
    autocomplete_fields = ['marca']
    fields = ['marca', 'porcentaje']
    verbose_name = "Marca Asignada"
    verbose_name_plural = "Marcas Asignadas (debe sumar 100%)"


class GastoLogisticoMarcaInline(admin.TabularInline):
    """Inline para asignar marcas con porcentajes a Gasto Logístico"""
    model = GastoLogisticoMarca
    extra = 1
    min_num = 1
    autocomplete_fields = ['marca']
    fields = ['marca', 'porcentaje']
    verbose_name = "Marca Asignada"
    verbose_name_plural = "Marcas Asignadas (debe sumar 100%)"


class GastoAdministrativoMarcaInline(admin.TabularInline):
    """Inline para asignar marcas con porcentajes a Gasto Administrativo"""
    model = GastoAdministrativoMarca
    extra = 1
    min_num = 1
    autocomplete_fields = ['marca']
    fields = ['marca', 'porcentaje']
    verbose_name = "Marca Asignada"
    verbose_name_plural = "Marcas Asignadas (debe sumar 100%)"


class ZonaMarcaInline(admin.TabularInline):
    """Inline para asignar marcas con porcentajes a Zona Comercial"""
    model = ZonaMarca
    extra = 1
    min_num = 1
    autocomplete_fields = ['marca']
    fields = ['marca', 'porcentaje']
    verbose_name = "Marca Asignada"
    verbose_name_plural = "Marcas Asignadas (debe sumar 100%)"


@admin.register(Escenario, site=dxv_admin_site)
class EscenarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'anio', 'activo', 'fecha_modificacion')
    list_filter = ('tipo', 'anio', 'activo')
    search_fields = ('nombre', 'notas')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'tipo', 'anio', 'activo')
        }),
        ('Detalles', {
            'fields': ('notas',)
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

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


# =============================================================================
# OPERACIONES (CENTROS DE COSTOS)
# =============================================================================

class MarcaOperacionInline(admin.TabularInline):
    """Inline para ver marcas asociadas a una operación (solo lectura de participaciones)"""
    model = MarcaOperacion
    extra = 0
    autocomplete_fields = ['marca']
    fields = ['marca', 'participacion_ventas', 'venta_proyectada_fmt', 'activo']
    readonly_fields = ['participacion_ventas', 'venta_proyectada_fmt']
    verbose_name_plural = 'Marcas en esta Operación (para editar participaciones use Distribución de Ventas)'

    def venta_proyectada_fmt(self, obj):
        if obj.venta_proyectada:
            return f"${obj.venta_proyectada:,.0f}"
        return "$0"
    venta_proyectada_fmt.short_description = "Venta Mensual"


@admin.register(Operacion, site=dxv_admin_site)
class OperacionAdmin(admin.ModelAdmin):
    """
    Admin para Operaciones (Centros de Costos).
    Permite gestionar operaciones geográficas dentro de un escenario.
    """
    list_display = ('nombre', 'codigo', 'escenario', 'municipio_base', 'activa', 'cantidad_marcas', 'cantidad_zonas')
    list_filter = ('escenario', 'activa')
    search_fields = ('nombre', 'codigo', 'escenario__nombre')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    autocomplete_fields = ['escenario', 'municipio_base']
    inlines = [MarcaOperacionInline]

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'codigo', 'escenario', 'activa', 'color')
        }),
        ('Ubicación', {
            'fields': ('municipio_base',),
            'description': 'Ubicación de la bodega/CEDI principal de esta operación'
        }),
        ('Impuestos', {
            'fields': ('tasa_ica',),
            'description': 'Tasa de ICA (Industria y Comercio) para esta operación'
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

    def cantidad_marcas(self, obj):
        return obj.marcas_asociadas.filter(activo=True).count()
    cantidad_marcas.short_description = 'Marcas'

    def cantidad_zonas(self, obj):
        return obj.zonas.filter(activo=True).count()
    cantidad_zonas.short_description = 'Zonas'


@admin.register(MarcaOperacion, site=dxv_admin_site)
class MarcaOperacionAdmin(admin.ModelAdmin):
    """
    Admin para la relación Marca-Operación.

    Flujo de ventas:
    - Usuario configura participacion_ventas desde Distribución de Ventas
    - venta_proyectada se calcula automáticamente desde ProyeccionVentasConfig
    """
    list_display = ('marca', 'operacion', 'escenario_display', 'participacion_ventas', 'venta_proyectada_fmt', 'activo')
    list_filter = ('operacion__escenario', 'operacion', 'marca', 'activo')
    search_fields = ('marca__nombre', 'operacion__nombre', 'operacion__escenario__nombre')
    readonly_fields = ('participacion_ventas', 'venta_proyectada', 'fecha_creacion', 'fecha_modificacion')
    autocomplete_fields = ['marca', 'operacion']

    fieldsets = (
        ('Relación', {
            'fields': ('marca', 'operacion', 'activo')
        }),
        ('Distribución de Ventas', {
            'fields': ('participacion_ventas', 'venta_proyectada'),
            'description': 'Solo lectura. Para modificar participaciones use <a href="/dxv/distribucion-ventas/">Distribución de Ventas</a> donde se valida que sumen 100%.'
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    def escenario_display(self, obj):
        return obj.operacion.escenario.nombre
    escenario_display.short_description = 'Escenario'

    def venta_proyectada_fmt(self, obj):
        if obj.venta_proyectada:
            return f"${obj.venta_proyectada:,.0f}"
        return "$0"
    venta_proyectada_fmt.short_description = "Venta Calculada"
    venta_proyectada_fmt.admin_order_field = "venta_proyectada"


class ColorPickerWidget(forms.TextInput):
    """Widget de selector de color HTML5"""
    input_type = 'color'

    def format_value(self, value):
        # Asegurar que el valor tenga formato #RRGGBB
        if value and not value.startswith('#'):
            value = f'#{value}'
        return value or '#000000'


class MarcaForm(forms.ModelForm):
    """Formulario personalizado para Marca con color picker"""
    class Meta:
        model = Marca
        fields = '__all__'
        widgets = {
            'color': ColorPickerWidget(attrs={'style': 'width: 80px; height: 40px; padding: 0; cursor: pointer;'})
        }


@admin.register(Marca, site=dxv_admin_site)
class MarcaAdmin(admin.ModelAdmin):
    form = MarcaForm
    list_display = ('nombre', 'marca_id', 'color_preview', 'activa', 'total_empleados', 'total_vehiculos', 'fecha_modificacion')
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

    def color_preview(self, obj):
        """Muestra preview del color en la lista"""
        if obj.color:
            return format_html(
                '<span style="background-color: {}; padding: 5px 15px; border-radius: 3px;">&nbsp;</span> {}',
                obj.color, obj.color
            )
        return '-'
    color_preview.short_description = 'Color'

    def total_empleados(self, obj):
        comercial = obj.personal_comercial.aggregate(total=Sum('cantidad'))['total'] or 0
        logistico = obj.personal_logistico.aggregate(total=Sum('cantidad'))['total'] or 0
        return comercial + logistico
    total_empleados.short_description = 'Total Empleados'

    def total_vehiculos(self, obj):
        return obj.vehiculos.aggregate(total=Sum('cantidad'))['total'] or 0
    total_vehiculos.short_description = 'Total Vehículos'


class AuxiliosNoPrestacionalesWidget(forms.Widget):
    """Widget para editar auxilios no prestacionales como campos individuales"""
    template_name = 'admin/widgets/auxilios_no_prestacionales.html'

    CAMPOS_AUXILIOS = [
        ('cuota_carro', 'Cuota Carro'),
        ('arriendo_vivienda', 'Arriendo Vivienda'),
        ('bono_alimentacion', 'Bono Alimentación'),
        ('rodamiento', 'Rodamiento'),
        ('otros', 'Otros'),
    ]

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        # Parsear el valor JSON
        if isinstance(value, str):
            try:
                import json
                value = json.loads(value) if value else {}
            except (json.JSONDecodeError, TypeError):
                value = {}
        elif value is None:
            value = {}

        context['widget']['campos'] = [
            {
                'key': key,
                'label': label,
                'value': value.get(key, ''),
                'id': f'{attrs.get("id", name)}_{key}',
                'name': f'{name}_{key}',
            }
            for key, label in self.CAMPOS_AUXILIOS
        ]
        context['widget']['hidden_name'] = name
        return context

    def value_from_datadict(self, data, files, name):
        import json
        result = {}
        for key, _ in self.CAMPOS_AUXILIOS:
            val = data.get(f'{name}_{key}', '').strip()
            if val:
                try:
                    # Limpiar separadores de miles y convertir
                    val_clean = val.replace('.', '').replace(',', '.')
                    result[key] = float(val_clean)
                except (ValueError, TypeError):
                    pass
        return json.dumps(result) if result else '{}'


class PersonalComercialForm(forms.ModelForm):
    """Form con campos monetarios localizados y widget de auxilios"""
    salario_base = forms.DecimalField(
        localize=True,
        label="Salario Base",
    )

    class Meta:
        model = PersonalComercial
        fields = '__all__'
        widgets = {
            'auxilios_no_prestacionales': AuxiliosNoPrestacionalesWidget(),
        }


@admin.register(PersonalComercial, site=dxv_admin_site)
class PersonalComercialAdmin(GlobalFilterMixin, DuplicarMixin, admin.ModelAdmin):
    form = PersonalComercialForm
    change_list_template = 'admin/core/change_list_with_total.html'
    list_display = ('marcas_display_admin', 'nombre', 'escenario', 'tipo', 'cantidad', 'salario_formateado', 'costo_total_estimado', 'operacion', 'zonas_asignadas_display', 'indice_incremento')
    list_filter = ('escenario', 'tipo', 'tipo_asignacion_operacion', 'indice_incremento', 'perfil_prestacional', 'operacion')
    search_fields = ('nombre', 'asignaciones_marca__marca__nombre', 'operacion__nombre')
    readonly_fields = ('zonas_asignadas_display', 'fecha_creacion', 'fecha_modificacion')
    actions = ['duplicar_registros']
    inlines = [PersonalComercialMarcaInline]

    fieldsets = (
        ('Información Básica', {
            'fields': ('escenario', 'nombre', 'tipo', 'cantidad', 'salario_base', 'perfil_prestacional')
        }),
        ('Asignación de Operación', {
            'fields': (
                'tipo_asignacion_operacion',
                'operacion',
                'criterio_prorrateo_operacion',
            ),
            'description': '''
                <b>Tipo:</b> Individual = 100% a una operación | Compartido = se distribuye entre operaciones<br>
                <b>Operación:</b> Centro de costos al que pertenece este vendedor (solo si tipo es Individual)
            '''
        }),
        ('Proyección Anual', {
            'fields': ('indice_incremento',),
            'description': 'Índice usado para proyectar este costo a años futuros.'
        }),
        ('Zonas Asignadas', {
            'fields': ('zonas_asignadas_display',),
            'description': '🔒 Solo lectura - Las zonas se asignan desde el módulo de Zonas Comerciales, no aquí.'
        }),
        ('Auxilios No Prestacionales', {
            'fields': ('auxilios_no_prestacionales',),
            'description': 'Auxilios que NO generan prestaciones sociales.',
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    class Media:
        js = ('admin/js/personal_condicional.js', 'admin/js/distribuir_equitativo.js')

    def zonas_asignadas_display(self, obj):
        """Muestra las zonas donde trabaja este vendedor"""
        zonas = obj.zonas_asignadas.all()
        if not zonas.exists():
            return format_html('<em style="color: #999;">Sin zonas asignadas</em>')

        from django.urls import reverse
        links = []
        for zona in zonas:
            url = reverse('admin:core_zona_change', args=[zona.pk])
            links.append(f'<a href="{url}" target="_blank">{zona.nombre}</a>')

        return format_html(', '.join(links))
    zonas_asignadas_display.short_description = 'Zonas Asignadas'

    def marcas_display_admin(self, obj):
        """Muestra las marcas asignadas en el list_display"""
        return obj.marcas_display
    marcas_display_admin.short_description = 'Marcas'

    def salario_formateado(self, obj):
        return f"${obj.salario_base:,.0f}" if obj.salario_base else "-"
    salario_formateado.short_description = 'Salario Base'
    salario_formateado.admin_order_field = 'salario_base'

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
        except Exception as e:
            return f"Error: {str(e)[:30]}"
    costo_total_estimado.short_description = 'Costo Total (Est.)'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data['cl'].queryset
            total_general = 0
            for obj in qs:
                try:
                    total_general += obj.calcular_costo_mensual() or 0
                except Exception:
                    pass  # Ignorar errores individuales
            total_registros = qs.count()
            promedio = total_general / total_registros if total_registros > 0 else 0

            response.context_data['total_valor_mensual'] = total_general
            response.context_data['total_registros'] = total_registros
            response.context_data['promedio_registro'] = promedio
        except (AttributeError, KeyError):
            pass
        return response


class PersonalLogisticoForm(forms.ModelForm):
    """Form con campos monetarios localizados y widget de auxilios"""
    salario_base = forms.DecimalField(
        localize=True,
        label="Salario Base",
    )

    class Meta:
        model = PersonalLogistico
        fields = '__all__'
        widgets = {
            'auxilios_no_prestacionales': AuxiliosNoPrestacionalesWidget(),
        }


@admin.register(PersonalLogistico, site=dxv_admin_site)
class PersonalLogisticoAdmin(GlobalFilterMixin, DuplicarMixin, admin.ModelAdmin):
    form = PersonalLogisticoForm
    change_list_template = 'admin/core/change_list_with_total.html'
    list_display = ('marcas_display_admin', 'nombre', 'escenario', 'tipo', 'cantidad', 'salario_formateado', 'costo_total_estimado', 'tipo_asignacion_operacion', 'tipo_asignacion_geo', 'indice_incremento')
    list_filter = ('escenario', 'tipo', 'tipo_asignacion_operacion', 'tipo_asignacion_geo', 'indice_incremento', 'perfil_prestacional')
    search_fields = ('nombre', 'asignaciones_marca__marca__nombre')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    actions = ['duplicar_registros']
    inlines = [PersonalLogisticoMarcaInline]

    fieldsets = (
        ('Información Básica', {
            'fields': ('escenario', 'nombre', 'tipo', 'cantidad', 'salario_base', 'perfil_prestacional')
        }),
        ('Proyección Anual', {
            'fields': ('indice_incremento',),
            'description': 'Índice usado para proyectar este costo a años futuros.'
        }),
        ('Distribución Geográfica y Operaciones', {
            'fields': (
                'tipo_asignacion_operacion',
                'operacion',
                'criterio_prorrateo_operacion',
                'tipo_asignacion_geo',
                'zona',
            ),
            'description': '''
                <b>Por Operación:</b> Individual = asignado a una operación | Compartido = se distribuye entre operaciones<br>
                <b>Por Zona:</b> Directo = 100% a una zona | Proporcional = según ventas | Compartido = equitativo
            '''
        }),
        ('Auxilios No Prestacionales', {
            'fields': ('auxilios_no_prestacionales',),
            'description': 'Auxilios que NO generan prestaciones sociales.',
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    class Media:
        js = ('admin/js/personal_condicional.js', 'admin/js/distribuir_equitativo.js')

    def marcas_display_admin(self, obj):
        """Muestra las marcas asignadas en el list_display"""
        return obj.marcas_display
    marcas_display_admin.short_description = 'Marcas'

    def salario_formateado(self, obj):
        return f"${obj.salario_base:,.0f}" if obj.salario_base else "-"
    salario_formateado.short_description = 'Salario Base'
    salario_formateado.admin_order_field = 'salario_base'

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

            # Sumar auxilio adicional (sin prestaciones)
            if obj.auxilio_adicional:
                total += obj.auxilio_adicional

            return f"${total:,.0f}"
        except FactorPrestacional.DoesNotExist:
            return f"${obj.salario_base:,.0f} (Sin Factor)"
        except Exception as e:
            return f"Error: {str(e)[:30]}"
    costo_total_estimado.short_description = 'Costo Total (Est.)'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data['cl'].queryset
            total_general = 0
            for obj in qs:
                try:
                    total_general += obj.calcular_costo_mensual() or 0
                except Exception:
                    pass  # Ignorar errores individuales
            total_registros = qs.count()
            promedio = total_general / total_registros if total_registros > 0 else 0

            response.context_data['total_valor_mensual'] = total_general
            response.context_data['total_registros'] = total_registros
            response.context_data['promedio_registro'] = promedio
        except (AttributeError, KeyError):
            pass
        return response


@admin.register(Vehiculo, site=dxv_admin_site)
class VehiculoAdmin(GlobalFilterMixin, DuplicarMixin, admin.ModelAdmin):
    change_list_template = 'admin/core/change_list_with_total.html'
    list_display = ('nombre_display', 'marca', 'escenario', 'tipo_vehiculo', 'esquema', 'cantidad', 'costo_mensual_estimado_formateado', 'asignacion', 'tipo_asignacion_operacion', 'indice_incremento')
    list_filter = ('escenario', 'marca', 'tipo_vehiculo', 'esquema', 'asignacion', 'tipo_asignacion_operacion', 'indice_incremento')
    search_fields = ['nombre', 'marca__nombre', 'tipo_vehiculo', 'esquema']
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    actions = ['duplicar_registros']

    class Media:
        js = ('admin/js/vehiculo_condicional.js',)

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'marca', 'escenario', 'tipo_vehiculo', 'esquema', 'cantidad'),
            'description': 'El campo "Nombre" permite identificar el vehículo de forma única (ej: "Turbo 01", "NKR Zona Norte")'
        }),
        ('Distribución de Costos', {
            'fields': (
                'asignacion', 'porcentaje_uso', 'criterio_prorrateo',
                'tipo_asignacion_operacion', 'operacion', 'criterio_prorrateo_operacion',
            ),
            'description': 'Define cómo se distribuye el costo del vehículo entre marcas y operaciones.'
        }),
        ('Proyección Anual', {
            'fields': ('indice_incremento',),
            'description': 'Índice usado para proyectar este costo a años futuros.'
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
        ('Consumo de Combustible', {
            'fields': ('tipo_combustible', 'consumo_galon_km'),
            'description': 'Requerido para calcular combustible en Recorridos Logísticos. Aplica a todos los esquemas.',
        }),
        ('Otros Costos Operativos (Propio/Renting)', {
            'fields': ('costo_lavado_mensual', 'costo_parqueadero_mensual'),
            'description': 'Aplica solo a vehículos Propios y Renting.',
            'classes': ('collapse',)
        }),
        ('Otros Costos', {
            'fields': ('costo_monitoreo_mensual', 'costo_seguro_mercancia_mensual'),
            'description': 'Monitoreo Satelital (GPS) y Seguro de Mercancía. Aplica a todos los esquemas.',
        }),
        ('Personal del Vehículo', {
            'fields': ('cantidad_auxiliares',),
            'description': 'Auxiliares de entrega fijos asignados a este vehículo. Se usa para calcular costos de personal en rutas logísticas.'
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


class ParametrosMacroForm(forms.ModelForm):
    """Form con campos monetarios localizados"""
    salario_minimo_legal = forms.DecimalField(
        localize=True,
        label="Salario Mínimo Legal",
        help_text="Salario mínimo mensual vigente"
    )
    subsidio_transporte = forms.DecimalField(
        localize=True,
        label="Subsidio de Transporte",
        help_text="Auxilio de transporte mensual"
    )

    class Meta:
        model = ParametrosMacro
        fields = '__all__'


@admin.register(ParametrosMacro, site=dxv_admin_site)
class ParametrosMacroAdmin(admin.ModelAdmin):
    form = ParametrosMacroForm
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
class FactorPrestacionalAdmin(GlobalFilterMixin, DuplicarMixin, admin.ModelAdmin):
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


class PersonalAdministrativoForm(forms.ModelForm):
    """Form con campos monetarios localizados y widget de auxilios"""
    salario_base = forms.DecimalField(
        localize=True,
        label="Salario Base",
        required=False,
    )
    honorarios_mensuales = forms.DecimalField(
        localize=True,
        label="Honorarios Mensuales",
        required=False,
    )

    class Meta:
        model = PersonalAdministrativo
        fields = '__all__'
        widgets = {
            'auxilios_no_prestacionales': AuxiliosNoPrestacionalesWidget(),
        }


@admin.register(PersonalAdministrativo, site=dxv_admin_site)
class PersonalAdministrativoAdmin(GlobalFilterMixin, DuplicarMixin, admin.ModelAdmin):
    form = PersonalAdministrativoForm
    change_list_template = 'admin/core/change_list_with_total.html'
    list_display = ('marcas_display_admin', 'nombre', 'escenario', 'tipo', 'cantidad', 'tipo_contrato', 'valor_mensual', 'costo_total_estimado', 'tipo_asignacion_operacion', 'tipo_asignacion_geo', 'indice_incremento')
    list_filter = ('escenario', 'tipo', 'tipo_asignacion_operacion', 'tipo_asignacion_geo', 'indice_incremento', 'tipo_contrato')
    search_fields = ('nombre', 'asignaciones_marca__marca__nombre')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    actions = ['duplicar_registros']
    inlines = [PersonalAdministrativoMarcaInline]

    fieldsets = (
        ('Información Básica', {
            'fields': ('escenario', 'nombre', 'tipo', 'cantidad')
        }),
        ('Compensación', {
            'fields': ('tipo_contrato', 'salario_base', 'perfil_prestacional', 'honorarios_mensuales'),
            'description': 'Nómina: Salario Base + Perfil Prestacional | Honorarios: Honorarios Mensuales'
        }),
        ('Proyección Anual', {
            'fields': ('indice_incremento',),
            'description': 'Índice usado para proyectar este costo a años futuros.'
        }),
        ('Distribución Geográfica y Operaciones', {
            'fields': (
                'tipo_asignacion_operacion',
                'operacion',
                'criterio_prorrateo_operacion',
                'tipo_asignacion_geo',
            ),
            'description': '''
                <b>Por Operación:</b> Individual = asignado a una operación | Compartido = se distribuye entre operaciones<br>
                <b>Por Zona:</b> Típicamente Proporcional o Compartido (personal admin no se asigna directo a zona)
            '''
        }),
        ('Auxilios No Prestacionales', {
            'fields': ('auxilios_no_prestacionales',),
            'description': 'Auxilios que NO generan prestaciones sociales.',
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    class Media:
        js = ('admin/js/personal_condicional.js', 'admin/js/distribuir_equitativo.js')

    def marcas_display_admin(self, obj):
        """Muestra las marcas asignadas en el list_display"""
        return obj.marcas_display
    marcas_display_admin.short_description = 'Marcas'

    def valor_mensual(self, obj):
        if obj.tipo_contrato == 'nomina' and obj.salario_base:
            return f"${obj.salario_base:,.0f}"
        elif obj.tipo_contrato == 'honorarios' and obj.honorarios_mensuales:
            return f"${obj.honorarios_mensuales:,.0f}"
        return "-"
    valor_mensual.short_description = 'Valor Mensual'

    def costo_total_estimado(self, obj):
        try:
            if obj.tipo_contrato == 'honorarios':
                return f"${obj.honorarios_mensuales:,.0f}" if obj.honorarios_mensuales else "-"

            if not obj.salario_base:
                return "-"

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

            # Sumar auxilio adicional (sin prestaciones)
            if obj.auxilio_adicional:
                total += obj.auxilio_adicional

            return f"${total:,.0f}"
        except FactorPrestacional.DoesNotExist:
            return f"${obj.salario_base:,.0f} (Sin Factor)"
        except Exception as e:
            return f"Error: {str(e)[:30]}"
    costo_total_estimado.short_description = 'Costo Total (Est.)'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data['cl'].queryset
            total_general = 0
            for obj in qs:
                try:
                    total_general += obj.calcular_costo_mensual() or 0
                except Exception:
                    pass  # Ignorar errores individuales
            total_registros = qs.count()
            promedio = total_general / total_registros if total_registros > 0 else 0

            response.context_data['total_valor_mensual'] = total_general
            response.context_data['total_registros'] = total_registros
            response.context_data['promedio_registro'] = promedio
        except (AttributeError, KeyError):
            pass
        return response


class GastoAdministrativoForm(forms.ModelForm):
    """Form con campo monetario localizado"""
    valor_mensual = forms.DecimalField(
        localize=True,
        label="Valor Mensual",
    )

    class Meta:
        model = GastoAdministrativo
        fields = '__all__'


@admin.register(GastoAdministrativo, site=dxv_admin_site)
class GastoAdministrativoAdmin(GlobalFilterMixin, DuplicarMixin, admin.ModelAdmin):
    form = GastoAdministrativoForm
    change_list_template = 'admin/core/change_list_with_total.html'
    list_display = ('marcas_display_admin', 'nombre', 'escenario', 'tipo', 'valor_mensual_formateado', 'tipo_asignacion_operacion', 'tipo_asignacion_geo', 'indice_incremento')
    list_filter = ('escenario', 'tipo', 'tipo_asignacion_operacion', 'tipo_asignacion_geo', 'indice_incremento')
    search_fields = ('nombre', 'notas', 'asignaciones_marca__marca__nombre')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    actions = ['duplicar_registros']
    inlines = [GastoAdministrativoMarcaInline]

    fieldsets = (
        ('Información Básica', {
            'fields': ('escenario', 'nombre', 'tipo', 'valor_mensual')
        }),
        ('Proyección Anual', {
            'fields': ('indice_incremento',),
            'description': 'Índice usado para proyectar este costo a años futuros.'
        }),
        ('Distribución Geográfica y Operaciones', {
            'fields': (
                'tipo_asignacion_operacion',
                'operacion',
                'criterio_prorrateo_operacion',
                'tipo_asignacion_geo',
            ),
            'description': '''
                <b>Por Operación:</b> Individual = asignado a una operación | Compartido = se distribuye entre operaciones<br>
                <b>Por Zona:</b> Típicamente Proporcional o Compartido (gastos admin no se asignan directo a zona)
            '''
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

    class Media:
        js = ('admin/js/personal_condicional.js', 'admin/js/distribuir_equitativo.js')

    def marcas_display_admin(self, obj):
        """Muestra las marcas asignadas en el list_display"""
        return obj.marcas_display
    marcas_display_admin.short_description = 'Marcas'

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


class GastoComercialForm(forms.ModelForm):
    """Form con campo monetario localizado"""
    valor_mensual = forms.DecimalField(
        localize=True,
        label="Valor Mensual",
    )

    class Meta:
        model = GastoComercial
        fields = '__all__'


@admin.register(GastoComercial, site=dxv_admin_site)
class GastoComercialAdmin(GlobalFilterMixin, DuplicarMixin, admin.ModelAdmin):
    form = GastoComercialForm
    change_list_template = 'admin/core/change_list_with_total.html'
    list_display = ('marcas_display_admin', 'escenario', 'nombre', 'tipo', 'valor_mensual_formateado', 'tipo_asignacion_operacion', 'tipo_asignacion_geo', 'indice_incremento')
    list_filter = ('escenario', 'tipo', 'tipo_asignacion_operacion', 'tipo_asignacion_geo', 'indice_incremento')
    search_fields = ('nombre', 'notas', 'asignaciones_marca__marca__nombre')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    actions = ['duplicar_registros']
    inlines = [GastoComercialMarcaInline]

    fieldsets = (
        ('Información Básica', {
            'fields': ('escenario', 'nombre', 'tipo', 'valor_mensual')
        }),
        ('Proyección Anual', {
            'fields': ('indice_incremento',),
            'description': 'Índice usado para proyectar este costo a años futuros.'
        }),
        ('Distribución Geográfica y Operaciones', {
            'fields': (
                'tipo_asignacion_operacion',
                'operacion',
                'criterio_prorrateo_operacion',
                'tipo_asignacion_geo',
                'zona',
            ),
            'description': '''
                <b>Por Operación:</b> Individual = asignado a una operación | Compartido = se distribuye entre operaciones<br>
                <b>Por Zona:</b> Directo = 100% a una zona | Proporcional = según ventas
            '''
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

    class Media:
        js = ('admin/js/personal_condicional.js', 'admin/js/distribuir_equitativo.js')

    def marcas_display_admin(self, obj):
        """Muestra las marcas asignadas en el list_display"""
        return obj.marcas_display
    marcas_display_admin.short_description = 'Marcas'

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


class GastoLogisticoForm(forms.ModelForm):
    """Form con campo monetario localizado"""
    valor_mensual = forms.DecimalField(
        localize=True,
        label="Valor Mensual",
    )

    class Meta:
        model = GastoLogistico
        fields = '__all__'


@admin.register(GastoLogistico, site=dxv_admin_site)
class GastoLogisticoAdmin(GlobalFilterMixin, DuplicarMixin, admin.ModelAdmin):
    form = GastoLogisticoForm
    change_list_template = 'admin/core/change_list_with_total.html'
    list_display = ('marcas_display_admin', 'escenario', 'nombre', 'tipo', 'valor_mensual_formateado', 'tipo_asignacion_operacion', 'tipo_asignacion_geo', 'indice_incremento')
    list_filter = ('escenario', 'tipo', 'tipo_asignacion_operacion', 'tipo_asignacion_geo', 'indice_incremento')
    search_fields = ('nombre', 'notas', 'asignaciones_marca__marca__nombre')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    actions = ['duplicar_registros']
    inlines = [GastoLogisticoMarcaInline]

    fieldsets = (
        ('Información Básica', {
            'fields': ('escenario', 'nombre', 'tipo', 'valor_mensual'),
            'description': 'Para fletes de terceros, usar VEHÍCULOS con esquema="Tercero".'
        }),
        ('Proyección Anual', {
            'fields': ('indice_incremento',),
            'description': 'Índice usado para proyectar este costo a años futuros.'
        }),
        ('Distribución Geográfica y Operaciones', {
            'fields': (
                'tipo_asignacion_operacion',
                'operacion',
                'criterio_prorrateo_operacion',
                'tipo_asignacion_geo',
                'zona',
            ),
            'description': '''
                <b>Por Operación:</b> Individual = asignado a una operación | Compartido = se distribuye entre operaciones<br>
                <b>Por Zona:</b> Directo = 100% a una zona | Proporcional = según ventas
            '''
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

    class Media:
        js = ('admin/js/personal_condicional.js', 'admin/js/distribuir_equitativo.js')

    def marcas_display_admin(self, obj):
        """Muestra las marcas asignadas en el list_display"""
        return obj.marcas_display
    marcas_display_admin.short_description = 'Marcas'

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
            'fields': ('nombre', 'tipo', 'aplicacion', 'periodicidad', 'activo'),
            'description': 'Nota: El ICA (Industria y Comercio) se configura directamente en cada Operación, no aquí.'
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
    extra = 0
    fields = ('orden', 'porcentaje_ventas', 'porcentaje_descuento')
    ordering = ('orden',)


@admin.register(ConfiguracionDescuentos, site=dxv_admin_site)
class ConfiguracionDescuentosAdmin(admin.ModelAdmin):
    list_display = (
        'marca',
        'porcentaje_rebate_display',
        'descuento_financiero_display',
        'cesantia_comercial_display',
        'total_tramos_display',
        'activa',
        'fecha_modificacion'
    )
    list_filter = ('activa', 'aplica_descuento_financiero', 'aplica_cesantia_comercial')
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
        ('Cesantía Comercial', {
            'fields': ('aplica_cesantia_comercial',),
            'description': 'Art. 1324 C.Co. - Provisión mensual de 1/12 (8.33%) sobre los ingresos del agente (Margen Bruto + Rebate + Desc. Financiero)'
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

    def cesantia_comercial_display(self, obj):
        if obj.aplica_cesantia_comercial:
            return "SÍ (1/12)"
        return "NO"
    cesantia_comercial_display.short_description = 'Cesantía Com.'

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


class PoliticaRecursosHumanosForm(forms.ModelForm):
    """Form con campos monetarios localizados"""
    valor_dotacion_completa = forms.DecimalField(
        localize=True,
        label="Valor Dotación Completa",
        help_text="Valor total de una dotación"
    )
    valor_epp_anual_comercial = forms.DecimalField(
        localize=True,
        label="Valor EPP Anual (Comercial)"
    )
    costo_examen_ingreso_comercial = forms.DecimalField(
        localize=True,
        label="Costo Examen Ingreso (Comercial)"
    )
    costo_examen_ingreso_operativo = forms.DecimalField(
        localize=True,
        label="Costo Examen Ingreso (Operativo)"
    )
    costo_examen_periodico_comercial = forms.DecimalField(
        localize=True,
        label="Costo Examen Periódico (Comercial)"
    )
    costo_examen_periodico_operativo = forms.DecimalField(
        localize=True,
        label="Costo Examen Periódico (Operativo)"
    )

    class Meta:
        model = PoliticaRecursosHumanos
        fields = '__all__'


@admin.register(PoliticaRecursosHumanos, site=dxv_admin_site)
class PoliticaRecursosHumanosAdmin(GlobalFilterMixin, DuplicarMixin, admin.ModelAdmin):
    form = PoliticaRecursosHumanosForm
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
class ConfiguracionLejaniaAdmin(GlobalFilterMixin, admin.ModelAdmin):
    list_display = ('escenario', 'municipio_bodega', 'umbral_logistica', 'umbral_comercial')
    list_filter = ('escenario__anio',)
    search_fields = ('escenario__nombre',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    autocomplete_fields = ['municipio_bodega', 'municipio_comite']

    class Media:
        js = ('admin/js/config_lejania_condicional.js',)

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
        ('Costos Adicionales por KM (Comercial)', {
            'fields': ('costo_adicional_km_moto', 'costo_adicional_km_automovil'),
            'description': 'Mantenimiento, depreciación y llantas por km. Aplica desde el mismo umbral que combustible.'
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
    extra = 0
    autocomplete_fields = ['municipio']
    fields = ('municipio', 'visitas_por_periodo', 'participacion_ventas', 'venta_proyectada')
    readonly_fields = ('participacion_ventas', 'venta_proyectada')


@admin.register(Zona, site=dxv_admin_site)
class ZonaAdmin(GlobalFilterMixin, DuplicarMixin, admin.ModelAdmin):
    """Admin para Zonas Comerciales (vendedores)"""
    list_display = ('nombre', 'marcas_display_admin', 'operacion', 'vendedor', 'participacion_ventas_fmt', 'venta_proyectada_fmt', 'tipo_vehiculo_comercial', 'frecuencia', 'requiere_pernocta', 'activo')
    list_filter = ('escenario', 'vendedor__operacion', 'frecuencia', 'requiere_pernocta', 'tipo_vehiculo_comercial', 'activo')
    search_fields = ['nombre', 'vendedor__nombre', 'vendedor__operacion__nombre']
    readonly_fields = ('operacion_display', 'marcas_heredadas_display', 'participacion_ventas', 'venta_proyectada', 'fecha_creacion', 'fecha_modificacion')
    autocomplete_fields = ['vendedor', 'municipio_base_vendedor']
    inlines = [ZonaMunicipioInline]  # ZonaMarcaInline eliminado - marcas se heredan del vendedor
    actions = ['duplicar_registros']

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'activo')
        }),
        ('Asignación de Vendedor', {
            'fields': ('escenario', 'vendedor', 'municipio_base_vendedor'),
            'description': 'Asigna el vendedor. La operación y marcas se heredan automáticamente del vendedor.'
        }),
        ('Información Heredada del Vendedor', {
            'fields': ('operacion_display', 'marcas_heredadas_display'),
            'description': '🔒 Solo lectura - Esta información se hereda del vendedor asignado',
            'classes': ('collapse',)
        }),
        ('Distribución de Ventas', {
            'fields': ('participacion_ventas', 'venta_proyectada'),
            'description': 'Solo lectura. Para modificar participaciones use <a href="/dxv/distribucion-ventas/">Distribución de Ventas</a> donde se valida que sumen 100%.'
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

    class Media:
        js = ('admin/js/personal_condicional.js', 'admin/js/distribuir_equitativo.js')

    def operacion_display(self, obj):
        """Muestra la operación heredada del vendedor"""
        if obj.vendedor and obj.vendedor.operacion:
            vendedor_nombre = obj.vendedor.nombre or "vendedor"
            return format_html(
                '<strong>{}</strong><br><small style="color: #666;">🔗 Heredado de: {}</small>',
                obj.vendedor.operacion.nombre,
                vendedor_nombre
            )
        return format_html('<em style="color: #999;">Sin vendedor asignado</em>')
    operacion_display.short_description = 'Operación (Heredada del Vendedor)'

    def marcas_heredadas_display(self, obj):
        """Muestra las marcas heredadas del vendedor"""
        if obj.vendedor:
            vendedor_nombre = obj.vendedor.nombre or "vendedor"
            marcas_texto = obj.vendedor.marcas_display
            return format_html(
                '<strong>{}</strong><br><small style="color: #666;">🔗 Heredado de: {}</small>',
                marcas_texto,
                vendedor_nombre
            )
        return format_html('<em style="color: #999;">Sin vendedor asignado</em>')
    marcas_heredadas_display.short_description = 'Marcas (Heredadas del Vendedor)'

    def marcas_display_admin(self, obj):
        """Muestra las marcas asignadas en el listado"""
        return obj.marcas_display
    marcas_display_admin.short_description = 'Marcas'

    def venta_proyectada_fmt(self, obj):
        return f"${obj.venta_proyectada:,.0f}"
    venta_proyectada_fmt.short_description = 'Venta Proy.'
    venta_proyectada_fmt.admin_order_field = 'venta_proyectada'

    def participacion_ventas_fmt(self, obj):
        return f"{obj.participacion_ventas:.2f}%"
    participacion_ventas_fmt.short_description = 'Part. %'
    participacion_ventas_fmt.admin_order_field = 'participacion_ventas'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('vendedor', 'municipio_base_vendedor').prefetch_related('asignaciones_marca__marca')


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
    extra = 0
    autocomplete_fields = ['municipio']
    fields = ('orden_visita', 'municipio', 'flete_base')
    ordering = ['orden_visita']


@admin.register(RutaLogistica, site=dxv_admin_site)
class RecorridoLogisticoAdmin(GlobalFilterMixin, DuplicarMixin, admin.ModelAdmin):
    """Admin para Recorridos Logísticos (circuitos que hace un vehículo)"""
    list_display = ('nombre', 'marca', 'asignacion', 'vehiculo', 'esquema_vehiculo', 'tipo_asignacion_operacion', 'total_flete_base', 'viajes_por_periodo', 'requiere_pernocta', 'activo')
    list_filter = ('marca', 'escenario', 'asignacion', 'vehiculo__esquema', 'tipo_asignacion_operacion', 'frecuencia', 'requiere_pernocta', 'activo')
    search_fields = ['nombre', 'vehiculo__tipo_vehiculo']
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    autocomplete_fields = ['vehiculo']
    inlines = [RecorridoMunicipioInline]
    actions = ['duplicar_registros']

    class Media:
        js = ('admin/js/ruta_logistica_condicional.js',)

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'escenario', 'vehiculo', 'activo'),
            'description': 'El vehículo puede ser propio, renting o tercero. Los auxiliares se configuran en el vehículo.'
        }),
        ('Distribución de Costos', {
            'fields': (
                'marca', 'asignacion', 'porcentaje_uso', 'criterio_prorrateo',
                'tipo_asignacion_operacion', 'operacion', 'criterio_prorrateo_operacion',
            ),
            'description': 'Define cómo se distribuye el costo de este recorrido entre marcas y operaciones.'
        }),
        ('Frecuencia', {
            'fields': ('frecuencia', 'viajes_por_periodo'),
            'description': 'Cuántas veces por periodo (semana/quincena/mes) se hace este recorrido completo'
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

    def total_flete_base(self, obj):
        total = obj.municipios.aggregate(total=Sum('flete_base'))['total'] or 0
        return f"${total:,.0f}"
    total_flete_base.short_description = 'Flete Base Total'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('marca', 'vehiculo', 'escenario').prefetch_related('municipios')


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


# Inlines para ProyeccionVentasConfig
class ProyeccionManualInline(admin.StackedInline):
    """Inline para ingresar valores de venta directos por mes (ajuste estacional)"""
    model = ProyeccionManual
    extra = 0
    max_num = 1
    verbose_name = "Valores Mensuales (Opcional)"
    verbose_name_plural = "Valores Mensuales (Opcional)"
    fieldsets = (
        (None, {
            'fields': (
                ('enero', 'febrero', 'marzo'),
                ('abril', 'mayo', 'junio'),
                ('julio', 'agosto', 'septiembre'),
                ('octubre', 'noviembre', 'diciembre'),
            ),
            'description': '<b>Si agrega valores aquí, REEMPLAZAN el cálculo de Tipologías.</b><br>Use para estacionalidad. Deje vacío para usar el cálculo automático de Tipologías.'
        }),
    )


# =============================================================================
# INLINE PARA TIPOLOGÍAS DE CLIENTE
# =============================================================================

class TipologiaProyeccionInline(admin.TabularInline):
    """Inline para tipologías de cliente (Tiendas, Minimercados, etc.)"""
    model = TipologiaProyeccion
    extra = 1
    verbose_name = "Tipología de Cliente"
    verbose_name_plural = "Tipologías de Cliente"
    fields = (
        'nombre',
        # Valores iniciales (mes 1)
        'numero_clientes', 'visitas_mes', 'efectividad', 'ticket_promedio',
        # Crecimiento mensual
        'crecimiento_clientes', 'crecimiento_efectividad', 'crecimiento_ticket',
        # Calculados
        'venta_mensual_fmt', 'venta_anual_fmt'
    )
    readonly_fields = ('venta_mensual_fmt', 'venta_anual_fmt')

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Ajustar ancho de campos según tipo"""
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if field:
            # Campos de porcentaje: más angostos (60px)
            if db_field.name in ('efectividad', 'crecimiento_clientes', 'crecimiento_efectividad', 'crecimiento_ticket'):
                field.widget.attrs.update({'style': 'width: 60px;'})
            # Campos numéricos pequeños (70px)
            elif db_field.name in ('numero_clientes', 'visitas_mes'):
                field.widget.attrs.update({'style': 'width: 70px;'})
            # Ticket promedio (90px)
            elif db_field.name == 'ticket_promedio':
                field.widget.attrs.update({'style': 'width: 90px;'})
            # Nombre (120px)
            elif db_field.name == 'nombre':
                field.widget.attrs.update({'style': 'width: 120px;'})
        return field

    def venta_mensual_fmt(self, obj):
        if not obj.pk:
            return "-"
        try:
            total = obj.get_venta_mensual_inicial()
            return f"${total:,.0f}"
        except (AttributeError, TypeError, ValueError) as e:
            # Método no disponible o datos inválidos
            logger.debug(f"No se pudo obtener venta mensual para {obj}: {e}")
            return "-"
    venta_mensual_fmt.short_description = 'Mes 1'

    def venta_anual_fmt(self, obj):
        if not obj.pk:
            return "-"
        try:
            total = obj.get_venta_anual()
            return f"${total:,.0f}"
        except (AttributeError, TypeError, ValueError) as e:
            # Método no disponible o datos inválidos
            logger.debug(f"No se pudo obtener venta anual para {obj}: {e}")
            return "-"
    venta_anual_fmt.short_description = 'Total Anual'


@admin.register(ProyeccionVentasConfig, site=dxv_admin_site)
class ProyeccionVentasConfigAdmin(GlobalFilterMixin, DuplicarMixin, admin.ModelAdmin):
    list_display = ('marca', 'escenario', 'anio', 'venta_anual_fmt', 'base_tipologias_fmt', 'fecha_modificacion')
    list_filter = ('marca', 'escenario', 'anio')
    search_fields = ('marca__nombre', 'escenario__nombre', 'notas')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion', 'venta_anual_calculada', 'base_tipologias_calculada', 'resumen_mensual_calculado')
    actions = ['duplicar_registros']

    fieldsets = (
        ('Configuración Básica', {
            'fields': ('marca', 'escenario', 'anio'),
        }),
        ('Proyección Mensual Calculada', {
            'fields': ('resumen_mensual_calculado',),
            'description': 'Calculado automáticamente desde Tipologías (o valores manuales si existen)',
        }),
        ('Notas y Metadata', {
            'fields': ('notas', 'fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

    inlines = [
        TipologiaProyeccionInline,
        ProyeccionManualInline,
    ]

    def venta_anual_fmt(self, obj):
        try:
            venta = obj.get_venta_anual()
            return f"${venta:,.0f}"
        except Exception:
            return "-"
    venta_anual_fmt.short_description = 'Venta Anual'

    def base_tipologias_fmt(self, obj):
        try:
            base = obj.get_base_tipologias_mensual()
            return f"${base:,.0f}/mes"
        except Exception:
            return "-"
    base_tipologias_fmt.short_description = 'Base Tipologías'

    def venta_anual_calculada(self, obj):
        try:
            venta = obj.get_venta_anual()
            return f"${venta:,.0f}"
        except Exception:
            return "Complete las tipologías o valores manuales"
    venta_anual_calculada.short_description = 'Venta Anual Calculada'

    def base_tipologias_calculada(self, obj):
        try:
            base = obj.get_base_tipologias_mensual()
            anual = base * 12
            return f"${base:,.0f}/mes (${anual:,.0f}/año)"
        except Exception:
            return "Agregue tipologías de cliente"
    base_tipologias_calculada.short_description = 'Base desde Tipologías'

    def resumen_mensual_calculado(self, obj):
        """Muestra tabla con los 12 meses calculados"""
        from django.utils.html import format_html

        try:
            ventas = obj.calcular_ventas_mensuales()
            total = sum(ventas.values())

            # Verificar si hay datos
            if total == 0:
                return format_html(
                    '<p style="color: #666; font-style: italic;">Agregue tipologías o valores manuales para ver la proyección</p>'
                )

            # Detectar fuente de datos (manual solo si tiene valores > 0)
            try:
                manual = obj.proyeccion_manual
                ventas_manual = manual.get_ventas_mensuales()
                if sum(ventas_manual.values()) > 0:
                    fuente = "Valores Manuales"
                    fuente_color = "#1976d2"
                else:
                    fuente = "Calculado desde Tipologías"
                    fuente_color = "#388e3c"
            except (AttributeError, ValueError, TypeError):
                # Proyección manual no existe o tiene datos inválidos
                # Usar tipologías por defecto
                fuente = "Calculado desde Tipologías"
                fuente_color = "#388e3c"

            # Nombres de meses abreviados
            meses_labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                           'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
            meses_keys = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                         'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

            # Construir tabla HTML compacta
            header_cells = ''.join([f'<th style="padding: 2px; text-align: center; background: #f5f5f5; border: 1px solid #ddd;">{m}</th>' for m in meses_labels])
            value_cells = ''.join([f'<td style="padding: 2px; text-align: right; border: 1px solid #ddd;">${ventas[k]:,.0f}</td>' for k in meses_keys])

            html = f'''
            <div style="margin: 10px 0 10px -150px; overflow-x: auto; width: calc(100% + 150px);">
                <p style="margin-bottom: 4px; color: {fuente_color}; font-weight: bold; font-size: 9px;">
                    📊 Fuente: {fuente}
                </p>
                <table style="border-collapse: collapse; width: 100%; font-size: 8px; white-space: nowrap;">
                    <tr>{header_cells}<th style="padding: 2px; text-align: center; background: #e3f2fd; border: 1px solid #ddd; font-weight: bold;">TOTAL</th></tr>
                    <tr>{value_cells}<td style="padding: 2px; text-align: right; border: 1px solid #ddd; background: #e3f2fd; font-weight: bold;">${total:,.0f}</td></tr>
                </table>
            </div>
            '''
            return format_html(html)

        except Exception as e:
            return format_html(f'<p style="color: #d32f2f;">Error: {e}</p>')
    resumen_mensual_calculado.short_description = 'Proyección Mensual'


