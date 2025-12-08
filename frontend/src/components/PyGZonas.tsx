'use client';

import React, { useState, useMemo } from 'react';
import { PyGZonasResponse, PyGZona, MESES, getMesActual, VentasMensualesDesglose } from '@/lib/api';
import { usePyGZonasData, usePyGMunicipios } from '@/hooks/usePyGQueries';
import { ChevronDown, ChevronRight, TrendingUp, TrendingDown, Users, Truck, Building2, Calendar, DollarSign, Percent, MapPin, Building } from 'lucide-react';

interface PyGZonasProps {
  escenarioId: number;
  marcaId: string;
}

export default function PyGZonas({ escenarioId, marcaId }: PyGZonasProps) {
  const { data, isLoading, error } = usePyGZonasData(escenarioId, marcaId);
  const [expandedZonas, setExpandedZonas] = useState<Set<number>>(new Set());
  const [expandedMunicipios, setExpandedMunicipios] = useState<Set<number>>(new Set());
  const [mesSeleccionado, setMesSeleccionado] = useState<string>(getMesActual());

  const toggleZona = (zonaId: number) => {
    setExpandedZonas(prev => {
      const newSet = new Set(prev);
      if (newSet.has(zonaId)) {
        newSet.delete(zonaId);
        // Colapsar municipios de esta zona
        setExpandedMunicipios(new Set());
      } else {
        newSet.add(zonaId);
      }
      return newSet;
    });
  };

  const toggleMunicipios = (zonaId: number) => {
    setExpandedMunicipios(prev => {
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
    return `${value.toFixed(2)}%`;
  };

  // Obtener ventas del mes seleccionado
  const getVentasMes = (): number => {
    if (!data?.ventas_mensuales) return 0;
    const ventas = data.ventas_mensuales as VentasMensualesDesglose;
    return ventas[mesSeleccionado as keyof VentasMensualesDesglose] || 0;
  };

  const ventasTotalMes = getVentasMes();

  // Pre-calcular ventas por zona con ajuste de redondeo
  const ventasPorZona = useMemo(() => {
    if (!data?.zonas) return new Map<number, number>();

    const ventasMap = new Map<number, number>();
    let sumaRedondeada = 0;

    const zonasOrdenadas = [...data.zonas].sort(
      (a, b) => b.zona.participacion_ventas - a.zona.participacion_ventas
    );

    zonasOrdenadas.slice(1).forEach(zona => {
      const ventasExactas = ventasTotalMes * (zona.zona.participacion_ventas / 100);
      const ventasRedondeadas = Math.round(ventasExactas);
      ventasMap.set(zona.zona.id, ventasRedondeadas);
      sumaRedondeada += ventasRedondeadas;
    });

    if (zonasOrdenadas.length > 0) {
      const zonaMayor = zonasOrdenadas[0];
      ventasMap.set(zonaMayor.zona.id, ventasTotalMes - sumaRedondeada);
    }

    return ventasMap;
  }, [data?.zonas, ventasTotalMes]);

  const calcularVentasZona = (zona: PyGZona): number => {
    return ventasPorZona.get(zona.zona.id) || 0;
  };

  const calcularMargenBrutoZona = (zona: PyGZona): number => {
    const ventas = calcularVentasZona(zona);
    const descuentoPonderado = data?.configuracion_descuentos?.descuento_pie_factura_ponderado || 0;
    return ventas * (descuentoPonderado / 100);
  };

  const calcularICA = (zona: PyGZona): number => {
    const ventas = calcularVentasZona(zona);
    // La tasa ICA ahora viene por zona (desde su operación)
    const tasaICA = zona.zona.tasa_ica || 0;
    return ventas * tasaICA;
  };

  const calcularCostosTotalConICA = (zona: PyGZona): number => {
    return zona.total_mensual + calcularICA(zona);
  };

  const calcularUtilidadOperacionalConICA = (zona: PyGZona): number => {
    const margenBruto = calcularMargenBrutoZona(zona);
    return margenBruto - calcularCostosTotalConICA(zona);
  };

  const calcularOtrosIngresos = (zona: PyGZona): number => {
    if (!data?.configuracion_descuentos) return 0;
    const ventas = calcularVentasZona(zona);
    const margenBruto = calcularMargenBrutoZona(zona);
    const config = data.configuracion_descuentos;

    const rebate = ventas * (config.porcentaje_rebate / 100);
    const descFinanciero = config.aplica_descuento_financiero
      ? ventas * (config.porcentaje_descuento_financiero / 100)
      : 0;

    const cesantiaComercial = config.aplica_cesantia_comercial
      ? (margenBruto + rebate + descFinanciero) / 12
      : 0;

    return rebate + descFinanciero + cesantiaComercial;
  };

  const calcularUtilidadAntesImpuestosConICA = (zona: PyGZona): number => {
    return calcularUtilidadOperacionalConICA(zona) + calcularOtrosIngresos(zona);
  };

  const calcularTotalesConsolidados = () => {
    if (!data?.zonas) return { utilidadAntesImpuestos: 0, ventasTotal: 0, impuestoTotal: 0 };

    let utilidadAntesImpuestos = 0;
    let ventasTotal = 0;

    data.zonas.forEach(zona => {
      utilidadAntesImpuestos += calcularUtilidadAntesImpuestosConICA(zona);
      ventasTotal += calcularVentasZona(zona);
    });

    const tasaImpuesto = data?.tasa_impuesto_renta || 0.33;
    const impuestoTotal = utilidadAntesImpuestos > 0 ? utilidadAntesImpuestos * tasaImpuesto : 0;

    return { utilidadAntesImpuestos, ventasTotal, impuestoTotal };
  };

  const consolidado = calcularTotalesConsolidados();

  const calcularImpuestoProrrateado = (zona: PyGZona): number => {
    if (consolidado.ventasTotal === 0 || consolidado.impuestoTotal === 0) return 0;
    const ventasZona = calcularVentasZona(zona);
    const participacion = ventasZona / consolidado.ventasTotal;
    return consolidado.impuestoTotal * participacion;
  };

  const calcularUtilidadNeta = (zona: PyGZona): number => {
    const utilidadAntesImp = calcularUtilidadAntesImpuestosConICA(zona);
    const impuestoProrrateado = calcularImpuestoProrrateado(zona);
    return utilidadAntesImp - impuestoProrrateado;
  };

  const calcularMargenNeto = (zona: PyGZona): number => {
    const ventas = calcularVentasZona(zona);
    if (ventas === 0) return 0;
    return (calcularUtilidadNeta(zona) / ventas) * 100;
  };

  const calcularTotales = () => {
    if (!data?.zonas) return {
      comercial: 0, logistico: 0, administrativo: 0, costoTotal: 0, ica: 0,
      ventas: 0, margenBruto: 0, utilidadOperacional: 0, utilidadNeta: 0, otrosIngresos: 0
    };

    return data.zonas.reduce((acc, zona) => {
      const icaZona = calcularICA(zona);
      return {
        comercial: acc.comercial + zona.comercial.total,
        logistico: acc.logistico + zona.logistico.total,
        administrativo: acc.administrativo + zona.administrativo.total + icaZona,
        costoTotal: acc.costoTotal + zona.total_mensual + icaZona,
        ica: acc.ica + icaZona,
        ventas: acc.ventas + calcularVentasZona(zona),
        margenBruto: acc.margenBruto + calcularMargenBrutoZona(zona),
        utilidadOperacional: acc.utilidadOperacional + calcularUtilidadOperacionalConICA(zona),
        utilidadNeta: acc.utilidadNeta + calcularUtilidadNeta(zona),
        otrosIngresos: acc.otrosIngresos + calcularOtrosIngresos(zona)
      };
    }, {
      comercial: 0, logistico: 0, administrativo: 0, costoTotal: 0, ica: 0,
      ventas: 0, margenBruto: 0, utilidadOperacional: 0, utilidadNeta: 0, otrosIngresos: 0
    });
  };

  const totales = calcularTotales();

  if (isLoading) {
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
        <p className="text-sm text-red-700">Error al cargar los datos</p>
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
      <div className="bg-white border border-gray-200 rounded">
        {/* Header */}
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-sm font-semibold text-gray-800">
                P&G por Zonas y Municipios - {data.marca_nombre}
              </h3>
              <p className="text-xs text-gray-500 mt-0.5">
                {data.total_zonas} zonas | {data.escenario_nombre} | Expande una zona para ver sus municipios
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Calendar size={14} className="text-gray-500" />
              <select
                value={mesSeleccionado}
                onChange={(e) => setMesSeleccionado(e.target.value)}
                className="text-xs border border-gray-300 rounded px-2 py-1 bg-white"
              >
                {MESES.map((mes) => (
                  <option key={mes.value} value={mes.value}>{mes.label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Resumen ejecutivo */}
        <div className="grid grid-cols-4 gap-4 p-4 bg-gradient-to-r from-slate-50 to-gray-50 border-b border-gray-200">
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-xs text-gray-500 mb-1">
              <DollarSign size={12} />
              <span>Ventas</span>
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
              <span>Costos</span>
            </div>
            <div className="text-sm font-bold text-gray-700">{formatCurrency(totales.costoTotal)}</div>
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

        {/* Tabla de zonas */}
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-gray-100 border-b border-gray-200">
              <tr>
                <th className="text-left px-2 py-2 font-semibold text-gray-700">Zona / Municipio</th>
                <th className="text-right px-2 py-2 font-semibold text-gray-700">Part.</th>
                <th className="text-right px-2 py-2 font-semibold text-gray-700">Ventas</th>
                <th className="text-right px-2 py-2 font-semibold text-gray-700">Margen</th>
                <th className="text-right px-2 py-2 font-semibold text-gray-500 text-[10px]">Comerc.</th>
                <th className="text-right px-2 py-2 font-semibold text-gray-500 text-[10px]">Logíst.</th>
                <th className="text-right px-2 py-2 font-semibold text-gray-500 text-[10px]">Admin.</th>
                <th className="text-right px-2 py-2 font-semibold text-gray-700">Costos</th>
                <th className="text-right px-2 py-2 font-semibold text-gray-700">Util. Neta</th>
                <th className="text-right px-2 py-2 font-semibold text-gray-700">%</th>
              </tr>
            </thead>
            <tbody>
              {[...data.zonas]
                .sort((a, b) => calcularMargenNeto(b) - calcularMargenNeto(a))
                .map((zona, idx) => {
                  const ventasZona = calcularVentasZona(zona);
                  const margenBruto = calcularMargenBrutoZona(zona);
                  const costosTotalConICA = calcularCostosTotalConICA(zona);
                  const utilidadNeta = calcularUtilidadNeta(zona);
                  const margenNeto = calcularMargenNeto(zona);
                  const ica = calcularICA(zona);
                  const isRentable = utilidadNeta >= 0;
                  const isExpanded = expandedZonas.has(zona.zona.id);
                  const showMunicipios = expandedMunicipios.has(zona.zona.id);

                  return (
                    <React.Fragment key={zona.zona.id}>
                      {/* Fila de zona */}
                      <tr className={`border-b border-gray-100 hover:bg-blue-50 transition-colors ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                        <td className="px-2 py-2">
                          <button
                            onClick={() => toggleZona(zona.zona.id)}
                            className="flex items-center gap-1 text-gray-800 hover:text-blue-600"
                          >
                            {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                            <MapPin size={10} className={isRentable ? 'text-green-500' : 'text-red-500'} />
                            <span className="font-medium text-[11px]">{zona.zona.nombre}</span>
                          </button>
                        </td>
                        <td className="text-right px-2 py-2">
                          <span className="px-1 py-0.5 bg-blue-100 text-blue-700 rounded text-[9px] font-medium">
                            {formatPercent(zona.zona.participacion_ventas)}
                          </span>
                        </td>
                        <td className="text-right px-2 py-2 text-gray-700 text-[11px]">{formatCurrency(ventasZona)}</td>
                        <td className="text-right px-2 py-2 text-emerald-600 text-[11px]">{formatCurrency(margenBruto)}</td>
                        <td className="text-right px-2 py-2 text-gray-500 text-[10px]">{formatCurrency(zona.comercial.total)}</td>
                        <td className="text-right px-2 py-2 text-gray-500 text-[10px]">{formatCurrency(zona.logistico.total)}</td>
                        <td className="text-right px-2 py-2 text-gray-500 text-[10px]">{formatCurrency(zona.administrativo.total + ica)}</td>
                        <td className="text-right px-2 py-2 text-gray-700 font-medium text-[11px]">{formatCurrency(costosTotalConICA)}</td>
                        <td className={`text-right px-2 py-2 font-semibold text-[11px] ${isRentable ? 'text-green-600' : 'text-red-600'}`}>
                          {formatCurrency(utilidadNeta)}
                        </td>
                        <td className="text-right px-2 py-2">
                          <span className={`px-1 py-0.5 rounded text-[9px] font-medium ${
                            isRentable ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                          }`}>
                            {formatPercent(margenNeto)}
                          </span>
                        </td>
                      </tr>

                      {/* Detalle expandido de zona */}
                      {isExpanded && (
                        <tr className="bg-slate-50">
                          <td colSpan={10} className="px-4 py-3">
                            {/* Desglose de costos */}
                            <div className="grid grid-cols-3 gap-3 mb-3">
                              <div className="bg-white rounded border border-gray-200 p-2">
                                <div className="font-semibold text-gray-700 text-[10px] mb-1 flex items-center gap-1">
                                  <Users size={10} /> Comercial
                                </div>
                                <div className="space-y-0.5 text-[10px]">
                                  <div className="flex justify-between">
                                    <span className="text-gray-500">Personal:</span>
                                    <span>{formatCurrency(zona.comercial.personal)}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-500">Gastos:</span>
                                    <span>{formatCurrency(zona.comercial.gastos)}</span>
                                  </div>
                                  {(zona.comercial.lejanias || 0) > 0 && (
                                    <div className="flex justify-between">
                                      <span className="text-gray-500">Lejanías:</span>
                                      <span className="text-orange-600">{formatCurrency(zona.comercial.lejanias || 0)}</span>
                                    </div>
                                  )}
                                </div>
                              </div>
                              <div className="bg-white rounded border border-gray-200 p-2">
                                <div className="font-semibold text-gray-700 text-[10px] mb-1 flex items-center gap-1">
                                  <Truck size={10} /> Logístico
                                </div>
                                <div className="space-y-0.5 text-[10px]">
                                  <div className="flex justify-between">
                                    <span className="text-gray-500">Personal:</span>
                                    <span>{formatCurrency(zona.logistico.personal)}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-500">Gastos:</span>
                                    <span>{formatCurrency(zona.logistico.gastos)}</span>
                                  </div>
                                  {(zona.logistico.lejanias || 0) > 0 && (
                                    <div className="flex justify-between">
                                      <span className="text-gray-500">Lejanías:</span>
                                      <span className="text-orange-600">{formatCurrency(zona.logistico.lejanias || 0)}</span>
                                    </div>
                                  )}
                                </div>
                              </div>
                              <div className="bg-white rounded border border-gray-200 p-2">
                                <div className="font-semibold text-gray-700 text-[10px] mb-1 flex items-center gap-1">
                                  <Building2 size={10} /> Administrativo
                                </div>
                                <div className="space-y-0.5 text-[10px]">
                                  <div className="flex justify-between">
                                    <span className="text-gray-500">Personal:</span>
                                    <span>{formatCurrency(zona.administrativo.personal)}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-500">Gastos:</span>
                                    <span>{formatCurrency(zona.administrativo.gastos)}</span>
                                  </div>
                                  {ica > 0 && (
                                    <div className="flex justify-between">
                                      <span className="text-gray-500">ICA:</span>
                                      <span className="text-orange-600">{formatCurrency(ica)}</span>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>

                            {/* Botón para ver municipios */}
                            <button
                              onClick={() => toggleMunicipios(zona.zona.id)}
                              className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white text-[10px] font-medium rounded hover:bg-blue-700 transition-colors"
                            >
                              {showMunicipios ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                              <Building size={12} />
                              {showMunicipios ? 'Ocultar Municipios' : 'Ver Municipios de esta Zona'}
                            </button>

                            {/* Tabla de municipios */}
                            {showMunicipios && (
                              <MunicipiosTable
                                zonaId={zona.zona.id}
                                zonaNombre={zona.zona.nombre}
                                zonaParticipacion={zona.zona.participacion_ventas}
                                ventasZona={ventasZona}
                                escenarioId={escenarioId}
                                marcaId={marcaId}
                                formatCurrency={formatCurrency}
                                formatPercent={formatPercent}
                                tasaICA={zona.zona.tasa_ica || 0}
                                tasaImpuesto={data.tasa_impuesto_renta || 0.33}
                                configuracionDescuentos={data.configuracion_descuentos}
                              />
                            )}
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
            </tbody>
            <tfoot className="bg-gray-100 border-t-2 border-gray-300">
              <tr>
                <td className="px-2 py-2 font-bold text-gray-800">TOTAL</td>
                <td className="text-right px-2 py-2 font-bold text-gray-800">100%</td>
                <td className="text-right px-2 py-2 font-bold text-gray-800 text-[11px]">{formatCurrency(totales.ventas)}</td>
                <td className="text-right px-2 py-2 font-bold text-emerald-700 text-[11px]">{formatCurrency(totales.margenBruto)}</td>
                <td className="text-right px-2 py-2 font-medium text-gray-600 text-[10px]">{formatCurrency(totales.comercial)}</td>
                <td className="text-right px-2 py-2 font-medium text-gray-600 text-[10px]">{formatCurrency(totales.logistico)}</td>
                <td className="text-right px-2 py-2 font-medium text-gray-600 text-[10px]">{formatCurrency(totales.administrativo)}</td>
                <td className="text-right px-2 py-2 font-bold text-gray-800 text-[11px]">{formatCurrency(totales.costoTotal)}</td>
                <td className={`text-right px-2 py-2 font-bold text-[11px] ${totales.utilidadNeta >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                  {formatCurrency(totales.utilidadNeta)}
                </td>
                <td className={`text-right px-2 py-2 font-bold ${margenNetoTotal >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                  {formatPercent(margenNetoTotal)}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  );
}

// Componente separado para municipios (usa su propio hook con caché)
interface MunicipiosTableProps {
  zonaId: number;
  zonaNombre: string;
  zonaParticipacion: number;
  ventasZona: number;
  escenarioId: number;
  marcaId: string;
  formatCurrency: (value: number) => string;
  formatPercent: (value: number) => string;
  tasaICA: number;
  tasaImpuesto: number;
  configuracionDescuentos: any;
}

function MunicipiosTable({
  zonaId, zonaNombre, zonaParticipacion, ventasZona, escenarioId, marcaId,
  formatCurrency, formatPercent, tasaICA, tasaImpuesto, configuracionDescuentos
}: MunicipiosTableProps) {
  const { data, isLoading, error } = usePyGMunicipios(zonaId, escenarioId, marcaId);

  if (isLoading) {
    return (
      <div className="mt-3 p-4 bg-white rounded border border-gray-200 text-center">
        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-1 text-[10px] text-gray-500">Cargando municipios...</p>
      </div>
    );
  }

  if (error || !data || data.municipios.length === 0) {
    return (
      <div className="mt-3 p-3 bg-yellow-50 rounded border border-yellow-200 text-center">
        <p className="text-[10px] text-yellow-700">No hay municipios configurados</p>
      </div>
    );
  }

  // Calcular totales y utilidades por municipio
  const calcularVentasMunicipio = (participacionZona: number) => {
    return ventasZona * (participacionZona / 100);
  };

  const calcularMargenBruto = (ventas: number) => {
    const descuentoPonderado = configuracionDescuentos?.descuento_pie_factura_ponderado || 0;
    return ventas * (descuentoPonderado / 100);
  };

  const calcularICAMun = (ventas: number) => ventas * tasaICA;

  const calcularOtrosIngresosMun = (ventas: number, margenBruto: number) => {
    if (!configuracionDescuentos) return 0;
    const config = configuracionDescuentos;
    const rebate = ventas * (config.porcentaje_rebate / 100);
    const descFinanciero = config.aplica_descuento_financiero
      ? ventas * (config.porcentaje_descuento_financiero / 100)
      : 0;
    const cesantia = config.aplica_cesantia_comercial
      ? (margenBruto + rebate + descFinanciero) / 12
      : 0;
    return rebate + descFinanciero + cesantia;
  };

  // Calcular totales consolidados para prorrateo
  let totalUtilidadAntesImp = 0;
  let totalVentas = 0;

  data.municipios.forEach(mun => {
    const ventas = calcularVentasMunicipio(mun.municipio.participacion_zona || 0);
    const margenBruto = calcularMargenBruto(ventas);
    const ica = calcularICAMun(ventas);
    const costoTotal = mun.total_mensual + ica;
    const utilOp = margenBruto - costoTotal;
    const otrosIng = calcularOtrosIngresosMun(ventas, margenBruto);
    totalUtilidadAntesImp += utilOp + otrosIng;
    totalVentas += ventas;
  });

  const impuestoTotal = totalUtilidadAntesImp > 0 ? totalUtilidadAntesImp * tasaImpuesto : 0;

  return (
    <div className="mt-3 bg-white rounded border border-gray-200 overflow-hidden">
      <div className="px-3 py-2 bg-green-50 border-b border-gray-200">
        <h5 className="text-[10px] font-semibold text-gray-700">
          Municipios de {zonaNombre} ({data.municipios.length})
        </h5>
      </div>
      <table className="w-full text-[10px]">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="text-left px-2 py-1.5 font-medium text-gray-600">Municipio</th>
            <th className="text-right px-2 py-1.5 font-medium text-gray-600">Part.</th>
            <th className="text-right px-2 py-1.5 font-medium text-gray-600">Ventas</th>
            <th className="text-right px-2 py-1.5 font-medium text-gray-600">Margen</th>
            <th className="text-right px-2 py-1.5 font-medium text-gray-500">Comerc.</th>
            <th className="text-right px-2 py-1.5 font-medium text-gray-500">Logíst.</th>
            <th className="text-right px-2 py-1.5 font-medium text-gray-500">Admin.</th>
            <th className="text-right px-2 py-1.5 font-medium text-gray-600">Costos</th>
            <th className="text-right px-2 py-1.5 font-medium text-gray-600">Util. Neta</th>
            <th className="text-right px-2 py-1.5 font-medium text-gray-600">%</th>
          </tr>
        </thead>
        <tbody>
          {[...data.municipios]
            .sort((a, b) => (b.municipio.participacion_zona || 0) - (a.municipio.participacion_zona || 0))
            .map((mun, idx) => {
              const participacionZona = mun.municipio.participacion_zona || 0;
              const ventas = calcularVentasMunicipio(participacionZona);
              const margenBruto = calcularMargenBruto(ventas);
              const ica = calcularICAMun(ventas);
              const costoTotal = mun.total_mensual + ica;
              const utilOp = margenBruto - costoTotal;
              const otrosIng = calcularOtrosIngresosMun(ventas, margenBruto);
              const utilAntesImp = utilOp + otrosIng;
              const impuesto = totalVentas > 0 ? impuestoTotal * (ventas / totalVentas) : 0;
              const utilNeta = utilAntesImp - impuesto;
              const margenNeto = ventas > 0 ? (utilNeta / ventas) * 100 : 0;
              const isRentable = utilNeta >= 0;

              return (
                <tr key={mun.municipio.id} className={`border-b border-gray-100 ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}`}>
                  <td className="px-2 py-1.5">
                    <div className="flex items-center gap-1">
                      <Building size={9} className={isRentable ? 'text-green-500' : 'text-red-500'} />
                      <span>{mun.municipio.nombre}</span>
                    </div>
                  </td>
                  <td className="text-right px-2 py-1.5">
                    <span className="px-1 py-0.5 bg-green-100 text-green-700 rounded text-[8px]">
                      {formatPercent(participacionZona)}
                    </span>
                  </td>
                  <td className="text-right px-2 py-1.5 text-gray-700">{formatCurrency(ventas)}</td>
                  <td className="text-right px-2 py-1.5 text-emerald-600">{formatCurrency(margenBruto)}</td>
                  <td className="text-right px-2 py-1.5 text-gray-500">{formatCurrency(mun.comercial.total)}</td>
                  <td className="text-right px-2 py-1.5 text-gray-500">{formatCurrency(mun.logistico.total)}</td>
                  <td className="text-right px-2 py-1.5 text-gray-500">{formatCurrency(mun.administrativo.total + ica)}</td>
                  <td className="text-right px-2 py-1.5 text-gray-700 font-medium">{formatCurrency(costoTotal)}</td>
                  <td className={`text-right px-2 py-1.5 font-semibold ${isRentable ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(utilNeta)}
                  </td>
                  <td className="text-right px-2 py-1.5">
                    <span className={`px-1 py-0.5 rounded text-[8px] font-medium ${
                      isRentable ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}>
                      {formatPercent(margenNeto)}
                    </span>
                  </td>
                </tr>
              );
            })}
        </tbody>
      </table>
    </div>
  );
}
