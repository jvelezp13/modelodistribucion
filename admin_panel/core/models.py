"""
Modelos Django para el Sistema DxV
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


# Choices globales para índices de incremento
INDICE_INCREMENTO_CHOICES = [
    ('salarios', 'Incremento Salarios General'),
    ('salario_minimo', 'Incremento Salario Mínimo'),
    ('ipc', 'IPC (Índice de Precios al Consumidor)'),
    ('ipt', 'IPT (Índice de Precios al Transportador)'),
    ('combustible', 'Incremento Combustible'),
    ('arriendos', 'Incremento Arriendos'),
    ('personalizado_1', 'Índice Personalizado 1'),
    ('personalizado_2', 'Índice Personalizado 2'),
    ('fijo', 'Sin Incremento (Valor Fijo)'),
]


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


class Escenario(models.Model):
    """Representa una versión de presupuesto o datos reales"""
    
    TIPO_CHOICES = [
        ('planeado', 'Planeado'),
        ('sugerido_marca', 'Sugerido por Marca'),
        ('real', 'Real Ejecutado'),
    ]
    
    PERIODO_TIPO_CHOICES = [
        ('anual', 'Anual'),
        ('trimestral', 'Trimestral'),
        ('mensual', 'Mensual'),
    ]
    
    nombre = models.CharField(max_length=200, verbose_name="Nombre", help_text="Ej: 'Plan 2025', 'Real Q1 2025'")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo de Escenario")
    anio = models.IntegerField(verbose_name="Año")
    periodo_tipo = models.CharField(max_length=20, choices=PERIODO_TIPO_CHOICES, default='anual', verbose_name="Tipo de Periodo")
    periodo_numero = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Número de Periodo",
        help_text="1-4 para trimestral, 1-12 para mensual. Dejar vacío para anual"
    )
    
    activo = models.BooleanField(default=False, verbose_name="Activo", help_text="Escenario activo para simulación")
    aprobado = models.BooleanField(default=False, verbose_name="Aprobado", help_text="Para workflow de aprobación")
    
    notas = models.TextField(blank=True, verbose_name="Notas")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dxv_escenario'
        verbose_name = "Escenario"
        verbose_name_plural = "Escenarios"
        ordering = ['-anio', '-periodo_numero', 'tipo']
        unique_together = [['nombre', 'anio']]
    
    def __str__(self):
        periodo_str = ""
        if self.periodo_tipo == 'trimestral' and self.periodo_numero:
            periodo_str = f" Q{self.periodo_numero}"
        elif self.periodo_tipo == 'mensual' and self.periodo_numero:
            meses = ['', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
            periodo_str = f" {meses[self.periodo_numero]}"
        
        return f"{self.nombre} ({self.anio}{periodo_str})"


class PersonalComercial(models.Model):
    """Personal del área comercial"""

    TIPO_CHOICES = [
        ('vendedor_geografico', 'Vendedor Geográfico'),
        ('vendedor_senior', 'Vendedor Senior'),
        ('vendedor_minimercado', 'Vendedor Minimercado'),
        ('vendedor_supernumerario', 'Vendedor Supernumerario'),
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

    escenario = models.ForeignKey(
        'Escenario',
        on_delete=models.CASCADE,
        related_name='personal_comercial_items',
        verbose_name="Escenario",
        help_text="Escenario al que pertenece este registro",
        null=True,
        blank=True
    )
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name='personal_comercial')
    nombre = models.CharField(max_length=200, verbose_name="Nombre/Descripción", help_text="Ej: 'Vendedor Zona Norte', 'Supervisor Equipo A'", default='', blank=True)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, verbose_name="Tipo de Personal")
    cantidad = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Cantidad")
    salario_base = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Salario Base")
    perfil_prestacional = models.CharField(max_length=20, choices=PERFIL_CHOICES, default='comercial')
    asignacion = models.CharField(max_length=20, choices=ASIGNACION_CHOICES, default='individual')
    auxilio_adicional = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Auxilio Adicional")
    
    # Índice de incremento para proyecciones
    indice_incremento = models.CharField(
        max_length=20,
        choices=INDICE_INCREMENTO_CHOICES,
        default='salarios',
        verbose_name="Índice de Incremento",
        help_text="Índice a usar para proyecciones de años futuros"
    )

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

    def calcular_costo_mensual(self):
        """Calcula el costo mensual total para este registro de personal"""
        if not self.salario_base or not self.cantidad:
            return 0

        try:
            # Obtener factor prestacional
            factor = FactorPrestacional.objects.get(perfil=self.perfil_prestacional)
            costo_unitario = self.salario_base * (1 + factor.factor_total)

            # Sumar auxilio de transporte si aplica (<= 2 SMLV)
            if self.escenario:
                try:
                    macro = ParametrosMacro.objects.get(anio=self.escenario.anio, activo=True)
                    if self.salario_base <= (macro.salario_minimo_legal * 2):
                        costo_unitario += macro.subsidio_transporte
                except ParametrosMacro.DoesNotExist:
                    pass

            # Sumar auxilio adicional
            costo_unitario += self.auxilio_adicional

            # Multiplicar por cantidad
            return costo_unitario * self.cantidad

        except FactorPrestacional.DoesNotExist:
            # Si no existe factor, retornar solo salario base * cantidad
            return self.salario_base * self.cantidad

    def __str__(self):
        return f"{self.marca.nombre} - {self.nombre} ({self.cantidad})"


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
        ('logistico_bodega', 'Logístico Bodega'),
        ('logistico_calle', 'Logístico Calle'),
        ('administrativo', 'Administrativo'),
    ]

    ASIGNACION_CHOICES = [
        ('individual', 'Individual'),
        ('compartido', 'Compartido'),
    ]

    escenario = models.ForeignKey(
        'Escenario',
        on_delete=models.CASCADE,
        related_name='personal_logistico_items',
        verbose_name="Escenario",
        help_text="Escenario al que pertenece este registro",
        null=True,
        blank=True
    )
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name='personal_logistico')
    nombre = models.CharField(max_length=200, verbose_name="Nombre/Descripción", help_text="Ej: 'Conductor Ruta Principal', 'Auxiliar Bodega CEDI'", default='', blank=True)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, verbose_name="Tipo de Personal")
    cantidad = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Cantidad")
    salario_base = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Salario Base")
    perfil_prestacional = models.CharField(max_length=20, choices=PERFIL_CHOICES, default='logistico')
    asignacion = models.CharField(max_length=20, choices=ASIGNACION_CHOICES, default='individual')
    
    # Índice de incremento para proyecciones
    indice_incremento = models.CharField(
        max_length=20,
        choices=INDICE_INCREMENTO_CHOICES,
        default='salarios',
        verbose_name="Índice de Incremento",
        help_text="Índice a usar para proyecciones de años futuros"
    )

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

    def calcular_costo_mensual(self):
        """Calcula el costo mensual total para este registro de personal"""
        if not self.salario_base or not self.cantidad:
            return 0

        try:
            # Obtener factor prestacional
            factor = FactorPrestacional.objects.get(perfil=self.perfil_prestacional)
            costo_unitario = self.salario_base * (1 + factor.factor_total)

            # Sumar auxilio de transporte si aplica (<= 2 SMLV)
            if self.escenario:
                try:
                    macro = ParametrosMacro.objects.get(anio=self.escenario.anio, activo=True)
                    if self.salario_base <= (macro.salario_minimo_legal * 2):
                        costo_unitario += macro.subsidio_transporte
                except ParametrosMacro.DoesNotExist:
                    pass

            # Multiplicar por cantidad
            return costo_unitario * self.cantidad

        except FactorPrestacional.DoesNotExist:
            # Si no existe factor, retornar solo salario base * cantidad
            return self.salario_base * self.cantidad

    def __str__(self):
        return f"{self.marca.nombre} - {self.nombre} ({self.cantidad})"


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
        ('tercero', 'Tercero (Flete)'),
    ]

    ASIGNACION_CHOICES = [
        ('individual', 'Individual'),
        ('compartido', 'Compartido'),
    ]

    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name='vehiculos')
    escenario = models.ForeignKey(
        'Escenario',
        on_delete=models.CASCADE,
        related_name='vehiculo_items',
        verbose_name="Escenario",
        help_text="Escenario al que pertenece este registro",
        null=True,
        blank=True
    )
    tipo_vehiculo = models.CharField(max_length=50, choices=TIPO_VEHICULO_CHOICES, verbose_name="Tipo de Vehículo")
    esquema = models.CharField(max_length=20, choices=ESQUEMA_CHOICES, verbose_name="Esquema")
    cantidad = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Cantidad")
    asignacion = models.CharField(max_length=20, choices=ASIGNACION_CHOICES, default='individual')
    kilometraje_promedio_mensual = models.IntegerField(default=3000, verbose_name="Km Promedio Mensual")
    
    # Campos para esquema Tercero
    valor_flete_mensual = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Valor Flete Mensual", help_text="Costo total mensual si es esquema Tercero")

    # Campos para esquema Renting
    canon_renting = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Canon Renting Mensual")

    # Campos para esquema Propio
    costo_compra = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Costo Compra Vehículo")
    vida_util_anios = models.IntegerField(default=5, verbose_name="Vida Útil (Años)")
    valor_residual = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Valor Residual", help_text="Valor estimado al final de la vida útil")
    costo_mantenimiento_mensual = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Mantenimiento Mensual")
    costo_seguro_mensual = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Seguro Mensual")
    
    # Campos para consumo (Propio y Renting)
    consumo_galon_km = models.DecimalField(max_digits=5, decimal_places=2, default=30, verbose_name="Km por Galón", help_text="Rendimiento del vehículo")
    tipo_combustible = models.CharField(
        max_length=10,
        choices=[
            ('gasolina', 'Gasolina'),
            ('acpm', 'ACPM (Diesel)'),
        ],
        default='acpm',
        verbose_name="Tipo de Combustible",
        help_text="Tipo de combustible que usa el vehículo"
    )

    # Otros costos operativos (Propio y Renting)
    costo_lavado_mensual = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Lavado Mensual")
    costo_parqueadero_mensual = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Parqueadero Mensual")
    costo_monitoreo_mensual = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Monitoreo Satelital (GPS)")

    # Otros costos (Todos los esquemas)
    costo_seguro_mercancia_mensual = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Seguro de Mercancía", help_text="Seguro de carga transportada")

    # Índice de incremento para proyecciones
    indice_incremento = models.CharField(
        max_length=20,
        choices=INDICE_INCREMENTO_CHOICES,
        default='combustible',
        verbose_name="Índice de Incremento",
        help_text="Índice a usar para proyecciones de años futuros"
    )

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

    def calcular_costo_mensual(self):
        """Calcula el costo mensual total para este vehículo"""
        try:
            total = 0
            cantidad = self.cantidad or 0

            # Obtener precio combustible del escenario según tipo
            precio_galon = 0
            if self.escenario:
                try:
                    macro = ParametrosMacro.objects.get(anio=self.escenario.anio, activo=True)
                    # Usar el precio según el tipo de combustible
                    if self.tipo_combustible == 'gasolina':
                        precio_galon = macro.precio_galon_gasolina or 0
                    else:  # acpm
                        precio_galon = macro.precio_galon_acpm or 0
                except ParametrosMacro.DoesNotExist:
                    pass

            # Costos comunes a todos los esquemas
            total += (self.costo_monitoreo_mensual or 0) * cantidad
            total += (self.costo_seguro_mercancia_mensual or 0) * cantidad

            if self.esquema == 'tercero':
                total += (self.valor_flete_mensual or 0) * cantidad

            elif self.esquema in ['renting', 'tradicional']:
                # Costos comunes Propio/Renting
                total += (self.costo_lavado_mensual or 0) * cantidad
                total += (self.costo_parqueadero_mensual or 0) * cantidad

                # Combustible
                consumo = self.consumo_galon_km or 0
                km_mensual = self.kilometraje_promedio_mensual or 0
                if consumo > 0:
                    galones = km_mensual / consumo
                    total += galones * precio_galon * cantidad

                if self.esquema == 'renting':
                    total += (self.canon_renting or 0) * cantidad

                elif self.esquema == 'tradicional':
                    # Depreciación
                    vida_util = self.vida_util_anios or 0
                    if vida_util > 0:
                        costo_compra = self.costo_compra or 0
                        valor_residual = self.valor_residual or 0
                        depreciacion = (costo_compra - valor_residual) / (vida_util * 12)
                        total += depreciacion * cantidad

                    total += (self.costo_mantenimiento_mensual or 0) * cantidad
                    total += (self.costo_seguro_mensual or 0) * cantidad

            return total
        except Exception:
            return 0

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
    escenario = models.ForeignKey(
        'Escenario',
        on_delete=models.CASCADE,
        related_name='proyeccion_ventas_items',
        verbose_name="Escenario",
        help_text="Escenario al que pertenece este registro",
        null=True,
        blank=True
    )
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
    ipc = models.DecimalField(max_digits=6, decimal_places=5, verbose_name="IPC (%)", help_text="Índice de Precios al Consumidor")
    ipt = models.DecimalField(max_digits=6, decimal_places=5, verbose_name="IPT (%)", help_text="Índice de Precios al Transportador")
    salario_minimo_legal = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Salario Mínimo Legal")
    salario_minimo_legal = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Salario Mínimo Legal")
    subsidio_transporte = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Subsidio de Transporte")
    precio_galon_gasolina = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=15000,
        verbose_name="Precio Galón Gasolina",
        help_text="Precio promedio galón de gasolina"
    )
    precio_galon_acpm = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=14000,
        verbose_name="Precio Galón ACPM (Diesel)",
        help_text="Precio promedio galón de ACPM/diesel"
    )
    incremento_salarios = models.DecimalField(max_digits=6, decimal_places=5, verbose_name="Incremento Salarios General (%)", help_text="Incremento general de salarios")
    
    # Nuevos índices para proyecciones
    incremento_salario_minimo = models.DecimalField(
        max_digits=6,
        decimal_places=5,
        default=0,
        verbose_name="Incremento Salario Mínimo (%)",
        help_text="Incremento específico del salario mínimo (puede diferir del general)"
    )
    incremento_combustible = models.DecimalField(
        max_digits=6,
        decimal_places=5,
        default=0,
        verbose_name="Incremento Combustible (%)",
        help_text="Índice de incremento de combustibles"
    )
    incremento_arriendos = models.DecimalField(
        max_digits=6,
        decimal_places=5,
        default=0,
        verbose_name="Incremento Arriendos (%)",
        help_text="Usualmente igual al IPC"
    )
    incremento_personalizado_1 = models.DecimalField(
        max_digits=6,
        decimal_places=5,
        default=0,
        verbose_name="Índice Personalizado 1 (%)"
    )
    nombre_personalizado_1 = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nombre Índice Personalizado 1",
        help_text="Ej: 'Incremento Tecnología', 'Incremento Servicios Públicos'"
    )
    incremento_personalizado_2 = models.DecimalField(
        max_digits=6,
        decimal_places=5,
        default=0,
        verbose_name="Índice Personalizado 2 (%)"
    )
    nombre_personalizado_2 = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nombre Índice Personalizado 2",
        help_text="Ej: 'Incremento Seguros', 'Incremento Mantenimiento'"
    )

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
        ('logistico_bodega', 'Logístico Bodega'),
        ('logistico_calle', 'Logístico Calle'),
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

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_factor_prestacional'
        verbose_name = "Factor Prestacional"
        verbose_name_plural = "Factores Prestacionales"
        ordering = ['perfil']

    @property
    def factor_total(self):
        """Calcula automáticamente el factor total sumando todos los componentes"""
        return (
            self.salud + self.pension + self.arl + self.caja_compensacion +
            self.icbf + self.sena + self.cesantias + self.intereses_cesantias +
            self.prima + self.vacaciones
        )

    def __str__(self):
        return f"{self.get_perfil_display()} - {self.factor_total * 100:.2f}%"


class PersonalAdministrativo(models.Model):
    """Personal administrativo (puede ser compartido entre marcas)"""

    TIPO_CHOICES = [
        ('gerente_general', 'Gerente General'),
        ('contador', 'Contador'),
        ('revisor_fiscal', 'Revisor Fiscal'),
        ('sgsst', 'Seguridad y Salud en el Trabajo (SGSST)'),
        ('pesv', 'Plan Estratégico de Seguridad Vial (PESV)'),
        ('auxiliar_administrativo', 'Auxiliar Administrativo'),
        ('servicios_generales', 'Servicios Generales'),
        ('practicante_sena', 'Practicante SENA'),
        ('asistente_gerencia', 'Asistente de Gerencia'),
        ('desarrollador_talento', 'Desarrollador de Talento'),
    ]

    TIPO_CONTRATO_CHOICES = [
        ('nomina', 'Nómina'),
        ('honorarios', 'Honorarios'),
    ]

    ASIGNACION_CHOICES = [
        ('individual', 'Individual (asignado a una marca)'),
        ('compartido', 'Compartido entre marcas'),
    ]

    escenario = models.ForeignKey(
        'Escenario',
        on_delete=models.CASCADE,
        related_name='personal_administrativo_items',
        verbose_name="Escenario",
        help_text="Escenario al que pertenece este registro",
        null=True,
        blank=True
    )
    marca = models.ForeignKey(
        Marca,
        on_delete=models.CASCADE,
        related_name='personal_administrativo',
        null=True,
        blank=True,
        verbose_name="Marca",
        help_text="Dejar vacío si es compartido entre todas las marcas"
    )
    nombre = models.CharField(max_length=200, verbose_name="Nombre/Descripción")
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, verbose_name="Tipo de Personal")
    cantidad = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Cantidad")
    tipo_contrato = models.CharField(max_length=20, choices=TIPO_CONTRATO_CHOICES, default='nomina')

    PERFIL_CHOICES = [
        ('administrativo', 'Administrativo'),
        ('aprendiz_sena', 'Aprendiz SENA'),
    ]

    # Para nómina
    salario_base = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Salario Base")
    perfil_prestacional = models.CharField(max_length=20, choices=PERFIL_CHOICES, default='administrativo', verbose_name="Perfil")

    # Para honorarios
    honorarios_mensuales = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Honorarios Mensuales")
    
    # Índice de incremento para proyecciones
    indice_incremento = models.CharField(
        max_length=20,
        choices=INDICE_INCREMENTO_CHOICES,
        default='salarios',
        verbose_name="Índice de Incremento",
        help_text="Índice a usar para proyecciones de años futuros"
    )

    asignacion = models.CharField(max_length=20, choices=ASIGNACION_CHOICES, default='compartido')
    criterio_prorrateo = models.CharField(
        max_length=20,
        choices=[
            ('ventas', 'Por Ventas'),
            ('headcount', 'Por Headcount'),
            ('equitativo', 'Equitativo'),
        ],
        default='equitativo',
        null=True,
        blank=True,
        help_text="Solo aplica para asignación compartida"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_personal_administrativo'
        verbose_name = "Personal Administrativo"
        verbose_name_plural = "Personal Administrativo"
        ordering = ['tipo']

    def calcular_costo_mensual(self):
        """Calcula el costo mensual total para este registro de personal"""
        if not self.cantidad:
            return 0

        # Si es contrato por honorarios
        if self.tipo_contrato == 'honorarios':
            if not self.honorarios_mensuales:
                return 0
            return self.honorarios_mensuales * self.cantidad

        # Si es contrato de nómina
        if not self.salario_base:
            return 0

        try:
            # Obtener factor prestacional
            factor = FactorPrestacional.objects.get(perfil=self.perfil_prestacional)
            costo_unitario = self.salario_base * (1 + factor.factor_total)

            # Sumar auxilio de transporte si aplica (<= 2 SMLV)
            if self.escenario:
                try:
                    macro = ParametrosMacro.objects.get(anio=self.escenario.anio, activo=True)
                    if self.salario_base <= (macro.salario_minimo_legal * 2):
                        costo_unitario += macro.subsidio_transporte
                except ParametrosMacro.DoesNotExist:
                    pass

            # Multiplicar por cantidad
            return costo_unitario * self.cantidad

        except FactorPrestacional.DoesNotExist:
            # Si no existe factor, retornar solo salario base * cantidad
            return self.salario_base * self.cantidad

    def __str__(self):
        if self.marca:
            return f"{self.marca.nombre} - {self.get_tipo_display()} ({self.cantidad})"
        return f"{self.get_tipo_display()} - Compartido ({self.cantidad})"


class GastoAdministrativo(models.Model):
    """Gastos administrativos generales (pueden ser compartidos o individuales)"""

    TIPO_CHOICES = [
        ('arriendo_oficina', 'Arriendo de Oficina'),
        ('servicios_publicos', 'Servicios Públicos'),
        ('internet_telefonia', 'Internet y Telefonía'),
        ('vigilancia', 'Vigilancia y Seguridad'),
        ('aseo_cafeteria', 'Aseo y Cafetería'),
        ('papeleria', 'Papelería y Útiles'),
        ('software_licencias', 'Software y Licencias'),
        ('facturacion_electronica', 'Facturación Electrónica'),
        ('seguros', 'Seguros'),
        ('servicios_legales', 'Servicios Jurídicos y Legales'),
        ('mantenimiento_locativo', 'Mantenimiento Locativo'),
        ('gastos_financieros', 'Gastos Bancarios y Financieros'),
        ('bienestar', 'Bienestar y Clima Laboral'),
        ('dotacion', 'Dotación'),
        ('examenes', 'Exámenes Médicos'),
        ('telefonia_celular', 'Telefonía Celular y Datos'),
        ('otros', 'Otros Gastos Administrativos'),
    ]

    ASIGNACION_CHOICES = [
        ('individual', 'Individual (asignado a una marca)'),
        ('compartido', 'Compartido entre marcas'),
    ]

    marca = models.ForeignKey(
        Marca,
        on_delete=models.CASCADE,
        related_name='gastos_administrativos',
        null=True,
        blank=True,
        verbose_name="Marca",
        help_text="Dejar vacío si es compartido entre todas las marcas"
    )
    escenario = models.ForeignKey(
        'Escenario',
        on_delete=models.CASCADE,
        related_name='gasto_administrativo_items',
        verbose_name="Escenario",
        help_text="Escenario al que pertenece este registro",
        null=True,
        blank=True
    )
    nombre = models.CharField(max_length=200, verbose_name="Nombre/Descripción")
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, verbose_name="Tipo de Gasto")
    valor_mensual = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Mensual")
    asignacion = models.CharField(max_length=20, choices=ASIGNACION_CHOICES, default='compartido')
    
    # Índice de incremento para proyecciones
    indice_incremento = models.CharField(
        max_length=20,
        choices=INDICE_INCREMENTO_CHOICES,
        default='arriendos',
        verbose_name="Índice de Incremento",
        help_text="Índice a usar para proyecciones de años futuros. Usar 'arriendos' para arriendos, 'ipc' para otros gastos"
    )
    
    criterio_prorrateo = models.CharField(
        max_length=20,
        choices=[
            ('ventas', 'Por Ventas'),
            ('headcount', 'Por Headcount'),
            ('equitativo', 'Equitativo'),
        ],
        default='ventas',
        null=True,
        blank=True,
        help_text="Solo aplica para asignación compartida"
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
        if self.marca:
            return f"{self.marca.nombre} - {self.get_tipo_display()} - ${self.valor_mensual:,.0f}"
        return f"{self.get_tipo_display()} - Compartido - ${self.valor_mensual:,.0f}"


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
        ('dotacion', 'Dotación'),
        ('epp', 'EPP (Solo Comercial)'),
        ('examenes', 'Exámenes Médicos'),
        ('telefonia_celular', 'Telefonía Celular y Datos'),
        ('otros', 'Otros Gastos Comerciales'),
    ]

    ASIGNACION_CHOICES = [
        ('individual', 'Individual (asignado a una marca)'),
        ('compartido', 'Compartido entre marcas'),
    ]

    escenario = models.ForeignKey(
        'Escenario',
        on_delete=models.CASCADE,
        related_name='gasto_comercial_items',
        verbose_name="Escenario",
        help_text="Escenario al que pertenece este registro",
        null=True,
        blank=True
    )
    marca = models.ForeignKey(
        Marca, 
        on_delete=models.CASCADE, 
        related_name='gastos_comerciales',
        null=True,
        blank=True,
        verbose_name="Marca",
        help_text="Dejar vacío si es compartido"
    )
    nombre = models.CharField(max_length=200, verbose_name="Nombre/Descripción")
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, verbose_name="Tipo de Gasto")
    valor_mensual = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Mensual")
    asignacion = models.CharField(max_length=20, choices=ASIGNACION_CHOICES, default='individual')
    
    # Índice de incremento para proyecciones
    indice_incremento = models.CharField(
        max_length=20,
        choices=INDICE_INCREMENTO_CHOICES,
        default='ipc',
        verbose_name="Índice de Incremento",
        help_text="Índice a usar para proyecciones de años futuros"
    )
    
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
        ('combustible', 'Combustible'),
        ('neumaticos', 'Neumáticos y Repuestos'),
        # ('flete_tercero', 'Flete Transporte (Tercero)'),  # DEPRECADO: Usar tabla Vehículos con esquema='tercero'
        ('canon_renting', 'Canon Renting'),
        ('depreciacion_vehiculo', 'Depreciación Vehículos'),
        ('lavado_vehiculos', 'Aseo y Limpieza Vehículos'),
        ('parqueadero_vehiculos', 'Parqueaderos'),
        ('monitoreo_satelital', 'Monitoreo Satelital (GPS)'),
        ('bodegaje', 'Bodegaje Externo'),
        ('equipos_bodega', 'Equipos de Bodega'),
        ('embalaje', 'Material de Embalaje'),
        ('arriendo_bodega', 'Arriendo Bodega y CEDI'),
        ('servicios_publicos_bodega', 'Servicios Públicos Bodega'),
        ('internet_bodega', 'Internet y Conectividad Bodega'),
        ('seguro_bodega', 'Seguro Todo Riesgo Bodega'),
        ('control_plagas', 'Control de Plagas y Fumigación'),
        ('dotacion', 'Dotación y EPP'),
        ('examenes', 'Exámenes Médicos'),
        ('telefonia_celular', 'Telefonía Celular y Datos'),
        ('otros', 'Otros Gastos Logísticos'),
    ]

    ASIGNACION_CHOICES = [
        ('individual', 'Individual (asignado a una marca)'),
        ('compartido', 'Compartido entre marcas'),
    ]

    escenario = models.ForeignKey(
        'Escenario',
        on_delete=models.CASCADE,
        related_name='gasto_logistico_items',
        verbose_name="Escenario",
        help_text="Escenario al que pertenece este registro",
        null=True,
        blank=True
    )
    marca = models.ForeignKey(
        Marca, 
        on_delete=models.CASCADE, 
        related_name='gastos_logisticos',
        null=True,
        blank=True,
        verbose_name="Marca",
        help_text="Dejar vacío si es compartido"
    )
    nombre = models.CharField(max_length=200, verbose_name="Nombre/Descripción")
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, verbose_name="Tipo de Gasto")
    valor_mensual = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Mensual")
    asignacion = models.CharField(max_length=20, choices=ASIGNACION_CHOICES, default='individual')
    
    # Índice de incremento para proyecciones
    indice_incremento = models.CharField(
        max_length=20,
        choices=INDICE_INCREMENTO_CHOICES,
        default='combustible',
        verbose_name="Índice de Incremento",
        help_text="Índice a usar para proyecciones de años futuros. Usar 'combustible' para gastos de vehículos"
    )
    
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

class PoliticaRecursosHumanos(models.Model):
    """Políticas de RRHH (Dotación, Exámenes, etc.)"""

    anio = models.IntegerField(unique=True, verbose_name="Año")
    
    # Dotación
    valor_dotacion_completa = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name="Valor Dotación Completa",
        help_text="Costo unitario de una dotación completa"
    )
    frecuencia_dotacion_anual = models.IntegerField(
        default=3,
        verbose_name="Frecuencia Anual",
        help_text="Cuántas veces al año se entrega dotación"
    )
    tope_smlv_dotacion = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=2.0,
        verbose_name="Tope SMLV para Dotación",
        help_text="Se entrega dotación a quienes ganen menos de X salarios mínimos"
    )

    # EPP (Solo Comercial)
    valor_epp_anual_comercial = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Valor EPP Anual (Comercial)")
    frecuencia_epp_anual = models.IntegerField(default=1, verbose_name="Frecuencia EPP Anual")

    # Exámenes Médicos
    costo_examen_ingreso_comercial = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Costo Examen Ingreso (Comercial)",
        help_text="Para vendedores, supervisores, etc."
    )
    costo_examen_ingreso_operativo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Costo Examen Ingreso (Otros)",
        help_text="Para administrativos, logísticos, etc."
    )
    
    costo_examen_periodico_comercial = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Costo Examen Periódico (Comercial)"
    )
    costo_examen_periodico_operativo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Costo Examen Periódico (Otros)"
    )
    tasa_rotacion_anual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Tasa de Rotación Anual (%)",
        help_text="Porcentaje de rotación estimado (para calcular exámenes de ingreso)"
    )

    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_politica_rrhh'
        verbose_name = "Política de RRHH"
        verbose_name_plural = "Políticas de RRHH"
        ordering = ['-anio']

    def __str__(self):
        return f"Políticas RRHH {self.anio}"


# ============================================================================
# MÓDULO DE LEJANÍAS - Gestión de Rutas y Gastos Variables
# ============================================================================

class Municipio(models.Model):
    """Municipios del territorio de operación"""
    codigo_dane = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Código DANE",
        help_text="Código DANE del municipio"
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    departamento = models.CharField(max_length=50, verbose_name="Departamento")
    latitud = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        verbose_name="Latitud"
    )
    longitud = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        verbose_name="Longitud"
    )

    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_municipio'
        verbose_name = "Municipio"
        verbose_name_plural = "Municipios"
        ordering = ['departamento', 'nombre']

    def __str__(self):
        return f"{self.nombre}, {self.departamento}"


class MatrizDesplazamiento(models.Model):
    """Matriz de distancias y tiempos entre municipios"""
    origen = models.ForeignKey(
        'Municipio',
        related_name='rutas_desde',
        on_delete=models.CASCADE,
        verbose_name="Origen"
    )
    destino = models.ForeignKey(
        'Municipio',
        related_name='rutas_hacia',
        on_delete=models.CASCADE,
        verbose_name="Destino"
    )
    distancia_km = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Distancia (km)"
    )
    tiempo_minutos = models.IntegerField(verbose_name="Tiempo (minutos)")

    notas = models.TextField(blank=True, verbose_name="Notas")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_matriz_desplazamiento'
        verbose_name = "Matriz de Desplazamiento"
        verbose_name_plural = "Matrices de Desplazamiento"
        unique_together = ('origen', 'destino')
        ordering = ['origen__nombre', 'destino__nombre']

    def __str__(self):
        return f"{self.origen} → {self.destino}: {self.distancia_km} km"


class ConfiguracionLejania(models.Model):
    """Configuración de cálculo de lejanías por escenario"""
    escenario = models.OneToOneField(
        'Escenario',
        on_delete=models.CASCADE,
        related_name='configuracion_lejania',
        verbose_name="Escenario"
    )
    municipio_bodega = models.ForeignKey(
        'Municipio',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Municipio Bodega",
        help_text="Centro de distribución principal"
    )

    # === UMBRALES ===
    umbral_lejania_logistica_km = models.IntegerField(
        default=60,
        verbose_name="Umbral Logística (km)",
        help_text="Aplicar lejania logística desde X km"
    )
    umbral_lejania_comercial_km = models.IntegerField(
        default=10,
        verbose_name="Umbral Comercial (km)",
        help_text="Aplicar lejania comercial desde X km"
    )

    # === COMBUSTIBLE COMERCIAL ===
    consumo_galon_km_moto = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=40,
        verbose_name="Consumo Moto (km/galón)",
        help_text="Rendimiento moto: típicamente 40 km/galón"
    )
    consumo_galon_km_automovil = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=12,
        verbose_name="Consumo Automóvil (km/galón)",
        help_text="Rendimiento automóvil: típicamente 12 km/galón"
    )

    # === GASTOS PERNOCTA LOGÍSTICA ===
    desayuno_logistica = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=15000,
        verbose_name="Desayuno Logística"
    )
    almuerzo_logistica = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=20000,
        verbose_name="Almuerzo Logística"
    )
    cena_logistica = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=20000,
        verbose_name="Cena Logística"
    )
    alojamiento_logistica = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=80000,
        verbose_name="Alojamiento Logística"
    )
    parqueadero_logistica = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=15000,
        verbose_name="Parqueadero Logística"
    )
    es_constitutiva_salario_logistica = models.BooleanField(
        default=False,
        verbose_name="¿Constitutiva Salario? (Logística)",
        help_text="Si marca Sí, se incluye en prestaciones sociales"
    )

    # === GASTOS PERNOCTA COMERCIAL ===
    desayuno_comercial = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=15000,
        verbose_name="Desayuno Comercial"
    )
    almuerzo_comercial = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=20000,
        verbose_name="Almuerzo Comercial"
    )
    cena_comercial = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=20000,
        verbose_name="Cena Comercial"
    )
    alojamiento_comercial = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=80000,
        verbose_name="Alojamiento Comercial"
    )
    es_constitutiva_salario_comercial = models.BooleanField(
        default=False,
        verbose_name="¿Constitutiva Salario? (Comercial)",
        help_text="Si marca Sí, se incluye en prestaciones sociales"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_configuracion_lejania'
        verbose_name = "Configuración de Lejanías"
        verbose_name_plural = "Configuraciones de Lejanías"

    def __str__(self):
        return f"Config Lejanías - {self.escenario}"


class Zona(models.Model):
    """Zonas comerciales (grupos de municipios atendidos)"""
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    codigo = models.CharField(max_length=20, verbose_name="Código")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")

    vendedor = models.ForeignKey(
        'PersonalComercial',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Vendedor Asignado"
    )
    marca = models.ForeignKey(
        'Marca',
        on_delete=models.CASCADE,
        verbose_name="Marca"
    )
    escenario = models.ForeignKey(
        'Escenario',
        on_delete=models.CASCADE,
        verbose_name="Escenario"
    )

    # Base del vendedor (para calcular rutas comerciales)
    municipio_base_vendedor = models.ForeignKey(
        'Municipio',
        on_delete=models.SET_NULL,
        null=True,
        related_name='zonas_base',
        verbose_name="Municipio Base Vendedor",
        help_text="Desde dónde parte el vendedor (su residencia)"
    )

    # Tipo de vehículo comercial
    tipo_vehiculo_comercial = models.CharField(
        max_length=20,
        choices=[
            ('MOTO', 'Moto'),
            ('AUTOMOVIL', 'Automóvil'),
        ],
        default='MOTO',
        verbose_name="Tipo Vehículo Comercial"
    )

    # Frecuencia de visitas
    frecuencia = models.CharField(
        max_length=20,
        choices=[
            ('SEMANAL', 'Semanal (4 periodos/mes)'),
            ('QUINCENAL', 'Quincenal (2 periodos/mes)'),
            ('MENSUAL', 'Mensual (1 periodo/mes)'),
        ],
        default='MENSUAL',
        verbose_name="Frecuencia de Visitas"
    )

    # Pernocta
    requiere_pernocta = models.BooleanField(
        default=False,
        verbose_name="¿Requiere Pernocta?",
        help_text="Si la ruta requiere pasar la noche fuera"
    )
    noches_pernocta = models.IntegerField(
        default=0,
        verbose_name="Noches de Pernocta",
        help_text="Cantidad de noches por periodo"
    )

    activo = models.BooleanField(default=True, verbose_name="Activa")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_zona'
        verbose_name = "Zona"
        verbose_name_plural = "Zonas"
        ordering = ['marca', 'nombre']

    def __str__(self):
        return f"{self.nombre} - {self.marca}"

    def periodos_por_mes(self):
        """Retorna cuántos periodos hay por mes según frecuencia"""
        if self.frecuencia == 'SEMANAL':
            return 4
        elif self.frecuencia == 'QUINCENAL':
            return 2
        else:  # MENSUAL
            return 1


class ZonaMunicipio(models.Model):
    """Relación entre Zona y Municipios con frecuencias específicas"""
    zona = models.ForeignKey(
        'Zona',
        on_delete=models.CASCADE,
        verbose_name="Zona"
    )
    municipio = models.ForeignKey(
        'Municipio',
        on_delete=models.CASCADE,
        verbose_name="Municipio"
    )

    # Frecuencias por periodo (según la frecuencia de la zona)
    visitas_por_periodo = models.IntegerField(
        default=1,
        verbose_name="Visitas Comerciales por Periodo",
        help_text="Ej: Si la zona es semanal, cuántas visitas por semana"
    )
    entregas_por_periodo = models.IntegerField(
        default=1,
        verbose_name="Entregas Logísticas por Periodo",
        help_text="Ej: Si la zona es semanal, cuántas entregas por semana"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_zona_municipio'
        verbose_name = "Zona-Municipio"
        verbose_name_plural = "Zonas-Municipios"
        unique_together = ('zona', 'municipio')
        ordering = ['zona', 'municipio__nombre']

    def __str__(self):
        return f"{self.zona.nombre} → {self.municipio}"

    def visitas_mensuales(self):
        """Calcula visitas comerciales mensuales"""
        return self.visitas_por_periodo * self.zona.periodos_por_mes()

    def entregas_mensuales(self):
        """Calcula entregas logísticas mensuales"""
        return self.entregas_por_periodo * self.zona.periodos_por_mes()
