'use client';

import React, { useState, useEffect } from 'react';
import { apiClient, PyGZonasResponse, PyGZona } from '@/lib/api';
import { ChevronDown, ChevronRight, MapPin, TrendingUp, Users, Truck, Building2 } from 'lucide-react';

interface PyGZonasProps {
  escenarioId: number;
  marcaId: string;
  onZonaSelect?: (zonaId: number, zonaNombre: string) => void;
}

export default function PyGZonas({ escenarioId, marcaId, onZonaSelect }: PyGZonasProps) {
  const [data, setData] = useState<PyGZonasResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedZonas, setExpandedZonas] = useState<Set<number>>(new Set());

  useEffect(() => {
    const fetchData = async () => {
      if (!escenarioId || !marcaId) return;

      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.obtenerPyGZonas(escenarioId, marcaId);
        setData(response);
      } catch (err) {
        console.error('Error cargando P&G por zonas:', err);
        setError('Error al cargar los datos de P&G por zonas');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [escenarioId, marcaId]);

  const toggleZona = (zonaId: number) => {
    setExpandedZonas(prev => {
      const newSet = new Set(prev);
      if (newSet.has(zonaId)) {
        newSet.delete(zonaId);
      } else {
        newSet.add(zonaId);
      }
      return newSet;
    });
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  // Calcular totales
  const calcularTotales = () => {
    if (!data?.zonas) return { comercial: 0, logistico: 0, administrativo: 0, total: 0 };

    return data.zonas.reduce((acc, zona) => ({
      comercial: acc.comercial + zona.comercial.total,
      logistico: acc.logistico + zona.logistico.total,
      administrativo: acc.administrativo + zona.administrativo.total,
      total: acc.total + zona.total_mensual
    }), { comercial: 0, logistico: 0, administrativo: 0, total: 0 });
  };

  const totales = calcularTotales();

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded p-8 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-2 text-sm text-gray-600">Cargando P&G por zonas...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded p-4 text-center">
        <p className="text-sm text-red-700">{error}</p>
      </div>
    );
  }

  if (!data || data.zonas.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded p-4 text-center">
        <p className="text-sm text-yellow-700">No hay zonas configuradas para esta marca</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-white border border-gray-200 rounded">
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-sm font-semibold text-gray-800">
                P&G por Zonas Comerciales - {data.marca_nombre}
              </h3>
              <p className="text-xs text-gray-500 mt-0.5">
                {data.total_zonas} zonas | {data.escenario_nombre}
              </p>
            </div>
            <div className="text-right">
              <div className="text-xs text-gray-500">Total Mensual</div>
              <div className="text-lg font-bold text-gray-900">{formatCurrency(totales.total)}</div>
            </div>
          </div>
        </div>

        {/* Resumen por categoría */}
        <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 border-b border-gray-200">
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-xs text-gray-500 mb-1">
              <Users size={12} />
              <span>Comercial</span>
            </div>
            <div className="text-sm font-semibold text-gray-800">{formatCurrency(totales.comercial)}</div>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-xs text-gray-500 mb-1">
              <Truck size={12} />
              <span>Logístico</span>
            </div>
            <div className="text-sm font-semibold text-gray-800">{formatCurrency(totales.logistico)}</div>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-xs text-gray-500 mb-1">
              <Building2 size={12} />
              <span>Administrativo</span>
            </div>
            <div className="text-sm font-semibold text-gray-800">{formatCurrency(totales.administrativo)}</div>
          </div>
        </div>

        {/* Tabla de zonas */}
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-gray-100 border-b border-gray-200">
              <tr>
                <th className="text-left px-3 py-2 font-semibold text-gray-700">Zona</th>
                <th className="text-right px-3 py-2 font-semibold text-gray-700">Part. Ventas</th>
                <th className="text-right px-3 py-2 font-semibold text-gray-700">Comercial</th>
                <th className="text-right px-3 py-2 font-semibold text-gray-700">Logístico</th>
                <th className="text-right px-3 py-2 font-semibold text-gray-700">Admin.</th>
                <th className="text-right px-3 py-2 font-semibold text-gray-700">Total Mensual</th>
                <th className="text-center px-3 py-2 font-semibold text-gray-700">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {data.zonas.map((zona, idx) => (
                <ZonaRow
                  key={zona.zona.id}
                  zona={zona}
                  isExpanded={expandedZonas.has(zona.zona.id)}
                  onToggle={() => toggleZona(zona.zona.id)}
                  onVerMunicipios={onZonaSelect ? () => onZonaSelect(zona.zona.id, zona.zona.nombre) : undefined}
                  formatCurrency={formatCurrency}
                  formatPercent={formatPercent}
                  isEven={idx % 2 === 0}
                />
              ))}
            </tbody>
            <tfoot className="bg-gray-100 border-t-2 border-gray-300">
              <tr>
                <td className="px-3 py-2 font-bold text-gray-800">TOTAL</td>
                <td className="text-right px-3 py-2 font-bold text-gray-800">100%</td>
                <td className="text-right px-3 py-2 font-bold text-gray-800">{formatCurrency(totales.comercial)}</td>
                <td className="text-right px-3 py-2 font-bold text-gray-800">{formatCurrency(totales.logistico)}</td>
                <td className="text-right px-3 py-2 font-bold text-gray-800">{formatCurrency(totales.administrativo)}</td>
                <td className="text-right px-3 py-2 font-bold text-gray-800">{formatCurrency(totales.total)}</td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* Gráfico de participación */}
      <div className="bg-white border border-gray-200 rounded p-4">
        <h4 className="text-xs font-semibold text-gray-700 mb-3 flex items-center gap-1">
          <TrendingUp size={14} />
          Distribución de Costos por Zona
        </h4>
        <div className="space-y-2">
          {data.zonas.map(zona => {
            const porcentaje = totales.total > 0 ? (zona.total_mensual / totales.total) * 100 : 0;
            return (
              <div key={zona.zona.id} className="flex items-center gap-2">
                <div className="w-24 text-xs text-gray-600 truncate" title={zona.zona.nombre}>
                  {zona.zona.nombre}
                </div>
                <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full transition-all duration-300"
                    style={{ width: `${porcentaje}%` }}
                  />
                </div>
                <div className="w-16 text-right text-xs font-medium text-gray-700">
                  {formatPercent(porcentaje)}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

interface ZonaRowProps {
  zona: PyGZona;
  isExpanded: boolean;
  onToggle: () => void;
  onVerMunicipios?: () => void;
  formatCurrency: (value: number) => string;
  formatPercent: (value: number) => string;
  isEven: boolean;
}

function ZonaRow({ zona, isExpanded, onToggle, onVerMunicipios, formatCurrency, formatPercent, isEven }: ZonaRowProps) {
  return (
    <>
      <tr className={`border-b border-gray-100 hover:bg-blue-50 transition-colors ${isEven ? 'bg-white' : 'bg-gray-50'}`}>
        <td className="px-3 py-2">
          <button
            onClick={onToggle}
            className="flex items-center gap-1.5 text-gray-800 hover:text-blue-600"
          >
            {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            <MapPin size={12} className="text-gray-400" />
            <span className="font-medium">{zona.zona.nombre}</span>
          </button>
        </td>
        <td className="text-right px-3 py-2">
          <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px] font-medium">
            {formatPercent(zona.zona.participacion_ventas)}
          </span>
        </td>
        <td className="text-right px-3 py-2 text-gray-700">{formatCurrency(zona.comercial.total)}</td>
        <td className="text-right px-3 py-2 text-gray-700">{formatCurrency(zona.logistico.total)}</td>
        <td className="text-right px-3 py-2 text-gray-700">{formatCurrency(zona.administrativo.total)}</td>
        <td className="text-right px-3 py-2 font-semibold text-gray-900">{formatCurrency(zona.total_mensual)}</td>
        <td className="text-center px-3 py-2">
          {onVerMunicipios && (
            <button
              onClick={onVerMunicipios}
              className="px-2 py-1 text-[10px] font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-100 rounded transition-colors"
            >
              Ver Municipios
            </button>
          )}
        </td>
      </tr>
      {isExpanded && (
        <tr className="bg-gray-50">
          <td colSpan={7} className="px-6 py-3">
            <div className="grid grid-cols-3 gap-4 text-xs">
              {/* Comercial */}
              <div className="bg-white rounded border border-gray-200 p-3">
                <div className="font-semibold text-gray-700 mb-2 flex items-center gap-1">
                  <Users size={12} />
                  Comercial
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Personal:</span>
                    <span className="font-medium">{formatCurrency(zona.comercial.personal)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Gastos:</span>
                    <span className="font-medium">{formatCurrency(zona.comercial.gastos)}</span>
                  </div>
                  <div className="flex justify-between border-t pt-1 mt-1">
                    <span className="font-medium text-gray-700">Total:</span>
                    <span className="font-bold text-gray-900">{formatCurrency(zona.comercial.total)}</span>
                  </div>
                </div>
              </div>

              {/* Logístico */}
              <div className="bg-white rounded border border-gray-200 p-3">
                <div className="font-semibold text-gray-700 mb-2 flex items-center gap-1">
                  <Truck size={12} />
                  Logístico
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Personal:</span>
                    <span className="font-medium">{formatCurrency(zona.logistico.personal)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Gastos:</span>
                    <span className="font-medium">{formatCurrency(zona.logistico.gastos)}</span>
                  </div>
                  <div className="flex justify-between border-t pt-1 mt-1">
                    <span className="font-medium text-gray-700">Total:</span>
                    <span className="font-bold text-gray-900">{formatCurrency(zona.logistico.total)}</span>
                  </div>
                </div>
              </div>

              {/* Administrativo */}
              <div className="bg-white rounded border border-gray-200 p-3">
                <div className="font-semibold text-gray-700 mb-2 flex items-center gap-1">
                  <Building2 size={12} />
                  Administrativo
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Personal:</span>
                    <span className="font-medium">{formatCurrency(zona.administrativo.personal)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Gastos:</span>
                    <span className="font-medium">{formatCurrency(zona.administrativo.gastos)}</span>
                  </div>
                  <div className="flex justify-between border-t pt-1 mt-1">
                    <span className="font-medium text-gray-700">Total:</span>
                    <span className="font-bold text-gray-900">{formatCurrency(zona.administrativo.total)}</span>
                  </div>
                </div>
              </div>
            </div>
            <div className="mt-3 text-right">
              <span className="text-xs text-gray-500">Total Anual: </span>
              <span className="text-sm font-bold text-gray-800">{formatCurrency(zona.total_anual)}</span>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
