'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { apiClient, DetalleLejaniasComercial, DetalleZonaComercial, ComiteComercialData } from '@/lib/api';
import { useFilters } from '@/hooks/useFilters';
import { ChevronDown, ChevronRight, Calendar, User, Car, Home, ChevronsUpDown, Users, MapPin } from 'lucide-react';

type OrdenamientoType = 'nombre' | 'costo' | 'km';

export default function LejaniasComercial() {
  const { filters } = useFilters();
  const { escenarioId, marcaId, operacionIds } = filters;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [datos, setDatos] = useState<DetalleLejaniasComercial | null>(null);
  const [zonasExpandidas, setZonasExpandidas] = useState<Set<number>>(new Set());
  const [ordenamiento, setOrdenamiento] = useState<OrdenamientoType>('costo');

  useEffect(() => {
    if (escenarioId && marcaId) {
      cargarDatos();
    }
  }, [escenarioId, marcaId, operacionIds]);

  const cargarDatos = async () => {
    if (!escenarioId || !marcaId) return;

    try {
      setLoading(true);
      setError(null);
      // Pasar operacionIds solo si hay alguna seleccionada (vacío = todas)
      const opsParam = operacionIds.length > 0 ? operacionIds : undefined;
      const resultado = await apiClient.obtenerDetalleLejaniasComercial(escenarioId, marcaId, opsParam);
      setDatos(resultado);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error cargando datos');
    } finally {
      setLoading(false);
    }
  };

  // Ordenar zonas según criterio seleccionado
  const zonasOrdenadas = useMemo(() => {
    if (!datos) return [];
    return [...datos.zonas].sort((a, b) => {
      if (ordenamiento === 'costo') return b.total_mensual - a.total_mensual;
      if (ordenamiento === 'km') return (b.km_mensual || 0) - (a.km_mensual || 0);
      return a.zona_nombre.localeCompare(b.zona_nombre);
    });
  }, [datos, ordenamiento]);

  const toggleZona = (zonaId: number) => {
    const nuevasExpandidas = new Set(zonasExpandidas);
    if (nuevasExpandidas.has(zonaId)) {
      nuevasExpandidas.delete(zonaId);
    } else {
      nuevasExpandidas.add(zonaId);
    }
    setZonasExpandidas(nuevasExpandidas);
  };

  const expandirTodo = () => {
    if (!datos) return;
    setZonasExpandidas(new Set(datos.zonas.map(z => z.zona_id)));
  };

  const colapsarTodo = () => {
    setZonasExpandidas(new Set());
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatNumber = (value: number, decimals: number = 0) => {
    return new Intl.NumberFormat('es-CO', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
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
        <div className="grid grid-cols-7 gap-3">
          <div>
            <div className="text-xs text-gray-500">Km Mensuales</div>
            <div className="text-sm font-semibold text-gray-700">
              {formatNumber(datos.total_km_mensual || 0)} km
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Combustible</div>
            <div className="text-sm font-semibold text-blue-600">
              {formatCurrency(datos.total_combustible_mensual)}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Mant/Deprec/Llan</div>
            <div className="text-sm font-semibold text-orange-600">
              {formatCurrency(datos.total_costos_adicionales_mensual || 0)}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Pernocta</div>
            <div className="text-sm font-semibold text-purple-600">
              {formatCurrency(datos.total_pernocta_mensual)}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Comité Comercial</div>
            <div className="text-sm font-semibold text-indigo-600">
              {formatCurrency(datos.total_comite_mensual || 0)}
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
        <div className="bg-gray-700 text-white px-4 py-2 flex justify-between items-center">
          <span className="text-xs font-semibold uppercase tracking-wide">
            Zonas Comerciales ({datos.zonas.length})
          </span>
          <div className="flex items-center gap-3">
            {/* Selector de ordenamiento */}
            <div className="flex items-center gap-1 text-xs">
              <ChevronsUpDown size={12} />
              <select
                value={ordenamiento}
                onChange={(e) => setOrdenamiento(e.target.value as OrdenamientoType)}
                className="bg-gray-600 text-white text-xs rounded px-2 py-1 border-none focus:ring-1 focus:ring-gray-400"
              >
                <option value="costo">Por Costo</option>
                <option value="km">Por Km</option>
                <option value="nombre">Por Nombre</option>
              </select>
            </div>
            {/* Botones expandir/colapsar */}
            <div className="flex gap-1">
              <button
                onClick={expandirTodo}
                className="text-xs bg-gray-600 hover:bg-gray-500 px-2 py-1 rounded"
              >
                Expandir
              </button>
              <button
                onClick={colapsarTodo}
                className="text-xs bg-gray-600 hover:bg-gray-500 px-2 py-1 rounded"
              >
                Colapsar
              </button>
            </div>
          </div>
        </div>

        {zonasOrdenadas.map((zona) => {
          const expandida = zonasExpandidas.has(zona.zona_id);

          // Buscar si esta zona tiene comité comercial asignado
          const comiteZona = datos.comite_comercial?.detalle_por_zona.find(c => c.zona_id === zona.zona_id);

          // Calcular totales de municipios para la fila de totales
          const municipios = zona.detalle?.municipios || [];
          const totalKmMunicipios = municipios.reduce((sum: number, m: any) => sum + (m.distancia_km || 0), 0) + (comiteZona?.distancia_km || 0);
          const totalVisitasMes = municipios.reduce((sum: number, m: any) => sum + (m.visitas_mensuales || 0), 0) + (comiteZona?.viajes_mes || 0);
          const totalCombustible = municipios.reduce((sum: number, m: any) => sum + (m.combustible_mensual || 0), 0) + (comiteZona?.combustible_mensual || 0);
          const totalCostosAdicionales = municipios.reduce((sum: number, m: any) => sum + (m.costos_adicionales_mensual || 0), 0) + (comiteZona?.costos_adicionales_mensual || 0);

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
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-gray-900">
                          {zona.zona_nombre}
                        </span>
                        {zona.requiere_pernocta && (
                          <span className="px-2 py-0.5 text-xs bg-purple-100 text-purple-700 rounded-full">
                            Pernocta
                          </span>
                        )}
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
                        <span className="flex items-center gap-1" title="Frecuencia de visita">
                          <Calendar size={12} />
                          {zona.frecuencia}
                        </span>
                        <span className="text-gray-400">
                          {formatNumber(zona.km_mensual || 0)} km/mes
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
                  <div className="grid grid-cols-4 gap-4 mb-4">
                    <div>
                      <div className="text-xs text-gray-500">Km Mensuales</div>
                      <div className="text-sm font-medium text-gray-700">
                        {formatNumber(zona.km_mensual || 0)} km
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Combustible Mensual</div>
                      <div className="text-sm font-medium text-blue-600">
                        {formatCurrency(zona.combustible_mensual)}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Mant/Deprec/Llantas</div>
                      <div className="text-sm font-medium text-orange-600">
                        {formatCurrency(zona.costos_adicionales_mensual || 0)}
                      </div>
                      {zona.detalle?.costo_adicional_km > 0 && (
                        <div className="text-xs text-gray-400">
                          @ {formatCurrency(zona.detalle.costo_adicional_km)}/km
                        </div>
                      )}
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Pernocta Mensual</div>
                      <div className="text-sm font-medium text-purple-600">
                        {formatCurrency(zona.pernocta_mensual)}
                      </div>
                    </div>
                  </div>

                  {/* Detalle de Pernocta - Compactado */}
                  {zona.detalle?.pernocta && (
                    <div className="mb-4 p-2 bg-purple-50 border border-purple-200 rounded text-xs">
                      <span className="font-semibold text-purple-800">Pernocta:</span>{' '}
                      <span className="text-purple-700">
                        {zona.detalle.pernocta.noches} noche{zona.detalle.pernocta.noches > 1 ? 's' : ''} × {zona.detalle.pernocta.periodos_mes.toFixed(1)} viajes/mes
                        {' '}({formatCurrency(zona.detalle.pernocta.gasto_por_noche)}/noche:
                        Desay. {formatCurrency(zona.detalle.pernocta.desayuno)} +
                        Alm. {formatCurrency(zona.detalle.pernocta.almuerzo)} +
                        Cena {formatCurrency(zona.detalle.pernocta.cena)} +
                        Aloj. {formatCurrency(zona.detalle.pernocta.alojamiento)})
                      </span>
                    </div>
                  )}

                  {/* Tabla de municipios */}
                  {municipios.length > 0 && (
                    <div>
                      <div className="text-xs font-semibold text-gray-700 mb-2">
                        Municipios ({municipios.length})
                      </div>
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-xs">
                          <thead className="bg-gray-100">
                            <tr>
                              <th className="px-2 py-1 text-left">Municipio</th>
                              <th className="px-2 py-1 text-right">Dist. (km)</th>
                              <th className="px-2 py-1 text-right" title={`Visitas por ciclo de ${zona.frecuencia}`}>Visitas/ciclo</th>
                              <th className="px-2 py-1 text-right">Visitas/mes</th>
                              <th className="px-2 py-1 text-right">Comb/visita</th>
                              <th className="px-2 py-1 text-right">Combustible</th>
                              <th className="px-2 py-1 text-right">Mant/Dep/Llan</th>
                            </tr>
                          </thead>
                          <tbody>
                            {municipios.map((municipio: any, idx: number) => (
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
                                <td className="px-2 py-1 text-right text-orange-600">
                                  {formatCurrency(municipio.costos_adicionales_mensual || 0)}
                                </td>
                              </tr>
                            ))}
                            {/* Fila de Comité Comercial (si aplica a esta zona) */}
                            {comiteZona && (
                              <tr className="border-b border-indigo-200 bg-indigo-50">
                                <td className="px-2 py-1 text-indigo-700 font-medium">
                                  <span className="flex items-center gap-1">
                                    <Users size={12} className="text-indigo-500" />
                                    Comité ({datos.comite_comercial?.municipio})
                                  </span>
                                </td>
                                <td className="px-2 py-1 text-right">{comiteZona.distancia_km}</td>
                                <td className="px-2 py-1 text-right">1</td>
                                <td className="px-2 py-1 text-right">{comiteZona.viajes_mes.toFixed(1)}</td>
                                <td className="px-2 py-1 text-right text-gray-600">-</td>
                                <td className="px-2 py-1 text-right text-blue-600">
                                  {formatCurrency(comiteZona.combustible_mensual || 0)}
                                </td>
                                <td className="px-2 py-1 text-right text-orange-600">
                                  {formatCurrency(comiteZona.costos_adicionales_mensual || 0)}
                                </td>
                              </tr>
                            )}
                            {/* Fila de totales */}
                            <tr className="bg-gray-200 font-semibold border-t border-gray-300">
                              <td className="px-2 py-1">TOTAL</td>
                              <td className="px-2 py-1 text-right">{formatNumber(totalKmMunicipios)}</td>
                              <td className="px-2 py-1 text-right">-</td>
                              <td className="px-2 py-1 text-right">{formatNumber(totalVisitasMes, 1)}</td>
                              <td className="px-2 py-1 text-right">-</td>
                              <td className="px-2 py-1 text-right text-blue-600">
                                {formatCurrency(totalCombustible)}
                              </td>
                              <td className="px-2 py-1 text-right text-orange-600">
                                {formatCurrency(totalCostosAdicionales)}
                              </td>
                            </tr>
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
