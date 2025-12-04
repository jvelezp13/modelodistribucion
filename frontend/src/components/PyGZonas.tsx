'use client';

import React, { useState, useEffect } from 'react';
import { apiClient, PyGZonasResponse, PyGZona, MESES, getMesActual, VentasMensualesDesglose } from '@/lib/api';
import { ChevronDown, ChevronRight, MapPin, TrendingUp, TrendingDown, Users, Truck, Building2, Calendar, DollarSign, Percent } from 'lucide-react';

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
  const [mesSeleccionado, setMesSeleccionado] = useState<string>(getMesActual());

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

  // Obtener ventas del mes seleccionado
  const getVentasMes = (): number => {
    if (!data?.ventas_mensuales) return 0;
    const ventas = data.ventas_mensuales as VentasMensualesDesglose;
    return ventas[mesSeleccionado as keyof VentasMensualesDesglose] || 0;
  };

  const ventasTotalMes = getVentasMes();

  // Calcular ventas de una zona según su participación
  const calcularVentasZona = (zona: PyGZona): number => {
    return ventasTotalMes * (zona.zona.participacion_ventas / 100);
  };

  // Calcular margen bruto de una zona (ventas - CMV)
  const calcularMargenBrutoZona = (zona: PyGZona): number => {
    const ventas = calcularVentasZona(zona);
    const descuentoPonderado = data?.configuracion_descuentos?.descuento_pie_factura_ponderado || 0;
    // Margen bruto = ventas * descuento_pie_factura (el descuento ES el margen del distribuidor)
    return ventas * (descuentoPonderado / 100);
  };

  // Calcular utilidad operacional de una zona
  const calcularUtilidadOperacional = (zona: PyGZona): number => {
    const margenBruto = calcularMargenBrutoZona(zona);
    return margenBruto - zona.total_mensual;
  };

  // Calcular otros ingresos (rebate + descuento financiero)
  const calcularOtrosIngresos = (zona: PyGZona): number => {
    if (!data?.configuracion_descuentos) return 0;
    const ventas = calcularVentasZona(zona);
    const config = data.configuracion_descuentos;

    const rebate = ventas * (config.porcentaje_rebate / 100);
    const descFinanciero = config.aplica_descuento_financiero
      ? ventas * (config.porcentaje_descuento_financiero / 100)
      : 0;

    return rebate + descFinanciero;
  };

  // Calcular utilidad antes de impuestos
  const calcularUtilidadAntesImpuestos = (zona: PyGZona): number => {
    return calcularUtilidadOperacional(zona) + calcularOtrosIngresos(zona);
  };

  // Calcular utilidad neta (después de impuestos)
  const calcularUtilidadNeta = (zona: PyGZona): number => {
    const utilidadAntesImp = calcularUtilidadAntesImpuestos(zona);
    const tasaImpuesto = data?.tasa_impuesto_renta || 0.33;
    const impuesto = utilidadAntesImp > 0 ? utilidadAntesImp * tasaImpuesto : 0;
    return utilidadAntesImp - impuesto;
  };

  // Calcular margen neto sobre ventas
  const calcularMargenNeto = (zona: PyGZona): number => {
    const ventas = calcularVentasZona(zona);
    if (ventas === 0) return 0;
    return (calcularUtilidadNeta(zona) / ventas) * 100;
  };

  // Calcular totales con desglose detallado para diagnóstico
  const calcularTotales = () => {
    if (!data?.zonas) return {
      comercial: 0, logistico: 0, administrativo: 0, costoTotal: 0,
      ventas: 0, margenBruto: 0, utilidadOperacional: 0, utilidadNeta: 0,
      // Subtotales para diagnóstico
      comercialPersonal: 0, comercialGastos: 0, comercialLejanias: 0,
      logisticoPersonal: 0, logisticoGastos: 0, logisticoLejanias: 0,
      administrativoPersonal: 0, administrativoGastos: 0
    };

    return data.zonas.reduce((acc, zona) => ({
      comercial: acc.comercial + zona.comercial.total,
      logistico: acc.logistico + zona.logistico.total,
      administrativo: acc.administrativo + zona.administrativo.total,
      costoTotal: acc.costoTotal + zona.total_mensual,
      ventas: acc.ventas + calcularVentasZona(zona),
      margenBruto: acc.margenBruto + calcularMargenBrutoZona(zona),
      utilidadOperacional: acc.utilidadOperacional + calcularUtilidadOperacional(zona),
      utilidadNeta: acc.utilidadNeta + calcularUtilidadNeta(zona),
      // Subtotales para diagnóstico
      comercialPersonal: acc.comercialPersonal + zona.comercial.personal,
      comercialGastos: acc.comercialGastos + zona.comercial.gastos,
      comercialLejanias: acc.comercialLejanias + (zona.comercial.lejanias || 0),
      logisticoPersonal: acc.logisticoPersonal + zona.logistico.personal,
      logisticoGastos: acc.logisticoGastos + zona.logistico.gastos,
      logisticoLejanias: acc.logisticoLejanias + (zona.logistico.lejanias || 0),
      administrativoPersonal: acc.administrativoPersonal + zona.administrativo.personal,
      administrativoGastos: acc.administrativoGastos + zona.administrativo.gastos
    }), {
      comercial: 0, logistico: 0, administrativo: 0, costoTotal: 0,
      ventas: 0, margenBruto: 0, utilidadOperacional: 0, utilidadNeta: 0,
      // Subtotales para diagnóstico
      comercialPersonal: 0, comercialGastos: 0, comercialLejanias: 0,
      logisticoPersonal: 0, logisticoGastos: 0, logisticoLejanias: 0,
      administrativoPersonal: 0, administrativoGastos: 0
    });
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

  const margenNetoTotal = totales.ventas > 0 ? (totales.utilidadNeta / totales.ventas) * 100 : 0;

  return (
    <div className="space-y-4">
      {/* Header con selector de mes */}
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
            <div className="flex items-center gap-4">
              {/* Selector de mes */}
              <div className="flex items-center gap-2">
                <Calendar size={14} className="text-gray-500" />
                <select
                  value={mesSeleccionado}
                  onChange={(e) => setMesSeleccionado(e.target.value)}
                  className="text-xs border border-gray-300 rounded px-2 py-1 bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {MESES.map((mes) => (
                    <option key={mes.value} value={mes.value}>
                      {mes.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Resumen ejecutivo */}
        <div className="grid grid-cols-4 gap-4 p-4 bg-gradient-to-r from-slate-50 to-gray-50 border-b border-gray-200">
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-xs text-gray-500 mb-1">
              <DollarSign size={12} />
              <span>Ventas del Mes</span>
            </div>
            <div className="text-sm font-bold text-gray-800">{formatCurrency(totales.ventas)}</div>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-xs text-gray-500 mb-1">
              <Percent size={12} />
              <span>Margen Bruto</span>
            </div>
            <div className="text-sm font-bold text-emerald-600">{formatCurrency(totales.margenBruto)}</div>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-xs text-gray-500 mb-1">
              <TrendingUp size={12} />
              <span>Util. Operacional</span>
            </div>
            <div className={`text-sm font-bold ${totales.utilidadOperacional >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
              {formatCurrency(totales.utilidadOperacional)}
            </div>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-xs text-gray-500 mb-1">
              {margenNetoTotal >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
              <span>Util. Neta</span>
            </div>
            <div className={`text-sm font-bold ${totales.utilidadNeta >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(totales.utilidadNeta)}
              <span className="text-[10px] ml-1">({formatPercent(margenNetoTotal)})</span>
            </div>
          </div>
        </div>

        {/* Resumen por categoría de costos */}
        <div className="grid grid-cols-4 gap-4 p-4 bg-gray-50 border-b border-gray-200">
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
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-xs text-gray-500 mb-1">
              <span>Total Costos</span>
            </div>
            <div className="text-sm font-bold text-gray-900">{formatCurrency(totales.costoTotal)}</div>
          </div>
        </div>

        {/* Panel de Diagnóstico - Subtotales detallados para comparar con P&G Detallado */}
        <div className="p-4 bg-amber-50 border-b border-amber-200">
          <h4 className="text-xs font-semibold text-amber-800 mb-3 flex items-center gap-2">
            <span className="px-2 py-0.5 bg-amber-200 rounded text-[10px]">DIAGNÓSTICO</span>
            Subtotales para validación vs P&G Detallado
          </h4>
          <div className="grid grid-cols-3 gap-4 text-xs">
            {/* Comercial */}
            <div className="bg-white rounded border border-amber-200 p-3">
              <div className="font-semibold text-gray-700 mb-2 flex items-center gap-1">
                <Users size={12} />
                COSTOS COMERCIALES
              </div>
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span className="text-gray-500">Personal Comercial:</span>
                  <span className="font-medium">{formatCurrency(totales.comercialPersonal)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Gastos Comerciales:</span>
                  <span className="font-medium">{formatCurrency(totales.comercialGastos)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Lejanías Comerciales:</span>
                  <span className="font-medium text-orange-600">{formatCurrency(totales.comercialLejanias)}</span>
                </div>
                <div className="flex justify-between border-t border-gray-200 pt-1 mt-1">
                  <span className="font-semibold text-gray-700">Total Comercial:</span>
                  <span className="font-bold text-gray-900">{formatCurrency(totales.comercial)}</span>
                </div>
              </div>
            </div>

            {/* Logístico */}
            <div className="bg-white rounded border border-amber-200 p-3">
              <div className="font-semibold text-gray-700 mb-2 flex items-center gap-1">
                <Truck size={12} />
                COSTOS LOGÍSTICOS
              </div>
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span className="text-gray-500">Personal Logístico:</span>
                  <span className="font-medium">{formatCurrency(totales.logisticoPersonal)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Gastos Logísticos:</span>
                  <span className="font-medium">{formatCurrency(totales.logisticoGastos)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Lejanías Logísticas:</span>
                  <span className="font-medium text-orange-600">{formatCurrency(totales.logisticoLejanias)}</span>
                </div>
                <div className="flex justify-between border-t border-gray-200 pt-1 mt-1">
                  <span className="font-semibold text-gray-700">Total Logístico:</span>
                  <span className="font-bold text-gray-900">{formatCurrency(totales.logistico)}</span>
                </div>
              </div>
            </div>

            {/* Administrativo */}
            <div className="bg-white rounded border border-amber-200 p-3">
              <div className="font-semibold text-gray-700 mb-2 flex items-center gap-1">
                <Building2 size={12} />
                COSTOS ADMINISTRATIVOS
              </div>
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span className="text-gray-500">Personal Admin:</span>
                  <span className="font-medium">{formatCurrency(totales.administrativoPersonal)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Gastos Admin:</span>
                  <span className="font-medium">{formatCurrency(totales.administrativoGastos)}</span>
                </div>
                <div className="flex justify-between border-t border-gray-200 pt-1 mt-1">
                  <span className="font-semibold text-gray-700">Total Admin:</span>
                  <span className="font-bold text-gray-900">{formatCurrency(totales.administrativo)}</span>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-3 text-[10px] text-amber-700">
            Compara estos valores con el P&G Detallado para identificar diferencias.
          </div>
        </div>

        {/* Tabla de zonas */}
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-gray-100 border-b border-gray-200">
              <tr>
                <th className="text-left px-3 py-2 font-semibold text-gray-700">Zona</th>
                <th className="text-right px-3 py-2 font-semibold text-gray-700">Part.</th>
                <th className="text-right px-3 py-2 font-semibold text-gray-700">Ventas</th>
                <th className="text-right px-3 py-2 font-semibold text-gray-700">Margen Bruto</th>
                <th className="text-right px-3 py-2 font-semibold text-gray-700">Costos</th>
                <th className="text-right px-3 py-2 font-semibold text-gray-700">Util. Oper.</th>
                <th className="text-right px-3 py-2 font-semibold text-gray-700">Util. Neta</th>
                <th className="text-right px-3 py-2 font-semibold text-gray-700">Margen</th>
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
                  ventasZona={calcularVentasZona(zona)}
                  margenBruto={calcularMargenBrutoZona(zona)}
                  utilidadOperacional={calcularUtilidadOperacional(zona)}
                  utilidadNeta={calcularUtilidadNeta(zona)}
                  margenNeto={calcularMargenNeto(zona)}
                  otrosIngresos={calcularOtrosIngresos(zona)}
                  tasaImpuesto={data.tasa_impuesto_renta}
                />
              ))}
            </tbody>
            <tfoot className="bg-gray-100 border-t-2 border-gray-300">
              <tr>
                <td className="px-3 py-2 font-bold text-gray-800">TOTAL</td>
                <td className="text-right px-3 py-2 font-bold text-gray-800">100%</td>
                <td className="text-right px-3 py-2 font-bold text-gray-800">{formatCurrency(totales.ventas)}</td>
                <td className="text-right px-3 py-2 font-bold text-emerald-700">{formatCurrency(totales.margenBruto)}</td>
                <td className="text-right px-3 py-2 font-bold text-gray-800">{formatCurrency(totales.costoTotal)}</td>
                <td className={`text-right px-3 py-2 font-bold ${totales.utilidadOperacional >= 0 ? 'text-blue-700' : 'text-red-700'}`}>
                  {formatCurrency(totales.utilidadOperacional)}
                </td>
                <td className={`text-right px-3 py-2 font-bold ${totales.utilidadNeta >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                  {formatCurrency(totales.utilidadNeta)}
                </td>
                <td className={`text-right px-3 py-2 font-bold ${margenNetoTotal >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                  {formatPercent(margenNetoTotal)}
                </td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* Gráfico de rentabilidad por zona */}
      <div className="bg-white border border-gray-200 rounded p-4">
        <h4 className="text-xs font-semibold text-gray-700 mb-3 flex items-center gap-1">
          <TrendingUp size={14} />
          Rentabilidad por Zona (Margen Neto %)
        </h4>
        <div className="space-y-2">
          {data.zonas
            .map(zona => ({
              zona,
              margen: calcularMargenNeto(zona),
              ventas: calcularVentasZona(zona)
            }))
            .sort((a, b) => b.margen - a.margen)
            .map(({ zona, margen, ventas }) => {
              const isPositive = margen >= 0;
              const barWidth = Math.min(Math.abs(margen) * 5, 100); // Escala para visualización

              return (
                <div key={zona.zona.id} className="flex items-center gap-2">
                  <div className="w-28 text-xs text-gray-600 truncate" title={zona.zona.nombre}>
                    {zona.zona.nombre}
                  </div>
                  <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden relative">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        isPositive ? 'bg-green-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                  <div className={`w-20 text-right text-xs font-medium ${
                    isPositive ? 'text-green-700' : 'text-red-700'
                  }`}>
                    {formatPercent(margen)}
                  </div>
                  <div className="w-24 text-right text-[10px] text-gray-500">
                    {formatCurrency(ventas)}
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
  ventasZona: number;
  margenBruto: number;
  utilidadOperacional: number;
  utilidadNeta: number;
  margenNeto: number;
  otrosIngresos: number;
  tasaImpuesto: number;
}

function ZonaRow({
  zona, isExpanded, onToggle, onVerMunicipios, formatCurrency, formatPercent, isEven,
  ventasZona, margenBruto, utilidadOperacional, utilidadNeta, margenNeto, otrosIngresos, tasaImpuesto
}: ZonaRowProps) {
  const isRentable = utilidadNeta >= 0;

  return (
    <>
      <tr className={`border-b border-gray-100 hover:bg-blue-50 transition-colors ${isEven ? 'bg-white' : 'bg-gray-50'}`}>
        <td className="px-3 py-2">
          <button
            onClick={onToggle}
            className="flex items-center gap-1.5 text-gray-800 hover:text-blue-600"
          >
            {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            <MapPin size={12} className={isRentable ? 'text-green-500' : 'text-red-500'} />
            <span className="font-medium">{zona.zona.nombre}</span>
          </button>
        </td>
        <td className="text-right px-3 py-2">
          <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px] font-medium">
            {formatPercent(zona.zona.participacion_ventas)}
          </span>
        </td>
        <td className="text-right px-3 py-2 text-gray-700">{formatCurrency(ventasZona)}</td>
        <td className="text-right px-3 py-2 text-emerald-600">{formatCurrency(margenBruto)}</td>
        <td className="text-right px-3 py-2 text-gray-700">{formatCurrency(zona.total_mensual)}</td>
        <td className={`text-right px-3 py-2 ${utilidadOperacional >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
          {formatCurrency(utilidadOperacional)}
        </td>
        <td className={`text-right px-3 py-2 font-semibold ${isRentable ? 'text-green-600' : 'text-red-600'}`}>
          {formatCurrency(utilidadNeta)}
        </td>
        <td className="text-right px-3 py-2">
          <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
            isRentable ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          }`}>
            {formatPercent(margenNeto)}
          </span>
        </td>
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
          <td colSpan={9} className="px-6 py-3">
            {/* Resumen P&G de la zona */}
            <div className="bg-white rounded border border-gray-200 p-4 mb-3">
              <h5 className="text-xs font-semibold text-gray-700 mb-3">Estado de Resultados - {zona.zona.nombre}</h5>
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div className="space-y-1">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Ventas del Período:</span>
                    <span className="font-medium">{formatCurrency(ventasZona)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">(-) CMV:</span>
                    <span className="font-medium text-gray-500">{formatCurrency(ventasZona - margenBruto)}</span>
                  </div>
                  <div className="flex justify-between border-t pt-1">
                    <span className="font-semibold text-emerald-700">Margen Bruto:</span>
                    <span className="font-bold text-emerald-700">{formatCurrency(margenBruto)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">(-) Costos Operativos:</span>
                    <span className="font-medium text-gray-500">{formatCurrency(zona.total_mensual)}</span>
                  </div>
                  <div className="flex justify-between border-t pt-1">
                    <span className="font-semibold text-blue-700">Utilidad Operacional:</span>
                    <span className={`font-bold ${utilidadOperacional >= 0 ? 'text-blue-700' : 'text-red-700'}`}>
                      {formatCurrency(utilidadOperacional)}
                    </span>
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between">
                    <span className="text-gray-600">(+) Otros Ingresos (Rebate, Desc. Fin.):</span>
                    <span className="font-medium text-teal-600">{formatCurrency(otrosIngresos)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Utilidad antes de Impuestos:</span>
                    <span className="font-medium">{formatCurrency(utilidadOperacional + otrosIngresos)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">(-) Impuesto Renta ({formatPercent(tasaImpuesto * 100)}):</span>
                    <span className="font-medium text-gray-500">
                      {formatCurrency((utilidadOperacional + otrosIngresos) > 0
                        ? (utilidadOperacional + otrosIngresos) * tasaImpuesto
                        : 0)}
                    </span>
                  </div>
                  <div className="flex justify-between border-t pt-1">
                    <span className="font-semibold text-green-700">Utilidad Neta:</span>
                    <span className={`font-bold ${isRentable ? 'text-green-700' : 'text-red-700'}`}>
                      {formatCurrency(utilidadNeta)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Margen Neto:</span>
                    <span className={`font-medium ${isRentable ? 'text-green-600' : 'text-red-600'}`}>
                      {formatPercent(margenNeto)}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Desglose de costos */}
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
                  {zona.comercial.lejanias !== undefined && zona.comercial.lejanias > 0 && (
                    <div className="flex justify-between">
                      <span className="text-gray-500">Lejanías:</span>
                      <span className="font-medium text-orange-600">{formatCurrency(zona.comercial.lejanias)}</span>
                    </div>
                  )}
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
                  {zona.logistico.lejanias !== undefined && zona.logistico.lejanias > 0 && (
                    <div className="flex justify-between">
                      <span className="text-gray-500">Lejanías:</span>
                      <span className="font-medium text-orange-600">{formatCurrency(zona.logistico.lejanias)}</span>
                    </div>
                  )}
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
          </td>
        </tr>
      )}
    </>
  );
}
