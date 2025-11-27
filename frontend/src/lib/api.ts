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

export interface Marca {
  marca_id: string;
  nombre: string;
  ventas_mensuales: number;
  ventas_netas_mensuales?: number;
  descuento_pie_factura?: number;
  rebate?: number;
  descuento_financiero?: number;
  porcentaje_descuento_total?: number;
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
  combustible_mensual: number;
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
  pernocta_mensual: number;
  total_mensual: number;
  detalle: any;
}

export interface DetalleLejaniasComercial {
  marca_id: string;
  marca_nombre: string;
  escenario_id: number;
  escenario_nombre: string;
  total_combustible_mensual: number;
  total_pernocta_mensual: number;
  total_mensual: number;
  total_anual: number;
  zonas: DetalleZonaComercial[];
}

export interface DetalleLejaniasLogistica {
  marca_id: string;
  marca_nombre: string;
  escenario_id: number;
  escenario_nombre: string;
  total_flete_base_mensual: number;
  total_combustible_mensual: number;
  total_peaje_mensual: number;
  total_pernocta_mensual: number;
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
   */
  async ejecutarSimulacion(marcas: string[], escenarioId?: number): Promise<SimulacionResult> {
    let url = '/api/simulate';
    if (escenarioId) {
      url += `?escenario_id=${escenarioId}`;
    }
    return this.request<SimulacionResult>(url, {
      method: 'POST',
      body: JSON.stringify(marcas),
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
    marcaId: string
  ): Promise<DetalleLejaniasComercial> {
    return this.request<DetalleLejaniasComercial>(
      `/api/lejanias/comercial?escenario_id=${escenarioId}&marca_id=${marcaId}`
    );
  }

  /**
   * Obtiene detalle de lejanías logísticas
   */
  async obtenerDetalleLejaniasLogistica(
    escenarioId: number,
    marcaId: string
  ): Promise<DetalleLejaniasLogistica> {
    return this.request<DetalleLejaniasLogistica>(
      `/api/lejanias/logistica?escenario_id=${escenarioId}&marca_id=${marcaId}`
    );
  }
}

export const apiClient = new APIClient();
