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
        verbose_name = "Factor Prestacional"
        verbose_name_plural = "Factores Prestacionales"
        ordering = ['perfil']

    def __str__(self):
        return f"{self.get_perfil_display()} - {self.factor_total * 100:.2f}%"
