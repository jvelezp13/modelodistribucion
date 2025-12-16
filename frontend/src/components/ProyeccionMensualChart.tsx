'use client';

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';
import {
  VentasMensualesDesglose,
  ProyeccionInfo,
  TipologiaProyeccionDetalle
} from '@/lib/api';

// Orden de meses
const MESES_ORDEN = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
];

const MESES_CORTOS: Record<string, string> = {
  enero: 'Ene',
  febrero: 'Feb',
  marzo: 'Mar',
  abril: 'Abr',
  mayo: 'May',
  junio: 'Jun',
  julio: 'Jul',
  agosto: 'Ago',
  septiembre: 'Sep',
  octubre: 'Oct',
  noviembre: 'Nov',
  diciembre: 'Dic'
};

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
};

const formatCurrencyShort = (value: number): string => {
  // Formato colombiano: M = millones, MM = miles de millones
  if (value >= 1000000000) {
    return `$${(value / 1000000).toLocaleString('es-CO', { maximumFractionDigits: 0 })}M`;
  }
  if (value >= 1000000) {
    return `$${(value / 1000000).toLocaleString('es-CO', { maximumFractionDigits: 0 })}M`;
  }
  if (value >= 1000) {
    return `$${(value / 1000).toLocaleString('es-CO', { maximumFractionDigits: 0 })}K`;
  }
  return formatCurrency(value);
};

interface ProyeccionMensualChartProps {
  ventasMensuales: VentasMensualesDesglose;
  ventaAnual: number;
  proyeccion: ProyeccionInfo;
  anio: number;
}

interface ChartDataItem {
  mes: string;
  mesCorto: string;
  venta: number;
}

export default function ProyeccionMensualChart({
  ventasMensuales,
  ventaAnual,
  proyeccion,
  anio
}: ProyeccionMensualChartProps) {
  // Preparar datos para el gráfico
  const chartData: ChartDataItem[] = MESES_ORDEN.map((mes) => ({
    mes: mes.charAt(0).toUpperCase() + mes.slice(1),
    mesCorto: MESES_CORTOS[mes],
    venta: ventasMensuales[mes as keyof VentasMensualesDesglose] || 0
  }));

  // Color según fuente
  const barColor = proyeccion.fuente === 'manual' ? '#1976D2' : '#10B981';
  const badgeClass = proyeccion.fuente === 'manual'
    ? 'bg-blue-100 text-blue-700'
    : 'bg-green-100 text-green-700';
  const fuenteLabel = proyeccion.fuente === 'manual'
    ? 'Manual'
    : `Tipologías (${proyeccion.tipologias.length})`;

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white shadow-lg border rounded px-3 py-2 text-sm">
          <p className="font-medium text-gray-800">{data.mes}</p>
          <p className="text-gray-600">{formatCurrency(data.venta)}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h3 className="font-semibold text-gray-800">
            Proyección Mensual {anio}
          </h3>
          {proyeccion.fuente && (
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${badgeClass}`}>
              {fuenteLabel}
            </span>
          )}
        </div>
        <div className="text-right">
          <div className="text-xs text-gray-500">Total Anual</div>
          <div className="text-lg font-bold text-gray-800">
            {formatCurrency(ventaAnual)}
          </div>
        </div>
      </div>

      {/* Gráfico de barras */}
      <div className="h-48 mb-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
            <XAxis
              dataKey="mesCorto"
              tick={{ fontSize: 11, fill: '#6B7280' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tickFormatter={formatCurrencyShort}
              tick={{ fontSize: 10, fill: '#9CA3AF' }}
              axisLine={false}
              tickLine={false}
              width={50}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="venta" radius={[4, 4, 0, 0]}>
              {chartData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={barColor} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Tabla de valores mensuales */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b">
              {MESES_ORDEN.map((mes) => (
                <th key={mes} className="px-1 py-1 text-gray-500 font-medium text-center">
                  {MESES_CORTOS[mes]}
                </th>
              ))}
              <th className="px-1 py-1 text-gray-700 font-semibold text-center bg-gray-50">
                Total
              </th>
            </tr>
          </thead>
          <tbody>
            <tr>
              {MESES_ORDEN.map((mes) => (
                <td key={mes} className="px-1 py-1 text-gray-700 text-center">
                  {formatCurrencyShort(ventasMensuales[mes as keyof VentasMensualesDesglose] || 0)}
                </td>
              ))}
              <td className="px-1 py-1 font-semibold text-gray-800 text-center bg-gray-50">
                {formatCurrencyShort(ventaAnual)}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Tabla de composición por tipología (solo si fuente es tipologías) */}
      {proyeccion.fuente === 'tipologias' && proyeccion.tipologias.length > 0 && (
        <div className="mt-4 pt-4 border-t">
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            Composición por Tipología
          </h4>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="px-2 py-1.5 text-left text-gray-600 font-medium">Tipología</th>
                  <th className="px-2 py-1.5 text-right text-gray-600 font-medium">Clientes</th>
                  <th className="px-2 py-1.5 text-right text-gray-600 font-medium">Ticket</th>
                  <th className="px-2 py-1.5 text-right text-gray-600 font-medium">Crec.</th>
                  <th className="px-2 py-1.5 text-right text-gray-600 font-medium">Venta Anual</th>
                </tr>
              </thead>
              <tbody>
                {proyeccion.tipologias.map((tip, idx) => (
                  <TipologiaRow key={idx} tipologia={tip} />
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t bg-gray-50">
                  <td className="px-2 py-1.5 font-medium text-gray-700">Total</td>
                  <td className="px-2 py-1.5 text-right font-medium text-gray-700">
                    {proyeccion.tipologias.reduce((sum, t) => sum + t.clientes, 0).toLocaleString('es-CO')}
                  </td>
                  <td className="px-2 py-1.5 text-right">-</td>
                  <td className="px-2 py-1.5 text-right">-</td>
                  <td className="px-2 py-1.5 text-right font-semibold text-gray-800">
                    {formatCurrency(proyeccion.tipologias.reduce((sum, t) => sum + t.venta_anual, 0))}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

interface TipologiaRowProps {
  tipologia: TipologiaProyeccionDetalle;
}

const TipologiaRow: React.FC<TipologiaRowProps> = ({ tipologia }) => {
  // Mostrar crecimiento combinado (clientes / ticket)
  const crecDisplay = `${(tipologia.crec_clientes * 100).toFixed(0)}%/${(tipologia.crec_ticket * 100).toFixed(0)}%`;

  return (
    <tr className="border-b hover:bg-gray-50">
      <td className="px-2 py-1.5 text-gray-700">{tipologia.nombre}</td>
      <td className="px-2 py-1.5 text-right text-gray-600">
        {tipologia.clientes.toLocaleString('es-CO')}
      </td>
      <td className="px-2 py-1.5 text-right text-gray-600">
        {formatCurrency(tipologia.ticket)}
      </td>
      <td className="px-2 py-1.5 text-right text-gray-500">
        {crecDisplay}
      </td>
      <td className="px-2 py-1.5 text-right text-gray-700">
        {formatCurrency(tipologia.venta_anual)}
      </td>
    </tr>
  );
};
