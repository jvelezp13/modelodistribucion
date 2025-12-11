/**
 * API Client para comunicarse con el backend FastAPI
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Debug: Log de la URL del API
if (typeof window !== 'undefined') {
  console.log('🔗 API URL configurada:', API_URL);
  console.log('🔗 NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL);
}

export interface Escenario {
  id: number;
  nombre: string;
  anio: number;
  tipo: string;
  activo: boolean;
  periodo: string;
}

export interface Operacion {
  id: number;
  nombre: string;
  codigo: string;
  activa: boolean;
  color?: string;
  tasa_ica: number;  // Porcentaje 0-100
  venta_total?: number;  // Suma de venta_proyectada de MarcaOperacion
  municipio_base?: string;  // Nombre del municipio base
  cantidad_zonas: number;
  cantidad_marcas: number;
}

export interface OperacionesResponse {
  escenario_id: number;
  escenario_nombre: string;
  operaciones: Operacion[];
}

export interface MarcaBasica {
  id: number;
  marca_id: string;
  nombre: string;
  operaciones: Array<{
    id: number;
    nombre: string;
    codigo: string;
  }>;
}

export interface MarcasPorOperacionesResponse {
  escenario_id: number;
  escenario_nombre: string;
  filtro_operaciones: string | null;
  marcas: MarcaBasica[];
}

// Meses en español para el selector
export const MESES = [
  { value: 'enero', label: 'Enero' },
  { value: 'febrero', label: 'Febrero' },
  { value: 'marzo', label: 'Marzo' },
  { value: 'abril', label: 'Abril' },
  { value: 'mayo', label: 'Mayo' },
  { value: 'junio', label: 'Junio' },
  { value: 'julio', label: 'Julio' },
  { value: 'agosto', label: 'Agosto' },
  { value: 'septiembre', label: 'Septiembre' },
  { value: 'octubre', label: 'Octubre' },
  { value: 'noviembre', label: 'Noviembre' },
  { value: 'diciembre', label: 'Diciembre' },
];

// Función para obtener el mes actual en español
export function getMesActual(): string {
  const mesesMap = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
  ];
  return mesesMap[new Date().getMonth()];
}

export interface VentasMensualesDesglose {
  enero?: number;
  febrero?: number;
  marzo?: number;
  abril?: number;
  mayo?: number;
  junio?: number;
  julio?: number;
  agosto?: number;
  septiembre?: number;
  octubre?: number;
  noviembre?: number;
  diciembre?: number;
}

export interface TramoDescuento {
  orden: number;
  porcentaje_ventas: number;
  porcentaje_descuento: number;
}

export interface ConfiguracionDescuentos {
  tiene_configuracion: boolean;
  descuento_pie_factura_ponderado: number;  // Porcentaje ponderado de todos los tramos
  tramos: TramoDescuento[];
  porcentaje_rebate: number;
  aplica_descuento_financiero: boolean;
  porcentaje_descuento_financiero: number;
  aplica_cesantia_comercial: boolean;  // Art. 1324 C.Co. - 1/12 de ingresos del agente
}

// ICA por operación individual
export interface IcaPorOperacion {
  operacion_id: number;
  operacion_nombre: string;
  operacion_codigo: string;
  venta_proyectada: number;
  tasa_ica: number;  // Porcentaje 0-100
  ica_calculado: number;
}

export interface Marca {
  marca_id: string;
  nombre: string;
  ventas_mensuales: number;
  ventas_netas_mensuales?: number;
  ventas_mensuales_desglose?: VentasMensualesDesglose;
  configuracion_descuentos?: ConfiguracionDescuentos;
  // ICA - Nuevo modelo por operaciones
  tasa_ica?: number;  // Tasa ICA ponderada (decimal 0-1)
  ica_por_operacion?: IcaPorOperacion[];  // Desglose por operación
  ica_total?: number;  // Suma total de ICA
  // Campos legacy (pueden eliminarse después)
  descuento_pie_factura?: number;
  rebate?: number;
  descuento_financiero?: number;
  porcentaje_descuento_total?: number;
  // Costos
  costo_total: number;
  costo_comercial: number;
  costo_logistico: number;
  costo_administrativo: number;
  lejania_comercial?: number;
  lejania_logistica?: number;
  margen_porcentaje: number;
  total_empleados: number;
  empleados_comerciales: number;
  empleados_logisticos: number;
  rubros_individuales: Rubro[];
  rubros_compartidos_asignados: Rubro[];
}

export interface Rubro {
  id: string;
  nombre: string;
  categoria: string;
  tipo: string;
  valor_total: number;
  cantidad?: number;
  valor_unitario?: number;
  tipo_asignacion?: string;
  criterio_prorrateo?: string;

  // Campos para personal
  salario_base?: number;
  prestaciones?: number;
  subsidio_transporte?: number;
  factor_prestacional?: number;
  // Auxilios no prestacionales (JSON flexible)
  auxilios_no_prestacionales?: {
    cuota_carro?: number;
    arriendo_vivienda?: number;
    bono_alimentacion?: number;
    rodamiento?: number;
    otros?: number;
    [key: string]: number | undefined;
  };
  total_auxilios_no_prestacionales?: number;
  // Campo legacy para retrocompatibilidad
  auxilio_adicional?: number;

  // Campos para vehículos (solo costos fijos)
  tipo_vehiculo?: string;
  esquema?: string;
  canon_mensual?: number;
  mantenimiento?: number;
  lavada?: number;
  reposicion?: number;
  depreciacion?: number;
  seguro?: number;
  impuestos?: number;
  monitoreo?: number;
  seguro_mercancia?: number;
}

export interface Consolidado {
  total_ventas_mensuales?: number; // backward compatibility
  total_ventas_brutas_mensuales?: number;
  total_ventas_netas_mensuales?: number;
  total_descuentos_mensuales?: number;
  porcentaje_descuento_promedio?: number;
  total_ventas_anuales: number;
  total_costos_mensuales: number;
  total_costos_anuales: number;
  margen_consolidado: number;
  total_empleados: number;
  costo_comercial_total: number;
  costo_logistico_total: number;
  costo_administrativo_total: number;
}

export interface SimulacionResult {
  consolidado: Consolidado;
  marcas: Marca[];
  rubros_compartidos: Rubro[];
  metadata: Record<string, any>;
  operaciones_filtradas?: number[];  // IDs de operaciones filtradas (si aplica)
}

export interface VentasData {
  marca_id: string;
  ventas_mensuales: Record<string, number>;
  resumen_anual: {
    total_ventas_anuales: number;
    promedio_mensual: number;
  };
}

export interface DetalleZonaComercial {
  zona_id: number;
  zona_nombre: string;
  vendedor: string;
  ciudad_base: string;
  tipo_vehiculo: string;
  frecuencia: string;
  requiere_pernocta: boolean;
  noches_pernocta: number;
  km_mensual: number;
  combustible_mensual: number;
  costos_adicionales_mensual: number;
  pernocta_mensual: number;
  total_mensual: number;
  detalle: any;
}

export interface DetalleRutaLogistica {
  ruta_id: number;
  ruta_nombre: string;
  ruta_codigo: string;
  vehiculo: string | null;
  vehiculo_id: number | null;
  esquema: string | null;
  tipo_vehiculo: string | null;
  frecuencia: string;
  requiere_pernocta: boolean;
  noches_pernocta: number;
  flete_base_mensual: number;
  combustible_mensual: number;
  peaje_mensual: number;
  pernocta_conductor_mensual: number;
  pernocta_auxiliar_mensual: number;
  parqueadero_mensual: number;
  pernocta_mensual: number;  // Total combinado
  total_mensual: number;
  detalle: any;
}

export interface DetalleComiteZona {
  zona_id: number;
  zona_nombre: string;
  vendedor: string;
  ciudad_base: string;
  tipo_vehiculo: string;
  distancia_km: number;
  viajes_mes: number;
  total_mensual: number;
}

export interface ComiteComercialData {
  municipio: string;
  frecuencia: string;
  viajes_mes: number;
  umbral_km: number;
  total_mensual: number;
  detalle_por_zona: DetalleComiteZona[];
}

export interface DetalleLejaniasComercial {
  marca_id: string;
  marca_nombre: string;
  escenario_id: number;
  escenario_nombre: string;
  total_km_mensual: number;
  total_combustible_mensual: number;
  total_costos_adicionales_mensual: number;
  total_pernocta_mensual: number;
  total_comite_mensual: number;
  total_mensual: number;
  total_anual: number;
  zonas: DetalleZonaComercial[];
  comite_comercial: ComiteComercialData | null;
}

export interface DetalleLejaniasLogistica {
  marca_id: string;
  marca_nombre: string;
  escenario_id: number;
  escenario_nombre: string;
  total_flete_base_mensual: number;
  total_combustible_mensual: number;
  total_peaje_mensual: number;
  total_pernocta_conductor_mensual: number;
  total_pernocta_auxiliar_mensual: number;
  total_parqueadero_mensual: number;
  total_auxiliar_empresa_mensual: number;  // Auxiliar siempre paga empresa
  total_pernocta_mensual: number;  // Total combinado
  total_mensual: number;
  total_anual: number;
  rutas: DetalleRutaLogistica[];
}

class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    console.log(`🌐 Fetching: ${url}`);

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      console.log(`📡 Response status: ${response.status} for ${url}`);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Error desconocido' }));
        console.error(`❌ API Error Response:`, error);
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      console.log(`✅ Success for ${endpoint}:`, data);
      return data;
    } catch (error) {
      console.error(`❌ API Error [${endpoint}]:`, error);
      console.error(`❌ Full URL attempted: ${url}`);
      throw error;
    }
  }

  /**
   * Lista todas las marcas activas
   */
  async listarMarcas(): Promise<string[]> {
    return this.request<string[]>('/api/marcas');
  }

  /**
   * Lista todos los escenarios disponibles
   */
  async listarEscenarios(): Promise<Escenario[]> {
    return this.request<Escenario[]>('/api/escenarios');
  }

  /**
   * Ejecuta la simulación para las marcas seleccionadas
   * @param marcas - Lista de IDs de marcas a simular
   * @param escenarioId - ID del escenario (opcional)
   * @param operacionIds - Lista de IDs de operaciones para filtrar (opcional)
   */
  async ejecutarSimulacion(
    marcas: string[],
    escenarioId?: number,
    operacionIds?: number[]
  ): Promise<SimulacionResult> {
    const url = `/api/simulate`;

    // El body incluye marcas, escenario_id y operacion_ids
    const body: {
      marcas_seleccionadas: string[];
      escenario_id?: number;
      operacion_ids?: number[]
    } = {
      marcas_seleccionadas: marcas,
    };
    if (escenarioId) {
      body.escenario_id = escenarioId;
    }
    if (operacionIds && operacionIds.length > 0) {
      body.operacion_ids = operacionIds;
    }

    return this.request<SimulacionResult>(url, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  /**
   * Obtiene datos comerciales de una marca (para debug)
   */
  async obtenerDatosComerciales(marcaId: string): Promise<any> {
    return this.request(`/api/marcas/${marcaId}/comercial`);
  }

  /**
   * Obtiene proyecciones de ventas de una marca
   */
  async obtenerDatosVentas(marcaId: string): Promise<VentasData> {
    return this.request<VentasData>(`/api/marcas/${marcaId}/ventas`);
  }

  /**
   * Obtiene detalle de lejanías comerciales
   */
  async obtenerDetalleLejaniasComercial(
    escenarioId: number,
    marcaId: string,
    operacionIds?: number[]
  ): Promise<DetalleLejaniasComercial> {
    let url = `/api/lejanias/comercial?escenario_id=${escenarioId}&marca_id=${marcaId}`;
    if (operacionIds && operacionIds.length > 0) {
      url += `&operacion_ids=${operacionIds.join(',')}`;
    }
    return this.request<DetalleLejaniasComercial>(url);
  }

  /**
   * Obtiene detalle de lejanías logísticas
   */
  async obtenerDetalleLejaniasLogistica(
    escenarioId: number,
    marcaId: string,
    operacionIds?: number[]
  ): Promise<DetalleLejaniasLogistica> {
    let url = `/api/lejanias/logistica?escenario_id=${escenarioId}&marca_id=${marcaId}`;
    if (operacionIds && operacionIds.length > 0) {
      url += `&operacion_ids=${operacionIds.join(',')}`;
    }
    return this.request<DetalleLejaniasLogistica>(url);
  }

  /**
   * Obtiene la tasa de impuesto de renta desde el backend
   */
  async obtenerTasaRenta(): Promise<TasaRentaResponse> {
    return this.request<TasaRentaResponse>('/api/impuestos/renta');
  }

  /**
   * Obtiene la tasa de ICA desde el backend
   */
  async obtenerTasaICA(): Promise<TasaICAResponse> {
    return this.request<TasaICAResponse>('/api/impuestos/ica');
  }

  /**
   * Obtiene el P&G desglosado por zonas para una marca
   */
  async obtenerPyGZonas(
    escenarioId: number,
    marcaId: string,
    operacionIds?: number[]
  ): Promise<PyGZonasResponse> {
    let url = `/api/pyg/zonas?escenario_id=${escenarioId}&marca_id=${marcaId}`;
    if (operacionIds && operacionIds.length > 0) {
      url += `&operacion_ids=${operacionIds.join(',')}`;
    }
    return this.request<PyGZonasResponse>(url);
  }

  /**
   * Obtiene el P&G desglosado por municipios para una zona
   */
  async obtenerPyGMunicipios(
    zonaId: number,
    escenarioId: number,
    marcaId: string
  ): Promise<PyGMunicipiosResponse> {
    return this.request<PyGMunicipiosResponse>(
      `/api/pyg/municipios?zona_id=${zonaId}&escenario_id=${escenarioId}&marca_id=${marcaId}`
    );
  }

  /**
   * Obtiene las zonas de una marca para el selector
   */
  async obtenerZonasMarca(
    escenarioId: number,
    marcaId: string
  ): Promise<ZonaBasica[]> {
    const response = await this.obtenerPyGZonas(escenarioId, marcaId);
    return response.zonas.map(z => ({
      id: z.zona.id,
      nombre: z.zona.nombre,
      participacion_ventas: z.zona.participacion_ventas
    }));
  }

  /**
   * Obtiene diagnóstico detallado del personal para validación
   */
  async obtenerDiagnosticoPersonal(
    escenarioId: number,
    marcaId: string
  ): Promise<DiagnosticoPersonalResponse> {
    return this.request<DiagnosticoPersonalResponse>(
      `/api/diagnostico/personal-detallado?escenario_id=${escenarioId}&marca_id=${marcaId}`
    );
  }

  /**
   * Obtiene comparación completa P&G Detallado vs P&G Zonas
   */
  async obtenerComparacionPyG(
    escenarioId: number,
    marcaId: string
  ): Promise<ComparacionPyGResponse> {
    return this.request<ComparacionPyGResponse>(
      `/api/diagnostico/comparar-pyg?escenario_id=${escenarioId}&marca_id=${marcaId}`
    );
  }

  /**
   * Obtiene diagnóstico detallado de costos logísticos por zona
   */
  async obtenerDiagnosticoLogistico(
    escenarioId: number,
    marcaId: string
  ): Promise<DiagnosticoLogisticoResponse> {
    return this.request<DiagnosticoLogisticoResponse>(
      `/api/diagnostico/logistico-detallado?escenario_id=${escenarioId}&marca_id=${marcaId}`
    );
  }

  /**
   * Obtiene las operaciones de un escenario
   */
  async obtenerOperaciones(escenarioId: number): Promise<OperacionesResponse> {
    return this.request<OperacionesResponse>(
      `/api/operaciones?escenario_id=${escenarioId}`
    );
  }

  /**
   * Obtiene las marcas filtradas por operaciones
   */
  async obtenerMarcasPorOperaciones(
    escenarioId: number,
    operacionIds?: number[]
  ): Promise<MarcasPorOperacionesResponse> {
    let url = `/api/marcas/por-operaciones?escenario_id=${escenarioId}`;
    if (operacionIds && operacionIds.length > 0) {
      url += `&operacion_ids=${operacionIds.join(',')}`;
    }
    return this.request<MarcasPorOperacionesResponse>(url);
  }

  /**
   * Obtiene la cascada de distribución de ventas
   * ProyeccionVentasConfig → MarcaOperacion → Zona → ZonaMunicipio
   */
  async obtenerDistribucionCascada(
    escenarioId: number,
    marcaId: string,
    operacionIds?: number[]
  ): Promise<DistribucionCascadaResponse> {
    let url = `/api/distribucion/cascada?escenario_id=${escenarioId}&marca_id=${marcaId}`;
    if (operacionIds && operacionIds.length > 0) {
      url += `&operacion_ids=${operacionIds.join(',')}`;
    }
    return this.request<DistribucionCascadaResponse>(url);
  }
}

// Interfaz para respuesta de tasa de renta
export interface TasaRentaResponse {
  configurado: boolean;
  tasa: number;           // En decimal (0.33)
  tasa_porcentaje: number; // En porcentaje (33)
  id?: number;
  nombre?: string;
  periodicidad?: string;
  mensaje?: string;
}

export interface TasaICAResponse {
  configurado: boolean;
  tasa: number;           // En decimal (0.0041)
  tasa_porcentaje: number; // En porcentaje (0.41)
  id?: number;
  nombre?: string;
  periodicidad?: string;
  mensaje?: string;
}

// Interfaces para P&G por Zonas y Municipios
export interface PyGCategoria {
  personal: number;
  gastos: number;
  lejanias?: number;  // Lejanías calculadas dinámicamente (comercial o logística)
  total: number;
}

export interface PyGZona {
  zona: {
    id: number;
    nombre: string;
    participacion_ventas: number;
    operacion?: {
      id: number;
      nombre: string;
      codigo: string;
    } | null;
    tasa_ica: number;  // Tasa ICA de la operación de esta zona
  };
  comercial: PyGCategoria;
  logistico: PyGCategoria;
  administrativo: PyGCategoria;
  total_mensual: number;
  total_anual: number;
}

export interface ConfigDescuentosZonas {
  descuento_pie_factura_ponderado: number;
  tramos: TramoDescuento[];
  porcentaje_rebate: number;
  aplica_descuento_financiero: boolean;
  porcentaje_descuento_financiero: number;
  aplica_cesantia_comercial: boolean;
}

export interface PyGZonasResponse {
  marca_id: string;
  marca_nombre: string;
  escenario_id: number;
  escenario_nombre: string;
  total_zonas: number;
  zonas: PyGZona[];
  ventas_mensuales: VentasMensualesDesglose;
  configuracion_descuentos: ConfigDescuentosZonas;
  tasa_impuesto_renta: number;
  // tasa_ica ahora está en cada zona (zona.tasa_ica)
}

export interface PyGMunicipio {
  municipio: {
    id: number;
    nombre: string;
    codigo_dane: string;
    venta_proyectada: number;  // Venta proyectada del municipio en esta zona
    participacion_zona: number;  // Peso relativo dentro de la zona (%)
    participacion_total: number;  // Peso sobre la marca total (%)
  };
  zona: {
    id: number;
    nombre: string;
  };
  comercial: PyGCategoria;
  logistico: PyGCategoria;
  administrativo: PyGCategoria;
  total_mensual: number;
  total_anual: number;
}

export interface PyGMunicipiosResponse {
  zona_id: number;
  zona_nombre: string;
  zona_participacion_ventas: number;
  escenario_id: number;
  escenario_nombre: string;
  marca_id: string;
  marca_nombre: string;
  total_municipios: number;
  municipios: PyGMunicipio[];
  ventas_mensuales: VentasMensualesDesglose;
  configuracion_descuentos: ConfigDescuentosZonas;
  tasa_impuesto_renta: number;
  tasa_ica: number;
}

export interface ZonaBasica {
  id: number;
  nombre: string;
  participacion_ventas: number;
}

// Interfaces para diagnóstico de personal
export interface PersonalItem {
  nombre: string;
  cantidad: number;
  salario_base: number;
  costo_unitario: number;
  costo_total: number;
  asignacion: 'directo' | 'proporcional' | 'compartido';
  zona_asignada: string | null;
  zona_destino: string;
  distribuido: number;
  perdido: number;
}

export interface GastoItem {
  nombre: string;
  valor: number;
  asignacion: 'directo' | 'proporcional' | 'compartido';
  zona_asignada: string | null;
  distribuido: number;
}

export interface PersonalResumen {
  items: PersonalItem[];
  total_costo: number;
  total_directo: number;
  total_proporcional: number;
  total_compartido: number;
  total_distribuido: number;
  diferencia: number;
}

export interface GastosResumen {
  items: GastoItem[];
  total: number;
  total_distribuido: number;
  diferencia: number;
}

export interface CategoriaResumen {
  personal: PersonalResumen;
  gastos: GastosResumen;
  total_categoria: number;
  total_distribuido: number;
  diferencia: number;
}

export interface DiagnosticoPersonalResponse {
  escenario: { id: number; nombre: string };
  marca: { id: string; nombre: string };
  zonas: {
    cantidad: number;
    suma_participaciones: number;
    lista: Array<{ id: number; nombre: string; participacion: number }>;
  };
  comercial: CategoriaResumen;
  logistico: CategoriaResumen;
  administrativo: CategoriaResumen;
}

// Interfaz para comparación P&G Detallado vs Zonas
export interface ComparacionPyGResponse {
  escenario: string;
  marca: string;
  suma_participaciones: number;
  pyg_detallado: {
    comercial: { personal: number; gastos: number; lejanias: number; total: number };
    logistico: { flota: number; personal: number; gastos: number; lejanias: number; total: number };
    administrativo: { personal: number; gastos: number; total: number };
    total: number;
  };
  pyg_zonas: {
    comercial: { personal: number; gastos: number; lejanias: number; total: number };
    logistico: { flota: number; personal: number; gastos: number; lejanias: number; total: number };
    administrativo: { personal: number; gastos: number; total: number };
    total: number;
  };
  diferencias: {
    comercial: Record<string, number>;
    logistico: Record<string, number>;
    administrativo: Record<string, number>;
    total: number;
  };
  alertas: Array<{
    categoria: string;
    campo: string;
    diferencia: number;
    valor_detallado: number;
    valor_zonas: number;
  }>;
  desglose: {
    flota_items: Array<{ nombre: string; esquema: string; cantidad: number; costo: number }>;
    flete_base: number;
    lejanias_log_desglose: { combustible: number; peajes: number; pernocta: number };
  };
  zonas_detalle: Array<{
    nombre: string;
    participacion: number;
    comercial: number;
    logistico: number;
    administrativo: number;
    total: number;
  }>;
}

// Interfaz para diagnóstico logístico detallado
export interface DiagnosticoLogisticoResponse {
  escenario: string;
  marca: string;
  resumen: {
    total_flota_simulador: number;
    total_flota_distribuida: number;
    total_personal_simulador: number;
    total_gastos_simulador: number;
    total_lejanias_simulador: number;
    total_costo_por_municipios: number;
    total_distribuido_a_zonas: number;
    diferencia_lejanias: number;
    diferencia_flota: number;
  };
  rubros_logisticos_simulador: Array<{
    nombre: string;
    tipo: string;
    valor: number;
    asignacion: string;
  }>;
  costos_por_municipio: Record<string, {
    municipio_nombre: string;
    flete_total: number;
    combustible_total: number;
    peaje_total: number;
    pernocta_total: number;
    costo_total: number;
    rutas: Array<{
      ruta_id: number;
      ruta_nombre: string;
      flete: number;
      combustible: number;
      peaje: number;
      pernocta: number;
    }>;
  }>;
  rutas_logisticas: Array<{
    ruta_id: number;
    ruta_nombre: string;
    vehiculo: string | null;
    vehiculo_id: number | null;
    esquema: string | null;
    frecuencia: string;
    viajes_por_periodo: number;
    recorridos_mensuales: number;
    municipios: Array<{
      orden: number;
      municipio_id: number;
      municipio_nombre: string;
      flete_base: number;
      zonas_que_lo_atienden: Array<{
        zona_id: number;
        zona_nombre: string;
        venta_proyectada: number;
      }>;
      cantidad_zonas: number;
    }>;
  }>;
  distribucion_a_zonas: Array<{
    zona_id: number;
    zona_nombre: string;
    participacion_ventas: number;
    flete_fijo_asignado: number;
    lejanias_asignado: number;
    costo_logistico_asignado: number;
    costo_flota_asignado: number;
    costo_total_asignado: number;
    municipios_con_costo: Array<{
      municipio_id: number;
      municipio_nombre: string;
      costo_total_municipio: number;
      flete_fijo: number;
      lejanias: number;
      venta_zona: number;
      venta_total: number;
      proporcion: number;
      flete_asignado: number;
      lejanias_asignado: number;
      costo_asignado: number;
    }>;
    vehiculos_con_costo: Array<{
      vehiculo_id: number;
      vehiculo_nombre: string;
      costo_vehiculo: number;
      metodo: string;
      costo_asignado: number;
    }>;
  }>;
}

// Interfaces para Distribución de Ventas (Cascada)
export interface MunicipioDistribucion {
  id: number;
  municipio_id: number;
  nombre: string;
  departamento: string;
  participacion_ventas: number;
  venta_proyectada: number;
}

export interface ZonaDistribucion {
  id: number;
  nombre: string;
  participacion_ventas: number;
  venta_proyectada: number;
  municipios: MunicipioDistribucion[];
  municipios_count: number;
  validacion: {
    suma_participaciones: number;
    es_valido: boolean;
  };
}

export interface OperacionDistribucion {
  id: number;
  operacion_id: number;
  nombre: string;
  codigo: string;
  participacion_ventas: number;
  venta_proyectada: number;
  zonas: ZonaDistribucion[];
  zonas_count: number;
  validacion: {
    suma_participaciones: number;
    es_valido: boolean;
  };
}

export interface DistribucionCascadaResponse {
  marca: {
    id: number;
    marca_id: string;
    nombre: string;
    venta_total_mensual: number;
    ventas_mensuales: VentasMensualesDesglose;
  };
  escenario: {
    id: number;
    nombre: string;
    anio: number;
  };
  operaciones: OperacionDistribucion[];
  validacion: {
    suma_participaciones_operaciones: number;
    operaciones_valido: boolean;
  };
}

export const apiClient = new APIClient();
