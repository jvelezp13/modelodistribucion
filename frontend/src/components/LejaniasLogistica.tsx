'use client';

import React, { useState, useEffect } from 'react';
import { apiClient, DetalleLejaniasLogistica, DetalleRutaLogistica } from '@/lib/api';
import { ChevronDown, ChevronRight, MapPin, Truck, DollarSign, Fuel, Route, ArrowRight } from 'lucide-react';

interface LejaniasLogisticaProps {
  escenarioId: number;
  marcaId: string;
}

export default function LejaniasLogistica({ escenarioId, marcaId }: LejaniasLogisticaProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [datos, setDatos] = useState<DetalleLejaniasLogistica | null>(null);
  const [recorridosExpandidos, setRecorridosExpandidos] = useState<Set<number>>(new Set());

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

  const toggleRecorrido = (recorridoId: number) => {
    const nuevosExpandidos = new Set(recorridosExpandidos);
    if (nuevosExpandidos.has(recorridoId)) {
      nuevosExpandidos.delete(recorridoId);
    } else {
      nuevosExpandidos.add(recorridoId);
    }
    setRecorridosExpandidos(nuevosExpandidos);
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
        <div className="grid grid-cols-6 gap-4">
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
            <div className="text-xs text-gray-500">Pernocta Total</div>
            <div className="text-sm font-semibold text-purple-600">
              {formatCurrency(datos.total_pernocta_mensual)}
            </div>
            <div className="text-[10px] text-gray-400 mt-0.5">
              <span>Cond: {formatCurrency(datos.total_pernocta_conductor_mensual || 0)}</span>
              <span className="mx-1">|</span>
              <span>Aux: {formatCurrency(datos.total_pernocta_auxiliar_mensual || 0)}</span>
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Parqueadero</div>
            <div className="text-sm font-semibold text-gray-600">
              {formatCurrency(datos.total_parqueadero_mensual || 0)}
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

      {/* Lista de recorridos */}
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
                      <div className="grid grid-cols-6 gap-2 text-xs">
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
                        <div>
                          <span className="text-gray-500">Recorridos/mes:</span>{' '}
                          <span className="font-medium">{recorrido.detalle.recorridos_mensuales != null ? Number(recorrido.detalle.recorridos_mensuales).toFixed(1) : 'N/A'}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Km lejanía:</span>{' '}
                          <span className="font-medium text-blue-600">{recorrido.detalle.distancia_efectiva_km != null ? Number(recorrido.detalle.distancia_efectiva_km).toFixed(1) : '0'}</span>
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
                              <th className="px-2 py-1 text-right">Entregas/recorrido</th>
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
                                <td className="px-2 py-1 text-right">
                                  <span className={municipio.entregas_por_periodo > 1 ? 'font-semibold text-orange-600' : ''}>
                                    {municipio.entregas_por_periodo}
                                  </span>
                                </td>
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
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
