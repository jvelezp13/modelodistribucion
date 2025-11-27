'use client';

import React, { useState, useEffect } from 'react';
import { apiClient, DetalleLejaniasLogistica, DetalleRutaLogistica } from '@/lib/api';
import { ChevronDown, ChevronRight, MapPin, Truck, DollarSign, Fuel, Route } from 'lucide-react';

interface LejaniasLogisticaProps {
  escenarioId: number;
  marcaId: string;
}

export default function LejaniasLogistica({ escenarioId, marcaId }: LejaniasLogisticaProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [datos, setDatos] = useState<DetalleLejaniasLogistica | null>(null);
  const [rutasExpandidas, setRutasExpandidas] = useState<Set<number>>(new Set());

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

  const toggleRuta = (rutaId: number) => {
    const nuevasExpandidas = new Set(rutasExpandidas);
    if (nuevasExpandidas.has(rutaId)) {
      nuevasExpandidas.delete(rutaId);
    } else {
      nuevasExpandidas.add(rutaId);
    }
    setRutasExpandidas(nuevasExpandidas);
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
        <div className="text-gray-500">Cargando datos de lejanías logísticas...</div>
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
        <p className="text-yellow-800">No hay rutas logísticas configuradas para esta marca.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header con totales */}
      <div className="bg-white border border-gray-200 rounded p-4">
        <h2 className="text-lg font-bold text-gray-800 mb-3">
          Lejanías Logísticas - {datos.marca_nombre}
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
            <div className="text-xs text-gray-500">Pernocta</div>
            <div className="text-sm font-semibold text-purple-600">
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

      {/* Lista de rutas */}
      <div className="bg-white border border-gray-200 rounded">
        <div className="bg-gray-700 text-white px-4 py-2">
          <span className="text-xs font-semibold uppercase tracking-wide">
            Rutas Logísticas ({datos.rutas.length})
          </span>
        </div>

        {datos.rutas.map((ruta) => {
          const expandida = rutasExpandidas.has(ruta.ruta_id);

          return (
            <div key={ruta.ruta_id} className="border-b border-gray-200 last:border-b-0">
              {/* Header de ruta */}
              <div
                className="px-4 py-3 hover:bg-gray-50 cursor-pointer"
                onClick={() => toggleRuta(ruta.ruta_id)}
              >
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-3">
                    {expandida ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-gray-900">
                          {ruta.ruta_nombre}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${getEsquemaColor(ruta.esquema)}`}>
                          {getEsquemaLabel(ruta.esquema)}
                        </span>
                      </div>
                      <div className="flex gap-4 mt-1 text-xs text-gray-600">
                        <span className="flex items-center gap-1">
                          <Truck size={12} />
                          {ruta.vehiculo || 'Sin vehículo'}
                        </span>
                        <span className="flex items-center gap-1">
                          <Route size={12} />
                          {ruta.frecuencia}
                        </span>
                        <span className="flex items-center gap-1">
                          <MapPin size={12} />
                          {ruta.detalle?.municipios?.length || 0} municipios
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-gray-900">
                      {formatCurrency(ruta.total_mensual)}
                    </div>
                    <div className="text-xs text-gray-500">mensual</div>
                  </div>
                </div>
              </div>

              {/* Detalle de ruta expandida */}
              {expandida && (
                <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
                  <div className="grid grid-cols-4 gap-4 mb-4">
                    <div>
                      <div className="text-xs text-gray-500">Flete Base</div>
                      <div className="text-sm font-medium text-orange-600">
                        {formatCurrency(ruta.flete_base_mensual)}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Combustible</div>
                      <div className="text-sm font-medium text-blue-600">
                        {formatCurrency(ruta.combustible_mensual)}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Peajes</div>
                      <div className="text-sm font-medium text-yellow-600">
                        {formatCurrency(ruta.peaje_mensual)}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Pernocta</div>
                      <div className="text-sm font-medium text-purple-600">
                        {formatCurrency(ruta.pernocta_mensual)}
                      </div>
                    </div>
                  </div>

                  {/* Info del vehículo */}
                  {ruta.detalle && (
                    <div className="mb-4 p-2 bg-white rounded border border-gray-200">
                      <div className="grid grid-cols-5 gap-2 text-xs">
                        <div>
                          <span className="text-gray-500">Bodega:</span>{' '}
                          <span className="font-medium">{ruta.detalle.bodega || 'N/A'}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Tipo:</span>{' '}
                          <span className="font-medium">{ruta.tipo_vehiculo || 'N/A'}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Combustible:</span>{' '}
                          <span className="font-medium">{ruta.detalle.tipo_combustible || 'N/A'}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Rendimiento:</span>{' '}
                          <span className="font-medium">{ruta.detalle.consumo_km_galon || 0} km/gal</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Viajes/mes:</span>{' '}
                          <span className="font-medium">{ruta.detalle.viajes_mensuales?.toFixed(1) || 'N/A'}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Detalle de Pernocta (costos por noche) */}
                  {ruta.detalle?.pernocta && (
                    <div className="mb-4 p-3 bg-purple-50 border border-purple-200 rounded">
                      <div className="text-xs font-semibold text-purple-800 mb-2">
                        Costos de Pernocta por Noche
                      </div>
                      <div className="grid grid-cols-6 gap-2 text-xs">
                        <div>
                          <span className="text-gray-500">Desayuno:</span>{' '}
                          <span className="font-medium">{formatCurrency(ruta.detalle.pernocta.desayuno)}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Almuerzo:</span>{' '}
                          <span className="font-medium">{formatCurrency(ruta.detalle.pernocta.almuerzo)}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Cena:</span>{' '}
                          <span className="font-medium">{formatCurrency(ruta.detalle.pernocta.cena)}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Alojamiento:</span>{' '}
                          <span className="font-medium">{formatCurrency(ruta.detalle.pernocta.alojamiento)}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Parqueadero:</span>{' '}
                          <span className="font-medium">{formatCurrency(ruta.detalle.pernocta.parqueadero)}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Total/noche:</span>{' '}
                          <span className="font-medium">{formatCurrency(ruta.detalle.pernocta.gasto_por_noche)}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tabla de municipios */}
                  {ruta.detalle?.municipios && ruta.detalle.municipios.length > 0 && (
                    <div>
                      <div className="text-xs font-semibold text-gray-700 mb-2">
                        Municipios ({ruta.detalle.municipios.length})
                      </div>
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-xs">
                          <thead className="bg-gray-100">
                            <tr>
                              <th className="px-2 py-1 text-left">Municipio</th>
                              <th className="px-2 py-1 text-right">Dist. (km)</th>
                              <th className="px-2 py-1 text-right">Km Lejanía</th>
                              <th className="px-2 py-1 text-right">Ent/periodo</th>
                              <th className="px-2 py-1 text-right">Ent/mes</th>
                              <th className="px-2 py-1 text-right">Flete Base</th>
                              <th className="px-2 py-1 text-right">Combustible</th>
                              <th className="px-2 py-1 text-right">Peaje</th>
                              <th className="px-2 py-1 text-center">Pernocta</th>
                              <th className="px-2 py-1 text-right">$ Pernocta</th>
                            </tr>
                          </thead>
                          <tbody>
                            {ruta.detalle.municipios.map((municipio: any, idx: number) => (
                              <tr key={idx} className="border-b border-gray-100">
                                <td className="px-2 py-1">{municipio.municipio}</td>
                                <td className="px-2 py-1 text-right">{municipio.distancia_km}</td>
                                <td className="px-2 py-1 text-right">
                                  <span className={municipio.distancia_efectiva_km > 0 ? 'font-semibold text-blue-600' : 'text-gray-400'}>
                                    {municipio.distancia_efectiva_km?.toFixed(1) || '0'}
                                  </span>
                                </td>
                                <td className="px-2 py-1 text-right">
                                  <span className={municipio.entregas_por_periodo > 1 ? 'font-semibold text-orange-600' : ''}>
                                    {municipio.entregas_por_periodo}
                                  </span>
                                </td>
                                <td className="px-2 py-1 text-right">{municipio.entregas_mensuales.toFixed(1)}</td>
                                <td className="px-2 py-1 text-right text-orange-600">
                                  {formatCurrency(municipio.flete_base || 0)}
                                </td>
                                <td className="px-2 py-1 text-right text-blue-600">
                                  {formatCurrency(municipio.combustible_mensual)}
                                </td>
                                <td className="px-2 py-1 text-right text-yellow-600">
                                  {formatCurrency(municipio.peaje_mensual || 0)}
                                </td>
                                <td className="px-2 py-1 text-center">
                                  {municipio.requiere_pernocta ? (
                                    <span className="text-purple-600 font-medium">{municipio.noches_pernocta} noche{municipio.noches_pernocta > 1 ? 's' : ''}</span>
                                  ) : '-'}
                                </td>
                                <td className="px-2 py-1 text-right text-purple-600">
                                  {formatCurrency(municipio.pernocta_mensual || 0)}
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
