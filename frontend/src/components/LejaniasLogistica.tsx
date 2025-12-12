'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { apiClient, DetalleLejaniasLogistica, DetalleRutaLogistica, DiagnosticoLogisticoResponse } from '@/lib/api';
import { useFilters } from '@/hooks/useFilters';
import { ChevronDown, ChevronRight, MapPin, Truck, DollarSign, Fuel, Route, Building2, AlertTriangle, ChevronsUpDown, Moon } from 'lucide-react';

type VistaType = 'recorrido' | 'vehiculo' | 'distribucion';
type OrdenamientoType = 'nombre' | 'costo' | 'km';

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

export default function LejaniasLogistica() {
  const { filters } = useFilters();
  const { escenarioId, marcaId, operacionIds } = filters;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [datos, setDatos] = useState<DetalleLejaniasLogistica | null>(null);
  const [distribucion, setDistribucion] = useState<DiagnosticoLogisticoResponse | null>(null);
  const [recorridosExpandidos, setRecorridosExpandidos] = useState<Set<number>>(new Set());
  const [vehiculosExpandidos, setVehiculosExpandidos] = useState<Set<number>>(new Set());
  const [vistaActiva, setVistaActiva] = useState<VistaType>('recorrido');
  const [ordenamiento, setOrdenamiento] = useState<OrdenamientoType>('costo');
  const [mostrarExplicacion, setMostrarExplicacion] = useState(false);
  const [mostrarComparacion, setMostrarComparacion] = useState(false);

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
      const [resultado, distResult] = await Promise.all([
        apiClient.obtenerDetalleLejaniasLogistica(escenarioId, marcaId, opsParam),
        apiClient.obtenerDiagnosticoLogistico(escenarioId, marcaId)
      ]);
      setDatos(resultado);
      setDistribucion(distResult);
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

  // Ordenar rutas según criterio seleccionado
  const rutasOrdenadas = useMemo(() => {
    if (!datos) return [];
    return [...datos.rutas].sort((a, b) => {
      if (ordenamiento === 'costo') return b.total_mensual - a.total_mensual;
      if (ordenamiento === 'km') return (b.detalle?.distancia_circuito_km || 0) - (a.detalle?.distancia_circuito_km || 0);
      return a.ruta_nombre.localeCompare(b.ruta_nombre);
    });
  }, [datos, ordenamiento]);

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

  const expandirTodoRecorridos = () => {
    if (!datos) return;
    setRecorridosExpandidos(new Set(datos.rutas.map(r => r.ruta_id)));
  };

  const colapsarTodoRecorridos = () => setRecorridosExpandidos(new Set());

  const expandirTodoVehiculos = () => {
    setVehiculosExpandidos(new Set(vehiculosAgrupados.map(v => v.vehiculo_id)));
  };

  const colapsarTodoVehiculos = () => setVehiculosExpandidos(new Set());

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

  // Colores sobrios pero distintos para cada zona
  const zonaColors = [
    'bg-slate-200 text-slate-700',
    'bg-stone-200 text-stone-700',
    'bg-zinc-200 text-zinc-700',
    'bg-neutral-300 text-neutral-700',
    'bg-gray-300 text-gray-700',
    'bg-slate-300 text-slate-700',
  ];

  const getZonaColor = (zonaId: number) => {
    return zonaColors[zonaId % zonaColors.length];
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
        <div className="grid grid-cols-4 gap-4">
          {/* Transporte (Flete + Peajes) */}
          <div className="p-3 bg-gray-50 rounded border border-gray-200">
            <div className="text-xs font-medium text-gray-600 mb-2">Transporte</div>
            <div className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Flete Base</span>
                <span className="font-semibold text-gray-700">{formatCurrency(datos.total_flete_base_mensual)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Peajes</span>
                <span className="font-semibold text-gray-700">{formatCurrency(datos.total_peaje_mensual)}</span>
              </div>
            </div>
          </div>

          {/* Combustible */}
          <div className="p-3 bg-blue-50 rounded border border-blue-200">
            <div className="text-xs font-medium text-blue-700 mb-1">Combustible</div>
            <div className="text-lg font-bold text-blue-600">
              {formatCurrency(datos.total_combustible_mensual)}
            </div>
          </div>

          {/* Pernocta (consolidado) */}
          <div className="p-3 bg-purple-50 rounded border border-purple-200">
            <div className="text-xs font-medium text-purple-700 mb-1">Pernocta</div>
            <div className="text-lg font-bold text-purple-600">
              {formatCurrency(datos.total_pernocta_mensual)}
            </div>
          </div>

          {/* Totales */}
          <div className="p-3 bg-green-50 rounded border border-green-200">
            <div className="text-xs font-medium text-green-700 mb-2">Totales</div>
            <div className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Mensual</span>
                <span className="font-bold text-gray-900">{formatCurrency(datos.total_mensual)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Anual</span>
                <span className="font-bold text-green-600">{formatCurrency(datos.total_anual)}</span>
              </div>
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
        <button
          onClick={() => setVistaActiva('distribucion')}
          className={`px-4 py-2 text-sm font-medium rounded-t transition-colors ${
            vistaActiva === 'distribucion'
              ? 'bg-gray-700 text-white'
              : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
          }`}
        >
          <span className="flex items-center gap-1">
            <Building2 size={14} />
            Distribución por Zona
          </span>
        </button>
      </div>

      {/* Vista por Recorrido */}
      {vistaActiva === 'recorrido' && (
        <div className="bg-white border border-gray-200 rounded">
          <div className="bg-gray-700 text-white px-4 py-2 flex justify-between items-center">
            <span className="text-xs font-semibold uppercase tracking-wide">
              Recorridos Logísticos ({rutasOrdenadas.length})
            </span>
            <div className="flex items-center gap-3">
              {/* Selector de ordenamiento */}
              <div className="flex items-center gap-1 text-xs">
                <ChevronsUpDown size={12} />
                <select
                  value={ordenamiento}
                  onChange={(e) => setOrdenamiento(e.target.value as OrdenamientoType)}
                  className="bg-gray-600 text-white text-xs rounded px-2 py-1 border-none cursor-pointer"
                >
                  <option value="costo">Por Costo</option>
                  <option value="km">Por Km</option>
                  <option value="nombre">Por Nombre</option>
                </select>
              </div>
              {/* Botones expandir/colapsar */}
              <div className="flex gap-1">
                <button
                  onClick={expandirTodoRecorridos}
                  className="text-xs bg-gray-600 hover:bg-gray-500 px-2 py-1 rounded"
                >
                  Expandir
                </button>
                <button
                  onClick={colapsarTodoRecorridos}
                  className="text-xs bg-gray-600 hover:bg-gray-500 px-2 py-1 rounded"
                >
                  Colapsar
                </button>
              </div>
            </div>
          </div>

          {rutasOrdenadas.map((recorrido) => {
            const expandido = recorridosExpandidos.has(recorrido.ruta_id);

            // Calcular costos unitarios (por recorrido)
            const recorridosMes = recorrido.detalle?.recorridos_mensuales || 1;
            const costoUnitario = {
              flete: recorrido.flete_base_mensual / recorridosMes,
              combustible: recorrido.detalle?.combustible_por_recorrido || 0,
              peajes: recorrido.detalle?.peaje_por_recorrido || 0,
              pernocta: recorrido.pernocta_mensual / recorridosMes,
              total: recorrido.total_mensual / recorridosMes
            };

            return (
              <div key={recorrido.ruta_id} className="border-b border-gray-200 last:border-b-0">
                {/* Header de recorrido - compacto */}
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
                          {recorrido.requiere_pernocta && (
                            <Moon size={14} className="text-purple-500" />
                          )}
                        </div>
                        <div className="text-xs text-gray-500">
                          {recorrido.vehiculo || 'Sin vehículo'}
                          {recorrido.tipo_vehiculo && (
                            <span className="text-gray-400"> ({recorrido.tipo_vehiculo})</span>
                          )}
                          <span className="text-gray-300 mx-1">•</span>
                          <span>{formatNumber(recorrido.detalle?.distancia_circuito_km || 0, 0)} km</span>
                        </div>
                      </div>
                    </div>
                    {/* Cálculo compacto: unitario × freq = mensual */}
                    <div className="text-right text-sm">
                      <div className="text-gray-500">
                        <span className="font-medium text-gray-700">{formatCurrency(costoUnitario.total)}</span>
                        <span className="text-gray-400 mx-1">×{recorridosMes}</span>
                        <span className="text-gray-400">=</span>
                      </div>
                      <div className="font-semibold text-gray-900">{formatCurrency(recorrido.total_mensual)}</div>
                    </div>
                  </div>
                </div>

                {/* Detalle de recorrido expandido */}
                {expandido && (
                  <DetalleRecorrido
                    recorrido={recorrido}
                    formatCurrency={formatCurrency}
                    getEsquemaColor={getEsquemaColor}
                    costoUnitario={costoUnitario}
                    recorridosMes={recorridosMes}
                  />
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Vista por Vehículo */}
      {vistaActiva === 'vehiculo' && (
        <div className="bg-white border border-gray-200 rounded">
          <div className="bg-gray-700 text-white px-4 py-2 flex justify-between items-center">
            <span className="text-xs font-semibold uppercase tracking-wide">
              Vehículos ({vehiculosAgrupados.length})
            </span>
            <div className="flex gap-1">
              <button
                onClick={expandirTodoVehiculos}
                className="text-xs bg-gray-600 hover:bg-gray-500 px-2 py-1 rounded"
              >
                Expandir
              </button>
              <button
                onClick={colapsarTodoVehiculos}
                className="text-xs bg-gray-600 hover:bg-gray-500 px-2 py-1 rounded"
              >
                Colapsar
              </button>
            </div>
          </div>

          {vehiculosAgrupados.map((vehiculo) => {
            const expandido = vehiculosExpandidos.has(vehiculo.vehiculo_id);
            const kmTotales = vehiculo.recorridos.reduce((sum, r) => sum + (r.detalle?.distancia_circuito_km || 0), 0);

            return (
              <div key={vehiculo.vehiculo_id} className="border-b border-gray-200 last:border-b-0">
                {/* Header de vehículo - compacto */}
                <div
                  className="px-4 py-3 hover:bg-gray-50 cursor-pointer"
                  onClick={() => toggleVehiculo(vehiculo.vehiculo_id)}
                >
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-3">
                      {expandido ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-gray-900">
                            {vehiculo.vehiculo}
                          </span>
                          <span className="text-xs text-gray-400">
                            ({vehiculo.tipo_vehiculo || 'N/A'})
                          </span>
                        </div>
                        <div className="text-xs text-gray-500">
                          {vehiculo.recorridos.length} recorrido(s)
                          <span className="text-gray-300 mx-1">•</span>
                          {formatNumber(kmTotales, 0)} km
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
                    {/* Totales del vehículo - tabla sobria */}
                    <div className="mb-4 p-3 bg-white rounded border border-gray-200">
                      <div className="text-xs font-medium text-gray-600 mb-2">Desglose mensual</div>
                      <table className="w-full text-xs">
                        <tbody className="text-gray-700">
                          <tr>
                            <td className="py-0.5">Flete Base</td>
                            <td className="text-right">{formatCurrency(vehiculo.total_flete_base)}</td>
                          </tr>
                          <tr>
                            <td className="py-0.5">Combustible</td>
                            <td className="text-right">{formatCurrency(vehiculo.total_combustible)}</td>
                          </tr>
                          <tr>
                            <td className="py-0.5">Peajes</td>
                            <td className="text-right">{formatCurrency(vehiculo.total_peaje)}</td>
                          </tr>
                          {vehiculo.total_pernocta > 0 && (
                            <tr>
                              <td className="py-0.5">Pernocta</td>
                              <td className="text-right">{formatCurrency(vehiculo.total_pernocta)}</td>
                            </tr>
                          )}
                          {vehiculo.total_parqueadero > 0 && (
                            <tr>
                              <td className="py-0.5">Parqueadero</td>
                              <td className="text-right">{formatCurrency(vehiculo.total_parqueadero)}</td>
                            </tr>
                          )}
                          <tr className="border-t border-gray-200 font-medium">
                            <td className="pt-1">Total Mensual</td>
                            <td className="text-right pt-1">{formatCurrency(vehiculo.total_mensual)}</td>
                          </tr>
                          <tr className="text-gray-500">
                            <td className="py-0.5">Total Anual</td>
                            <td className="text-right">{formatCurrency(vehiculo.total_mensual * 12)}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>

                    {/* Lista de recorridos del vehículo */}
                    <div className="text-xs font-medium text-gray-600 mb-2">
                      Recorridos ({vehiculo.recorridos.length})
                    </div>
                    <div className="space-y-1">
                      {vehiculo.recorridos.map((recorrido) => {
                        const recorridosMes = recorrido.detalle?.recorridos_mensuales || 1;
                        const costoUnitario = recorrido.total_mensual / recorridosMes;
                        return (
                          <div key={recorrido.ruta_id} className="p-2 bg-white rounded border border-gray-200 flex justify-between items-center">
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-gray-900">{recorrido.ruta_nombre}</span>
                              {recorrido.requiere_pernocta && <Moon size={12} className="text-purple-500" />}
                              <span className="text-xs text-gray-400">
                                {formatNumber(recorrido.detalle?.distancia_circuito_km || 0, 0)} km
                              </span>
                            </div>
                            <div className="text-right text-sm">
                              <span className="text-gray-500">{formatCurrency(costoUnitario)}</span>
                              <span className="text-gray-400 mx-1">×{recorridosMes}</span>
                              <span className="font-medium text-gray-900">= {formatCurrency(recorrido.total_mensual)}</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Vista Distribución por Zona */}
      {vistaActiva === 'distribucion' && distribucion && (
        <div className="bg-white border border-gray-200 rounded">
          <div className="bg-gray-700 text-white px-4 py-2">
            <span className="text-xs font-semibold uppercase tracking-wide">
              Distribución de Costos Logísticos por Zona Comercial
            </span>
          </div>

          <div className="p-4">
            {/* KPIs de Resumen - sobrios */}
            <div className="mb-6 p-3 bg-gray-50 rounded border border-gray-200">
              <div className="grid grid-cols-4 gap-4 text-sm">
                <div>
                  <div className="text-xs text-gray-500">Flete Fijo</div>
                  <div className="font-semibold text-gray-900">
                    {formatCurrency(distribucion.distribucion_a_zonas.reduce((sum, z) => sum + (z.flete_fijo_asignado || 0), 0))}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Lejanías</div>
                  <div className="font-semibold text-gray-900">
                    {formatCurrency(distribucion.distribucion_a_zonas.reduce((sum, z) => sum + (z.lejanias_asignado || 0), 0))}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Gastos Fijos Flota</div>
                  <div className="font-semibold text-gray-900">
                    {formatCurrency(distribucion.distribucion_a_zonas.reduce((sum, z) => sum + z.costo_flota_asignado, 0))}
                  </div>
                </div>
                <div className="border-l border-gray-300 pl-4">
                  <div className="text-xs text-gray-500">Total Distribuido</div>
                  <div className="font-bold text-gray-900">
                    {formatCurrency(distribucion.distribucion_a_zonas.reduce((sum, z) => sum + z.costo_total_asignado, 0))}
                  </div>
                </div>
              </div>
            </div>

            {/* Tabla Rutas → Municipios → Zonas */}
            <div className="mb-6">
              <div className="text-xs font-medium text-gray-600 mb-2">
                Rutas Logísticas → Municipios → Zonas
              </div>
              <div className="bg-white rounded border overflow-hidden">
                <table className="w-full text-xs">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="text-left px-3 py-2 font-medium text-gray-600">Ruta / Vehículo</th>
                      <th className="text-left px-3 py-2 font-medium text-gray-600">Municipios</th>
                      <th className="text-left px-3 py-2 font-medium text-gray-600">Zonas</th>
                    </tr>
                  </thead>
                  <tbody>
                    {distribucion.rutas_logisticas.map((ruta) => (
                      <tr key={ruta.ruta_id} className="border-t border-gray-100 hover:bg-gray-50">
                        <td className="px-3 py-2 align-top">
                          <div className="font-medium text-gray-800">{ruta.ruta_nombre}</div>
                          <div className="text-[10px] text-gray-500">{ruta.vehiculo}</div>
                        </td>
                        <td className="px-3 py-2 align-top">
                          <div className="space-y-0.5">
                            {ruta.municipios.map((mun) => (
                              <div key={mun.municipio_id} className="text-gray-700">
                                {mun.municipio_nombre}
                                {mun.flete_base > 0 && (
                                  <span className="text-gray-400 ml-1">
                                    ({formatCurrency(mun.flete_base)})
                                  </span>
                                )}
                              </div>
                            ))}
                          </div>
                        </td>
                        <td className="px-3 py-2 align-top">
                          <div className="space-y-0.5">
                            {ruta.municipios.map((mun) => (
                              <div key={mun.municipio_id}>
                                {mun.cantidad_zonas === 0 ? (
                                  <span className="text-red-500 flex items-center gap-1">
                                    <AlertTriangle size={10} />
                                    Sin zona
                                  </span>
                                ) : (
                                  <div className="flex flex-wrap gap-1">
                                    {mun.zonas_que_lo_atienden.map((z) => (
                                      <span key={z.zona_id} className={`px-1.5 py-0.5 rounded text-[10px] ${getZonaColor(z.zona_id)}`}>
                                        {z.zona_nombre}
                                      </span>
                                    ))}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Explicación (colapsable) */}
            <div className="mb-4">
              <button
                onClick={() => setMostrarExplicacion(!mostrarExplicacion)}
                className="flex items-center gap-2 text-xs text-gray-500 hover:text-gray-700"
              >
                {mostrarExplicacion ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                <span>¿Cómo se distribuyen los costos?</span>
              </button>
              {mostrarExplicacion && (
                <div className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded text-xs text-gray-600">
                  <ul className="ml-4 list-disc space-y-1">
                    <li><strong>Flete Fijo:</strong> Se asigna según los municipios que atiende cada ruta.</li>
                    <li><strong>Lejanías:</strong> Combustible + Peajes + Pernoctas.</li>
                    <li><strong>Gastos Fijos:</strong> Canon, seguros, mantenimiento, según las rutas del vehículo.</li>
                  </ul>
                </div>
              )}
            </div>

            {/* Tabla de distribución por zona */}
            <div className="text-xs font-medium text-gray-600 mb-2">
              Costos Asignados por Zona
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="text-left px-3 py-2 font-medium text-gray-600">Zona</th>
                    <th className="text-right px-3 py-2 font-medium text-gray-600">Part.</th>
                    <th className="text-right px-3 py-2 font-medium text-gray-600">Flete Fijo</th>
                    <th className="text-right px-3 py-2 font-medium text-gray-600">Lejanías</th>
                    <th className="text-right px-3 py-2 font-medium text-gray-600">Gastos Flota</th>
                    <th className="text-right px-3 py-2 font-medium text-gray-600">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {distribucion.distribucion_a_zonas.map((zona) => (
                    <tr key={zona.zona_id} className="border-t border-gray-100 hover:bg-gray-50">
                      <td className="px-3 py-2 text-gray-800">
                        {zona.zona_nombre}
                      </td>
                      <td className="px-3 py-2 text-right text-gray-500">
                        {zona.participacion_ventas.toFixed(1)}%
                      </td>
                      <td className="px-3 py-2 text-right text-gray-700">
                        {formatCurrency(zona.flete_fijo_asignado || 0)}
                      </td>
                      <td className="px-3 py-2 text-right text-gray-700">
                        {formatCurrency(zona.lejanias_asignado || 0)}
                      </td>
                      <td className="px-3 py-2 text-right text-gray-700">
                        {formatCurrency(zona.costo_flota_asignado)}
                      </td>
                      <td className="px-3 py-2 text-right font-medium text-gray-900">
                        {formatCurrency(zona.costo_total_asignado)}
                      </td>
                    </tr>
                  ))}
                  {/* Fila de totales */}
                  <tr className="border-t-2 border-gray-300 bg-gray-50 font-medium">
                    <td className="px-3 py-2 text-gray-800">TOTAL</td>
                    <td className="px-3 py-2 text-right text-gray-500">100%</td>
                    <td className="px-3 py-2 text-right text-gray-700">
                      {formatCurrency(distribucion.distribucion_a_zonas.reduce((sum, z) => sum + (z.flete_fijo_asignado || 0), 0))}
                    </td>
                    <td className="px-3 py-2 text-right text-gray-700">
                      {formatCurrency(distribucion.distribucion_a_zonas.reduce((sum, z) => sum + (z.lejanias_asignado || 0), 0))}
                    </td>
                    <td className="px-3 py-2 text-right text-gray-700">
                      {formatCurrency(distribucion.distribucion_a_zonas.reduce((sum, z) => sum + z.costo_flota_asignado, 0))}
                    </td>
                    <td className="px-3 py-2 text-right font-bold text-gray-900">
                      {formatCurrency(distribucion.distribucion_a_zonas.reduce((sum, z) => sum + z.costo_total_asignado, 0))}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Comparación con Simulador (colapsable) */}
            <div className="mt-4">
              <button
                onClick={() => setMostrarComparacion(!mostrarComparacion)}
                className="flex items-center gap-2 text-xs text-gray-500 hover:text-gray-700"
              >
                {mostrarComparacion ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                <span>Comparación con Simulador</span>
                {(Math.abs(distribucion.resumen.diferencia_lejanias) < 1 && Math.abs(distribucion.resumen.diferencia_flota) < 1) && (
                  <span className="text-green-600 text-[10px]">✓ OK</span>
                )}
              </button>
              {mostrarComparacion && (
                <div className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded text-xs">
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <span className="text-gray-500">Lejanías (Sim):</span>
                      <span className="ml-1 font-medium">{formatCurrency(distribucion.resumen.total_lejanias_simulador)}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Distribuidas:</span>
                      <span className="ml-1 font-medium">{formatCurrency(distribucion.resumen.total_costo_por_municipios)}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Δ:</span>
                      <span className={`ml-1 font-medium ${Math.abs(distribucion.resumen.diferencia_lejanias) < 1 ? 'text-green-600' : 'text-amber-600'}`}>
                        {formatCurrency(distribucion.resumen.diferencia_lejanias)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Flota (Sim):</span>
                      <span className="ml-1 font-medium">{formatCurrency(distribucion.resumen.total_flota_simulador)}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Distribuida:</span>
                      <span className="ml-1 font-medium">{formatCurrency(distribucion.resumen.total_flota_distribuida)}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Δ:</span>
                      <span className={`ml-1 font-medium ${Math.abs(distribucion.resumen.diferencia_flota) < 1 ? 'text-green-600' : 'text-amber-600'}`}>
                        {formatCurrency(distribucion.resumen.diferencia_flota)}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Componente separado para el detalle del recorrido (para mantener el código limpio)
function DetalleRecorrido({
  recorrido,
  formatCurrency,
  getEsquemaColor,
  costoUnitario,
  recorridosMes
}: {
  recorrido: DetalleRutaLogistica;
  formatCurrency: (value: number) => string;
  getEsquemaColor: (esquema: string | null) => string;
  costoUnitario: { flete: number; combustible: number; peajes: number; pernocta: number; total: number };
  recorridosMes: number;
}) {
  return (
    <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
      {/* Desglose de costos: Unitario → Mensual */}
      <div className="mb-4 p-3 bg-white rounded border border-gray-200">
        <div className="text-xs font-medium text-gray-600 mb-2">Desglose de costos</div>
        <table className="w-full text-xs">
          <thead>
            <tr className="text-gray-500">
              <th className="text-left font-medium pb-1">Concepto</th>
              <th className="text-right font-medium pb-1">Por recorrido</th>
              <th className="text-center font-medium pb-1 w-16">×{recorridosMes}</th>
              <th className="text-right font-medium pb-1">Mensual</th>
            </tr>
          </thead>
          <tbody className="text-gray-700">
            <tr>
              <td className="py-0.5">Flete</td>
              <td className="text-right">{formatCurrency(costoUnitario.flete)}</td>
              <td className="text-center text-gray-400">→</td>
              <td className="text-right">{formatCurrency(recorrido.flete_base_mensual)}</td>
            </tr>
            <tr>
              <td className="py-0.5">Combustible</td>
              <td className="text-right">{formatCurrency(costoUnitario.combustible)}</td>
              <td className="text-center text-gray-400">→</td>
              <td className="text-right">{formatCurrency(recorrido.combustible_mensual)}</td>
            </tr>
            <tr>
              <td className="py-0.5">Peajes</td>
              <td className="text-right">{formatCurrency(costoUnitario.peajes)}</td>
              <td className="text-center text-gray-400">→</td>
              <td className="text-right">{formatCurrency(recorrido.peaje_mensual)}</td>
            </tr>
            {recorrido.requiere_pernocta && (
              <tr>
                <td className="py-0.5">Pernocta</td>
                <td className="text-right">{formatCurrency(costoUnitario.pernocta)}</td>
                <td className="text-center text-gray-400">→</td>
                <td className="text-right">{formatCurrency(recorrido.pernocta_mensual)}</td>
              </tr>
            )}
            <tr className="border-t border-gray-200 font-medium">
              <td className="pt-1">Total</td>
              <td className="text-right pt-1">{formatCurrency(costoUnitario.total)}</td>
              <td className="text-center text-gray-400 pt-1">→</td>
              <td className="text-right pt-1">{formatCurrency(recorrido.total_mensual)}</td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Info técnica del vehículo */}
      {recorrido.detalle && (
        <div className="mb-4 p-2 bg-white rounded border border-gray-200">
          <div className="grid grid-cols-4 gap-2 text-xs">
            <div>
              <span className="text-gray-500">Bodega:</span>{' '}
              <span className="font-medium">{recorrido.detalle.bodega || 'N/A'}</span>
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
              <span className="text-gray-500">Km lejanía:</span>{' '}
              <span className="font-medium">{recorrido.detalle.distancia_efectiva_km != null ? Number(recorrido.detalle.distancia_efectiva_km).toFixed(1) : '0'} km</span>
            </div>
          </div>
        </div>
      )}

      {/* Tramos del circuito */}
      {recorrido.detalle?.tramos && recorrido.detalle.tramos.length > 0 && (
        <div className="mb-4 p-3 bg-gray-50 border border-gray-200 rounded">
          <div className="text-xs font-medium text-gray-600 mb-2">
            Circuito: {Math.round(recorrido.detalle.distancia_circuito_km || 0)} km
          </div>
          <div className="text-xs text-gray-500">
            {recorrido.detalle.tramos.map((tramo: any, idx: number) => (
              <span key={idx}>
                {idx === 0 && tramo.origen}
                {' → '}
                {tramo.destino}
                <span className="text-gray-400 ml-1">({tramo.distancia_km || 0}km{tramo.peaje > 0 && `, peaje ${formatCurrency(tramo.peaje)}`})</span>
              </span>
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
                {/* Fila TOTAL */}
                <tr className="bg-gray-200 font-semibold border-t border-gray-300">
                  <td className="px-2 py-1 text-center">-</td>
                  <td className="px-2 py-1">TOTAL</td>
                  <td className="px-2 py-1 text-right text-orange-600">
                    {formatCurrency(recorrido.detalle.municipios.reduce((sum: number, m: any) => sum + (m.flete_base || 0), 0))}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
