'use client';

import React, { useState, useEffect } from 'react';
import { apiClient, DetalleLejaniasComercial, DetalleZonaComercial } from '@/lib/api';
import { useFilters } from '@/hooks/useFilters';
import { ChevronDown, ChevronRight, MapPin, User, Car, Home } from 'lucide-react';

export default function LejaniasComercial() {
  const { filters } = useFilters();
  const { escenarioId, marcaId } = filters;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [datos, setDatos] = useState<DetalleLejaniasComercial | null>(null);
  const [zonasExpandidas, setZonasExpandidas] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (escenarioId && marcaId) {
      cargarDatos();
    }
  }, [escenarioId, marcaId]);

  const cargarDatos = async () => {
    if (!escenarioId || !marcaId) return;

    try {
      setLoading(true);
      setError(null);
      const resultado = await apiClient.obtenerDetalleLejaniasComercial(escenarioId, marcaId);
      setDatos(resultado);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error cargando datos');
    } finally {
      setLoading(false);
    }
  };

  const toggleZona = (zonaId: number) => {
    const nuevasExpandidas = new Set(zonasExpandidas);
    if (nuevasExpandidas.has(zonaId)) {
      nuevasExpandidas.delete(zonaId);
    } else {
      nuevasExpandidas.add(zonaId);
    }
    setZonasExpandidas(nuevasExpandidas);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Cargando datos de lejanías comerciales...</div>
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

  if (!datos || datos.zonas.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded p-4">
        <p className="text-yellow-800">No hay zonas configuradas para esta marca.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header con totales */}
      <div className="bg-white border border-gray-200 rounded p-4">
        <h2 className="text-lg font-bold text-gray-800 mb-3">
          Lejanías Comerciales - {datos.marca_nombre}
        </h2>
        <div className="grid grid-cols-4 gap-4">
          <div>
            <div className="text-xs text-gray-500">Combustible Mensual</div>
            <div className="text-sm font-semibold text-blue-600">
              {formatCurrency(datos.total_combustible_mensual)}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Pernocta Mensual</div>
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

      {/* Lista de zonas */}
      <div className="bg-white border border-gray-200 rounded">
        <div className="bg-gray-700 text-white px-4 py-2">
          <span className="text-xs font-semibold uppercase tracking-wide">
            Zonas Comerciales ({datos.zonas.length})
          </span>
        </div>

        {datos.zonas.map((zona) => {
          const expandida = zonasExpandidas.has(zona.zona_id);

          return (
            <div key={zona.zona_id} className="border-b border-gray-200 last:border-b-0">
              {/* Header de zona */}
              <div
                className="px-4 py-3 hover:bg-gray-50 cursor-pointer"
                onClick={() => toggleZona(zona.zona_id)}
              >
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-3">
                    {expandida ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                    <div>
                      <div className="text-sm font-semibold text-gray-900">
                        {zona.zona_nombre}
                      </div>
                      <div className="flex gap-4 mt-1 text-xs text-gray-600">
                        <span className="flex items-center gap-1">
                          <User size={12} />
                          {zona.vendedor}
                        </span>
                        <span className="flex items-center gap-1">
                          <Home size={12} />
                          {zona.ciudad_base}
                        </span>
                        <span className="flex items-center gap-1">
                          <Car size={12} />
                          {zona.tipo_vehiculo}
                        </span>
                        <span className="flex items-center gap-1">
                          <MapPin size={12} />
                          {zona.frecuencia}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-gray-900">
                      {formatCurrency(zona.total_mensual)}
                    </div>
                    <div className="text-xs text-gray-500">mensual</div>
                  </div>
                </div>
              </div>

              {/* Detalle de zona expandida */}
              {expandida && (
                <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <div className="text-xs text-gray-500">Combustible Mensual</div>
                      <div className="text-sm font-medium text-blue-600">
                        {formatCurrency(zona.combustible_mensual)}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Pernocta Mensual</div>
                      <div className="text-sm font-medium text-purple-600">
                        {formatCurrency(zona.pernocta_mensual)}
                      </div>
                    </div>
                  </div>

                  {/* Detalle de Pernocta */}
                  {zona.detalle?.pernocta && (
                    <div className="mb-4 p-3 bg-purple-50 border border-purple-200 rounded">
                      <div className="text-xs font-semibold text-purple-800 mb-2">
                        Detalle Pernocta ({zona.detalle.pernocta.noches} noche{zona.detalle.pernocta.noches > 1 ? 's' : ''} × {zona.detalle.pernocta.periodos_mes.toFixed(2)} viajes/mes)
                      </div>
                      <div className="grid grid-cols-5 gap-2 text-xs">
                        <div>
                          <span className="text-gray-500">Desayuno:</span>{' '}
                          <span className="font-medium">{formatCurrency(zona.detalle.pernocta.desayuno)}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Almuerzo:</span>{' '}
                          <span className="font-medium">{formatCurrency(zona.detalle.pernocta.almuerzo)}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Cena:</span>{' '}
                          <span className="font-medium">{formatCurrency(zona.detalle.pernocta.cena)}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Alojamiento:</span>{' '}
                          <span className="font-medium">{formatCurrency(zona.detalle.pernocta.alojamiento)}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Total/noche:</span>{' '}
                          <span className="font-medium">{formatCurrency(zona.detalle.pernocta.gasto_por_noche)}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tabla de municipios */}
                  {zona.detalle?.municipios && zona.detalle.municipios.length > 0 && (
                    <div>
                      <div className="text-xs font-semibold text-gray-700 mb-2">
                        Municipios ({zona.detalle.municipios.length})
                      </div>
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-xs">
                          <thead className="bg-gray-100">
                            <tr>
                              <th className="px-2 py-1 text-left">Municipio</th>
                              <th className="px-2 py-1 text-right">Distancia (km)</th>
                              <th className="px-2 py-1 text-right">Visitas/periodo</th>
                              <th className="px-2 py-1 text-right">Visitas/mes</th>
                              <th className="px-2 py-1 text-right">Comb/visita</th>
                              <th className="px-2 py-1 text-right">Combustible</th>
                            </tr>
                          </thead>
                          <tbody>
                            {zona.detalle.municipios.map((municipio: any, idx: number) => (
                              <tr key={idx} className="border-b border-gray-100">
                                <td className="px-2 py-1">{municipio.municipio}</td>
                                <td className="px-2 py-1 text-right">{municipio.distancia_km}</td>
                                <td className="px-2 py-1 text-right">
                                  <span className={municipio.visitas_por_periodo > 1 ? 'font-semibold text-orange-600' : ''}>
                                    {municipio.visitas_por_periodo}
                                  </span>
                                </td>
                                <td className="px-2 py-1 text-right">{municipio.visitas_mensuales.toFixed(1)}</td>
                                <td className="px-2 py-1 text-right text-gray-600">
                                  {formatCurrency(municipio.combustible_por_visita || 0)}
                                </td>
                                <td className="px-2 py-1 text-right text-blue-600">
                                  {formatCurrency(municipio.combustible_mensual)}
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
