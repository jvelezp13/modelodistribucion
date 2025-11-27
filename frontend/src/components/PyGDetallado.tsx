'use client';

import React, { useState } from 'react';
import { Marca, Rubro } from '@/lib/api';
import { ChevronDown, ChevronRight } from 'lucide-react';

interface PyGDetalladoProps {
  marca: Marca;
}

interface SeccionState {
  ingresos: boolean;
  comercial: boolean;
  logistico: boolean;
  administrativo: boolean;
  impuestos: boolean;
}

interface SubSeccionState {
  comercialPersonal: boolean;
  comercialGastos: boolean;
  logisticoVehiculos: boolean;
  logisticoPersonal: boolean;
  logisticoGastos: boolean;
  administrativoPersonal: boolean;
  administrativoGastos: boolean;
}

export default function PyGDetallado({ marca }: PyGDetalladoProps) {
  const [seccionesAbiertas, setSeccionesAbiertas] = useState<SeccionState>({
    ingresos: true,
    comercial: false,
    logistico: false,
    administrativo: false,
    impuestos: false,
  });

  const [subSeccionesAbiertas, setSubSeccionesAbiertas] = useState<SubSeccionState>({
    comercialPersonal: false,
    comercialGastos: false,
    logisticoVehiculos: false,
    logisticoPersonal: false,
    logisticoGastos: false,
    administrativoPersonal: false,
    administrativoGastos: false,
  });

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

  // Calcular subtotales
  const subtotalComercialPersonal = grupos.comercialPersonal.reduce((sum, r) => sum + r.valor_total, 0);
  const subtotalComercialGastos = grupos.comercialGastos.reduce((sum, r) => sum + r.valor_total, 0);
  const totalComercial = subtotalComercialPersonal + subtotalComercialGastos;

  const subtotalLogisticoVehiculos = grupos.logisticoVehiculos.reduce((sum, r) => sum + r.valor_total, 0);
  const subtotalLogisticoPersonal = grupos.logisticoPersonal.reduce((sum, r) => sum + r.valor_total, 0);
  const subtotalLogisticoGastos = grupos.logisticoGastos.reduce((sum, r) => sum + r.valor_total, 0);
  const totalLogistico = subtotalLogisticoVehiculos + subtotalLogisticoPersonal + subtotalLogisticoGastos;

  const subtotalAdministrativoPersonal = grupos.administrativoPersonal.reduce((sum, r) => sum + r.valor_total, 0);
  const subtotalAdministrativoGastos = grupos.administrativoGastos.reduce((sum, r) => sum + r.valor_total, 0);
  const totalAdministrativo = subtotalAdministrativoPersonal + subtotalAdministrativoGastos;

  // Ventas y descuentos
  const ventasBrutas = marca.ventas_mensuales || 0;
  const totalDescuentos = (marca.descuento_pie_factura || 0) +
                          (marca.rebate || 0) +
                          (marca.descuento_financiero || 0);
  const ventasNetas = marca.ventas_netas_mensuales || ventasBrutas;

  // Costos e impuestos
  const totalCostos = totalComercial + totalLogistico + totalAdministrativo;
  const utilidadAntesImpuestos = ventasNetas - totalCostos;

  // Calcular impuesto de renta (33% en Colombia)
  const tasaImpuesto = 0.33;
  const impuestoRenta = utilidadAntesImpuestos > 0 ? utilidadAntesImpuestos * tasaImpuesto : 0;
  const utilidadNeta = utilidadAntesImpuestos - impuestoRenta;

  // Márgenes
  const margenOperacional = ventasNetas > 0 ? (utilidadAntesImpuestos / ventasNetas) * 100 : 0;
  const margenNeto = ventasNetas > 0 ? (utilidadNeta / ventasNetas) * 100 : 0;

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const SeccionHeader = ({
    titulo,
    seccion,
    valor,
    bgColor = 'bg-gray-700'
  }: {
    titulo: string;
    seccion: keyof SeccionState;
    valor?: number;
    bgColor?: string;
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
          <span className="text-sm font-bold">{formatCurrency(valor)}</span>
        )}
      </div>
    );
  };

  const SubSeccionHeader = ({
    titulo,
    subSeccion,
    valor
  }: {
    titulo: string;
    subSeccion: keyof SubSeccionState;
    valor: number;
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
        <span className="text-xs font-semibold text-gray-900">{formatCurrency(valor)}</span>
      </div>
    );
  };

  const RubroItem = ({ rubro }: { rubro: Rubro }) => {
    const [expandido, setExpandido] = useState(false);

    // Determinar si tiene detalles para expandir
    const tieneDetalles = (rubro.tipo === 'personal' && rubro.salario_base) ||
                          (rubro.tipo === 'vehiculo' && rubro.tipo_vehiculo);

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
            {rubro.tipo === 'vehiculo' && rubro.esquema && (
              <span className="px-1.5 py-0.5 bg-purple-100 text-purple-700 text-[10px] font-medium rounded">
                {rubro.esquema === 'renting' ? 'Renting' : rubro.esquema === 'tercero' ? 'Tercero' : 'Propio'}
              </span>
            )}
            {rubro.tipo_vehiculo && (
              <span className="text-gray-500 text-[10px]">[{rubro.tipo_vehiculo.toUpperCase()}]</span>
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
                    <span>Prestaciones ({(rubro.factor_prestacional || 0) * 100}%):</span>
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

            {/* Desglose para Vehículos Renting (solo costos fijos) */}
            {rubro.tipo === 'vehiculo' && rubro.esquema === 'renting' && (
              <>
                {rubro.canon_mensual !== undefined && rubro.canon_mensual > 0 && (
                  <div className="flex justify-between">
                    <span>Canon Mensual:</span>
                    <span className="font-medium text-gray-700">{formatCurrency(rubro.canon_mensual * (rubro.cantidad || 1))}</span>
                  </div>
                )}
                {rubro.lavada !== undefined && rubro.lavada > 0 && (
                  <div className="flex justify-between">
                    <span>Lavada:</span>
                    <span className="font-medium text-gray-700">{formatCurrency(rubro.lavada * (rubro.cantidad || 1))}</span>
                  </div>
                )}
                {rubro.reposicion !== undefined && rubro.reposicion > 0 && (
                  <div className="flex justify-between">
                    <span>Reposición:</span>
                    <span className="font-medium text-gray-700">{formatCurrency(rubro.reposicion * (rubro.cantidad || 1))}</span>
                  </div>
                )}
                <div className="text-gray-500 italic text-[9px] mt-1">
                  Combustible y peajes en Lejanías Logísticas
                </div>
              </>
            )}

            {/* Desglose para Vehículos Propios (solo costos fijos) */}
            {rubro.tipo === 'vehiculo' && rubro.esquema === 'tradicional' && (
              <>
                {rubro.depreciacion !== undefined && rubro.depreciacion > 0 && (
                  <div className="flex justify-between">
                    <span>Depreciación:</span>
                    <span className="font-medium text-gray-700">{formatCurrency(rubro.depreciacion * (rubro.cantidad || 1))}</span>
                  </div>
                )}
                {rubro.mantenimiento !== undefined && rubro.mantenimiento > 0 && (
                  <div className="flex justify-between">
                    <span>Mantenimiento:</span>
                    <span className="font-medium text-gray-700">{formatCurrency(rubro.mantenimiento * (rubro.cantidad || 1))}</span>
                  </div>
                )}
                {rubro.seguro !== undefined && rubro.seguro > 0 && (
                  <div className="flex justify-between">
                    <span>Seguro:</span>
                    <span className="font-medium text-gray-700">{formatCurrency(rubro.seguro * (rubro.cantidad || 1))}</span>
                  </div>
                )}
                {rubro.impuestos !== undefined && rubro.impuestos > 0 && (
                  <div className="flex justify-between">
                    <span>Impuestos (mensual):</span>
                    <span className="font-medium text-gray-700">{formatCurrency((rubro.impuestos / 12) * (rubro.cantidad || 1))}</span>
                  </div>
                )}
                <div className="text-gray-500 italic text-[9px] mt-1">
                  Combustible y peajes en Lejanías Logísticas
                </div>
              </>
            )}

            {/* Desglose para Vehículos Terceros */}
            {rubro.tipo === 'vehiculo' && rubro.esquema === 'tercero' && (
              <div className="text-gray-500 italic">
                El flete base se calcula en Lejanías Logísticas (Recorridos)
              </div>
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
      {/* Header */}
      <div className="px-3 py-2 border-b border-gray-200 bg-gray-50">
        <h3 className="text-sm font-semibold text-gray-800">
          Estado de Resultados - {marca.nombre}
        </h3>
      </div>

      {/* SECCIÓN: INGRESOS */}
      <SeccionHeader titulo="Ingresos" seccion="ingresos" valor={ventasNetas} bgColor="bg-blue-700" />
      {seccionesAbiertas.ingresos && (
        <div>
          <LineaItem titulo="Ventas Brutas" valor={ventasBrutas} indent={1} />
          {totalDescuentos > 0 && (
            <>
              <LineaItem titulo="Descuentos Totales" valor={totalDescuentos} indent={1} negativo />
              {marca.descuento_pie_factura && marca.descuento_pie_factura > 0 && (
                <LineaItem titulo="Descuento Pie de Factura" valor={marca.descuento_pie_factura} indent={2} negativo />
              )}
              {marca.rebate && marca.rebate > 0 && (
                <LineaItem titulo="Rebate" valor={marca.rebate} indent={2} negativo />
              )}
              {marca.descuento_financiero && marca.descuento_financiero > 0 && (
                <LineaItem titulo="Descuento Financiero" valor={marca.descuento_financiero} indent={2} negativo />
              )}
            </>
          )}
          <LineaItem titulo="Ventas Netas" valor={ventasNetas} bold />
        </div>
      )}

      {/* SECCIÓN: COSTOS COMERCIALES */}
      <SeccionHeader titulo="Costos Comerciales" seccion="comercial" valor={totalComercial} bgColor="bg-gray-700" />
      {seccionesAbiertas.comercial && (
        <div>
          {/* Personal Comercial */}
          {grupos.comercialPersonal.length > 0 && (
            <>
              <SubSeccionHeader
                titulo="Personal Comercial"
                subSeccion="comercialPersonal"
                valor={subtotalComercialPersonal}
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
            <LineaItem titulo="Lejanías Comerciales (Rutas)" valor={marca.lejania_comercial} indent={1} />
          )}

          <LineaItem titulo="Total Costos Comerciales" valor={totalComercial} bold />
        </div>
      )}

      {/* SECCIÓN: COSTOS LOGÍSTICOS */}
      <SeccionHeader titulo="Costos Logísticos" seccion="logistico" valor={totalLogistico} bgColor="bg-gray-700" />
      {seccionesAbiertas.logistico && (
        <div>
          {/* Vehículos */}
          {grupos.logisticoVehiculos.length > 0 && (
            <>
              <SubSeccionHeader
                titulo="Flota de Vehículos"
                subSeccion="logisticoVehiculos"
                valor={subtotalLogisticoVehiculos}
              />
              {subSeccionesAbiertas.logisticoVehiculos && (
                <>
                  {grupos.logisticoVehiculos.map((rubro, idx) => (
                    <RubroItem key={`log-veh-${idx}`} rubro={rubro} />
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

          {/* Lejanías Logísticas */}
          {typeof marca.lejania_logistica === 'number' && marca.lejania_logistica > 0 && (
            <LineaItem titulo="Lejanías Logísticas (Rutas)" valor={marca.lejania_logistica} indent={1} />
          )}

          <LineaItem titulo="Total Costos Logísticos" valor={totalLogistico} bold />
        </div>
      )}

      {/* SECCIÓN: COSTOS ADMINISTRATIVOS */}
      <SeccionHeader titulo="Costos Administrativos" seccion="administrativo" valor={totalAdministrativo} bgColor="bg-gray-700" />
      {seccionesAbiertas.administrativo && (
        <div>
          {/* Personal Administrativo */}
          {grupos.administrativoPersonal.length > 0 && (
            <>
              <SubSeccionHeader
                titulo="Personal Administrativo"
                subSeccion="administrativoPersonal"
                valor={subtotalAdministrativoPersonal}
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

      {/* UTILIDAD OPERACIONAL */}
      <div className="bg-blue-50 border-y-2 border-blue-500">
        <div className="flex justify-between items-center px-3 py-2">
          <span className="text-xs font-bold text-blue-900 uppercase">Utilidad Operacional</span>
          <div className="text-right">
            <div className="text-sm font-bold text-blue-900">{formatCurrency(utilidadAntesImpuestos)}</div>
            <div className="text-xs text-blue-700">Margen: {margenOperacional.toFixed(2)}%</div>
          </div>
        </div>
      </div>

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
