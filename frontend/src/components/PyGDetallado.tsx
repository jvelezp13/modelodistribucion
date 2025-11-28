'use client';

import React, { useState, useEffect } from 'react';
import { Marca, Rubro, DetalleLejaniasLogistica, apiClient, MESES, getMesActual, VentasMensualesDesglose } from '@/lib/api';
import { ChevronDown, ChevronRight, Truck, Calendar } from 'lucide-react';

interface PyGDetalladoProps {
  marca: Marca;
  escenarioId: number;
}

interface SeccionState {
  ingresos: boolean;
  cmv: boolean;
  comercial: boolean;
  logistico: boolean;
  administrativo: boolean;
  otrosIngresos: boolean;
  impuestos: boolean;
}

interface SubSeccionState {
  comercialPersonal: boolean;
  comercialGastos: boolean;
  logisticoVehiculos: boolean;
  logisticoPersonal: boolean;
  logisticoGastos: boolean;
  logisticoLejanias: boolean;
  administrativoPersonal: boolean;
  administrativoGastos: boolean;
}

// Interfaz para vehículo con flete base agregado
interface VehiculoConFlete {
  rubro: Rubro;
  fleteBase: number;
  totalConFlete: number;
}

export default function PyGDetallado({ marca, escenarioId }: PyGDetalladoProps) {
  const [seccionesAbiertas, setSeccionesAbiertas] = useState<SeccionState>({
    ingresos: true,
    cmv: false,
    comercial: false,
    logistico: false,
    administrativo: false,
    otrosIngresos: false,
    impuestos: false,
  });

  const [subSeccionesAbiertas, setSubSeccionesAbiertas] = useState<SubSeccionState>({
    comercialPersonal: false,
    comercialGastos: false,
    logisticoVehiculos: false,
    logisticoPersonal: false,
    logisticoGastos: false,
    logisticoLejanias: false,
    administrativoPersonal: false,
    administrativoGastos: false,
  });

  const [lejaniasLogistica, setLejaniasLogistica] = useState<DetalleLejaniasLogistica | null>(null);
  const [loadingLejanias, setLoadingLejanias] = useState(false);
  const [mesSeleccionado, setMesSeleccionado] = useState<string>(getMesActual());

  // Cargar datos de lejanías logísticas
  useEffect(() => {
    const fetchLejanias = async () => {
      if (!escenarioId || !marca.marca_id) return;

      setLoadingLejanias(true);
      try {
        const data = await apiClient.obtenerDetalleLejaniasLogistica(escenarioId, marca.marca_id);
        setLejaniasLogistica(data);
      } catch (error) {
        console.error('Error cargando lejanías logísticas:', error);
        setLejaniasLogistica(null);
      } finally {
        setLoadingLejanias(false);
      }
    };

    fetchLejanias();
  }, [escenarioId, marca.marca_id]);

  const toggleSeccion = (seccion: keyof SeccionState) => {
    setSeccionesAbiertas(prev => ({ ...prev, [seccion]: !prev[seccion] }));
  };

  const toggleSubSeccion = (subSeccion: keyof SubSeccionState) => {
    setSubSeccionesAbiertas(prev => ({ ...prev, [subSeccion]: !prev[subSeccion] }));
  };

  // Combinar rubros individuales y compartidos
  const todosLosRubros = [
    ...marca.rubros_individuales,
    ...marca.rubros_compartidos_asignados
  ];

  // Agrupar rubros por categoría y tipo
  const agruparRubros = () => {
    const grupos = {
      comercialPersonal: [] as Rubro[],
      comercialGastos: [] as Rubro[],
      logisticoVehiculos: [] as Rubro[],
      logisticoPersonal: [] as Rubro[],
      logisticoGastos: [] as Rubro[],
      administrativoPersonal: [] as Rubro[],
      administrativoGastos: [] as Rubro[],
    };

    todosLosRubros.forEach(rubro => {
      if (rubro.categoria === 'comercial') {
        if (rubro.tipo === 'personal') {
          grupos.comercialPersonal.push(rubro);
        } else {
          grupos.comercialGastos.push(rubro);
        }
      } else if (rubro.categoria === 'logistico') {
        if (rubro.tipo === 'vehiculo') {
          grupos.logisticoVehiculos.push(rubro);
        } else if (rubro.tipo === 'personal') {
          grupos.logisticoPersonal.push(rubro);
        } else {
          grupos.logisticoGastos.push(rubro);
        }
      } else if (rubro.categoria === 'administrativo') {
        if (rubro.tipo === 'personal') {
          grupos.administrativoPersonal.push(rubro);
        } else {
          grupos.administrativoGastos.push(rubro);
        }
      }
    });

    return grupos;
  };

  const grupos = agruparRubros();

  // Calcular flete base por vehículo desde las rutas logísticas
  const calcularFleteBasePorVehiculo = (): Map<string, number> => {
    const fletesPorVehiculo = new Map<string, number>();

    if (lejaniasLogistica?.rutas) {
      lejaniasLogistica.rutas.forEach(ruta => {
        if (ruta.vehiculo) {
          const vehiculoKey = ruta.vehiculo;
          const fleteActual = fletesPorVehiculo.get(vehiculoKey) || 0;
          fletesPorVehiculo.set(vehiculoKey, fleteActual + ruta.flete_base_mensual);
        }
      });
    }

    return fletesPorVehiculo;
  };

  const fleteBasePorVehiculo = calcularFleteBasePorVehiculo();

  // Combinar vehículos con su flete base
  const vehiculosConFlete: VehiculoConFlete[] = grupos.logisticoVehiculos.map(rubro => {
    // Buscar el flete base que corresponde a este vehículo
    let fleteBase = 0;
    fleteBasePorVehiculo.forEach((flete, vehiculoNombre) => {
      // Intentar hacer match por nombre del rubro o ID
      if (vehiculoNombre.includes(rubro.nombre) || rubro.nombre.includes(vehiculoNombre.split(' (')[0])) {
        fleteBase += flete;
      }
    });

    // Si no encontramos match por nombre, intentar por índice (para terceros)
    if (fleteBase === 0 && rubro.esquema === 'tercero' && lejaniasLogistica?.rutas) {
      // Para terceros, sumar todos los fletes de rutas con ese esquema
      const rutasTercero = lejaniasLogistica.rutas.filter(r => r.esquema === 'tercero');
      fleteBase = rutasTercero.reduce((sum, r) => sum + r.flete_base_mensual, 0);
    }

    return {
      rubro,
      fleteBase,
      totalConFlete: rubro.valor_total + fleteBase
    };
  });

  // Calcular subtotales
  const subtotalComercialPersonal = grupos.comercialPersonal.reduce((sum, r) => sum + r.valor_total, 0);
  const subtotalComercialGastos = grupos.comercialGastos.reduce((sum, r) => sum + r.valor_total, 0);
  const totalComercial = subtotalComercialPersonal + subtotalComercialGastos + (marca.lejania_comercial || 0);

  // Subtotal de vehículos ahora incluye flete base
  const subtotalLogisticoVehiculos = vehiculosConFlete.reduce((sum, v) => sum + v.totalConFlete, 0);
  const subtotalLogisticoPersonal = grupos.logisticoPersonal.reduce((sum, r) => sum + r.valor_total, 0);
  const subtotalLogisticoGastos = grupos.logisticoGastos.reduce((sum, r) => sum + r.valor_total, 0);

  // Lejanías logísticas ahora solo incluye combustible + peajes + pernocta (sin flete base)
  const subtotalLejanias = lejaniasLogistica
    ? (lejaniasLogistica.total_combustible_mensual || 0) +
      (lejaniasLogistica.total_peaje_mensual || 0) +
      (lejaniasLogistica.total_pernocta_mensual || 0)
    : 0;

  const totalLogistico = subtotalLogisticoVehiculos + subtotalLogisticoPersonal + subtotalLogisticoGastos + subtotalLejanias;

  const subtotalAdministrativoPersonal = grupos.administrativoPersonal.reduce((sum, r) => sum + r.valor_total, 0);
  const subtotalAdministrativoGastos = grupos.administrativoGastos.reduce((sum, r) => sum + r.valor_total, 0);
  const totalAdministrativo = subtotalAdministrativoPersonal + subtotalAdministrativoGastos;

  // ==========================================
  // CÁLCULOS P&G MODELO DISTRIBUIDOR
  // ==========================================

  // 1. INGRESOS POR VENTAS - usar mes seleccionado si hay desglose disponible
  const obtenerVentasMes = (): number => {
    if (marca.ventas_mensuales_desglose) {
      const desglose = marca.ventas_mensuales_desglose as VentasMensualesDesglose;
      return desglose[mesSeleccionado as keyof VentasMensualesDesglose] || marca.ventas_mensuales || 0;
    }
    return marca.ventas_mensuales || 0;
  };

  const ingresosPorVentas = obtenerVentasMes();

  // 2. COSTO DE MERCANCÍA VENDIDA (CMV)
  // CMV = Ventas × (1 - descuento_pie_factura_ponderado)
  const config = marca.configuracion_descuentos;
  const descuentoPieFacturaPonderado = config?.descuento_pie_factura_ponderado || 0;
  const costoMercanciaVendida = ingresosPorVentas * (1 - descuentoPieFacturaPonderado / 100);

  // 3. MARGEN BRUTO (Utilidad Bruta de Distribución)
  const margenBruto = ingresosPorVentas - costoMercanciaVendida;

  // 4. COSTOS OPERATIVOS
  const totalCostosOperativos = totalComercial + totalLogistico + totalAdministrativo;

  // 5. UTILIDAD OPERACIONAL
  const utilidadOperacional = margenBruto - totalCostosOperativos;

  // 6. OTROS INGRESOS (Rebate y Descuento Financiero)
  const porcentajeRebate = config?.porcentaje_rebate || 0;
  const ingresoRebate = ingresosPorVentas * (porcentajeRebate / 100);

  const porcentajeDescFinanciero = config?.aplica_descuento_financiero
    ? (config?.porcentaje_descuento_financiero || 0)
    : 0;
  const ingresoDescuentoFinanciero = ingresosPorVentas * (porcentajeDescFinanciero / 100);

  const totalOtrosIngresos = ingresoRebate + ingresoDescuentoFinanciero;

  // 7. UTILIDAD ANTES DE IMPUESTOS
  const utilidadAntesImpuestos = utilidadOperacional + totalOtrosIngresos;

  // 8. IMPUESTOS (33% en Colombia)
  const tasaImpuesto = 0.33;
  const impuestoRenta = utilidadAntesImpuestos > 0 ? utilidadAntesImpuestos * tasaImpuesto : 0;

  // 9. UTILIDAD NETA
  const utilidadNeta = utilidadAntesImpuestos - impuestoRenta;

  // MÁRGENES
  const margenBrutoPorcentaje = ingresosPorVentas > 0 ? (margenBruto / ingresosPorVentas) * 100 : 0;
  const margenOperacional = ingresosPorVentas > 0 ? (utilidadOperacional / ingresosPorVentas) * 100 : 0;
  const margenNeto = ingresosPorVentas > 0 ? (utilidadNeta / ingresosPorVentas) * 100 : 0;

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Función para calcular porcentaje sobre ventas
  const calcularPorcentajeSobreVentas = (valor: number): string => {
    if (ingresosPorVentas === 0) return '0.0%';
    return ((valor / ingresosPorVentas) * 100).toFixed(1) + '%';
  };

  const SeccionHeader = ({
    titulo,
    seccion,
    valor,
    bgColor = 'bg-gray-700',
    mostrarPorcentaje = false
  }: {
    titulo: string;
    seccion: keyof SeccionState;
    valor?: number;
    bgColor?: string;
    mostrarPorcentaje?: boolean;
  }) => {
    const isOpen = seccionesAbiertas[seccion];

    return (
      <div
        className={`${bgColor} text-white px-3 py-2 cursor-pointer flex justify-between items-center`}
        onClick={() => toggleSeccion(seccion)}
      >
        <div className="flex items-center gap-2">
          {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          <span className="text-xs font-semibold uppercase tracking-wide">{titulo}</span>
        </div>
        {valor !== undefined && (
          <div className="flex items-center gap-3">
            {mostrarPorcentaje && (
              <span className="text-xs opacity-75">{calcularPorcentajeSobreVentas(valor)}</span>
            )}
            <span className="text-sm font-bold">{formatCurrency(valor)}</span>
          </div>
        )}
      </div>
    );
  };

  const SubSeccionHeader = ({
    titulo,
    subSeccion,
    valor,
    mostrarPorcentaje = false
  }: {
    titulo: string;
    subSeccion: keyof SubSeccionState;
    valor: number;
    mostrarPorcentaje?: boolean;
  }) => {
    const isOpen = subSeccionesAbiertas[subSeccion];

    return (
      <div
        className="bg-gray-100 px-3 py-1.5 cursor-pointer flex justify-between items-center border-b border-gray-200"
        onClick={() => toggleSubSeccion(subSeccion)}
      >
        <div className="flex items-center gap-1.5">
          {isOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          <span className="text-xs font-medium text-gray-700">{titulo}</span>
        </div>
        <div className="flex items-center gap-2">
          {mostrarPorcentaje && (
            <span className="text-[10px] text-gray-500">{calcularPorcentajeSobreVentas(valor)}</span>
          )}
          <span className="text-xs font-semibold text-gray-900">{formatCurrency(valor)}</span>
        </div>
      </div>
    );
  };

  // Componente para mostrar vehículo con flete base integrado
  const VehiculoItem = ({ vehiculo }: { vehiculo: VehiculoConFlete }) => {
    const [expandido, setExpandido] = useState(false);
    const { rubro, fleteBase, totalConFlete } = vehiculo;

    const esCompartido = rubro.tipo_asignacion === 'compartido';

    return (
      <div className="border-b border-gray-100">
        {/* Línea principal */}
        <div
          className="flex justify-between items-center py-1.5 px-3 hover:bg-gray-50 text-xs cursor-pointer"
          onClick={() => setExpandido(!expandido)}
        >
          <div className="flex-1 flex items-center gap-2">
            <Truck size={12} className="text-gray-400" />
            <span className="text-gray-700">{rubro.nombre}</span>
            {rubro.cantidad && rubro.cantidad > 1 && (
              <span className="text-gray-500 text-xs">(x{rubro.cantidad})</span>
            )}
            {esCompartido && (
              <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 text-[10px] font-medium rounded">
                Compartido
              </span>
            )}
            <span className="px-1.5 py-0.5 bg-purple-100 text-purple-700 text-[10px] font-medium rounded">
              {rubro.esquema === 'renting' ? 'Renting' : rubro.esquema === 'tercero' ? 'Tercero' : 'Propio'}
            </span>
            {rubro.tipo_vehiculo && (
              <span className="text-gray-500 text-[10px]">[{rubro.tipo_vehiculo.toUpperCase()}]</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className="font-medium text-gray-900">{formatCurrency(totalConFlete)}</span>
            <ChevronDown
              size={12}
              className={`text-gray-400 transition-transform ${expandido ? 'rotate-180' : ''}`}
            />
          </div>
        </div>

        {/* Detalles expandidos */}
        {expandido && (
          <div className="px-3 py-1.5 bg-gray-50 text-[10px] text-gray-600 space-y-0.5">
            {/* Costos fijos del vehículo */}
            {rubro.valor_total > 0 && (
              <div className="flex justify-between">
                <span>Costos Fijos (GPS, Seguro, etc.):</span>
                <span className="font-medium text-gray-700">{formatCurrency(rubro.valor_total)}</span>
              </div>
            )}

            {/* Desglose de costos fijos según esquema */}
            {rubro.esquema === 'renting' && (
              <>
                {rubro.canon_mensual !== undefined && rubro.canon_mensual > 0 && (
                  <div className="flex justify-between pl-3">
                    <span className="text-gray-500">Canon Mensual:</span>
                    <span className="text-gray-600">{formatCurrency(rubro.canon_mensual * (rubro.cantidad || 1))}</span>
                  </div>
                )}
                {rubro.lavada !== undefined && rubro.lavada > 0 && (
                  <div className="flex justify-between pl-3">
                    <span className="text-gray-500">Lavado:</span>
                    <span className="text-gray-600">{formatCurrency(rubro.lavada * (rubro.cantidad || 1))}</span>
                  </div>
                )}
              </>
            )}

            {rubro.esquema === 'tradicional' && (
              <>
                {rubro.depreciacion !== undefined && rubro.depreciacion > 0 && (
                  <div className="flex justify-between pl-3">
                    <span className="text-gray-500">Depreciación:</span>
                    <span className="text-gray-600">{formatCurrency(rubro.depreciacion * (rubro.cantidad || 1))}</span>
                  </div>
                )}
                {rubro.mantenimiento !== undefined && rubro.mantenimiento > 0 && (
                  <div className="flex justify-between pl-3">
                    <span className="text-gray-500">Mantenimiento:</span>
                    <span className="text-gray-600">{formatCurrency(rubro.mantenimiento * (rubro.cantidad || 1))}</span>
                  </div>
                )}
                {rubro.seguro !== undefined && rubro.seguro > 0 && (
                  <div className="flex justify-between pl-3">
                    <span className="text-gray-500">Seguro:</span>
                    <span className="text-gray-600">{formatCurrency(rubro.seguro * (rubro.cantidad || 1))}</span>
                  </div>
                )}
              </>
            )}

            {/* Flete base de recorridos */}
            {fleteBase > 0 && (
              <div className="flex justify-between border-t border-gray-200 pt-1 mt-1">
                <span>Flete Base (de Recorridos):</span>
                <span className="font-medium text-gray-700">{formatCurrency(fleteBase)}</span>
              </div>
            )}

            {/* Total */}
            <div className="flex justify-between border-t border-gray-300 pt-1 mt-1 font-semibold">
              <span>Total Vehículo:</span>
              <span className="text-gray-800">{formatCurrency(totalConFlete)}</span>
            </div>
          </div>
        )}
      </div>
    );
  };

  const RubroItem = ({ rubro }: { rubro: Rubro }) => {
    const [expandido, setExpandido] = useState(false);

    // Determinar si tiene detalles para expandir
    const tieneDetalles = rubro.tipo === 'personal' && rubro.salario_base;

    const esCompartido = rubro.tipo_asignacion === 'compartido';

    return (
      <div className="border-b border-gray-100">
        {/* Línea principal */}
        <div
          className={`flex justify-between items-center py-1.5 px-3 hover:bg-gray-50 text-xs ${tieneDetalles ? 'cursor-pointer' : ''}`}
          onClick={() => tieneDetalles && setExpandido(!expandido)}
        >
          <div className="flex-1 flex items-center gap-2">
            <span className="text-gray-700">{rubro.nombre}</span>
            {rubro.cantidad && rubro.cantidad > 1 && (
              <span className="text-gray-500 text-xs">(x{rubro.cantidad})</span>
            )}
            {esCompartido && (
              <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 text-[10px] font-medium rounded">
                Compartido{rubro.criterio_prorrateo ? ` - ${rubro.criterio_prorrateo}` : ''}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {rubro.valor_unitario && rubro.cantidad && rubro.cantidad > 1 && (
              <span className="text-gray-500 text-[10px]">
                {formatCurrency(rubro.valor_unitario)} c/u
              </span>
            )}
            <span className="font-medium text-gray-900">{formatCurrency(rubro.valor_total)}</span>
            {tieneDetalles && (
              <ChevronDown
                size={12}
                className={`text-gray-400 transition-transform ${expandido ? 'rotate-180' : ''}`}
              />
            )}
          </div>
        </div>

        {/* Detalles expandidos */}
        {expandido && tieneDetalles && (
          <div className="px-3 py-1.5 bg-gray-50 text-[10px] text-gray-600 space-y-0.5">
            {/* Desglose para Personal */}
            {rubro.tipo === 'personal' && rubro.salario_base !== undefined && (
              <>
                <div className="flex justify-between">
                  <span>Salario Base:</span>
                  <span className="font-medium text-gray-700">{formatCurrency(rubro.salario_base * (rubro.cantidad || 1))}</span>
                </div>
                {rubro.prestaciones !== undefined && rubro.prestaciones > 0 && (
                  <div className="flex justify-between">
                    <span>Prestaciones ({((rubro.factor_prestacional || 0) * 100).toFixed(1)}%):</span>
                    <span className="font-medium text-gray-700">{formatCurrency(rubro.prestaciones * (rubro.cantidad || 1))}</span>
                  </div>
                )}
                {rubro.subsidio_transporte !== undefined && rubro.subsidio_transporte > 0 && (
                  <div className="flex justify-between">
                    <span>Subsidio Transporte:</span>
                    <span className="font-medium text-gray-700">{formatCurrency(rubro.subsidio_transporte * (rubro.cantidad || 1))}</span>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    );
  };

  const LineaItem = ({
    titulo,
    valor,
    indent = 0,
    bold = false,
    negativo = false
  }: {
    titulo: string;
    valor: number;
    indent?: number;
    bold?: boolean;
    negativo?: boolean;
  }) => {
    const paddingLeft = `${indent * 12 + 12}px`;
    const fontWeight = bold ? 'font-semibold' : 'font-normal';
    const textColor = negativo ? 'text-red-600' : 'text-gray-900';
    const bgColor = bold && indent === 0 ? 'bg-gray-50' : '';

    return (
      <div className={`flex justify-between items-center py-1 text-xs ${bgColor} border-b border-gray-100`} style={{ paddingLeft, paddingRight: '12px' }}>
        <span className={`${fontWeight} text-gray-700`}>{titulo}</span>
        <span className={`${fontWeight} ${textColor}`}>
          {negativo && valor > 0 ? '-' : ''}{formatCurrency(Math.abs(valor))}
        </span>
      </div>
    );
  };

  return (
    <div className="bg-white border border-gray-200 rounded">
      {/* Header con selector de mes */}
      <div className="px-3 py-2 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
        <h3 className="text-sm font-semibold text-gray-800">
          Estado de Resultados - {marca.nombre}
        </h3>
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

      {/* SECCIÓN: INGRESOS POR VENTAS */}
      <SeccionHeader titulo="Ingresos por Ventas" seccion="ingresos" valor={ingresosPorVentas} bgColor="bg-slate-600" />
      {seccionesAbiertas.ingresos && (
        <div>
          <LineaItem titulo="Ventas del Período" valor={ingresosPorVentas} indent={1} />
        </div>
      )}

      {/* SECCIÓN: COSTO DE MERCANCÍA VENDIDA */}
      <SeccionHeader titulo="Costo de Mercancía Vendida" seccion="cmv" valor={costoMercanciaVendida} bgColor="bg-stone-600" />
      {seccionesAbiertas.cmv && (
        <div>
          <LineaItem
            titulo={`CMV (${(100 - descuentoPieFacturaPonderado).toFixed(1)}% de las ventas)`}
            valor={costoMercanciaVendida}
            indent={1}
          />
          {config?.tramos && config.tramos.length > 0 && (
            <div className="px-3 py-1.5 bg-gray-50 text-[10px] text-gray-600 border-b border-gray-100">
              <div className="font-medium text-gray-700 mb-1">Descuento Pie de Factura por Tramos:</div>
              {config.tramos.map((tramo, idx) => (
                <div key={idx} className="flex justify-between pl-2">
                  <span>Tramo {tramo.orden}: {tramo.porcentaje_ventas}% de ventas</span>
                  <span>{tramo.porcentaje_descuento}% descuento</span>
                </div>
              ))}
              <div className="flex justify-between pl-2 mt-1 pt-1 border-t border-gray-200 font-medium">
                <span>Descuento Ponderado:</span>
                <span>{descuentoPieFacturaPonderado.toFixed(2)}%</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* MARGEN BRUTO */}
      <div className="bg-emerald-50 border-y border-emerald-300">
        <div className="flex justify-between items-center px-3 py-2">
          <span className="text-xs font-bold text-emerald-900 uppercase">Margen Bruto (Utilidad de Distribución)</span>
          <div className="text-right">
            <div className="text-sm font-bold text-emerald-900">{formatCurrency(margenBruto)}</div>
            <div className="text-xs text-emerald-700">Margen: {margenBrutoPorcentaje.toFixed(2)}%</div>
          </div>
        </div>
      </div>

      {/* SECCIÓN: COSTOS COMERCIALES */}
      <SeccionHeader titulo="Costos Comerciales" seccion="comercial" valor={totalComercial} bgColor="bg-gray-700" mostrarPorcentaje />
      {seccionesAbiertas.comercial && (
        <div>
          {/* Personal Comercial */}
          {grupos.comercialPersonal.length > 0 && (
            <>
              <SubSeccionHeader
                titulo="Personal Comercial"
                subSeccion="comercialPersonal"
                valor={subtotalComercialPersonal}
                mostrarPorcentaje
              />
              {subSeccionesAbiertas.comercialPersonal && (
                <>
                  {grupos.comercialPersonal.map((rubro, idx) => (
                    <RubroItem key={`com-pers-${idx}`} rubro={rubro} />
                  ))}
                </>
              )}
            </>
          )}

          {/* Gastos Comerciales */}
          {grupos.comercialGastos.length > 0 && (
            <>
              <SubSeccionHeader
                titulo="Gastos Comerciales"
                subSeccion="comercialGastos"
                valor={subtotalComercialGastos}
                mostrarPorcentaje
              />
              {subSeccionesAbiertas.comercialGastos && (
                <>
                  {grupos.comercialGastos.map((rubro, idx) => (
                    <RubroItem key={`com-gasto-${idx}`} rubro={rubro} />
                  ))}
                </>
              )}
            </>
          )}

          {/* Lejanías Comerciales */}
          {typeof marca.lejania_comercial === 'number' && marca.lejania_comercial > 0 && (
            <LineaItem titulo="Lejanías Comerciales (Combustible + Pernocta)" valor={marca.lejania_comercial} indent={1} />
          )}

          <LineaItem titulo="Total Costos Comerciales" valor={totalComercial} bold />
        </div>
      )}

      {/* SECCIÓN: COSTOS LOGÍSTICOS */}
      <SeccionHeader titulo="Costos Logísticos" seccion="logistico" valor={totalLogistico} bgColor="bg-gray-700" mostrarPorcentaje />
      {seccionesAbiertas.logistico && (
        <div>
          {/* Flota de Vehículos (ahora incluye flete base) */}
          {vehiculosConFlete.length > 0 && (
            <>
              <SubSeccionHeader
                titulo="Flota de Vehículos"
                subSeccion="logisticoVehiculos"
                valor={subtotalLogisticoVehiculos}
                mostrarPorcentaje
              />
              {subSeccionesAbiertas.logisticoVehiculos && (
                <>
                  {vehiculosConFlete.map((vehiculo, idx) => (
                    <VehiculoItem key={`log-veh-${idx}`} vehiculo={vehiculo} />
                  ))}
                </>
              )}
            </>
          )}

          {/* Personal Logístico */}
          {grupos.logisticoPersonal.length > 0 && (
            <>
              <SubSeccionHeader
                titulo="Personal Logístico"
                subSeccion="logisticoPersonal"
                valor={subtotalLogisticoPersonal}
                mostrarPorcentaje
              />
              {subSeccionesAbiertas.logisticoPersonal && (
                <>
                  {grupos.logisticoPersonal.map((rubro, idx) => (
                    <RubroItem key={`log-pers-${idx}`} rubro={rubro} />
                  ))}
                </>
              )}
            </>
          )}

          {/* Gastos Logísticos */}
          {grupos.logisticoGastos.length > 0 && (
            <>
              <SubSeccionHeader
                titulo="Gastos Logísticos"
                subSeccion="logisticoGastos"
                valor={subtotalLogisticoGastos}
                mostrarPorcentaje
              />
              {subSeccionesAbiertas.logisticoGastos && (
                <>
                  {grupos.logisticoGastos.map((rubro, idx) => (
                    <RubroItem key={`log-gasto-${idx}`} rubro={rubro} />
                  ))}
                </>
              )}
            </>
          )}

          {/* Lejanías Logísticas (solo costos variables: combustible, peajes, pernocta) */}
          {subtotalLejanias > 0 && (
            <>
              <SubSeccionHeader
                titulo="Lejanías Logísticas (Costos Variables)"
                subSeccion="logisticoLejanias"
                valor={subtotalLejanias}
                mostrarPorcentaje
              />
              {subSeccionesAbiertas.logisticoLejanias && lejaniasLogistica && (
                <div className="px-3 py-1.5 bg-gray-50 text-xs space-y-1">
                  {lejaniasLogistica.total_combustible_mensual > 0 && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Combustible</span>
                      <span className="font-medium text-gray-800">{formatCurrency(lejaniasLogistica.total_combustible_mensual)}</span>
                    </div>
                  )}
                  {lejaniasLogistica.total_peaje_mensual > 0 && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Peajes</span>
                      <span className="font-medium text-gray-800">{formatCurrency(lejaniasLogistica.total_peaje_mensual)}</span>
                    </div>
                  )}
                  {/* Pernocta desglosado */}
                  {lejaniasLogistica.total_pernocta_mensual > 0 && (
                    <>
                      <div className="flex justify-between pt-1 border-t border-gray-200">
                        <span className="text-gray-700 font-medium">Pernocta (Total)</span>
                        <span className="font-medium text-gray-800">{formatCurrency(lejaniasLogistica.total_pernocta_mensual)}</span>
                      </div>
                      {(lejaniasLogistica.total_pernocta_conductor_mensual || 0) > 0 && (
                        <div className="flex justify-between pl-3">
                          <span className="text-gray-500">Conductor (va al Tercero si aplica)</span>
                          <span className="text-gray-600">{formatCurrency(lejaniasLogistica.total_pernocta_conductor_mensual || 0)}</span>
                        </div>
                      )}
                      {(lejaniasLogistica.total_pernocta_auxiliar_mensual || 0) > 0 && (
                        <div className="flex justify-between pl-3">
                          <span className="text-gray-500">Auxiliar (paga Empresa)</span>
                          <span className="text-gray-600">{formatCurrency(lejaniasLogistica.total_pernocta_auxiliar_mensual || 0)}</span>
                        </div>
                      )}
                      {(lejaniasLogistica.total_parqueadero_mensual || 0) > 0 && (
                        <div className="flex justify-between pl-3">
                          <span className="text-gray-500">Parqueadero</span>
                          <span className="text-gray-600">{formatCurrency(lejaniasLogistica.total_parqueadero_mensual || 0)}</span>
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}
            </>
          )}

          {loadingLejanias && (
            <div className="px-3 py-2 text-xs text-gray-500 italic">
              Cargando datos de lejanías...
            </div>
          )}

          <LineaItem titulo="Total Costos Logísticos" valor={totalLogistico} bold />
        </div>
      )}

      {/* SECCIÓN: COSTOS ADMINISTRATIVOS */}
      <SeccionHeader titulo="Costos Administrativos" seccion="administrativo" valor={totalAdministrativo} bgColor="bg-gray-700" mostrarPorcentaje />
      {seccionesAbiertas.administrativo && (
        <div>
          {/* Personal Administrativo */}
          {grupos.administrativoPersonal.length > 0 && (
            <>
              <SubSeccionHeader
                titulo="Personal Administrativo"
                subSeccion="administrativoPersonal"
                valor={subtotalAdministrativoPersonal}
                mostrarPorcentaje
              />
              {subSeccionesAbiertas.administrativoPersonal && (
                <>
                  {grupos.administrativoPersonal.map((rubro, idx) => (
                    <RubroItem key={`adm-pers-${idx}`} rubro={rubro} />
                  ))}
                </>
              )}
            </>
          )}

          {/* Gastos Administrativos */}
          {grupos.administrativoGastos.length > 0 && (
            <>
              <SubSeccionHeader
                titulo="Gastos Administrativos"
                subSeccion="administrativoGastos"
                valor={subtotalAdministrativoGastos}
                mostrarPorcentaje
              />
              {subSeccionesAbiertas.administrativoGastos && (
                <>
                  {grupos.administrativoGastos.map((rubro, idx) => (
                    <RubroItem key={`adm-gasto-${idx}`} rubro={rubro} />
                  ))}
                </>
              )}
            </>
          )}

          <LineaItem titulo="Total Costos Administrativos" valor={totalAdministrativo} bold />
        </div>
      )}

      {/* EBITDA - Antes de Utilidad Operacional */}
      <div className="bg-amber-50 border-y border-amber-300">
        <div className="flex justify-between items-center px-3 py-2">
          <div>
            <span className="text-xs font-bold text-amber-900 uppercase">EBITDA</span>
            <span className="text-[10px] text-amber-700 ml-2">(Utilidad antes de Intereses, Impuestos, Depreciación y Amortización)</span>
          </div>
          <div className="text-right">
            <div className="text-sm font-bold text-amber-900">{formatCurrency(utilidadOperacional)}</div>
            <div className="text-xs text-amber-700">{calcularPorcentajeSobreVentas(utilidadOperacional)}</div>
          </div>
        </div>
      </div>

      {/* UTILIDAD OPERACIONAL */}
      <div className="bg-blue-50 border-y-2 border-blue-500">
        <div className="flex justify-between items-center px-3 py-2">
          <span className="text-xs font-bold text-blue-900 uppercase">Utilidad Operacional</span>
          <div className="text-right">
            <div className="text-sm font-bold text-blue-900">{formatCurrency(utilidadOperacional)}</div>
            <div className="text-xs text-blue-700">Margen: {margenOperacional.toFixed(2)}%</div>
          </div>
        </div>
      </div>

      {/* SECCIÓN: OTROS INGRESOS (Rebate y Descuento Financiero) */}
      {totalOtrosIngresos > 0 && (
        <>
          <SeccionHeader titulo="Otros Ingresos" seccion="otrosIngresos" valor={totalOtrosIngresos} bgColor="bg-teal-700" />
          {seccionesAbiertas.otrosIngresos && (
            <div>
              {ingresoRebate > 0 && (
                <LineaItem
                  titulo={`Rebate / RxP (${porcentajeRebate.toFixed(2)}% s/ ventas)`}
                  valor={ingresoRebate}
                  indent={1}
                />
              )}
              {ingresoDescuentoFinanciero > 0 && (
                <LineaItem
                  titulo={`Descuento Financiero (${porcentajeDescFinanciero.toFixed(2)}% s/ ventas)`}
                  valor={ingresoDescuentoFinanciero}
                  indent={1}
                />
              )}
              <LineaItem titulo="Total Otros Ingresos" valor={totalOtrosIngresos} bold />
            </div>
          )}
        </>
      )}

      {/* UTILIDAD ANTES DE IMPUESTOS */}
      {totalOtrosIngresos > 0 && (
        <div className="bg-indigo-50 border-y border-indigo-300">
          <div className="flex justify-between items-center px-3 py-1.5">
            <span className="text-xs font-semibold text-indigo-900">Utilidad Antes de Impuestos</span>
            <div className="text-sm font-bold text-indigo-900">{formatCurrency(utilidadAntesImpuestos)}</div>
          </div>
        </div>
      )}

      {/* SECCIÓN: IMPUESTOS */}
      <SeccionHeader titulo="Impuestos" seccion="impuestos" valor={impuestoRenta} bgColor="bg-gray-700" />
      {seccionesAbiertas.impuestos && (
        <div>
          <LineaItem titulo={`Impuesto de Renta (${(tasaImpuesto * 100).toFixed(0)}%)`} valor={impuestoRenta} indent={1} negativo />
          <LineaItem titulo="Total Impuestos" valor={impuestoRenta} bold />
        </div>
      )}

      {/* UTILIDAD NETA */}
      <div className="bg-green-50 border-y-2 border-green-500">
        <div className="flex justify-between items-center px-3 py-2">
          <span className="text-xs font-bold text-green-900 uppercase">Utilidad Neta</span>
          <div className="text-right">
            <div className="text-sm font-bold text-green-900">{formatCurrency(utilidadNeta)}</div>
            <div className="text-xs text-green-700">Margen: {margenNeto.toFixed(2)}%</div>
          </div>
        </div>
      </div>
    </div>
  );
}
