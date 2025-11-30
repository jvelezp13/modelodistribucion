'use client';

import React, { useState, useEffect } from 'react';
import { apiClient, PyGMunicipiosResponse, PyGMunicipio } from '@/lib/api';
import { ChevronDown, ChevronRight, Building, TrendingUp, Users, Truck, Building2, ArrowLeft } from 'lucide-react';

interface PyGMunicipiosProps {
  escenarioId: number;
  zonaId: number;
  zonaNombre?: string;
  onBack?: () => void;
}

export default function PyGMunicipios({ escenarioId, zonaId, zonaNombre, onBack }: PyGMunicipiosProps) {
  const [data, setData] = useState<PyGMunicipiosResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedMunicipios, setExpandedMunicipios] = useState<Set<number>>(new Set());

  useEffect(() => {
    const fetchData = async () => {
      if (!escenarioId || !zonaId) return;

      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.obtenerPyGMunicipios(zonaId, escenarioId);
        setData(response);
      } catch (err) {
        console.error('Error cargando P&G por municipios:', err);
        setError('Error al cargar los datos de P&G por municipios');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [escenarioId, zonaId]);

  const toggleMunicipio = (municipioId: number) => {
    setExpandedMunicipios(prev => {
      const newSet = new Set(prev);
      if (newSet.has(municipioId)) {
        newSet.delete(municipioId);
      } else {
        newSet.add(municipioId);
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
    if (!data?.municipios) return { comercial: 0, logistico: 0, administrativo: 0, total: 0 };

    return data.municipios.reduce((acc, mun) => ({
      comercial: acc.comercial + mun.comercial.total,
      logistico: acc.logistico + mun.logistico.total,
      administrativo: acc.administrativo + mun.administrativo.total,
      total: acc.total + mun.total_mensual
    }), { comercial: 0, logistico: 0, administrativo: 0, total: 0 });
  };

  const totales = calcularTotales();

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded p-8 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-2 text-sm text-gray-600">Cargando P&G por municipios...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded p-4 text-center">
        <p className="text-sm text-red-700">{error}</p>
        {onBack && (
          <button
            onClick={onBack}
            className="mt-2 text-xs text-blue-600 hover:text-blue-800"
          >
            Volver a zonas
          </button>
        )}
      </div>
    );
  }

  if (!data || data.municipios.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded p-4 text-center">
        <p className="text-sm text-yellow-700">No hay municipios configurados para esta zona</p>
        {onBack && (
          <button
            onClick={onBack}
            className="mt-2 text-xs text-blue-600 hover:text-blue-800"
          >
            Volver a zonas
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-white border border-gray-200 rounded">
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              {onBack && (
                <button
                  onClick={onBack}
                  className="p-1.5 hover:bg-gray-200 rounded transition-colors"
                  title="Volver a zonas"
                >
                  <ArrowLeft size={16} className="text-gray-600" />
                </button>
              )}
              <div>
                <h3 className="text-sm font-semibold text-gray-800">
                  P&G por Municipios - {zonaNombre || data.zona_nombre}
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  {data.total_municipios} municipios | {data.escenario_nombre}
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs text-gray-500">Total Mensual Zona</div>
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

        {/* Tabla de municipios */}
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-gray-100 border-b border-gray-200">
              <tr>
                <th className="text-left px-3 py-2 font-semibold text-gray-700">Municipio</th>
                <th className="text-center px-3 py-2 font-semibold text-gray-700">DANE</th>
                <th className="text-right px-3 py-2 font-semibold text-gray-700">Part. Zona</th>
                <th className="text-right px-3 py-2 font-semibold text-gray-700">Part. Total</th>
                <th className="text-right px-3 py-2 font-semibold text-gray-700">Comercial</th>
                <th className="text-right px-3 py-2 font-semibold text-gray-700">Logístico</th>
                <th className="text-right px-3 py-2 font-semibold text-gray-700">Admin.</th>
                <th className="text-right px-3 py-2 font-semibold text-gray-700">Total Mensual</th>
              </tr>
            </thead>
            <tbody>
              {data.municipios.map((municipio, idx) => (
                <MunicipioRow
                  key={municipio.municipio.id}
                  municipio={municipio}
                  isExpanded={expandedMunicipios.has(municipio.municipio.id)}
                  onToggle={() => toggleMunicipio(municipio.municipio.id)}
                  formatCurrency={formatCurrency}
                  formatPercent={formatPercent}
                  isEven={idx % 2 === 0}
                />
              ))}
            </tbody>
            <tfoot className="bg-gray-100 border-t-2 border-gray-300">
              <tr>
                <td className="px-3 py-2 font-bold text-gray-800">TOTAL ZONA</td>
                <td></td>
                <td className="text-right px-3 py-2 font-bold text-gray-800">100%</td>
                <td></td>
                <td className="text-right px-3 py-2 font-bold text-gray-800">{formatCurrency(totales.comercial)}</td>
                <td className="text-right px-3 py-2 font-bold text-gray-800">{formatCurrency(totales.logistico)}</td>
                <td className="text-right px-3 py-2 font-bold text-gray-800">{formatCurrency(totales.administrativo)}</td>
                <td className="text-right px-3 py-2 font-bold text-gray-800">{formatCurrency(totales.total)}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* Gráfico de participación */}
      <div className="bg-white border border-gray-200 rounded p-4">
        <h4 className="text-xs font-semibold text-gray-700 mb-3 flex items-center gap-1">
          <TrendingUp size={14} />
          Distribución de Costos por Municipio
        </h4>
        <div className="space-y-2">
          {data.municipios.map(mun => {
            const porcentaje = totales.total > 0 ? (mun.total_mensual / totales.total) * 100 : 0;
            return (
              <div key={mun.municipio.id} className="flex items-center gap-2">
                <div className="w-28 text-xs text-gray-600 truncate" title={mun.municipio.nombre}>
                  {mun.municipio.nombre}
                </div>
                <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                  <div
                    className="h-full bg-green-500 rounded-full transition-all duration-300"
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

interface MunicipioRowProps {
  municipio: PyGMunicipio;
  isExpanded: boolean;
  onToggle: () => void;
  formatCurrency: (value: number) => string;
  formatPercent: (value: number) => string;
  isEven: boolean;
}

function MunicipioRow({ municipio, isExpanded, onToggle, formatCurrency, formatPercent, isEven }: MunicipioRowProps) {
  return (
    <>
      <tr className={`border-b border-gray-100 hover:bg-green-50 transition-colors ${isEven ? 'bg-white' : 'bg-gray-50'}`}>
        <td className="px-3 py-2">
          <button
            onClick={onToggle}
            className="flex items-center gap-1.5 text-gray-800 hover:text-green-600"
          >
            {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            <Building size={12} className="text-gray-400" />
            <span className="font-medium">{municipio.municipio.nombre}</span>
          </button>
        </td>
        <td className="text-center px-3 py-2 text-gray-500 text-[10px]">
          {municipio.municipio.codigo_dane}
        </td>
        <td className="text-right px-3 py-2">
          <span className="px-1.5 py-0.5 bg-green-100 text-green-700 rounded text-[10px] font-medium">
            {formatPercent(municipio.municipio.participacion_ventas)}
          </span>
        </td>
        <td className="text-right px-3 py-2">
          <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px] font-medium">
            {formatPercent(municipio.municipio.participacion_total)}
          </span>
        </td>
        <td className="text-right px-3 py-2 text-gray-700">{formatCurrency(municipio.comercial.total)}</td>
        <td className="text-right px-3 py-2 text-gray-700">{formatCurrency(municipio.logistico.total)}</td>
        <td className="text-right px-3 py-2 text-gray-700">{formatCurrency(municipio.administrativo.total)}</td>
        <td className="text-right px-3 py-2 font-semibold text-gray-900">{formatCurrency(municipio.total_mensual)}</td>
      </tr>
      {isExpanded && (
        <tr className="bg-gray-50">
          <td colSpan={8} className="px-6 py-3">
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
                    <span className="font-medium">{formatCurrency(municipio.comercial.personal)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Gastos:</span>
                    <span className="font-medium">{formatCurrency(municipio.comercial.gastos)}</span>
                  </div>
                  <div className="flex justify-between border-t pt-1 mt-1">
                    <span className="font-medium text-gray-700">Total:</span>
                    <span className="font-bold text-gray-900">{formatCurrency(municipio.comercial.total)}</span>
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
                    <span className="font-medium">{formatCurrency(municipio.logistico.personal)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Gastos:</span>
                    <span className="font-medium">{formatCurrency(municipio.logistico.gastos)}</span>
                  </div>
                  <div className="flex justify-between border-t pt-1 mt-1">
                    <span className="font-medium text-gray-700">Total:</span>
                    <span className="font-bold text-gray-900">{formatCurrency(municipio.logistico.total)}</span>
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
                    <span className="font-medium">{formatCurrency(municipio.administrativo.personal)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Gastos:</span>
                    <span className="font-medium">{formatCurrency(municipio.administrativo.gastos)}</span>
                  </div>
                  <div className="flex justify-between border-t pt-1 mt-1">
                    <span className="font-medium text-gray-700">Total:</span>
                    <span className="font-bold text-gray-900">{formatCurrency(municipio.administrativo.total)}</span>
                  </div>
                </div>
              </div>
            </div>
            <div className="mt-3 text-right">
              <span className="text-xs text-gray-500">Total Anual: </span>
              <span className="text-sm font-bold text-gray-800">{formatCurrency(municipio.total_anual)}</span>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
