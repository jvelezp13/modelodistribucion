"""
Modelos Django para el Sistema DxV
"""
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# Import de la calculadora de prestaciones compartida
# Usamos import diferido para evitar dependencia circular
def _calcular_costo_nomina_compartido(salario_base, factores, subsidio_transporte=0, auxilio_adicional=0, cantidad=1):
    """
    Wrapper para calcular costo de nómina usando la función compartida.
    Import diferido para evitar dependencia circular.
    """
    from core.calculadora_prestaciones import calcular_costo_nomina, crear_factores_desde_modelo_django
    factores_obj = crear_factores_desde_modelo_django(factores)
    return calcular_costo_nomina(
        salario_base=salario_base,
        factores=factores_obj,
        subsidio_transporte=subsidio_transporte,
        auxilio_adicional=auxilio_adicional,
        cantidad=cantidad,
    )


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

# Choices globales para asignación geográfica (P&G por zona/municipio)
TIPO_ASIGNACION_GEO_CHOICES = [
    ('directo', 'Directo a Zona'),
    ('proporcional', 'Proporcional a Ventas'),
    ('compartido', 'Compartido Equitativo'),
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

    # Perfiles disponibles para personal comercial
    PERFIL_CHOICES = [
        ('comercial', 'Comercial (Riesgo II - Vendedores)'),
        ('administrativo', 'Administrativo (Riesgo I - Coordinadores)'),
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

    # Campos para compartidos (entre marcas)
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

    # Asignación geográfica (para P&G por zona)
    tipo_asignacion_geo = models.CharField(
        max_length=20,
        choices=TIPO_ASIGNACION_GEO_CHOICES,
        default='directo',
        verbose_name="Asignación Geográfica",
        help_text="Cómo se asigna este costo a las zonas"
    )
    zona = models.ForeignKey(
        'Zona',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='personal_comercial',
        verbose_name="Zona",
        help_text="Zona asignada (solo si asignación es 'Directo a Zona')"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_personal_comercial'
        verbose_name = "Personal Comercial"
        verbose_name_plural = "Personal Comercial"
        ordering = ['marca', 'tipo']

    def calcular_costo_mensual(self):
        """
        Calcula el costo mensual total para este registro de personal.

        Usa la función compartida `calculadora_prestaciones.calcular_costo_nomina`
        para garantizar consistencia con el simulador.

        Según normativa laboral colombiana:
        - Seguridad social y parafiscales: base = solo salario
        - Cesantías, intereses cesantías y prima: base = salario + subsidio transporte
        - Vacaciones: base = solo salario
        """
        if not self.salario_base or not self.cantidad:
            return 0

        try:
            # Obtener factor prestacional
            factor = FactorPrestacional.objects.get(perfil=self.perfil_prestacional)

            # Determinar subsidio de transporte si aplica (<= 2 SMLV)
            subsidio_transporte = Decimal('0')
            if self.escenario:
                try:
                    macro = ParametrosMacro.objects.get(anio=self.escenario.anio, activo=True)
                    if self.salario_base <= (macro.salario_minimo_legal * 2):
                        subsidio_transporte = macro.subsidio_transporte
                except ParametrosMacro.DoesNotExist:
                    pass

            # Usar función compartida
            resultado = _calcular_costo_nomina_compartido(
                salario_base=self.salario_base,
                factores=factor,
                subsidio_transporte=subsidio_transporte,
                auxilio_adicional=self.auxilio_adicional or Decimal('0'),
                cantidad=self.cantidad,
            )
            return resultado.costo_total

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

    # Perfiles disponibles para personal logístico
    # Usar logistico_bodega para operarios y logistico_calle para conductores/auxiliares
    PERFIL_CHOICES = [
        ('logistico_bodega', 'Logístico Bodega (Riesgo III - Operarios)'),
        ('logistico_calle', 'Logístico Calle (Riesgo IV - Conductores)'),
        ('administrativo', 'Administrativo (Riesgo I - Coordinadores)'),
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
    perfil_prestacional = models.CharField(max_length=20, choices=PERFIL_CHOICES, default='logistico_calle')
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

    # Asignación geográfica (para P&G por zona)
    tipo_asignacion_geo = models.CharField(
        max_length=20,
        choices=TIPO_ASIGNACION_GEO_CHOICES,
        default='proporcional',
        verbose_name="Asignación Geográfica",
        help_text="Cómo se asigna este costo a las zonas. Personal logístico típicamente se distribuye proporcional a ventas."
    )
    zona = models.ForeignKey(
        'Zona',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='personal_logistico',
        verbose_name="Zona",
        help_text="Zona asignada (solo si asignación es 'Directo a Zona')"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_personal_logistico'
        verbose_name = "Personal Logístico"
        verbose_name_plural = "Personal Logístico"
        ordering = ['marca', 'tipo']

    def calcular_costo_mensual(self):
        """
        Calcula el costo mensual total para este registro de personal.

        Usa la función compartida `calculadora_prestaciones.calcular_costo_nomina`
        para garantizar consistencia con el simulador.
        """
        if not self.salario_base or not self.cantidad:
            return 0

        try:
            # Obtener factor prestacional
            factor = FactorPrestacional.objects.get(perfil=self.perfil_prestacional)

            # Determinar subsidio de transporte si aplica (<= 2 SMLV)
            subsidio_transporte = Decimal('0')
            if self.escenario:
                try:
                    macro = ParametrosMacro.objects.get(anio=self.escenario.anio, activo=True)
                    if self.salario_base <= (macro.salario_minimo_legal * 2):
                        subsidio_transporte = macro.subsidio_transporte
                except ParametrosMacro.DoesNotExist:
                    pass

            # Usar función compartida
            resultado = _calcular_costo_nomina_compartido(
                salario_base=self.salario_base,
                factores=factor,
                subsidio_transporte=subsidio_transporte,
                auxilio_adicional=Decimal('0'),
                cantidad=self.cantidad,
            )
            return resultado.costo_total

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
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre/Identificador",
        help_text="Identificador único del vehículo. Ej: 'Turbo 01', 'NKR Zona Norte'",
        default='',
        blank=True
    )
    tipo_vehiculo = models.CharField(max_length=50, choices=TIPO_VEHICULO_CHOICES, verbose_name="Tipo de Vehículo")
    esquema = models.CharField(max_length=20, choices=ESQUEMA_CHOICES, verbose_name="Esquema")
    cantidad = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Cantidad")
    asignacion = models.CharField(max_length=20, choices=ASIGNACION_CHOICES, default='individual')

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

    # Personal asociado al vehículo
    cantidad_auxiliares = models.IntegerField(
        default=1,
        validators=[MinValueValidator(0)],
        verbose_name="Auxiliares por Vehículo",
        help_text="Cantidad de auxiliares de entrega fijos asignados a este vehículo"
    )

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
        """
        Calcula el costo mensual FIJO del vehículo.

        NOTA: El combustible y costos variables se calculan desde los Recorridos Logísticos,
        no desde este método. Este método solo incluye costos fijos del vehículo.
        """
        try:
            total = 0
            cantidad = self.cantidad or 0

            # Costos comunes a todos los esquemas
            total += (self.costo_monitoreo_mensual or 0) * cantidad
            total += (self.costo_seguro_mercancia_mensual or 0) * cantidad

            if self.esquema == 'tercero':
                # Para terceros, el costo viene del flete base en los recorridos
                # Aquí solo se incluyen costos adicionales fijos si los hay
                pass

            elif self.esquema in ['renting', 'tradicional']:
                # Costos comunes Propio/Renting
                total += (self.costo_lavado_mensual or 0) * cantidad
                total += (self.costo_parqueadero_mensual or 0) * cantidad

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
        if self.nombre:
            return f"{self.nombre} ({self.get_tipo_vehiculo_display()} - {self.get_esquema_display()})"
        return f"{self.marca.nombre} - {self.get_tipo_vehiculo_display()} {self.get_esquema_display()} ({self.cantidad})"


class ParametrosMacro(models.Model):
    """Parámetros macroeconómicos del sistema"""

    anio = models.IntegerField(unique=True, verbose_name="Año")

    # Índices de incremento (0-100, ej: 9.5 = 9.5%)
    ipc = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="IPC (%)",
        help_text="Índice de Precios al Consumidor (ej: 9.5 para 9.5%)"
    )
    ipt = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="IPT (%)",
        help_text="Índice de Precios al Transportador (ej: 8.0 para 8%)"
    )
    incremento_salarios = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Incremento Salarios (%)",
        help_text="Incremento general de salarios (ej: 10.0 para 10%)"
    )
    incremento_salario_minimo = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Incremento Salario Mínimo (%)",
        help_text="Incremento específico del salario mínimo (ej: 12.0 para 12%)"
    )
    incremento_combustible = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Incremento Combustible (%)",
        help_text="Índice de incremento de combustibles (ej: 5.0 para 5%)"
    )
    incremento_arriendos = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Incremento Arriendos (%)",
        help_text="Usualmente igual al IPC (ej: 9.5 para 9.5%)"
    )
    incremento_personalizado_1 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Índice Personalizado 1 (%)"
    )
    nombre_personalizado_1 = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nombre Índice Personalizado 1",
        help_text="Ej: 'Incremento Tecnología', 'Incremento Servicios Públicos'"
    )
    incremento_personalizado_2 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Índice Personalizado 2 (%)"
    )
    nombre_personalizado_2 = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nombre Índice Personalizado 2",
        help_text="Ej: 'Incremento Seguros', 'Incremento Mantenimiento'"
    )

    # Valores monetarios
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
    """
    Factores prestacionales por perfil.

    Todos los porcentajes se almacenan en formato 0-100 (ej: 8.5 = 8.5%).
    El factor_total retorna el valor en decimal para usar en cálculos.

    GUÍA DE SELECCIÓN DE NIVEL DE RIESGO ARL:
    =========================================
    Clase I (0.522%): Riesgo mínimo
        - Trabajo de oficina, actividades administrativas
        - Vendedores de mostrador, recepcionistas
        - Contadores, secretarias, sistemas

    Clase II (1.044%): Riesgo bajo
        - Vendedores externos, preventa, TAT
        - Mercaderistas, impulsadores
        - Supervisores comerciales en campo

    Clase III (2.436%): Riesgo medio
        - Operarios de manufactura ligera
        - Técnicos de mantenimiento
        - Personal de empaque y embalaje

    Clase IV (4.350%): Riesgo alto
        - Conductores de vehículos de carga
        - Operarios de montacargas
        - Trabajo en bodega con carga pesada
        - Auxiliares de entrega/reparto

    Clase V (6.960%): Riesgo máximo
        - Minería, construcción pesada
        - Trabajo en alturas
        - Manejo de explosivos
        - Generalmente NO aplica para distribución
    """

    # Perfiles predefinidos con nivel de riesgo incluido para claridad
    PERFIL_CHOICES = [
        # Riesgo I - Oficina
        ('administrativo', 'Administrativo (Riesgo I - Oficina)'),

        # Riesgo II - Vendedores externos
        ('comercial', 'Comercial (Riesgo II - Vendedores)'),

        # Riesgo III - Operaciones ligeras
        ('logistico_bodega', 'Logístico Bodega (Riesgo III - Operaciones)'),

        # Riesgo IV - Conductores y carga
        ('logistico_calle', 'Logístico Calle (Riesgo IV - Conductores)'),

        # Aprendices
        ('aprendiz_sena', 'Aprendiz SENA (Etapa Productiva)'),
    ]

    # Tabla de referencia: Valores ARL por clase de riesgo
    ARL_POR_CLASE = {
        'I': 0.522,    # Riesgo mínimo - oficina
        'II': 1.044,   # Riesgo bajo - vendedores
        'III': 2.436,  # Riesgo medio - operaciones
        'IV': 4.350,   # Riesgo alto - conductores
        'V': 6.960,    # Riesgo máximo - no común en distribución
    }

    # Mapeo de perfil a clase de riesgo recomendada
    RIESGO_RECOMENDADO = {
        'administrativo': 'I',
        'comercial': 'II',
        'logistico_bodega': 'III',
        'logistico_calle': 'IV',
        'aprendiz_sena': 'I',  # Aprendices: según actividad, típicamente I o II
    }

    perfil = models.CharField(max_length=50, choices=PERFIL_CHOICES, unique=True, verbose_name="Perfil")

    # ==========================================================================
    # SEGURIDAD SOCIAL - Base de cálculo: SOLO SALARIO
    # Exonerados por Ley 1607/2012 para empleados < 10 SMLV: Salud (0%)
    # ==========================================================================
    salud = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Salud (%)",
        help_text="Base: salario. Normal: 8.5%. EXONERADO (0%) por Ley 1607 para empleados < 10 SMLV"
    )
    pension = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Pensión (%)",
        help_text="Base: salario. Siempre 12% (NO está exonerado)"
    )
    arl = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="ARL (%)",
        help_text="Base: salario. Clases: I=0.522 (oficina), II=1.044 (vendedores), III=2.436 (bodega), IV=4.350 (conductores), V=6.960"
    )

    # ==========================================================================
    # PARAFISCALES - Base de cálculo: SOLO SALARIO
    # Exonerados por Ley 1607/2012 para empleados < 10 SMLV: ICBF y SENA (0%)
    # ==========================================================================
    caja_compensacion = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Caja Compensación (%)",
        help_text="Base: salario. Siempre 4% (NO está exonerado)"
    )
    icbf = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="ICBF (%)",
        help_text="Base: salario. Normal: 3%. EXONERADO (0%) por Ley 1607 para empleados < 10 SMLV"
    )
    sena = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="SENA (%)",
        help_text="Base: salario. Normal: 2%. EXONERADO (0%) por Ley 1607 para empleados < 10 SMLV"
    )

    # ==========================================================================
    # PRESTACIONES SOCIALES - Base de cálculo: SALARIO + SUBSIDIO TRANSPORTE
    # (excepto vacaciones que es solo salario)
    # ==========================================================================
    cesantias = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Cesantías (%)",
        help_text="Base: salario + subsidio. Provisión: 8.33% (equivale a 1 mes de salario al año)"
    )
    intereses_cesantias = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Int. Cesantías (%)",
        help_text="Base: salario + subsidio. Provisión: 1.0% (es el 12% anual sobre cesantías, dividido 12)"
    )
    prima = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Prima (%)",
        help_text="Base: salario + subsidio. Provisión: 8.33% (equivale a 1 mes de salario al año)"
    )
    vacaciones = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Vacaciones (%)",
        help_text="Base: SOLO salario. Usar 0% si supernumerarios se modelan aparte (recomendado). Usar 4.17% solo para provisión contable."
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_factor_prestacional'
        verbose_name = "Factor Prestacional"
        verbose_name_plural = "Factores Prestacionales"
        ordering = ['perfil']

    @property
    def factor_total(self):
        """
        Calcula el factor total sumando todos los componentes.
        Retorna en formato Decimal (0.52 para 52%) para usar en cálculos.
        """
        suma_porcentajes = (
            self.salud + self.pension + self.arl + self.caja_compensacion +
            self.icbf + self.sena + self.cesantias + self.intereses_cesantias +
            self.prima + self.vacaciones
        )
        return suma_porcentajes / Decimal('100')

    @property
    def factor_total_porcentaje(self):
        """Retorna el factor total en formato porcentaje (52.0 para 52%)"""
        return (
            self.salud + self.pension + self.arl + self.caja_compensacion +
            self.icbf + self.sena + self.cesantias + self.intereses_cesantias +
            self.prima + self.vacaciones
        )

    def __str__(self):
        return f"{self.get_perfil_display()} - {self.factor_total_porcentaje:.2f}%"


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

    # Perfiles disponibles para personal administrativo
    PERFIL_CHOICES = [
        ('administrativo', 'Administrativo (Riesgo I - Oficina)'),
        ('aprendiz_sena', 'Aprendiz SENA (Etapa Productiva)'),
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

    # Asignación geográfica (para P&G por zona)
    # Personal administrativo típicamente se distribuye equitativamente entre zonas
    tipo_asignacion_geo = models.CharField(
        max_length=20,
        choices=TIPO_ASIGNACION_GEO_CHOICES,
        default='compartido',
        verbose_name="Asignación Geográfica",
        help_text="Cómo se asigna este costo a las zonas. Personal admin se distribuye equitativamente."
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_personal_administrativo'
        verbose_name = "Personal Administrativo"
        verbose_name_plural = "Personal Administrativo"
        ordering = ['tipo']

    def calcular_costo_mensual(self):
        """
        Calcula el costo mensual total para este registro de personal.

        Usa la función compartida `calculadora_prestaciones.calcular_costo_nomina`
        para garantizar consistencia con el simulador.
        """
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

            # Determinar subsidio de transporte si aplica (<= 2 SMLV)
            subsidio_transporte = Decimal('0')
            if self.escenario:
                try:
                    macro = ParametrosMacro.objects.get(anio=self.escenario.anio, activo=True)
                    if self.salario_base <= (macro.salario_minimo_legal * 2):
                        subsidio_transporte = macro.subsidio_transporte
                except ParametrosMacro.DoesNotExist:
                    pass

            # Usar función compartida
            resultado = _calcular_costo_nomina_compartido(
                salario_base=self.salario_base,
                factores=factor,
                subsidio_transporte=subsidio_transporte,
                auxilio_adicional=Decimal('0'),
                cantidad=self.cantidad,
            )
            return resultado.costo_total

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

    # Asignación geográfica (para P&G por zona)
    tipo_asignacion_geo = models.CharField(
        max_length=20,
        choices=TIPO_ASIGNACION_GEO_CHOICES,
        default='compartido',
        verbose_name="Asignación Geográfica",
        help_text="Cómo se asigna este gasto a las zonas. Gastos admin se distribuyen equitativamente."
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

    # Asignación geográfica (para P&G por zona)
    tipo_asignacion_geo = models.CharField(
        max_length=20,
        choices=TIPO_ASIGNACION_GEO_CHOICES,
        default='directo',
        verbose_name="Asignación Geográfica",
        help_text="Cómo se asigna este gasto a las zonas"
    )
    zona = models.ForeignKey(
        'Zona',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gastos_comerciales',
        verbose_name="Zona",
        help_text="Zona asignada (solo si asignación es 'Directo a Zona')"
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

    # Asignación geográfica (para P&G por zona)
    tipo_asignacion_geo = models.CharField(
        max_length=20,
        choices=TIPO_ASIGNACION_GEO_CHOICES,
        default='proporcional',
        verbose_name="Asignación Geográfica",
        help_text="Cómo se asigna este gasto a las zonas. Gastos logísticos se distribuyen proporcional a ventas."
    )
    zona = models.ForeignKey(
        'Zona',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gastos_logisticos',
        verbose_name="Zona",
        help_text="Zona asignada (solo si asignación es 'Directo a Zona')"
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

    # Para impuestos porcentuales (formato 0-100)
    porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Porcentaje (%)",
        help_text="Ingrese en formato 0-100 (ej: 33 para 33%, 0.41 para 0.41%)"
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
            return f"{self.get_tipo_display()} - {self.porcentaje:.2f}%"
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

    # Índice de incremento para proyecciones
    indice_incremento = models.CharField(
        max_length=20,
        choices=INDICE_INCREMENTO_CHOICES,
        default='ipc',
        verbose_name="Índice de Incremento",
        help_text="Índice a usar para proyectar valores monetarios al siguiente año"
    )

    # Dotación
    valor_dotacion_completa = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Valor Dotación Completa",
        help_text="Costo unitario de una dotación completa"
    )
    frecuencia_dotacion_meses = models.IntegerField(
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        verbose_name="Frecuencia Dotación (meses)",
        help_text="Cada cuántos meses se entrega dotación (ej: 4 = cada 4 meses = 3 veces al año)"
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
    frecuencia_epp_meses = models.IntegerField(
        default=12,
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        verbose_name="Frecuencia EPP (meses)",
        help_text="Cada cuántos meses se entrega EPP (ej: 24 = cada 2 años, 12 = cada año)"
    )

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
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Tasa de Rotación Anual (%)",
        help_text="Porcentaje de rotación estimado 0-100 (ej: 25 para 25%)"
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

    # Peajes (solo aplica para vehículos logísticos, no para motos)
    peaje_ida = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Peaje",
        help_text="Costo total de peajes en este tramo (cada tramo es unidireccional)"
    )

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

    # === GASTOS PERNOCTA LOGÍSTICA - CONDUCTOR ===
    # Estos gastos van al tercero cuando el esquema es 'tercero'
    desayuno_conductor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=15000,
        verbose_name="Desayuno Conductor"
    )
    almuerzo_conductor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=20000,
        verbose_name="Almuerzo Conductor"
    )
    cena_conductor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=20000,
        verbose_name="Cena Conductor"
    )
    alojamiento_conductor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=80000,
        verbose_name="Alojamiento Conductor"
    )

    # === GASTOS PERNOCTA LOGÍSTICA - AUXILIAR ===
    # Estos gastos siempre los paga la empresa (convenios, etc.)
    desayuno_auxiliar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=15000,
        verbose_name="Desayuno Auxiliar"
    )
    almuerzo_auxiliar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=20000,
        verbose_name="Almuerzo Auxiliar"
    )
    cena_auxiliar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=20000,
        verbose_name="Cena Auxiliar"
    )
    alojamiento_auxiliar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=80000,
        verbose_name="Alojamiento Auxiliar"
    )

    # === GASTOS VEHÍCULO ===
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

    # === PRECIOS DE COMBUSTIBLE ===
    precio_galon_gasolina = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=15000,
        verbose_name="Precio Galón Gasolina",
        help_text="Precio promedio galón de gasolina (para comerciales y vehículos gasolina)"
    )
    precio_galon_acpm = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=10000,
        verbose_name="Precio Galón ACPM",
        help_text="Precio promedio galón de ACPM/Diesel (para vehículos logísticos)"
    )

    # === COMITÉ COMERCIAL ===
    tiene_comite_comercial = models.BooleanField(
        default=False,
        verbose_name="¿Tiene Comité Comercial?",
        help_text="Si hay reunión periódica de vendedores en un municipio fijo"
    )
    municipio_comite = models.ForeignKey(
        'Municipio',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comites_comerciales',
        verbose_name="Municipio del Comité",
        help_text="Dónde se realiza el comité comercial"
    )
    frecuencia_comite = models.CharField(
        max_length=20,
        choices=[
            ('SEMANAL', 'Semanal (4 veces/mes)'),
            ('TRISEMANAL', '3 veces al mes'),
            ('QUINCENAL', 'Quincenal (2 veces/mes)'),
            ('MENSUAL', 'Mensual (1 vez/mes)'),
        ],
        default='SEMANAL',
        verbose_name="Frecuencia del Comité"
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
    """Zonas comerciales (grupos de municipios atendidos por vendedores)"""
    nombre = models.CharField(max_length=100, verbose_name="Nombre")

    vendedor = models.ForeignKey(
        'PersonalComercial',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='zonas_asignadas',
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
        default='SEMANAL',
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

    # Venta proyectada (valor absoluto editable)
    venta_proyectada = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Venta Proyectada",
        help_text="Valor de venta proyectada para esta zona (en pesos)"
    )

    # Participación calculada automáticamente (solo lectura)
    participacion_ventas = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Participación Ventas %",
        help_text="Calculado automáticamente: (venta_zona / venta_total_marca) × 100",
        editable=False
    )

    activo = models.BooleanField(default=True, verbose_name="Activa")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_zona'
        verbose_name = "Zona Comercial"
        verbose_name_plural = "Zonas Comerciales"
        ordering = ['marca', 'nombre']
        unique_together = [['marca', 'escenario', 'nombre']]

    def __str__(self):
        return f"{self.nombre} - {self.marca}"

    def calcular_participacion(self):
        """Calcula el % de participación basado en venta_proyectada vs total marca"""
        if not self.marca or not self.escenario:
            return Decimal('0')

        total_marca = Zona.objects.filter(
            marca=self.marca,
            escenario=self.escenario,
            activo=True
        ).aggregate(total=models.Sum('venta_proyectada'))['total'] or Decimal('0')

        if total_marca > 0:
            return (self.venta_proyectada / total_marca) * 100
        return Decimal('0')

    def save(self, *args, **kwargs):
        # Calcular participación antes de guardar
        super().save(*args, **kwargs)
        # Recalcular participación de todas las zonas de la marca después de guardar
        self._recalcular_participaciones_marca()

    def _recalcular_participaciones_marca(self):
        """Recalcula participación de todas las zonas de la misma marca/escenario"""
        if not self.marca or not self.escenario:
            return

        zonas = Zona.objects.filter(
            marca=self.marca,
            escenario=self.escenario,
            activo=True
        )
        total = zonas.aggregate(total=models.Sum('venta_proyectada'))['total'] or Decimal('0')

        for zona in zonas:
            if total > 0:
                nueva_part = (zona.venta_proyectada / total) * 100
            else:
                nueva_part = Decimal('0')
            # Usar update para evitar recursión
            Zona.objects.filter(pk=zona.pk).update(participacion_ventas=nueva_part)

    def periodos_por_mes(self):
        """
        Retorna cuántos periodos hay por mes según frecuencia.

        Usa cálculos exactos:
        - SEMANAL: 52 semanas / 12 meses = 4.33
        - QUINCENAL: 24 quincenas / 12 meses = 2.00
        - MENSUAL: 12 meses / 12 meses = 1.00
        """
        if self.frecuencia == 'SEMANAL':
            return Decimal('4.33')  # 52 semanas / 12 meses
        elif self.frecuencia == 'QUINCENAL':
            return Decimal('2.00')
        else:  # MENSUAL
            return Decimal('1.00')


class ZonaMunicipio(models.Model):
    """Municipios de una Zona Comercial (para visitas de vendedores)"""
    zona = models.ForeignKey(
        'Zona',
        on_delete=models.CASCADE,
        related_name='municipios',
        verbose_name="Zona"
    )
    municipio = models.ForeignKey(
        'Municipio',
        on_delete=models.CASCADE,
        verbose_name="Municipio"
    )

    # Frecuencia de visitas comerciales por periodo (según la frecuencia de la zona)
    visitas_por_periodo = models.IntegerField(
        default=1,
        verbose_name="Visitas por Periodo",
        help_text="Ej: Si la zona es semanal, cuántas visitas por semana"
    )

    # Venta proyectada del municipio (valor absoluto editable)
    venta_proyectada = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Venta Proyectada",
        help_text="Valor de venta proyectada para este municipio (en pesos)"
    )

    # Participación calculada automáticamente (solo lectura)
    participacion_ventas = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Participación Ventas %",
        help_text="Calculado automáticamente: (venta_municipio / venta_zona) × 100",
        editable=False
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_zona_municipio'
        verbose_name = "Municipio de Zona Comercial"
        verbose_name_plural = "Municipios de Zonas Comerciales"
        unique_together = ('zona', 'municipio')
        ordering = ['zona', 'municipio__nombre']

    def __str__(self):
        return f"{self.zona.nombre} → {self.municipio}"

    def visitas_mensuales(self):
        """Calcula visitas comerciales mensuales"""
        return self.visitas_por_periodo * self.zona.periodos_por_mes()

    def calcular_participacion(self):
        """Calcula el % de participación basado en venta_proyectada vs total zona"""
        if not self.zona:
            return Decimal('0')

        total_zona = ZonaMunicipio.objects.filter(
            zona=self.zona
        ).aggregate(total=models.Sum('venta_proyectada'))['total'] or Decimal('0')

        if total_zona > 0:
            return (self.venta_proyectada / total_zona) * 100
        return Decimal('0')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Recalcular participación de todos los municipios de la zona
        self._recalcular_participaciones_zona()

    def _recalcular_participaciones_zona(self):
        """Recalcula participación de todos los municipios de la misma zona"""
        if not self.zona:
            return

        municipios = ZonaMunicipio.objects.filter(zona=self.zona)
        total = municipios.aggregate(total=models.Sum('venta_proyectada'))['total'] or Decimal('0')

        for mun in municipios:
            if total > 0:
                nueva_part = (mun.venta_proyectada / total) * 100
            else:
                nueva_part = Decimal('0')
            ZonaMunicipio.objects.filter(pk=mun.pk).update(participacion_ventas=nueva_part)

    def participacion_ventas_total(self):
        """Calcula la participación de ventas sobre el total de la marca"""
        return (self.zona.participacion_ventas / 100) * (self.participacion_ventas / 100) * 100


class VentaMunicipio(models.Model):
    """
    Venta proyectada por municipio (independiente de zonas comerciales).
    Usado para análisis geográfico de distribución de ventas.
    """
    marca = models.ForeignKey(
        'Marca',
        on_delete=models.CASCADE,
        related_name='ventas_municipio',
        verbose_name="Marca"
    )
    escenario = models.ForeignKey(
        'Escenario',
        on_delete=models.CASCADE,
        related_name='ventas_municipio',
        verbose_name="Escenario"
    )
    municipio = models.ForeignKey(
        'Municipio',
        on_delete=models.CASCADE,
        related_name='ventas',
        verbose_name="Municipio"
    )

    venta_proyectada = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Venta Proyectada",
        help_text="Valor de venta proyectada para este municipio (en pesos)"
    )

    # Participación calculada automáticamente
    participacion_ventas = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Participación %",
        help_text="Calculado automáticamente",
        editable=False
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_venta_municipio'
        verbose_name = "Venta por Municipio"
        verbose_name_plural = "Ventas por Municipio"
        unique_together = [['marca', 'escenario', 'municipio']]
        ordering = ['municipio__departamento', 'municipio__nombre']

    def __str__(self):
        return f"{self.municipio} - {self.marca} ({self.escenario.anio})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._recalcular_participaciones()

    def _recalcular_participaciones(self):
        """Recalcula participación de todos los municipios de la misma marca/escenario"""
        if not self.marca or not self.escenario:
            return

        ventas = VentaMunicipio.objects.filter(
            marca=self.marca,
            escenario=self.escenario
        )
        total = ventas.aggregate(total=models.Sum('venta_proyectada'))['total'] or Decimal('0')

        for vm in ventas:
            if total > 0:
                nueva_part = (vm.venta_proyectada / total) * 100
            else:
                nueva_part = Decimal('0')
            VentaMunicipio.objects.filter(pk=vm.pk).update(participacion_ventas=nueva_part)


# ============================================================================
# MÓDULO DE RUTAS LOGÍSTICAS - Independiente de Zonas Comerciales
# ============================================================================

class RutaLogistica(models.Model):
    """Recorridos de distribución logística (circuitos que hace un vehículo)"""

    FRECUENCIA_CHOICES = [
        ('SEMANAL', 'Semanal (4.33 periodos/mes)'),
        ('QUINCENAL', 'Quincenal (2 periodos/mes)'),
        ('MENSUAL', 'Mensual (1 periodo/mes)'),
    ]

    nombre = models.CharField(max_length=100, verbose_name="Nombre del Recorrido")

    vehiculo = models.ForeignKey(
        'Vehiculo',
        on_delete=models.CASCADE,
        related_name='recorridos',
        verbose_name="Vehículo Asignado",
        help_text="Vehículo (propio, renting o tercero) que realiza este recorrido"
    )
    marca = models.ForeignKey(
        'Marca',
        on_delete=models.CASCADE,
        related_name='recorridos',
        verbose_name="Marca"
    )
    escenario = models.ForeignKey(
        'Escenario',
        on_delete=models.CASCADE,
        related_name='recorridos',
        verbose_name="Escenario"
    )

    # Frecuencia del recorrido
    frecuencia = models.CharField(
        max_length=20,
        choices=FRECUENCIA_CHOICES,
        default='SEMANAL',
        verbose_name="Frecuencia"
    )
    viajes_por_periodo = models.IntegerField(
        default=1,
        verbose_name="Veces por Periodo",
        help_text="Cuántas veces se hace este recorrido por periodo. Ej: 2 veces/semana"
    )

    # Pernocta del recorrido
    requiere_pernocta = models.BooleanField(
        default=False,
        verbose_name="¿Requiere Pernocta?",
        help_text="Si el recorrido requiere que el conductor pase la noche fuera"
    )
    noches_pernocta = models.IntegerField(
        default=0,
        verbose_name="Noches de Pernocta",
        help_text="Cantidad de noches por recorrido completo"
    )

    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_ruta_logistica'
        verbose_name = "Recorrido Logístico"
        verbose_name_plural = "Recorridos Logísticos"
        ordering = ['marca', 'vehiculo', 'nombre']

    def __str__(self):
        return f"{self.nombre} - {self.vehiculo}"

    def periodos_por_mes(self):
        """Retorna cuántos periodos hay por mes según frecuencia."""
        if self.frecuencia == 'SEMANAL':
            return Decimal('4.33')
        elif self.frecuencia == 'QUINCENAL':
            return Decimal('2.00')
        else:  # MENSUAL
            return Decimal('1.00')

    def recorridos_mensuales(self):
        """Retorna cuántas veces se hace el recorrido completo por mes."""
        return self.viajes_por_periodo * self.periodos_por_mes()


class RutaMunicipio(models.Model):
    """Municipios que atiende cada recorrido logístico"""
    ruta = models.ForeignKey(
        'RutaLogistica',
        on_delete=models.CASCADE,
        related_name='municipios',
        verbose_name="Recorrido"
    )
    municipio = models.ForeignKey(
        'Municipio',
        on_delete=models.CASCADE,
        verbose_name="Municipio"
    )

    # Orden de visita en el recorrido (para calcular circuito)
    orden_visita = models.IntegerField(
        default=1,
        verbose_name="Orden de Visita",
        help_text="Secuencia en el recorrido: 1=primer municipio, 2=segundo, etc."
    )

    # Flete base para terceros
    flete_base = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Flete Base",
        help_text="Valor base del flete para este municipio (aplica para vehículos terceros)"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_ruta_municipio'
        verbose_name = "Municipio del Recorrido"
        verbose_name_plural = "Municipios del Recorrido"
        unique_together = ('ruta', 'municipio')
        ordering = ['ruta', 'orden_visita']

    def __str__(self):
        return f"{self.ruta.nombre} → {self.orden_visita}. {self.municipio}"


# =============================================================================
# MÓDULO DE PROYECCIÓN DE VENTAS
# =============================================================================

class CanalVenta(models.Model):
    """Canales de venta personalizables"""

    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Canal")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_canal_venta'
        verbose_name = "Canal de Venta"
        verbose_name_plural = "Canales de Venta"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class CategoriaProducto(models.Model):
    """Categorías de productos para proyección agregada"""

    nombre = models.CharField(max_length=100, verbose_name="Nombre de Categoría")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    marca = models.ForeignKey(
        Marca,
        on_delete=models.CASCADE,
        related_name='categorias_producto',
        verbose_name="Marca",
        null=True,
        blank=True,
        help_text="Dejar vacío para categoría compartida entre marcas"
    )
    precio_promedio = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Precio Promedio",
        help_text="Precio promedio por unidad en esta categoría"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_categoria_producto'
        verbose_name = "Categoría de Producto"
        verbose_name_plural = "Categorías de Producto"
        ordering = ['marca', 'nombre']

    def __str__(self):
        if self.marca:
            return f"{self.marca.nombre} - {self.nombre}"
        return self.nombre


class Producto(models.Model):
    """Productos/SKUs individuales para proyección detallada"""

    sku = models.CharField(max_length=50, verbose_name="SKU")
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Producto")
    marca = models.ForeignKey(
        Marca,
        on_delete=models.CASCADE,
        related_name='productos',
        verbose_name="Marca"
    )
    categoria = models.ForeignKey(
        CategoriaProducto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos',
        verbose_name="Categoría"
    )
    precio_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Precio Unitario"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_producto'
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        unique_together = ['marca', 'sku']
        ordering = ['marca', 'categoria', 'nombre']

    def __str__(self):
        return f"{self.sku} - {self.nombre}"


class PlantillaEstacional(models.Model):
    """Plantillas de distribución mensual para estacionalidad"""

    nombre = models.CharField(max_length=100, verbose_name="Nombre de Plantilla")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    marca = models.ForeignKey(
        Marca,
        on_delete=models.CASCADE,
        related_name='plantillas_estacionales',
        verbose_name="Marca",
        null=True,
        blank=True,
        help_text="Dejar vacío para plantilla global"
    )

    # Porcentajes por mes (deben sumar 100%)
    enero = models.DecimalField(max_digits=5, decimal_places=2, default=8.33, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Enero %")
    febrero = models.DecimalField(max_digits=5, decimal_places=2, default=8.33, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Febrero %")
    marzo = models.DecimalField(max_digits=5, decimal_places=2, default=8.33, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Marzo %")
    abril = models.DecimalField(max_digits=5, decimal_places=2, default=8.33, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Abril %")
    mayo = models.DecimalField(max_digits=5, decimal_places=2, default=8.33, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Mayo %")
    junio = models.DecimalField(max_digits=5, decimal_places=2, default=8.33, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Junio %")
    julio = models.DecimalField(max_digits=5, decimal_places=2, default=8.33, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Julio %")
    agosto = models.DecimalField(max_digits=5, decimal_places=2, default=8.33, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Agosto %")
    septiembre = models.DecimalField(max_digits=5, decimal_places=2, default=8.33, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Septiembre %")
    octubre = models.DecimalField(max_digits=5, decimal_places=2, default=8.33, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Octubre %")
    noviembre = models.DecimalField(max_digits=5, decimal_places=2, default=8.33, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Noviembre %")
    diciembre = models.DecimalField(max_digits=5, decimal_places=2, default=8.37, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Diciembre %")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_plantilla_estacional'
        verbose_name = "Plantilla Estacional"
        verbose_name_plural = "Plantillas Estacionales"
        ordering = ['marca', 'nombre']

    def __str__(self):
        if self.marca:
            return f"{self.marca.nombre} - {self.nombre}"
        return f"{self.nombre} (Global)"

    def clean(self):
        """Valida que los porcentajes sumen 100%"""
        from django.core.exceptions import ValidationError
        total = self.total_porcentaje()
        if abs(total - 100) > 0.5:  # Tolerancia de 0.5%
            raise ValidationError(
                f"Los porcentajes deben sumar 100%. Suma actual: {total:.2f}%"
            )

    def total_porcentaje(self):
        """Retorna la suma de todos los porcentajes"""
        return (self.enero + self.febrero + self.marzo + self.abril +
                self.mayo + self.junio + self.julio + self.agosto +
                self.septiembre + self.octubre + self.noviembre + self.diciembre)

    def get_distribucion(self):
        """Retorna diccionario con la distribución mensual"""
        return {
            'enero': float(self.enero) / 100,
            'febrero': float(self.febrero) / 100,
            'marzo': float(self.marzo) / 100,
            'abril': float(self.abril) / 100,
            'mayo': float(self.mayo) / 100,
            'junio': float(self.junio) / 100,
            'julio': float(self.julio) / 100,
            'agosto': float(self.agosto) / 100,
            'septiembre': float(self.septiembre) / 100,
            'octubre': float(self.octubre) / 100,
            'noviembre': float(self.noviembre) / 100,
            'diciembre': float(self.diciembre) / 100,
        }


class DefinicionMercado(models.Model):
    """Definición de mercados objetivo para proyección por penetración"""

    TIPO_CHOICES = [
        ('geografico', 'Geográfico (región/ciudad)'),
        ('segmento', 'Segmento de Mercado'),
        ('clientes', 'Base de Clientes'),
        ('categoria', 'Categoría de Producto'),
    ]

    nombre = models.CharField(max_length=100, verbose_name="Nombre del Mercado")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo de Mercado")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")

    tamano_mercado = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Tamaño del Mercado ($)",
        help_text="Valor total del mercado en pesos"
    )
    crecimiento_anual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Crecimiento Anual %",
        help_text="Tasa de crecimiento esperada del mercado"
    )
    ticket_promedio = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Ticket Promedio",
        help_text="Para tipo 'clientes': valor promedio por cliente"
    )
    numero_clientes_potenciales = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Clientes Potenciales",
        help_text="Para tipo 'clientes': número total de clientes en el mercado"
    )

    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_definicion_mercado'
        verbose_name = "Definición de Mercado"
        verbose_name_plural = "Definiciones de Mercado"
        ordering = ['tipo', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"


class ProyeccionVentasConfig(models.Model):
    """Configuración principal de proyección de ventas por marca/escenario"""

    METODO_CHOICES = [
        ('manual', 'Entrada Manual Directa'),
        ('crecimiento', 'Crecimiento sobre Base'),
        ('precio_unidades', 'Precio × Unidades'),
        ('canal', 'Por Canal de Venta'),
        ('penetracion', 'Penetración de Mercado'),
    ]

    marca = models.ForeignKey(
        Marca,
        on_delete=models.CASCADE,
        related_name='proyecciones_config',
        verbose_name="Marca"
    )
    escenario = models.ForeignKey(
        'Escenario',
        on_delete=models.CASCADE,
        related_name='proyecciones_config',
        verbose_name="Escenario"
    )
    anio = models.IntegerField(verbose_name="Año de Proyección")
    metodo = models.CharField(
        max_length=20,
        choices=METODO_CHOICES,
        verbose_name="Método de Proyección"
    )

    # Configuración opcional de estacionalidad
    plantilla_estacional = models.ForeignKey(
        PlantillaEstacional,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proyecciones',
        verbose_name="Plantilla Estacional",
        help_text="Distribución mensual a aplicar (si aplica al método)"
    )

    notas = models.TextField(blank=True, verbose_name="Notas")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_proyeccion_ventas_config'
        verbose_name = "Configuración de Proyección"
        verbose_name_plural = "Configuraciones de Proyección"
        unique_together = ['marca', 'escenario', 'anio']
        ordering = ['marca', 'escenario', 'anio']

    def __str__(self):
        return f"{self.marca.nombre} - {self.escenario.nombre} - {self.anio} ({self.get_metodo_display()})"

    def calcular_ventas_mensuales(self):
        """Calcula las ventas mensuales según el método configurado"""
        if self.metodo == 'manual':
            return self._calcular_manual()
        elif self.metodo == 'crecimiento':
            return self._calcular_crecimiento()
        elif self.metodo == 'precio_unidades':
            return self._calcular_precio_unidades()
        elif self.metodo == 'canal':
            return self._calcular_canal()
        elif self.metodo == 'penetracion':
            return self._calcular_penetracion()
        return {}

    def _calcular_manual(self):
        """Obtiene ventas de ProyeccionManual"""
        try:
            manual = self.proyeccion_manual
            return manual.get_ventas_mensuales()
        except ProyeccionManual.DoesNotExist:
            return {}

    def _calcular_crecimiento(self):
        """Calcula ventas basado en crecimiento sobre base"""
        try:
            crec = self.proyeccion_crecimiento
            return crec.calcular_ventas_mensuales()
        except ProyeccionCrecimiento.DoesNotExist:
            return {}

    def _calcular_precio_unidades(self):
        """Suma ventas de todos los productos/categorías"""
        detalles = self.proyecciones_producto.all()
        ventas = {}
        meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

        for mes in meses:
            ventas[mes] = sum(
                float(getattr(d, f'unidades_{mes}', 0) or 0) * float(d.precio_unitario)
                for d in detalles
            )
        return ventas

    def _calcular_canal(self):
        """Suma ventas de todos los canales"""
        detalles = self.proyecciones_canal.all()
        ventas = {}
        meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

        for mes in meses:
            ventas[mes] = sum(
                float(getattr(d, mes, 0) or 0)
                for d in detalles
            )
        return ventas

    def _calcular_penetracion(self):
        """Calcula ventas basado en penetración de mercado"""
        try:
            pene = self.proyeccion_penetracion
            return pene.calcular_ventas_mensuales()
        except ProyeccionPenetracion.DoesNotExist:
            return {}

    def get_venta_anual(self):
        """Retorna el total anual proyectado"""
        ventas = self.calcular_ventas_mensuales()
        return sum(ventas.values())


class ProyeccionManual(models.Model):
    """Proyección manual con vista anual compacta (12 meses en 1 registro)"""

    config = models.OneToOneField(
        ProyeccionVentasConfig,
        on_delete=models.CASCADE,
        related_name='proyeccion_manual',
        verbose_name="Configuración"
    )

    # Ventas por mes
    enero = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Enero")
    febrero = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Febrero")
    marzo = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Marzo")
    abril = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Abril")
    mayo = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Mayo")
    junio = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Junio")
    julio = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Julio")
    agosto = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Agosto")
    septiembre = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Septiembre")
    octubre = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Octubre")
    noviembre = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Noviembre")
    diciembre = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Diciembre")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_proyeccion_manual'
        verbose_name = "Proyección Manual"
        verbose_name_plural = "Proyecciones Manuales"

    def __str__(self):
        return f"Manual: {self.config}"

    def get_ventas_mensuales(self):
        """Retorna diccionario con ventas por mes"""
        return {
            'enero': float(self.enero),
            'febrero': float(self.febrero),
            'marzo': float(self.marzo),
            'abril': float(self.abril),
            'mayo': float(self.mayo),
            'junio': float(self.junio),
            'julio': float(self.julio),
            'agosto': float(self.agosto),
            'septiembre': float(self.septiembre),
            'octubre': float(self.octubre),
            'noviembre': float(self.noviembre),
            'diciembre': float(self.diciembre),
        }

    def get_total_anual(self):
        """Retorna el total anual"""
        return sum(self.get_ventas_mensuales().values())


class ProyeccionCrecimiento(models.Model):
    """Proyección basada en crecimiento sobre una base"""

    config = models.OneToOneField(
        ProyeccionVentasConfig,
        on_delete=models.CASCADE,
        related_name='proyeccion_crecimiento',
        verbose_name="Configuración"
    )

    ventas_base_anual = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Ventas Base Anual",
        help_text="Valor de ventas del año base (año anterior o referencia)"
    )
    anio_base = models.IntegerField(
        verbose_name="Año Base",
        help_text="Año de referencia para el crecimiento"
    )
    factor_crecimiento = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(-100), MaxValueValidator(500)],
        verbose_name="Factor de Crecimiento %",
        help_text="Porcentaje de crecimiento esperado (ej: 10 para 10%, -5 para decrecimiento)"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_proyeccion_crecimiento'
        verbose_name = "Proyección por Crecimiento"
        verbose_name_plural = "Proyecciones por Crecimiento"

    def __str__(self):
        return f"Crecimiento: {self.config} ({self.factor_crecimiento}%)"

    def get_venta_anual_proyectada(self):
        """Calcula la venta anual aplicando el factor de crecimiento"""
        factor = 1 + (float(self.factor_crecimiento) / 100)
        return float(self.ventas_base_anual) * factor

    def calcular_ventas_mensuales(self):
        """Distribuye la venta anual según la plantilla estacional"""
        venta_anual = self.get_venta_anual_proyectada()

        # Usar plantilla estacional si existe
        if self.config.plantilla_estacional:
            distribucion = self.config.plantilla_estacional.get_distribucion()
        else:
            # Distribución uniforme
            distribucion = {mes: 1/12 for mes in [
                'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
            ]}

        return {mes: venta_anual * pct for mes, pct in distribucion.items()}


class ProyeccionProducto(models.Model):
    """Proyección por producto/categoría con precio × unidades"""

    TIPO_CHOICES = [
        ('producto', 'Producto (SKU)'),
        ('categoria', 'Categoría'),
    ]

    config = models.ForeignKey(
        ProyeccionVentasConfig,
        on_delete=models.CASCADE,
        related_name='proyecciones_producto',
        verbose_name="Configuración"
    )

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo")
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='proyecciones',
        verbose_name="Producto",
        help_text="Seleccionar si tipo es 'Producto'"
    )
    categoria = models.ForeignKey(
        CategoriaProducto,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='proyecciones',
        verbose_name="Categoría",
        help_text="Seleccionar si tipo es 'Categoría'"
    )
    precio_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Precio Unitario",
        help_text="Precio por unidad (se auto-completa del producto/categoría)"
    )

    # Unidades por mes
    unidades_enero = models.IntegerField(default=0, verbose_name="Unid. Enero")
    unidades_febrero = models.IntegerField(default=0, verbose_name="Unid. Febrero")
    unidades_marzo = models.IntegerField(default=0, verbose_name="Unid. Marzo")
    unidades_abril = models.IntegerField(default=0, verbose_name="Unid. Abril")
    unidades_mayo = models.IntegerField(default=0, verbose_name="Unid. Mayo")
    unidades_junio = models.IntegerField(default=0, verbose_name="Unid. Junio")
    unidades_julio = models.IntegerField(default=0, verbose_name="Unid. Julio")
    unidades_agosto = models.IntegerField(default=0, verbose_name="Unid. Agosto")
    unidades_septiembre = models.IntegerField(default=0, verbose_name="Unid. Septiembre")
    unidades_octubre = models.IntegerField(default=0, verbose_name="Unid. Octubre")
    unidades_noviembre = models.IntegerField(default=0, verbose_name="Unid. Noviembre")
    unidades_diciembre = models.IntegerField(default=0, verbose_name="Unid. Diciembre")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_proyeccion_producto'
        verbose_name = "Proyección por Producto"
        verbose_name_plural = "Proyecciones por Producto"

    def __str__(self):
        if self.tipo == 'producto' and self.producto:
            return f"{self.producto.nombre}"
        elif self.tipo == 'categoria' and self.categoria:
            return f"{self.categoria.nombre}"
        return f"Proyección Producto #{self.pk}"

    def get_unidades_mensuales(self):
        """Retorna diccionario con unidades por mes"""
        return {
            'enero': self.unidades_enero,
            'febrero': self.unidades_febrero,
            'marzo': self.unidades_marzo,
            'abril': self.unidades_abril,
            'mayo': self.unidades_mayo,
            'junio': self.unidades_junio,
            'julio': self.unidades_julio,
            'agosto': self.unidades_agosto,
            'septiembre': self.unidades_septiembre,
            'octubre': self.unidades_octubre,
            'noviembre': self.unidades_noviembre,
            'diciembre': self.unidades_diciembre,
        }

    def get_ventas_mensuales(self):
        """Calcula ventas = precio × unidades por mes"""
        unidades = self.get_unidades_mensuales()
        precio = float(self.precio_unitario)
        return {mes: unid * precio for mes, unid in unidades.items()}

    def get_total_unidades(self):
        """Total de unidades en el año"""
        return sum(self.get_unidades_mensuales().values())

    def get_total_ventas(self):
        """Total de ventas en el año"""
        return sum(self.get_ventas_mensuales().values())


class ProyeccionCanal(models.Model):
    """Proyección de ventas por canal"""

    config = models.ForeignKey(
        ProyeccionVentasConfig,
        on_delete=models.CASCADE,
        related_name='proyecciones_canal',
        verbose_name="Configuración"
    )
    canal = models.ForeignKey(
        CanalVenta,
        on_delete=models.CASCADE,
        related_name='proyecciones',
        verbose_name="Canal de Venta"
    )

    # Ventas por mes para este canal
    enero = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Enero")
    febrero = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Febrero")
    marzo = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Marzo")
    abril = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Abril")
    mayo = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Mayo")
    junio = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Junio")
    julio = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Julio")
    agosto = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Agosto")
    septiembre = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Septiembre")
    octubre = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Octubre")
    noviembre = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Noviembre")
    diciembre = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Diciembre")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_proyeccion_canal'
        verbose_name = "Proyección por Canal"
        verbose_name_plural = "Proyecciones por Canal"
        unique_together = ['config', 'canal']

    def __str__(self):
        return f"{self.canal.nombre}: {self.config}"

    def get_ventas_mensuales(self):
        """Retorna diccionario con ventas por mes"""
        return {
            'enero': float(self.enero),
            'febrero': float(self.febrero),
            'marzo': float(self.marzo),
            'abril': float(self.abril),
            'mayo': float(self.mayo),
            'junio': float(self.junio),
            'julio': float(self.julio),
            'agosto': float(self.agosto),
            'septiembre': float(self.septiembre),
            'octubre': float(self.octubre),
            'noviembre': float(self.noviembre),
            'diciembre': float(self.diciembre),
        }

    def get_total_anual(self):
        """Total anual para este canal"""
        return sum(self.get_ventas_mensuales().values())


class ProyeccionPenetracion(models.Model):
    """Proyección basada en penetración de mercado"""

    config = models.OneToOneField(
        ProyeccionVentasConfig,
        on_delete=models.CASCADE,
        related_name='proyeccion_penetracion',
        verbose_name="Configuración"
    )
    mercado = models.ForeignKey(
        DefinicionMercado,
        on_delete=models.CASCADE,
        related_name='proyecciones',
        verbose_name="Mercado Objetivo"
    )

    penetracion_inicial = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Penetración Inicial %",
        help_text="Porcentaje del mercado que se espera capturar al inicio del año (0-100)"
    )
    penetracion_final = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Penetración Final %",
        help_text="Porcentaje del mercado que se espera capturar al final del año (0-100)"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dxv_proyeccion_penetracion'
        verbose_name = "Proyección por Penetración"
        verbose_name_plural = "Proyecciones por Penetración"

    def __str__(self):
        return f"Penetración: {self.config} - {self.mercado.nombre}"

    def get_venta_anual_proyectada(self):
        """Calcula ventas basado en penetración promedio del mercado"""
        tamano = float(self.mercado.tamano_mercado)
        penetracion_promedio = (float(self.penetracion_inicial) + float(self.penetracion_final)) / 2 / 100
        return tamano * penetracion_promedio

    def calcular_ventas_mensuales(self):
        """Distribuye ventas con crecimiento gradual de penetración"""
        tamano = float(self.mercado.tamano_mercado)
        pct_inicial = float(self.penetracion_inicial) / 100
        pct_final = float(self.penetracion_final) / 100
        incremento_mensual = (pct_final - pct_inicial) / 11  # 11 incrementos para 12 meses

        meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

        # Usar plantilla estacional si existe, sino distribución uniforme
        if self.config.plantilla_estacional:
            distribucion = self.config.plantilla_estacional.get_distribucion()
            venta_anual = self.get_venta_anual_proyectada()
            return {mes: venta_anual * distribucion[mes] for mes in meses}
        else:
            # Sin plantilla: crecimiento lineal de penetración
            ventas = {}
            for i, mes in enumerate(meses):
                penetracion_mes = pct_inicial + (incremento_mensual * i)
                ventas[mes] = (tamano * penetracion_mes) / 12
            return ventas
