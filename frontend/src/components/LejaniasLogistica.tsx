'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { apiClient, DetalleLejaniasLogistica, DetalleRutaLogistica } from '@/lib/api';
import { ChevronDown, ChevronRight, MapPin, Truck, DollarSign, Fuel, Route, ArrowRight } from 'lucide-react';

interface LejaniasLogisticaProps {
  escenarioId: number;
  marcaId: string;
}

type VistaType = 'recorrido' | 'vehiculo';

interface VehiculoAgrupado {
  vehiculo_id: number;
  vehiculo: string;
  esquema: string | null;
  tipo_vehiculo: string | null;
  recorridos: DetalleRutaLogistica[];
  total_flete_base: number;
  total_combustible: number;
  total_peaje: number;
  total_pernocta_conductor: number;
  total_pernocta_auxiliar: number;
  total_parqueadero: number;
  total_pernocta: number;
  total_mensual: number;
}

export default function LejaniasLogistica({ escenarioId, marcaId }: LejaniasLogisticaProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [datos, setDatos] = useState<DetalleLejaniasLogistica | null>(null);
  const [recorridosExpandidos, setRecorridosExpandidos] = useState<Set<number>>(new Set());
  const [vehiculosExpandidos, setVehiculosExpandidos] = useState<Set<number>>(new Set());
  const [vistaActiva, setVistaActiva] = useState<VistaType>('recorrido');

  useEffect(() => {
    cargarDatos();
  }, [escenarioId, marcaId]);

  const cargarDatos = async () => {
    try {
      setLoading(true);
      setError(null);
      const resultado = await apiClient.obtenerDetalleLejaniasLogistica(escenarioId, marcaId);
      setDatos(resultado);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error cargando datos');
    } finally {
      setLoading(false);
    }
  };

  // Agrupar recorridos por vehículo
  const vehiculosAgrupados = useMemo(() => {
    if (!datos) return [];

    const vehiculoMap = new Map<number, VehiculoAgrupado>();

    for (const recorrido of datos.rutas) {
      const vehiculoId = recorrido.vehiculo_id || 0;

      if (!vehiculoMap.has(vehiculoId)) {
        vehiculoMap.set(vehiculoId, {
          vehiculo_id: vehiculoId,
          vehiculo: recorrido.vehiculo || 'Sin vehículo',
          esquema: recorrido.esquema,
          tipo_vehiculo: recorrido.tipo_vehiculo,
          recorridos: [],
          total_flete_base: 0,
          total_combustible: 0,
          total_peaje: 0,
          total_pernocta_conductor: 0,
          total_pernocta_auxiliar: 0,
          total_parqueadero: 0,
          total_pernocta: 0,
          total_mensual: 0,
        });
      }

      const vehiculo = vehiculoMap.get(vehiculoId)!;
      vehiculo.recorridos.push(recorrido);
      vehiculo.total_flete_base += recorrido.flete_base_mensual;
      vehiculo.total_combustible += recorrido.combustible_mensual;
      vehiculo.total_peaje += recorrido.peaje_mensual;
      vehiculo.total_pernocta_conductor += recorrido.pernocta_conductor_mensual || 0;
      vehiculo.total_pernocta_auxiliar += recorrido.pernocta_auxiliar_mensual || 0;
      vehiculo.total_parqueadero += recorrido.parqueadero_mensual || 0;
      vehiculo.total_pernocta += recorrido.pernocta_mensual;
      vehiculo.total_mensual += recorrido.total_mensual;
    }

    return Array.from(vehiculoMap.values()).sort((a, b) => b.total_mensual - a.total_mensual);
  }, [datos]);

  const toggleRecorrido = (recorridoId: number) => {
    const nuevosExpandidos = new Set(recorridosExpandidos);
    if (nuevosExpandidos.has(recorridoId)) {
      nuevosExpandidos.delete(recorridoId);
    } else {
      nuevosExpandidos.add(recorridoId);
    }
    setRecorridosExpandidos(nuevosExpandidos);
  };

  const toggleVehiculo = (vehiculoId: number) => {
    const nuevosExpandidos = new Set(vehiculosExpandidos);
    if (nuevosExpandidos.has(vehiculoId)) {
      nuevosExpandidos.delete(vehiculoId);
    } else {
      nuevosExpandidos.add(vehiculoId);
    }
    setVehiculosExpandidos(nuevosExpandidos);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const getEsquemaLabel = (esquema: string | null) => {
    switch (esquema) {
      case 'tradicional': return 'Propio';
      case 'renting': return 'Renting';
      case 'tercero': return 'Tercero';
      default: return esquema || 'N/A';
    }
  };

  const getEsquemaColor = (esquema: string | null) => {
    switch (esquema) {
      case 'tradicional': return 'bg-blue-100 text-blue-800';
      case 'renting': return 'bg-green-100 text-green-800';
      case 'tercero': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Cargando datos de recorridos logísticos...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded p-4">
        <p className="text-red-800">Error: {error}</p>
      </div>
    );
  }

  if (!datos || datos.rutas.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded p-4">
        <p className="text-yellow-800">No hay recorridos logísticos configurados para esta marca.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header con totales */}
      <div className="bg-white border border-gray-200 rounded p-4">
        <h2 className="text-lg font-bold text-gray-800 mb-3">
          Recorridos Logísticos - {datos.marca_nombre}
        </h2>
        <div className="grid grid-cols-8 gap-3">
          <div>
            <div className="text-xs text-gray-500">Flete Base</div>
            <div className="text-sm font-semibold text-orange-600">
              {formatCurrency(datos.total_flete_base_mensual)}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Combustible</div>
            <div className="text-sm font-semibold text-blue-600">
              {formatCurrency(datos.total_combustible_mensual)}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Peajes</div>
            <div className="text-sm font-semibold text-yellow-600">
              {formatCurrency(datos.total_peaje_mensual)}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Pernocta (Vehículo)</div>
            <div className="text-sm font-semibold text-purple-600">
              {formatCurrency((datos.total_pernocta_conductor_mensual || 0) + (datos.total_parqueadero_mensual || 0))}
            </div>
            <div className="text-[10px] text-gray-400 mt-0.5">
              <span>Cond: {formatCurrency(datos.total_pernocta_conductor_mensual || 0)}</span>
              <span className="mx-1">|</span>
              <span>Parq: {formatCurrency(datos.total_parqueadero_mensual || 0)}</span>
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Auxiliar (Empresa)</div>
            <div className="text-sm font-semibold text-teal-600">
              {formatCurrency(datos.total_auxiliar_empresa_mensual || 0)}
            </div>
            <div className="text-[10px] text-gray-400 mt-0.5">
              Siempre paga empresa
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Pernocta Total</div>
            <div className="text-sm font-semibold text-purple-800">
              {formatCurrency(datos.total_pernocta_mensual)}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Total Mensual</div>
            <div className="text-sm font-semibold text-gray-900">
              {formatCurrency(datos.total_mensual)}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Total Anual</div>
            <div className="text-sm font-semibold text-green-600">
              {formatCurrency(datos.total_anual)}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        <button
          onClick={() => setVistaActiva('recorrido')}
          className={`px-4 py-2 text-sm font-medium rounded-t transition-colors ${
            vistaActiva === 'recorrido'
              ? 'bg-gray-700 text-white'
              : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
          }`}
        >
          Por Recorrido ({datos.rutas.length})
        </button>
        <button
          onClick={() => setVistaActiva('vehiculo')}
          className={`px-4 py-2 text-sm font-medium rounded-t transition-colors ${
            vistaActiva === 'vehiculo'
              ? 'bg-gray-700 text-white'
              : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
          }`}
        >
          Por Vehículo ({vehiculosAgrupados.length})
        </button>
      </div>

      {/* Vista por Recorrido */}
      {vistaActiva === 'recorrido' && (
        <div className="bg-white border border-gray-200 rounded">
          <div className="bg-gray-700 text-white px-4 py-2">
            <span className="text-xs font-semibold uppercase tracking-wide">
              Recorridos Logísticos ({datos.rutas.length})
            </span>
          </div>

          {datos.rutas.map((recorrido) => {
            const expandido = recorridosExpandidos.has(recorrido.ruta_id);

            return (
              <div key={recorrido.ruta_id} className="border-b border-gray-200 last:border-b-0">
                {/* Header de recorrido */}
                <div
                  className="px-4 py-3 hover:bg-gray-50 cursor-pointer"
                  onClick={() => toggleRecorrido(recorrido.ruta_id)}
                >
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-3">
                      {expandido ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-gray-900">
                            {recorrido.ruta_nombre}
                          </span>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${getEsquemaColor(recorrido.esquema)}`}>
                            {getEsquemaLabel(recorrido.esquema)}
                          </span>
                        </div>
                        <div className="flex gap-4 mt-1 text-xs text-gray-600">
                          <span className="flex items-center gap-1">
                            <Truck size={12} />
                            {recorrido.vehiculo || 'Sin vehículo'}
                          </span>
                          <span className="flex items-center gap-1">
                            <Route size={12} />
                            {recorrido.frecuencia} ({recorrido.detalle?.recorridos_por_periodo || 1}x)
                          </span>
                          <span className="flex items-center gap-1">
                            <MapPin size={12} />
                            {recorrido.detalle?.municipios?.length || 0} municipios
                          </span>
                          {recorrido.detalle?.distancia_circuito_km != null && (
                            <span className="text-blue-600 font-medium">
                              {Number(recorrido.detalle.distancia_circuito_km).toFixed(1)} km/circuito
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-semibold text-gray-900">
                        {formatCurrency(recorrido.total_mensual)}
                      </div>
                      <div className="text-xs text-gray-500">mensual</div>
                    </div>
                  </div>
                </div>

                {/* Detalle de recorrido expandido */}
                {expandido && (
                  <DetalleRecorrido recorrido={recorrido} formatCurrency={formatCurrency} getEsquemaColor={getEsquemaColor} />
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Vista por Vehículo */}
      {vistaActiva === 'vehiculo' && (
        <div className="bg-white border border-gray-200 rounded">
          <div className="bg-gray-700 text-white px-4 py-2">
            <span className="text-xs font-semibold uppercase tracking-wide">
              Vehículos ({vehiculosAgrupados.length})
            </span>
          </div>

          {vehiculosAgrupados.map((vehiculo) => {
            const expandido = vehiculosExpandidos.has(vehiculo.vehiculo_id);

            return (
              <div key={vehiculo.vehiculo_id} className="border-b border-gray-200 last:border-b-0">
                {/* Header de vehículo */}
                <div
                  className="px-4 py-3 hover:bg-gray-50 cursor-pointer"
                  onClick={() => toggleVehiculo(vehiculo.vehiculo_id)}
                >
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-3">
                      {expandido ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                      <div>
                        <div className="flex items-center gap-2">
                          <Truck size={16} className="text-gray-600" />
                          <span className="text-sm font-semibold text-gray-900">
                            {vehiculo.vehiculo}
                          </span>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${getEsquemaColor(vehiculo.esquema)}`}>
                            {getEsquemaLabel(vehiculo.esquema)}
                          </span>
                          <span className="text-xs text-gray-500">
                            ({vehiculo.tipo_vehiculo || 'N/A'})
                          </span>
                        </div>
                        <div className="flex gap-4 mt-1 text-xs text-gray-600">
                          <span className="flex items-center gap-1">
                            <Route size={12} />
                            {vehiculo.recorridos.length} recorrido(s)
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-semibold text-gray-900">
                        {formatCurrency(vehiculo.total_mensual)}
                      </div>
                      <div className="text-xs text-gray-500">mensual</div>
                    </div>
                  </div>
                </div>

                {/* Detalle de vehículo expandido */}
                {expandido && (
                  <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
                    {/* Totales del vehículo */}
                    <div className="grid grid-cols-5 gap-4 mb-4 p-3 bg-white rounded border border-gray-200">
                      <div>
                        <div className="text-xs text-gray-500">Flete Base</div>
                        <div className="text-sm font-medium text-orange-600">
                          {formatCurrency(vehiculo.total_flete_base)}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500">Combustible</div>
                        <div className="text-sm font-medium text-blue-600">
                          {formatCurrency(vehiculo.total_combustible)}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500">Peajes</div>
                        <div className="text-sm font-medium text-yellow-600">
                          {formatCurrency(vehiculo.total_peaje)}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500">Pernocta</div>
                        <div className="text-sm font-medium text-purple-600">
                          {formatCurrency(vehiculo.total_pernocta)}
                        </div>
                        {vehiculo.total_pernocta > 0 && (
                          <div className="text-[10px] text-gray-400 mt-0.5">
                            <span>Cond: {formatCurrency(vehiculo.total_pernocta_conductor)}</span>
                            <span className="mx-1">|</span>
                            <span>Aux: {formatCurrency(vehiculo.total_pernocta_auxiliar)}</span>
                          </div>
                        )}
                      </div>
                      <div>
                        <div className="text-xs text-gray-500">Parqueadero</div>
                        <div className="text-sm font-medium text-gray-600">
                          {formatCurrency(vehiculo.total_parqueadero)}
                        </div>
                      </div>
                    </div>

                    {/* Lista de recorridos del vehículo */}
                    <div className="text-xs font-semibold text-gray-700 mb-2">
                      Recorridos de este vehículo ({vehiculo.recorridos.length})
                    </div>
                    <div className="space-y-2">
                      {vehiculo.recorridos.map((recorrido) => (
                        <div key={recorrido.ruta_id} className="p-3 bg-white rounded border border-gray-200">
                          <div className="flex justify-between items-start">
                            <div>
                              <div className="text-sm font-medium text-gray-900">
                                {recorrido.ruta_nombre}
                              </div>
                              <div className="flex gap-3 mt-1 text-xs text-gray-500">
                                <span>{recorrido.frecuencia}</span>
                                <span>{recorrido.detalle?.municipios?.length || 0} municipios</span>
                                <span>{recorrido.detalle?.distancia_circuito_km?.toFixed(1) || 0} km</span>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-sm font-semibold text-gray-900">
                                {formatCurrency(recorrido.total_mensual)}
                              </div>
                              <div className="text-[10px] text-gray-400 mt-1">
                                <div>Flete: {formatCurrency(recorrido.flete_base_mensual)}</div>
                                <div>Comb: {formatCurrency(recorrido.combustible_mensual)}</div>
                                <div>Peajes: {formatCurrency(recorrido.peaje_mensual)}</div>
                                {recorrido.pernocta_mensual > 0 && (
                                  <div>Pernocta: {formatCurrency(recorrido.pernocta_mensual)}</div>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Componente separado para el detalle del recorrido (para mantener el código limpio)
function DetalleRecorrido({
  recorrido,
  formatCurrency,
  getEsquemaColor
}: {
  recorrido: DetalleRutaLogistica;
  formatCurrency: (value: number) => string;
  getEsquemaColor: (esquema: string | null) => string;
}) {
  return (
    <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
      <div className="grid grid-cols-4 gap-4 mb-4">
        <div>
          <div className="text-xs text-gray-500">Flete Base</div>
          <div className="text-sm font-medium text-orange-600">
            {formatCurrency(recorrido.flete_base_mensual)}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500">Combustible</div>
          <div className="text-sm font-medium text-blue-600">
            {formatCurrency(recorrido.combustible_mensual)}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500">Peajes</div>
          <div className="text-sm font-medium text-yellow-600">
            {formatCurrency(recorrido.peaje_mensual)}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500">Pernocta Total</div>
          <div className="text-sm font-medium text-purple-600">
            {formatCurrency(recorrido.pernocta_mensual)}
          </div>
          {recorrido.pernocta_mensual > 0 && (
            <div className="text-[10px] text-gray-400 mt-0.5">
              <div>Cond: {formatCurrency(recorrido.pernocta_conductor_mensual || 0)}</div>
              <div>Aux: {formatCurrency(recorrido.pernocta_auxiliar_mensual || 0)}</div>
              <div>Parq: {formatCurrency(recorrido.parqueadero_mensual || 0)}</div>
            </div>
          )}
        </div>
      </div>

      {/* Info del vehículo y circuito */}
      {recorrido.detalle && (
        <div className="mb-4 p-2 bg-white rounded border border-gray-200">
          <div className="grid grid-cols-4 gap-2 text-xs mb-2">
            <div>
              <span className="text-gray-500">Bodega:</span>{' '}
              <span className="font-medium">{recorrido.detalle.bodega || 'N/A'}</span>
            </div>
            <div>
              <span className="text-gray-500">Tipo:</span>{' '}
              <span className="font-medium">{recorrido.tipo_vehiculo || 'N/A'}</span>
            </div>
            <div>
              <span className="text-gray-500">Combustible:</span>{' '}
              <span className="font-medium">{recorrido.detalle.tipo_combustible || 'N/A'}</span>
            </div>
            <div>
              <span className="text-gray-500">Rendimiento:</span>{' '}
              <span className="font-medium">{recorrido.detalle.consumo_km_galon || 0} km/gal</span>
            </div>
          </div>
          <div className="grid grid-cols-4 gap-2 text-xs pt-2 border-t border-gray-100">
            <div>
              <span className="text-gray-500">Recorridos/mes:</span>{' '}
              <span className="font-medium">{recorrido.detalle.recorridos_mensuales != null ? Number(recorrido.detalle.recorridos_mensuales).toFixed(1) : 'N/A'}</span>
            </div>
            <div>
              <span className="text-gray-500">Km lejanía:</span>{' '}
              <span className="font-medium text-blue-600">{recorrido.detalle.distancia_efectiva_km != null ? Number(recorrido.detalle.distancia_efectiva_km).toFixed(1) : '0'}</span>
            </div>
            <div>
              <span className="text-gray-500">Comb/recorrido:</span>{' '}
              <span className="font-medium text-blue-600">{formatCurrency(recorrido.detalle.combustible_por_recorrido || 0)}</span>
            </div>
            <div>
              <span className="text-gray-500">Peaje/recorrido:</span>{' '}
              <span className="font-medium text-yellow-600">{formatCurrency(recorrido.detalle.peaje_por_recorrido || 0)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Tramos del circuito */}
      {recorrido.detalle?.tramos && recorrido.detalle.tramos.length > 0 && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
          <div className="text-xs font-semibold text-blue-800 mb-2">
            Circuito ({recorrido.detalle.distancia_circuito_km != null ? Number(recorrido.detalle.distancia_circuito_km).toFixed(1) : '0'} km total)
          </div>
          <div className="flex flex-wrap items-center gap-1 text-xs">
            {recorrido.detalle.tramos.map((tramo: any, idx: number) => (
              <React.Fragment key={idx}>
                {idx === 0 && (
                  <span className="font-medium text-gray-700">{tramo.origen}</span>
                )}
                <span className="flex items-center gap-1 text-blue-600">
                  <ArrowRight size={12} />
                  <span className="text-gray-500">{tramo.distancia_km || 0} km</span>
                  {tramo.peaje > 0 && (
                    <span className="text-yellow-600">({formatCurrency(tramo.peaje)})</span>
                  )}
                </span>
                <span className="font-medium text-gray-700">{tramo.destino}</span>
              </React.Fragment>
            ))}
          </div>
        </div>
      )}

      {/* Detalle de Pernocta (costos por noche) */}
      {recorrido.detalle?.pernocta && (
        <div className="mb-4 p-3 bg-purple-50 border border-purple-200 rounded">
          <div className="text-xs font-semibold text-purple-800 mb-2">
            Pernocta: {recorrido.detalle.pernocta.noches} noche(s) por recorrido
          </div>

          {/* Conductor */}
          {recorrido.detalle.pernocta.conductor && (
            <div className="mb-2">
              <div className="text-xs font-medium text-purple-700 mb-1">
                Conductor {recorrido.esquema === 'tercero' ? '(va al pago del Tercero)' : ''}
              </div>
              <div className="grid grid-cols-5 gap-2 text-xs pl-2">
                <div>
                  <span className="text-gray-500">Desayuno:</span>{' '}
                  <span className="font-medium">{formatCurrency(recorrido.detalle.pernocta.conductor.desayuno)}</span>
                </div>
                <div>
                  <span className="text-gray-500">Almuerzo:</span>{' '}
                  <span className="font-medium">{formatCurrency(recorrido.detalle.pernocta.conductor.almuerzo)}</span>
                </div>
                <div>
                  <span className="text-gray-500">Cena:</span>{' '}
                  <span className="font-medium">{formatCurrency(recorrido.detalle.pernocta.conductor.cena)}</span>
                </div>
                <div>
                  <span className="text-gray-500">Alojamiento:</span>{' '}
                  <span className="font-medium">{formatCurrency(recorrido.detalle.pernocta.conductor.alojamiento)}</span>
                </div>
                <div>
                  <span className="text-gray-500">Total/noche:</span>{' '}
                  <span className="font-medium">{formatCurrency(recorrido.detalle.pernocta.conductor.gasto_por_noche)}</span>
                </div>
              </div>
            </div>
          )}

          {/* Auxiliar */}
          {recorrido.detalle.pernocta.auxiliar && (
            <div className="mb-2">
              <div className="text-xs font-medium text-purple-700 mb-1">
                Auxiliar (siempre paga la Empresa)
              </div>
              <div className="grid grid-cols-5 gap-2 text-xs pl-2">
                <div>
                  <span className="text-gray-500">Desayuno:</span>{' '}
                  <span className="font-medium">{formatCurrency(recorrido.detalle.pernocta.auxiliar.desayuno)}</span>
                </div>
                <div>
                  <span className="text-gray-500">Almuerzo:</span>{' '}
                  <span className="font-medium">{formatCurrency(recorrido.detalle.pernocta.auxiliar.almuerzo)}</span>
                </div>
                <div>
                  <span className="text-gray-500">Cena:</span>{' '}
                  <span className="font-medium">{formatCurrency(recorrido.detalle.pernocta.auxiliar.cena)}</span>
                </div>
                <div>
                  <span className="text-gray-500">Alojamiento:</span>{' '}
                  <span className="font-medium">{formatCurrency(recorrido.detalle.pernocta.auxiliar.alojamiento)}</span>
                </div>
                <div>
                  <span className="text-gray-500">Total/noche:</span>{' '}
                  <span className="font-medium">{formatCurrency(recorrido.detalle.pernocta.auxiliar.gasto_por_noche)}</span>
                </div>
              </div>
            </div>
          )}

          {/* Parqueadero */}
          <div className="pt-2 border-t border-purple-200">
            <span className="text-xs text-gray-500">Parqueadero/noche:</span>{' '}
            <span className="text-xs font-medium">{formatCurrency(recorrido.detalle.pernocta.parqueadero || 0)}</span>
          </div>
        </div>
      )}

      {/* Tabla de municipios */}
      {recorrido.detalle?.municipios && recorrido.detalle.municipios.length > 0 && (
        <div>
          <div className="text-xs font-semibold text-gray-700 mb-2">
            Municipios del Recorrido ({recorrido.detalle.municipios.length})
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-2 py-1 text-center">Orden</th>
                  <th className="px-2 py-1 text-left">Municipio</th>
                  <th className="px-2 py-1 text-right">Flete Base</th>
                </tr>
              </thead>
              <tbody>
                {recorrido.detalle.municipios.map((municipio: any, idx: number) => (
                  <tr key={idx} className="border-b border-gray-100">
                    <td className="px-2 py-1 text-center font-medium text-blue-600">
                      {municipio.orden}
                    </td>
                    <td className="px-2 py-1">{municipio.municipio}</td>
                    <td className="px-2 py-1 text-right text-orange-600">
                      {formatCurrency(municipio.flete_base || 0)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
