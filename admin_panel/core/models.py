"""
Modelos Django para el Sistema DxV
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Marca(models.Model):
    """Modelo para las marcas del sistema"""
    marca_id = models.CharField(max_length=100, unique=True, verbose_name="ID Marca")
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    activa = models.BooleanField(default=True, verbose_name="Activa")
    color = models.CharField(max_length=7, default="#1f77b4", verbose_name="Color (hex)")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_marca'
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class PersonalComercial(models.Model):
    """Personal del área comercial"""

    TIPO_CHOICES = [
        ('vendedor_geografico', 'Vendedor Geográfico'),
        ('vendedor_senior', 'Vendedor Senior'),
        ('vendedor_minimercado', 'Vendedor Minimercado'),
        ('supervisor', 'Supervisor'),
        ('coordinador_comercial', 'Coordinador Comercial'),
        ('auxiliar_informacion', 'Auxiliar de Información'),
    ]

    PERFIL_CHOICES = [
        ('comercial', 'Comercial'),
        ('administrativo', 'Administrativo'),
    ]

    ASIGNACION_CHOICES = [
        ('individual', 'Individual'),
        ('compartido', 'Compartido'),
    ]

    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name='personal_comercial')
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, verbose_name="Tipo de Personal")
    cantidad = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Cantidad")
    salario_base = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Salario Base")
    perfil_prestacional = models.CharField(max_length=20, choices=PERFIL_CHOICES, default='comercial')
    asignacion = models.CharField(max_length=20, choices=ASIGNACION_CHOICES, default='individual')
    auxilio_adicional = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Auxilio Adicional")

    # Campos para compartidos
    porcentaje_dedicacion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Solo para asignación compartida (0.0 - 1.0)"
    )
    criterio_prorrateo = models.CharField(
        max_length=20,
        choices=[
            ('ventas', 'Por Ventas'),
            ('volumen', 'Por Volumen'),
            ('headcount', 'Por Headcount'),
            ('equitativo', 'Equitativo'),
        ],
        null=True,
        blank=True
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_personal_comercial'
        verbose_name = "Personal Comercial"
        verbose_name_plural = "Personal Comercial"
        ordering = ['marca', 'tipo']

    def __str__(self):
        return f"{self.marca.nombre} - {self.get_tipo_display()} ({self.cantidad})"


class PersonalLogistico(models.Model):
    """Personal del área logística"""

    TIPO_CHOICES = [
        ('conductor', 'Conductor'),
        ('auxiliar_entrega', 'Auxiliar de Entrega'),
        ('coordinador_logistica', 'Coordinador Logística'),
        ('supervisor_bodega', 'Supervisor de Bodega'),
        ('operario_bodega', 'Operario de Bodega'),
    ]

    PERFIL_CHOICES = [
        ('logistico', 'Logístico'),
        ('administrativo', 'Administrativo'),
    ]

    ASIGNACION_CHOICES = [
        ('individual', 'Individual'),
        ('compartido', 'Compartido'),
    ]

    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name='personal_logistico')
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, verbose_name="Tipo de Personal")
    cantidad = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Cantidad")
    salario_base = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Salario Base")
    perfil_prestacional = models.CharField(max_length=20, choices=PERFIL_CHOICES, default='logistico')
    asignacion = models.CharField(max_length=20, choices=ASIGNACION_CHOICES, default='individual')

    # Campos para compartidos
    porcentaje_dedicacion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    criterio_prorrateo = models.CharField(
        max_length=20,
        choices=[
            ('ventas', 'Por Ventas'),
            ('volumen', 'Por Volumen'),
            ('headcount', 'Por Headcount'),
            ('equitativo', 'Equitativo'),
        ],
        null=True,
        blank=True
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_personal_logistico'
        verbose_name = "Personal Logístico"
        verbose_name_plural = "Personal Logístico"
        ordering = ['marca', 'tipo']

    def __str__(self):
        return f"{self.marca.nombre} - {self.get_tipo_display()} ({self.cantidad})"


class Vehiculo(models.Model):
    """Flota de vehículos"""

    TIPO_VEHICULO_CHOICES = [
        ('bicicleta_electrica', 'Bicicleta Eléctrica'),
        ('motocarro', 'Motocarro'),
        ('minitruck', 'Minitruck'),
        ('pickup', 'Pickup'),
        ('nhr', 'NHR'),
        ('nkr', 'NKR'),
        ('npr', 'NPR'),
    ]

    ESQUEMA_CHOICES = [
        ('renting', 'Renting'),
        ('tradicional', 'Tradicional (Propio)'),
    ]

    ASIGNACION_CHOICES = [
        ('individual', 'Individual'),
        ('compartido', 'Compartido'),
    ]

    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name='vehiculos')
    tipo_vehiculo = models.CharField(max_length=50, choices=TIPO_VEHICULO_CHOICES, verbose_name="Tipo de Vehículo")
    esquema = models.CharField(max_length=20, choices=ESQUEMA_CHOICES, verbose_name="Esquema")
    cantidad = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Cantidad")
    asignacion = models.CharField(max_length=20, choices=ASIGNACION_CHOICES, default='individual')
    kilometraje_promedio_mensual = models.IntegerField(default=3000, verbose_name="Km Promedio Mensual")

    # Campos para compartidos
    porcentaje_uso = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    criterio_prorrateo = models.CharField(
        max_length=20,
        choices=[
            ('volumen', 'Por Volumen'),
            ('ventas', 'Por Ventas'),
            ('uso_real', 'Por Uso Real'),
        ],
        default='volumen',
        null=True,
        blank=True
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_vehiculo'
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"
        ordering = ['marca', 'tipo_vehiculo']

    def __str__(self):
        return f"{self.marca.nombre} - {self.get_tipo_vehiculo_display()} {self.get_esquema_display()} ({self.cantidad})"


class ProyeccionVentas(models.Model):
    """Proyecciones mensuales de ventas por marca"""

    MESES = [
        ('enero', 'Enero'),
        ('febrero', 'Febrero'),
        ('marzo', 'Marzo'),
        ('abril', 'Abril'),
        ('mayo', 'Mayo'),
        ('junio', 'Junio'),
        ('julio', 'Julio'),
        ('agosto', 'Agosto'),
        ('septiembre', 'Septiembre'),
        ('octubre', 'Octubre'),
        ('noviembre', 'Noviembre'),
        ('diciembre', 'Diciembre'),
    ]

    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name='proyecciones_ventas')
    anio = models.IntegerField(verbose_name="Año")
    mes = models.CharField(max_length=20, choices=MESES, verbose_name="Mes")
    ventas = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Ventas Proyectadas")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_proyeccion_ventas'
        verbose_name = "Proyección de Ventas"
        verbose_name_plural = "Proyecciones de Ventas"
        ordering = ['marca', 'anio', 'mes']
        unique_together = ['marca', 'anio', 'mes']

    def __str__(self):
        return f"{self.marca.nombre} - {self.get_mes_display()} {self.anio}: ${self.ventas:,.0f}"


class VolumenOperacion(models.Model):
    """Volumen de operación logística por marca"""

    marca = models.OneToOneField(Marca, on_delete=models.CASCADE, related_name='volumen_operacion')
    pallets_mensuales = models.IntegerField(default=0, verbose_name="Pallets Mensuales")
    metros_cubicos_mensuales = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="M³ Mensuales")
    toneladas_mensuales = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Toneladas Mensuales")
    entregas_mensuales = models.IntegerField(default=0, verbose_name="Entregas Mensuales")
    rutas_activas = models.IntegerField(default=0, verbose_name="Rutas Activas")
    zonas_cobertura = models.IntegerField(default=0, verbose_name="Zonas de Cobertura")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_volumen_operacion'
        verbose_name = "Volumen de Operación"
        verbose_name_plural = "Volúmenes de Operación"

    def __str__(self):
        return f"{self.marca.nombre} - Volumen Operación"


class ParametrosMacro(models.Model):
    """Parámetros macroeconómicos del sistema"""

    anio = models.IntegerField(unique=True, verbose_name="Año")
    ipc = models.DecimalField(max_digits=5, decimal_places=4, verbose_name="IPC (%)")
    ipt = models.DecimalField(max_digits=5, decimal_places=4, verbose_name="IPT (%)")
    salario_minimo_legal = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Salario Mínimo Legal")
    subsidio_transporte = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Subsidio de Transporte")
    incremento_salarios = models.DecimalField(max_digits=5, decimal_places=4, verbose_name="Incremento Salarios (%)")

    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_parametros_macro'
        verbose_name = "Parámetros Macroeconómicos"
        verbose_name_plural = "Parámetros Macroeconómicos"
        ordering = ['-anio']

    def __str__(self):
        return f"Parámetros {self.anio}"


class FactorPrestacional(models.Model):
    """Factores prestacionales por perfil"""

    PERFIL_CHOICES = [
        ('comercial', 'Comercial'),
        ('administrativo', 'Administrativo'),
        ('logistico', 'Logístico'),
        ('aprendiz_sena', 'Aprendiz SENA'),
    ]

    perfil = models.CharField(max_length=50, choices=PERFIL_CHOICES, unique=True, verbose_name="Perfil")
    salud = models.DecimalField(max_digits=6, decimal_places=5, verbose_name="Salud (%)")
    pension = models.DecimalField(max_digits=6, decimal_places=5, verbose_name="Pensión (%)")
    arl = models.DecimalField(max_digits=6, decimal_places=5, verbose_name="ARL (%)")
    caja_compensacion = models.DecimalField(max_digits=6, decimal_places=5, verbose_name="Caja Compensación (%)")
    icbf = models.DecimalField(max_digits=6, decimal_places=5, verbose_name="ICBF (%)")
    sena = models.DecimalField(max_digits=6, decimal_places=5, verbose_name="SENA (%)")
    cesantias = models.DecimalField(max_digits=6, decimal_places=5, verbose_name="Cesantías (%)")
    intereses_cesantias = models.DecimalField(max_digits=6, decimal_places=5, verbose_name="Int. Cesantías (%)")
    prima = models.DecimalField(max_digits=6, decimal_places=5, verbose_name="Prima (%)")
    vacaciones = models.DecimalField(max_digits=6, decimal_places=5, verbose_name="Vacaciones (%)")
    factor_total = models.DecimalField(max_digits=6, decimal_places=5, verbose_name="Factor Total (%)")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_factor_prestacional'
        verbose_name = "Factor Prestacional"
        verbose_name_plural = "Factores Prestacionales"
        ordering = ['perfil']

    def __str__(self):
        return f"{self.get_perfil_display()} - {self.factor_total * 100:.2f}%"


class PersonalAdministrativo(models.Model):
    """Personal administrativo (puede ser compartido entre marcas)"""

    TIPO_CHOICES = [
        ('gerente_general', 'Gerente General'),
        ('contador', 'Contador'),
        ('auxiliar_administrativo', 'Auxiliar Administrativo'),
        ('servicios_generales', 'Servicios Generales'),
        ('practicante_sena', 'Practicante SENA'),
        ('asistente_gerencia', 'Asistente de Gerencia'),
    ]

    TIPO_CONTRATO_CHOICES = [
        ('nomina', 'Nómina'),
        ('honorarios', 'Honorarios'),
    ]

    ASIGNACION_CHOICES = [
        ('compartido', 'Compartido entre marcas'),
    ]

    nombre = models.CharField(max_length=200, verbose_name="Nombre/Descripción")
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, verbose_name="Tipo de Personal")
    cantidad = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Cantidad")
    tipo_contrato = models.CharField(max_length=20, choices=TIPO_CONTRATO_CHOICES, default='nomina')

    # Para nómina
    salario_base = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Salario Base")
    perfil_prestacional = models.CharField(max_length=20, default='administrativo', verbose_name="Perfil")

    # Para honorarios
    honorarios_mensuales = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Honorarios Mensuales")

    asignacion = models.CharField(max_length=20, choices=ASIGNACION_CHOICES, default='compartido')
    criterio_prorrateo = models.CharField(
        max_length=20,
        choices=[
            ('ventas', 'Por Ventas'),
            ('headcount', 'Por Headcount'),
            ('equitativo', 'Equitativo'),
        ],
        default='equitativo'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_personal_administrativo'
        verbose_name = "Personal Administrativo"
        verbose_name_plural = "Personal Administrativo"
        ordering = ['tipo']

    def __str__(self):
        return f"{self.get_tipo_display()} ({self.cantidad})"


class GastoAdministrativo(models.Model):
    """Gastos administrativos generales (compartidos)"""

    TIPO_CHOICES = [
        ('arriendo_oficina', 'Arriendo de Oficina'),
        ('servicios_publicos', 'Servicios Públicos'),
        ('internet_telefonia', 'Internet y Telefonía'),
        ('vigilancia', 'Vigilancia y Seguridad'),
        ('aseo_cafeteria', 'Aseo y Cafetería'),
        ('papeleria', 'Papelería y Útiles'),
        ('software_licencias', 'Software y Licencias'),
        ('seguros', 'Seguros'),
        ('impuestos_predial', 'Impuestos Prediales'),
        ('otros', 'Otros Gastos Administrativos'),
    ]

    nombre = models.CharField(max_length=200, verbose_name="Nombre/Descripción")
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, verbose_name="Tipo de Gasto")
    valor_mensual = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Mensual")
    criterio_prorrateo = models.CharField(
        max_length=20,
        choices=[
            ('ventas', 'Por Ventas'),
            ('headcount', 'Por Headcount'),
            ('equitativo', 'Equitativo'),
        ],
        default='ventas'
    )
    notas = models.TextField(blank=True, verbose_name="Notas")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_gasto_administrativo'
        verbose_name = "Gasto Administrativo"
        verbose_name_plural = "Gastos Administrativos"
        ordering = ['tipo', 'nombre']

    def __str__(self):
        return f"{self.get_tipo_display()} - ${self.valor_mensual:,.0f}"


class GastoComercial(models.Model):
    """Gastos comerciales por marca"""

    TIPO_CHOICES = [
        ('comisiones', 'Comisiones de Ventas'),
        ('merchandising', 'Materiales de Merchandising'),
        ('capacitacion', 'Capacitación y Entrenamiento'),
        ('eventos', 'Eventos Comerciales'),
        ('herramientas_digitales', 'Herramientas Digitales (CRM, Apps)'),
        ('transporte_vendedores', 'Transporte de Vendedores'),
        ('viaticos', 'Viáticos'),
        ('publicidad', 'Publicidad y Marketing'),
        ('muestras', 'Muestras y Degustaciones'),
        ('otros', 'Otros Gastos Comerciales'),
    ]

    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name='gastos_comerciales')
    nombre = models.CharField(max_length=200, verbose_name="Nombre/Descripción")
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, verbose_name="Tipo de Gasto")
    valor_mensual = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Mensual")
    notas = models.TextField(blank=True, verbose_name="Notas")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_gasto_comercial'
        verbose_name = "Gasto Comercial"
        verbose_name_plural = "Gastos Comerciales"
        ordering = ['marca', 'tipo']

    def __str__(self):
        return f"{self.marca.nombre} - {self.get_tipo_display()}: ${self.valor_mensual:,.0f}"


class GastoLogistico(models.Model):
    """Gastos logísticos por marca"""

    TIPO_CHOICES = [
        ('mantenimiento_vehiculos', 'Mantenimiento de Vehículos'),
        ('seguros_carga', 'Seguros de Carga'),
        ('peajes', 'Peajes y Parqueaderos'),
        ('equipos_carga', 'Equipos de Carga (Estibas, Carretas)'),
        ('combustible_adicional', 'Combustible Adicional'),
        ('neumaticos', 'Neumáticos y Repuestos'),
        ('bodegaje', 'Bodegaje Externo'),
        ('equipos_bodega', 'Equipos de Bodega'),
        ('embalaje', 'Material de Embalaje'),
        ('otros', 'Otros Gastos Logísticos'),
    ]

    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name='gastos_logisticos')
    nombre = models.CharField(max_length=200, verbose_name="Nombre/Descripción")
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, verbose_name="Tipo de Gasto")
    valor_mensual = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Mensual")
    notas = models.TextField(blank=True, verbose_name="Notas")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_gasto_logistico'
        verbose_name = "Gasto Logístico"
        verbose_name_plural = "Gastos Logísticos"
        ordering = ['marca', 'tipo']

    def __str__(self):
        return f"{self.marca.nombre} - {self.get_tipo_display()}: ${self.valor_mensual:,.0f}"


class Impuesto(models.Model):
    """Impuestos y obligaciones tributarias"""

    TIPO_CHOICES = [
        ('iva', 'IVA'),
        ('renta', 'Impuesto de Renta'),
        ('ica', 'ICA (Industria y Comercio)'),
        ('retefuente', 'Retención en la Fuente'),
        ('reteica', 'Retención ICA'),
        ('predial', 'Predial'),
        ('vehiculos', 'Impuesto Vehículos'),
        ('estampillas', 'Estampillas'),
        ('otros', 'Otros Impuestos'),
    ]

    PERIODICIDAD_CHOICES = [
        ('mensual', 'Mensual'),
        ('bimestral', 'Bimestral'),
        ('trimestral', 'Trimestral'),
        ('anual', 'Anual'),
    ]

    APLICACION_CHOICES = [
        ('sobre_ventas', 'Sobre Ventas'),
        ('sobre_utilidad', 'Sobre Utilidad'),
        ('fijo', 'Valor Fijo'),
    ]

    nombre = models.CharField(max_length=200, verbose_name="Nombre del Impuesto")
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, verbose_name="Tipo")
    aplicacion = models.CharField(max_length=20, choices=APLICACION_CHOICES, verbose_name="Aplicación")

    # Para impuestos porcentuales
    porcentaje = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Porcentaje (%)",
        help_text="Para impuestos sobre ventas o utilidad"
    )

    # Para impuestos fijos
    valor_fijo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor Fijo",
        help_text="Para impuestos de valor fijo"
    )

    periodicidad = models.CharField(max_length=20, choices=PERIODICIDAD_CHOICES, default='mensual')
    activo = models.BooleanField(default=True, verbose_name="Activo")
    notas = models.TextField(blank=True, verbose_name="Notas")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_impuesto'
        verbose_name = "Impuesto"
        verbose_name_plural = "Impuestos"
        ordering = ['tipo', 'nombre']

    def __str__(self):
        if self.porcentaje:
            return f"{self.get_tipo_display()} - {self.porcentaje * 100:.2f}%"
        elif self.valor_fijo:
            return f"{self.get_tipo_display()} - ${self.valor_fijo:,.0f}"
        return self.get_tipo_display()


class ConfiguracionDescuentos(models.Model):
    """Configuración de descuentos e incentivos por marca"""

    marca = models.OneToOneField(
        Marca,
        on_delete=models.CASCADE,
        related_name='configuracion_descuentos',
        verbose_name="Marca"
    )

    # REBATE / RxP
    porcentaje_rebate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Rebate (%)",
        help_text="Porcentaje de rebate sobre ventas netas (0-100%)"
    )

    # DESCUENTO FINANCIERO
    aplica_descuento_financiero = models.BooleanField(
        default=False,
        verbose_name="¿Aplica Descuento Financiero?"
    )
    porcentaje_descuento_financiero = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Descuento Financiero (%)",
        help_text="Porcentaje de descuento por pronto pago (0-100%)"
    )

    activa = models.BooleanField(default=True, verbose_name="Activa")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_configuracion_descuentos'
        verbose_name = "Configuración de Descuentos"
        verbose_name_plural = "Configuraciones de Descuentos"
        ordering = ['marca']

    def __str__(self):
        return f"{self.marca.nombre} - Descuentos"

    def clean(self):
        """Validación: si no aplica descuento financiero, el porcentaje debe ser 0"""
        from django.core.exceptions import ValidationError
        if not self.aplica_descuento_financiero and self.porcentaje_descuento_financiero > 0:
            raise ValidationError(
                "El porcentaje de descuento financiero debe ser 0 si no aplica descuento financiero"
            )

    def total_tramos_porcentaje(self):
        """Calcula la suma de porcentajes de todos los tramos"""
        return self.tramos.aggregate(
            total=models.Sum('porcentaje_ventas')
        )['total'] or 0

    def validar_tramos(self):
        """Valida que los tramos sumen 100%"""
        total = self.total_tramos_porcentaje()
        return abs(total - 100) < 0.01  # Tolerancia por decimales

    total_tramos_porcentaje.short_description = "Total % Tramos"


class TramoDescuentoFactura(models.Model):
    """Tramos de descuento a pie de factura"""

    configuracion = models.ForeignKey(
        ConfiguracionDescuentos,
        on_delete=models.CASCADE,
        related_name='tramos',
        verbose_name="Configuración"
    )
    orden = models.PositiveIntegerField(
        verbose_name="Orden",
        help_text="Orden del tramo (1, 2, 3...)"
    )
    porcentaje_ventas = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="% de Ventas",
        help_text="Porcentaje del total de ventas (ej: 50%)"
    )
    porcentaje_descuento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="% de Descuento",
        help_text="Porcentaje de descuento aplicado (ej: 19%)"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_tramo_descuento_factura'
        verbose_name = "Tramo de Descuento"
        verbose_name_plural = "Tramos de Descuento"
        ordering = ['configuracion', 'orden']
        unique_together = ['configuracion', 'orden']

    def __str__(self):
        return f"Tramo {self.orden}: {self.porcentaje_ventas}% ventas → {self.porcentaje_descuento}% desc."

    def clean(self):
        """Validaciones del tramo"""
        from django.core.exceptions import ValidationError

        if self.porcentaje_ventas <= 0:
            raise ValidationError("El porcentaje de ventas debe ser mayor a 0")

        if self.porcentaje_descuento < 0:
            raise ValidationError("El porcentaje de descuento no puede ser negativo")
