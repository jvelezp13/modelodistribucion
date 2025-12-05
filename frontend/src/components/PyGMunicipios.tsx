'use client';

import React, { useState, useEffect } from 'react';
import { apiClient, PyGMunicipiosResponse, PyGMunicipio, MESES, getMesActual, VentasMensualesDesglose } from '@/lib/api';
import { ChevronDown, ChevronRight, Building, TrendingUp, TrendingDown, Users, Truck, Building2, ArrowLeft, Calendar, MapPin } from 'lucide-react';

interface PyGMunicipiosProps {
  escenarioId: number;
  zonaId: number;
  zonaNombre?: string;
  marcaId: string;
  onBack?: () => void;
}

export default function PyGMunicipios({ escenarioId, zonaId, zonaNombre, marcaId, onBack }: PyGMunicipiosProps) {
  const [data, setData] = useState<PyGMunicipiosResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedMunicipios, setExpandedMunicipios] = useState<Set<number>>(new Set());
  const [mesSeleccionado, setMesSeleccionado] = useState<string>(getMesActual());

  useEffect(() => {
    const fetchData = async () => {
      if (!escenarioId || !zonaId || !marcaId) return;

      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.obtenerPyGMunicipios(zonaId, escenarioId, marcaId);
        setData(response);
      } catch (err) {
        console.error('Error cargando P&G por municipios:', err);
        setError('Error al cargar los datos de P&G por municipios');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [escenarioId, zonaId, marcaId]);

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
    return `${value.toFixed(2)}%`;
  };

  // Obtener ventas del mes seleccionado (total marca)
  const getVentasMesMarca = (): number => {
    if (!data?.ventas_mensuales) return 0;
    const ventas = data.ventas_mensuales as VentasMensualesDesglose;
    return ventas[mesSeleccionado as keyof VentasMensualesDesglose] || 0;
  };

  // Ventas de la zona (según participación)
  const ventasMesMarca = getVentasMesMarca();
  const ventasZona = ventasMesMarca * ((data?.zona_participacion_ventas || 0) / 100);

  // Pre-calcular ventas por municipio usando participacion_zona (peso relativo dentro de la zona)
  const ventasPorMunicipio = React.useMemo(() => {
    if (!data?.municipios || data.municipios.length === 0) return new Map<number, number>();

    const ventasMap = new Map<number, number>();
    let sumaRedondeada = 0;

    // Ordenar municipios por participación en zona descendente
    const municipiosOrdenados = [...data.municipios].sort(
      (a, b) => (b.municipio.participacion_zona || 0) - (a.municipio.participacion_zona || 0)
    );

    // Calcular ventas redondeadas para todos excepto el primero
    municipiosOrdenados.slice(1).forEach(mun => {
      const participacionZona = mun.municipio.participacion_zona || 0;
      const ventasExactas = ventasZona * (participacionZona / 100);
      const ventasRedondeadas = Math.round(ventasExactas);
      ventasMap.set(mun.municipio.id, ventasRedondeadas);
      sumaRedondeada += ventasRedondeadas;
    });

    // El municipio más grande absorbe la diferencia de redondeo
    if (municipiosOrdenados.length > 0) {
      const munMayor = municipiosOrdenados[0];
      ventasMap.set(munMayor.municipio.id, Math.round(ventasZona) - sumaRedondeada);
    }

    return ventasMap;
  }, [data?.municipios, ventasZona]);

  const calcularVentasMunicipio = (mun: PyGMunicipio): number => {
    return ventasPorMunicipio.get(mun.municipio.id) || 0;
  };

  const calcularMargenBrutoMunicipio = (mun: PyGMunicipio): number => {
    const ventas = calcularVentasMunicipio(mun);
    const descuentoPonderado = data?.configuracion_descuentos?.descuento_pie_factura_ponderado || 0;
    return ventas * (descuentoPonderado / 100);
  };

  const calcularICA = (mun: PyGMunicipio): number => {
    const ventas = calcularVentasMunicipio(mun);
    const tasaICA = data?.tasa_ica || 0;
    return ventas * tasaICA;
  };

  const calcularCostosTotalConICA = (mun: PyGMunicipio): number => {
    return mun.total_mensual + calcularICA(mun);
  };

  const calcularUtilidadOperacionalConICA = (mun: PyGMunicipio): number => {
    const margenBruto = calcularMargenBrutoMunicipio(mun);
    return margenBruto - calcularCostosTotalConICA(mun);
  };

  const calcularOtrosIngresos = (mun: PyGMunicipio): number => {
    if (!data?.configuracion_descuentos) return 0;
    const ventas = calcularVentasMunicipio(mun);
    const margenBruto = calcularMargenBrutoMunicipio(mun);
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

  const calcularUtilidadAntesImpuestosConICA = (mun: PyGMunicipio): number => {
    return calcularUtilidadOperacionalConICA(mun) + calcularOtrosIngresos(mun);
  };

  // Calcular totales consolidados para prorrateo de impuesto
  const calcularTotalesConsolidados = () => {
    if (!data?.municipios) return { utilidadAntesImpuestos: 0, ventasTotal: 0, impuestoTotal: 0 };

    let utilidadAntesImpuestos = 0;
    let ventasTotal = 0;

    data.municipios.forEach(mun => {
      utilidadAntesImpuestos += calcularUtilidadAntesImpuestosConICA(mun);
      ventasTotal += calcularVentasMunicipio(mun);
    });

    const tasaImpuesto = data?.tasa_impuesto_renta || 0.33;
    const impuestoTotal = utilidadAntesImpuestos > 0 ? utilidadAntesImpuestos * tasaImpuesto : 0;

    return { utilidadAntesImpuestos, ventasTotal, impuestoTotal };
  };

  const consolidado = calcularTotalesConsolidados();

  const calcularImpuestoProrrateado = (mun: PyGMunicipio): number => {
    if (consolidado.ventasTotal === 0 || consolidado.impuestoTotal === 0) return 0;
    const ventasMun = calcularVentasMunicipio(mun);
    const participacion = ventasMun / consolidado.ventasTotal;
    return consolidado.impuestoTotal * participacion;
  };

  const calcularUtilidadNeta = (mun: PyGMunicipio): number => {
    const utilidadAntesImp = calcularUtilidadAntesImpuestosConICA(mun);
    const impuestoProrrateado = calcularImpuestoProrrateado(mun);
    return utilidadAntesImp - impuestoProrrateado;
  };

  const calcularMargenNeto = (mun: PyGMunicipio): number => {
    const ventas = calcularVentasMunicipio(mun);
    if (ventas === 0) return 0;
    return (calcularUtilidadNeta(mun) / ventas) * 100;
  };

  // Obtener participación del municipio dentro de la zona (viene del backend)
  const getParticipacionZona = (mun: PyGMunicipio): number => {
    return mun.municipio.participacion_zona || 0;
  };

  // Calcular totales
  const calcularTotales = () => {
    if (!data?.municipios) return {
      comercial: 0, logistico: 0, administrativo: 0, costoTotal: 0, ica: 0,
      ventas: 0, margenBruto: 0, utilidadOperacional: 0, utilidadNeta: 0, otrosIngresos: 0
    };

    return data.municipios.reduce((acc, mun) => {
      const icaMun = calcularICA(mun);
      return {
        comercial: acc.comercial + mun.comercial.total,
        logistico: acc.logistico + mun.logistico.total,
        administrativo: acc.administrativo + mun.administrativo.total + icaMun,
        costoTotal: acc.costoTotal + mun.total_mensual + icaMun,
        ica: acc.ica + icaMun,
        ventas: acc.ventas + calcularVentasMunicipio(mun),
        margenBruto: acc.margenBruto + calcularMargenBrutoMunicipio(mun),
        utilidadOperacional: acc.utilidadOperacional + calcularUtilidadOperacionalConICA(mun),
        utilidadNeta: acc.utilidadNeta + calcularUtilidadNeta(mun),
        otrosIngresos: acc.otrosIngresos + calcularOtrosIngresos(mun)
      };
    }, {
      comercial: 0, logistico: 0, administrativo: 0, costoTotal: 0, ica: 0,
      ventas: 0, margenBruto: 0, utilidadOperacional: 0, utilidadNeta: 0, otrosIngresos: 0
    });
  };

  const totales = calcularTotales();
  const margenNetoTotal = totales.ventas > 0 ? (totales.utilidadNeta / totales.ventas) * 100 : 0;

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
          <button onClick={onBack} className="mt-2 text-xs text-blue-600 hover:text-blue-800">
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
          <button onClick={onBack} className="mt-2 text-xs text-blue-600 hover:text-blue-800">
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
                  {data.total_municipios} municipios | {data.marca_nombre} | {data.escenario_nombre}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {/* Selector de mes */}
              <div className="flex items-center gap-1">
                <Calendar size={12} className="text-gray-400" />
                <select
                  value={mesSeleccionado}
                  onChange={(e) => setMesSeleccionado(e.target.value)}
                  className="text-xs px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {MESES.map(mes => (
                    <option key={mes.value} value={mes.value}>{mes.label}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Resumen de la zona */}
        <div className="grid grid-cols-6 gap-3 p-3 bg-gray-50 border-b border-gray-200 text-center">
          <div>
            <div className="text-[10px] text-gray-500 mb-0.5">Ventas Zona</div>
            <div className="text-sm font-bold text-gray-800">{formatCurrency(totales.ventas)}</div>
          </div>
          <div>
            <div className="text-[10px] text-gray-500 mb-0.5">Margen Bruto</div>
            <div className="text-sm font-bold text-emerald-600">{formatCurrency(totales.margenBruto)}</div>
          </div>
          <div>
            <div className="text-[10px] text-gray-500 mb-0.5">Costos</div>
            <div className="text-sm font-bold text-gray-700">{formatCurrency(totales.costoTotal)}</div>
          </div>
          <div>
            <div className="text-[10px] text-gray-500 mb-0.5">Otros Ingresos</div>
            <div className="text-sm font-bold text-teal-600">{formatCurrency(totales.otrosIngresos)}</div>
          </div>
          <div>
            <div className="text-[10px] text-gray-500 mb-0.5">Util. Neta</div>
            <div className={`text-sm font-bold ${totales.utilidadNeta >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(totales.utilidadNeta)}
            </div>
          </div>
          <div>
            <div className="text-[10px] text-gray-500 mb-0.5">Margen</div>
            <div className={`text-sm font-bold ${margenNetoTotal >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatPercent(margenNetoTotal)}
            </div>
          </div>
        </div>

        {/* Tabla de municipios */}
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-gray-100 border-b border-gray-200">
              <tr>
                <th className="text-left px-2 py-2 font-semibold text-gray-700">Municipio</th>
                <th className="text-right px-2 py-2 font-semibold text-gray-700">Part.</th>
                <th className="text-right px-2 py-2 font-semibold text-gray-700">Ventas</th>
                <th className="text-right px-2 py-2 font-semibold text-gray-700">Margen</th>
                <th className="text-right px-2 py-2 font-semibold text-gray-500 text-[10px]">Comerc.</th>
                <th className="text-right px-2 py-2 font-semibold text-gray-500 text-[10px]">Logíst.</th>
                <th className="text-right px-2 py-2 font-semibold text-gray-500 text-[10px]">Admin.</th>
                <th className="text-right px-2 py-2 font-semibold text-gray-700">Costos</th>
                <th className="text-right px-2 py-2 font-semibold text-gray-500 text-[10px]">Otros Ing.</th>
                <th className="text-right px-2 py-2 font-semibold text-gray-700">Util. Neta</th>
                <th className="text-right px-2 py-2 font-semibold text-gray-700">%</th>
              </tr>
            </thead>
            <tbody>
              {[...data.municipios]
                .sort((a, b) => calcularMargenNeto(b) - calcularMargenNeto(a))
                .map((mun, idx) => {
                  const ventasMun = calcularVentasMunicipio(mun);
                  const margenBruto = calcularMargenBrutoMunicipio(mun);
                  const costosTotalConICA = calcularCostosTotalConICA(mun);
                  const utilidadNeta = calcularUtilidadNeta(mun);
                  const margenNeto = calcularMargenNeto(mun);
                  const otrosIngresos = calcularOtrosIngresos(mun);
                  const ica = calcularICA(mun);
                  const isRentable = utilidadNeta >= 0;

                  return (
                    <React.Fragment key={mun.municipio.id}>
                      <tr className={`border-b border-gray-100 hover:bg-green-50 transition-colors ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                        <td className="px-2 py-2">
                          <button
                            onClick={() => toggleMunicipio(mun.municipio.id)}
                            className="flex items-center gap-1 text-gray-800 hover:text-green-600"
                          >
                            {expandedMunicipios.has(mun.municipio.id) ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                            <Building size={10} className={isRentable ? 'text-green-500' : 'text-red-500'} />
                            <span className="font-medium text-[11px]">{mun.municipio.nombre}</span>
                          </button>
                        </td>
                        <td className="text-right px-2 py-2">
                          <span className="px-1 py-0.5 rounded text-[9px] font-medium bg-green-100 text-green-700"
                            title={`Part. marca: ${formatPercent(mun.municipio.participacion_ventas)}`}>
                            {formatPercent(getParticipacionZona(mun))}
                          </span>
                        </td>
                        <td className="text-right px-2 py-2 text-gray-700 text-[11px]">{formatCurrency(ventasMun)}</td>
                        <td className="text-right px-2 py-2 text-emerald-600 text-[11px]">{formatCurrency(margenBruto)}</td>
                        <td className="text-right px-2 py-2 text-gray-500 text-[10px]">{formatCurrency(mun.comercial.total)}</td>
                        <td className="text-right px-2 py-2 text-gray-500 text-[10px]">{formatCurrency(mun.logistico.total)}</td>
                        <td className="text-right px-2 py-2 text-gray-500 text-[10px]">{formatCurrency(mun.administrativo.total + ica)}</td>
                        <td className="text-right px-2 py-2 text-gray-700 font-medium text-[11px]">{formatCurrency(costosTotalConICA)}</td>
                        <td className="text-right px-2 py-2 text-teal-600 text-[10px]">{formatCurrency(otrosIngresos)}</td>
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
                      {expandedMunicipios.has(mun.municipio.id) && (
                        <tr className="bg-gray-50">
                          <td colSpan={11} className="px-6 py-3">
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
                                    <span className="font-medium">{formatCurrency(mun.comercial.personal)}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-500">Gastos:</span>
                                    <span className="font-medium">{formatCurrency(mun.comercial.gastos)}</span>
                                  </div>
                                  <div className="flex justify-between border-t pt-1 mt-1">
                                    <span className="font-medium text-gray-700">Total:</span>
                                    <span className="font-bold text-gray-900">{formatCurrency(mun.comercial.total)}</span>
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
                                    <span className="font-medium">{formatCurrency(mun.logistico.personal)}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-500">Gastos:</span>
                                    <span className="font-medium">{formatCurrency(mun.logistico.gastos)}</span>
                                  </div>
                                  <div className="flex justify-between border-t pt-1 mt-1">
                                    <span className="font-medium text-gray-700">Total:</span>
                                    <span className="font-bold text-gray-900">{formatCurrency(mun.logistico.total)}</span>
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
                                    <span className="font-medium">{formatCurrency(mun.administrativo.personal)}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-500">Gastos:</span>
                                    <span className="font-medium">{formatCurrency(mun.administrativo.gastos)}</span>
                                  </div>
                                  {ica > 0 && (
                                    <div className="flex justify-between">
                                      <span className="text-gray-500">ICA:</span>
                                      <span className="font-medium text-orange-600">{formatCurrency(ica)}</span>
                                    </div>
                                  )}
                                  <div className="flex justify-between border-t pt-1 mt-1">
                                    <span className="font-medium text-gray-700">Total:</span>
                                    <span className="font-bold text-gray-900">{formatCurrency(mun.administrativo.total + ica)}</span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
            </tbody>
            <tfoot className="bg-gray-100 border-t-2 border-gray-300">
              <tr>
                <td className="px-2 py-2 font-bold text-gray-800">TOTAL ZONA</td>
                <td className="text-right px-2 py-2 font-bold text-gray-800">100%</td>
                <td className="text-right px-2 py-2 font-bold text-gray-800 text-[11px]">{formatCurrency(totales.ventas)}</td>
                <td className="text-right px-2 py-2 font-bold text-emerald-700 text-[11px]">{formatCurrency(totales.margenBruto)}</td>
                <td className="text-right px-2 py-2 font-medium text-gray-600 text-[10px]">{formatCurrency(totales.comercial)}</td>
                <td className="text-right px-2 py-2 font-medium text-gray-600 text-[10px]">{formatCurrency(totales.logistico)}</td>
                <td className="text-right px-2 py-2 font-medium text-gray-600 text-[10px]">{formatCurrency(totales.administrativo)}</td>
                <td className="text-right px-2 py-2 font-bold text-gray-800 text-[11px]">{formatCurrency(totales.costoTotal)}</td>
                <td className="text-right px-2 py-2 font-medium text-teal-600 text-[10px]">{formatCurrency(totales.otrosIngresos)}</td>
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
