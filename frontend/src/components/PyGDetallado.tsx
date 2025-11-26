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
    comercial: true,
    logistico: true,
    administrativo: true,
    impuestos: true,
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
    nivel = 1
  }: {
    titulo: string;
    seccion: keyof SeccionState;
    valor?: number;
    nivel?: number;
  }) => {
    const isOpen = seccionesAbiertas[seccion];
    const bgColor = nivel === 1 ? 'bg-gray-800' : 'bg-gray-700';
    const textSize = nivel === 1 ? 'text-lg' : 'text-base';

    return (
      <div
        className={`${bgColor} text-white p-3 cursor-pointer flex justify-between items-center rounded-lg mb-2`}
        onClick={() => toggleSeccion(seccion)}
      >
        <div className="flex items-center gap-2">
          {isOpen ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
          <span className={`font-semibold ${textSize}`}>{titulo}</span>
        </div>
        {valor !== undefined && (
          <span className={`font-bold ${textSize}`}>{formatCurrency(valor)}</span>
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
        className="bg-gray-600 text-white p-2 cursor-pointer flex justify-between items-center rounded mb-1"
        onClick={() => toggleSubSeccion(subSeccion)}
      >
        <div className="flex items-center gap-2">
          {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          <span className="font-medium">{titulo}</span>
        </div>
        <span className="font-semibold">{formatCurrency(valor)}</span>
      </div>
    );
  };

  const RubroItem = ({ rubro }: { rubro: Rubro }) => (
    <div className="flex justify-between items-center py-2 px-4 hover:bg-gray-50 border-b border-gray-100">
      <div className="flex-1">
        <span className="text-gray-700">{rubro.nombre}</span>
        {rubro.cantidad && rubro.cantidad > 1 && (
          <span className="text-gray-500 text-sm ml-2">
            (x{rubro.cantidad})
          </span>
        )}
        {rubro.esquema && (
          <span className="text-gray-500 text-sm ml-2">
            [{rubro.esquema}]
          </span>
        )}
      </div>
      <span className="font-medium text-gray-900">{formatCurrency(rubro.valor_total)}</span>
    </div>
  );

  const LineaItem = ({
    titulo,
    valor,
    nivel = 1,
    negativo = false
  }: {
    titulo: string;
    valor: number;
    nivel?: number;
    negativo?: boolean;
  }) => {
    const fontWeight = nivel === 1 ? 'font-bold' : 'font-semibold';
    const textSize = nivel === 1 ? 'text-base' : 'text-sm';
    const bgColor = nivel === 1 ? 'bg-gray-100' : '';
    const textColor = negativo ? 'text-red-600' : 'text-gray-900';

    return (
      <div className={`flex justify-between items-center py-2 px-4 ${bgColor}`}>
        <span className={`${fontWeight} ${textSize} text-gray-700`}>{titulo}</span>
        <span className={`${fontWeight} ${textSize} ${textColor}`}>
          {negativo && valor > 0 ? '-' : ''}{formatCurrency(Math.abs(valor))}
        </span>
      </div>
    );
  };

  return (
    <div className="max-w-6xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">
        Estado de Resultados - {marca.nombre}
      </h2>

      {/* SECCIÓN: INGRESOS */}
      <SeccionHeader titulo="INGRESOS" seccion="ingresos" valor={ventasNetas} />
      {seccionesAbiertas.ingresos && (
        <div className="mb-4 border border-gray-200 rounded-lg">
          <LineaItem titulo="Ventas Brutas" valor={ventasBrutas} nivel={2} />
          {totalDescuentos > 0 && (
            <>
              <LineaItem titulo="Descuentos Totales" valor={totalDescuentos} nivel={2} negativo />
              {marca.descuento_pie_factura && marca.descuento_pie_factura > 0 && (
                <div className="pl-8">
                  <LineaItem titulo="Descuento Pie de Factura" valor={marca.descuento_pie_factura} nivel={3} negativo />
                </div>
              )}
              {marca.rebate && marca.rebate > 0 && (
                <div className="pl-8">
                  <LineaItem titulo="Rebate" valor={marca.rebate} nivel={3} negativo />
                </div>
              )}
              {marca.descuento_financiero && marca.descuento_financiero > 0 && (
                <div className="pl-8">
                  <LineaItem titulo="Descuento Financiero" valor={marca.descuento_financiero} nivel={3} negativo />
                </div>
              )}
            </>
          )}
          <LineaItem titulo="Ventas Netas" valor={ventasNetas} nivel={1} />
        </div>
      )}

      {/* SECCIÓN: COSTOS COMERCIALES */}
      <SeccionHeader titulo="COSTOS COMERCIALES" seccion="comercial" valor={totalComercial} />
      {seccionesAbiertas.comercial && (
        <div className="mb-4 border border-gray-200 rounded-lg">
          {/* Personal Comercial */}
          {grupos.comercialPersonal.length > 0 && (
            <>
              <SubSeccionHeader
                titulo="Personal Comercial"
                subSeccion="comercialPersonal"
                valor={subtotalComercialPersonal}
              />
              {subSeccionesAbiertas.comercialPersonal && (
                <div className="bg-gray-50">
                  {grupos.comercialPersonal.map((rubro, idx) => (
                    <RubroItem key={`com-pers-${idx}`} rubro={rubro} />
                  ))}
                </div>
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
                <div className="bg-gray-50">
                  {grupos.comercialGastos.map((rubro, idx) => (
                    <RubroItem key={`com-gasto-${idx}`} rubro={rubro} />
                  ))}
                </div>
              )}
            </>
          )}

          <LineaItem titulo="Total Costos Comerciales" valor={totalComercial} nivel={1} />
        </div>
      )}

      {/* SECCIÓN: COSTOS LOGÍSTICOS */}
      <SeccionHeader titulo="COSTOS LOGÍSTICOS" seccion="logistico" valor={totalLogistico} />
      {seccionesAbiertas.logistico && (
        <div className="mb-4 border border-gray-200 rounded-lg">
          {/* Vehículos */}
          {grupos.logisticoVehiculos.length > 0 && (
            <>
              <SubSeccionHeader
                titulo="Flota de Vehículos"
                subSeccion="logisticoVehiculos"
                valor={subtotalLogisticoVehiculos}
              />
              {subSeccionesAbiertas.logisticoVehiculos && (
                <div className="bg-gray-50">
                  {grupos.logisticoVehiculos.map((rubro, idx) => (
                    <RubroItem key={`log-veh-${idx}`} rubro={rubro} />
                  ))}
                </div>
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
                <div className="bg-gray-50">
                  {grupos.logisticoPersonal.map((rubro, idx) => (
                    <RubroItem key={`log-pers-${idx}`} rubro={rubro} />
                  ))}
                </div>
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
                <div className="bg-gray-50">
                  {grupos.logisticoGastos.map((rubro, idx) => (
                    <RubroItem key={`log-gasto-${idx}`} rubro={rubro} />
                  ))}
                </div>
              )}
            </>
          )}

          <LineaItem titulo="Total Costos Logísticos" valor={totalLogistico} nivel={1} />
        </div>
      )}

      {/* SECCIÓN: COSTOS ADMINISTRATIVOS */}
      <SeccionHeader titulo="COSTOS ADMINISTRATIVOS" seccion="administrativo" valor={totalAdministrativo} />
      {seccionesAbiertas.administrativo && (
        <div className="mb-4 border border-gray-200 rounded-lg">
          {/* Personal Administrativo */}
          {grupos.administrativoPersonal.length > 0 && (
            <>
              <SubSeccionHeader
                titulo="Personal Administrativo"
                subSeccion="administrativoPersonal"
                valor={subtotalAdministrativoPersonal}
              />
              {subSeccionesAbiertas.administrativoPersonal && (
                <div className="bg-gray-50">
                  {grupos.administrativoPersonal.map((rubro, idx) => (
                    <RubroItem key={`adm-pers-${idx}`} rubro={rubro} />
                  ))}
                </div>
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
                <div className="bg-gray-50">
                  {grupos.administrativoGastos.map((rubro, idx) => (
                    <RubroItem key={`adm-gasto-${idx}`} rubro={rubro} />
                  ))}
                </div>
              )}
            </>
          )}

          <LineaItem titulo="Total Costos Administrativos" valor={totalAdministrativo} nivel={1} />
        </div>
      )}

      {/* UTILIDAD OPERACIONAL */}
      <div className="mb-4 border-2 border-blue-500 rounded-lg bg-blue-50">
        <div className="flex justify-between items-center p-4">
          <span className="text-xl font-bold text-blue-900">UTILIDAD OPERACIONAL</span>
          <div className="text-right">
            <div className="text-xl font-bold text-blue-900">{formatCurrency(utilidadAntesImpuestos)}</div>
            <div className="text-sm text-blue-700">Margen: {margenOperacional.toFixed(2)}%</div>
          </div>
        </div>
      </div>

      {/* SECCIÓN: IMPUESTOS */}
      <SeccionHeader titulo="IMPUESTOS" seccion="impuestos" valor={impuestoRenta} />
      {seccionesAbiertas.impuestos && (
        <div className="mb-4 border border-gray-200 rounded-lg">
          <LineaItem titulo={`Impuesto de Renta (${(tasaImpuesto * 100).toFixed(0)}%)`} valor={impuestoRenta} nivel={2} negativo />
          <LineaItem titulo="Total Impuestos" valor={impuestoRenta} nivel={1} />
        </div>
      )}

      {/* UTILIDAD NETA */}
      <div className="mb-4 border-2 border-green-500 rounded-lg bg-green-50">
        <div className="flex justify-between items-center p-4">
          <span className="text-xl font-bold text-green-900">UTILIDAD NETA</span>
          <div className="text-right">
            <div className="text-xl font-bold text-green-900">{formatCurrency(utilidadNeta)}</div>
            <div className="text-sm text-green-700">Margen: {margenNeto.toFixed(2)}%</div>
          </div>
        </div>
      </div>
    </div>
  );
}
