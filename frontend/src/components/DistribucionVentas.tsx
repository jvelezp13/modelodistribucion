'use client';

import React, { useState, useEffect, useMemo } from 'react';
import {
  ChevronDown,
  ChevronRight,
  CheckCircle,
  AlertCircle,
  Building2,
  MapPin,
  Map
} from 'lucide-react';
import {
  apiClient,
  DistribucionCascadaResponse,
  OperacionDistribucion,
  ZonaDistribucion,
  VentasMensualesDesglose
} from '@/lib/api';
import { useFilters } from '@/hooks/useFilters';
import ProyeccionMensualChart from './ProyeccionMensualChart';

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
};

const formatPercent = (value: number): string => {
  return `${value.toFixed(2)}%`;
};

interface ValidationBadgeProps {
  suma: number;
  esValido: boolean;
}

const ValidationBadge: React.FC<ValidationBadgeProps> = ({ suma, esValido }) => {
  if (esValido) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs">
        <CheckCircle size={12} />
        {formatPercent(suma)}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs">
      <AlertCircle size={12} />
      {formatPercent(suma)}
    </span>
  );
};

interface ProgressBarProps {
  value: number;
  color?: string;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ value, color = 'bg-blue-500' }) => {
  const width = Math.min(Math.max(value, 0), 100);
  return (
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div
        className={`h-2 rounded-full ${color}`}
        style={{ width: `${width}%` }}
      />
    </div>
  );
};

export default function DistribucionVentas() {
  const { filters } = useFilters();
  const { escenarioId, marcaId, operacionIds, mes: mesSeleccionado } = filters;

  const [data, setData] = useState<DistribucionCascadaResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedOperaciones, setExpandedOperaciones] = useState<Set<number>>(new Set());
  const [expandedZonas, setExpandedZonas] = useState<Set<number>>(new Set());

  useEffect(() => {
    const fetchData = async () => {
      if (!escenarioId || !marcaId) {
        setData(null);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        // Pasar operacionIds solo si hay alguna seleccionada (vacío = todas)
        const opsParam = operacionIds.length > 0 ? operacionIds : undefined;
        const response = await apiClient.obtenerDistribucionCascada(escenarioId, marcaId, opsParam);
        setData(response);
        // Expandir todas las operaciones por defecto
        setExpandedOperaciones(new Set(response.operaciones.map(op => op.id)));
      } catch (err) {
        console.error('Error fetching distribucion cascada:', err);
        setError(err instanceof Error ? err.message : 'Error desconocido');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [escenarioId, marcaId, operacionIds]);

  // Calcular ventas del mes seleccionado
  const ventasMes = useMemo(() => {
    if (!data?.marca.ventas_mensuales) {
      return data?.marca.venta_total_mensual || 0;
    }
    const ventas = data.marca.ventas_mensuales as VentasMensualesDesglose;
    return ventas[mesSeleccionado as keyof VentasMensualesDesglose] || data.marca.venta_total_mensual || 0;
  }, [data, mesSeleccionado]);

  // Factor de ajuste para recalcular ventas proyectadas según el mes
  const factorAjuste = useMemo(() => {
    if (!data?.marca.venta_total_mensual || data.marca.venta_total_mensual === 0) return 1;
    return ventasMes / data.marca.venta_total_mensual;
  }, [ventasMes, data?.marca.venta_total_mensual]);

  const toggleOperacion = (id: number) => {
    setExpandedOperaciones(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const toggleZona = (id: number) => {
    setExpandedZonas(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  if (!escenarioId || !marcaId) {
    return (
      <div className="p-6 text-center text-gray-500">
        Selecciona un escenario y una marca para ver la distribucion de ventas.
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-6 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-500 border-t-transparent" />
        <p className="mt-2 text-gray-500">Cargando distribucion...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-center text-red-600">
        <AlertCircle className="mx-auto mb-2" size={32} />
        <p>Error: {error}</p>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div className="p-4 max-w-5xl mx-auto">
      {/* Header con info de marca */}
      <div className="bg-white rounded-lg shadow-sm border p-4 mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-800">
              {data.marca.nombre}
            </h2>
            <p className="text-sm text-gray-500">
              {data.escenario.nombre} ({data.escenario.anio})
            </p>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-500">
              Ventas {mesSeleccionado.charAt(0).toUpperCase() + mesSeleccionado.slice(1)}
            </div>
            <div className="text-2xl font-bold text-blue-600">
              {formatCurrency(ventasMes)}
            </div>
          </div>
        </div>

        {/* Validacion global de operaciones */}
        <div className="mt-4 pt-4 border-t flex items-center justify-between">
          <span className="text-sm text-gray-600">
            Suma de participaciones por operacion:
          </span>
          <ValidationBadge
            suma={data.validacion.suma_participaciones_operaciones}
            esValido={data.validacion.operaciones_valido}
          />
        </div>
      </div>

      {/* Gráfico y tabla de proyección mensual */}
      {data.proyeccion && data.marca.ventas_mensuales && (
        <div className="mb-4">
          <ProyeccionMensualChart
            ventasMensuales={data.marca.ventas_mensuales}
            ventaAnual={data.marca.venta_anual || 0}
            proyeccion={data.proyeccion}
            anio={data.escenario.anio}
          />
        </div>
      )}

      {/* Lista de operaciones */}
      <div className="space-y-3">
        {data.operaciones.map((operacion) => (
          <OperacionCard
            key={operacion.id}
            operacion={operacion}
            isExpanded={expandedOperaciones.has(operacion.id)}
            onToggle={() => toggleOperacion(operacion.id)}
            expandedZonas={expandedZonas}
            onToggleZona={toggleZona}
          />
        ))}
      </div>

      {data.operaciones.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No hay operaciones configuradas para esta marca.
        </div>
      )}
    </div>
  );
}

interface OperacionCardProps {
  operacion: OperacionDistribucion;
  isExpanded: boolean;
  onToggle: () => void;
  expandedZonas: Set<number>;
  onToggleZona: (id: number) => void;
}

const OperacionCard: React.FC<OperacionCardProps> = ({
  operacion,
  isExpanded,
  onToggle,
  expandedZonas,
  onToggleZona
}) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
      {/* Header de operacion */}
      <div
        className="flex items-center p-3 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={onToggle}
      >
        <button className="mr-2 text-gray-400">
          {isExpanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
        </button>
        <Building2 size={18} className="text-purple-500 mr-2" />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium text-gray-800">{operacion.nombre}</span>
            <span className="text-xs bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded">
              {operacion.codigo}
            </span>
          </div>
          <div className="text-xs text-gray-500">
            {operacion.zonas_count} zonas
          </div>
        </div>
        <div className="text-right mr-4">
          <div className="text-sm font-medium text-gray-800">
            {formatPercent(operacion.participacion_ventas)}
          </div>
          <div className="text-xs text-gray-500">
            {formatCurrency(operacion.venta_proyectada)}
          </div>
        </div>
        <div className="w-24">
          <ProgressBar value={operacion.participacion_ventas} color="bg-purple-500" />
        </div>
      </div>

      {/* Zonas expandidas */}
      {isExpanded && (
        <div className="border-t bg-gray-50 p-3">
          {/* Validacion de zonas */}
          <div className="flex items-center justify-between mb-3 text-sm">
            <span className="text-gray-600">Suma participaciones zonas:</span>
            <ValidationBadge
              suma={operacion.validacion.suma_participaciones}
              esValido={operacion.validacion.es_valido}
            />
          </div>

          {/* Lista de zonas */}
          <div className="space-y-2">
            {operacion.zonas.map((zona) => (
              <ZonaRow
                key={zona.id}
                zona={zona}
                isExpanded={expandedZonas.has(zona.id)}
                onToggle={() => onToggleZona(zona.id)}
              />
            ))}
          </div>

          {operacion.zonas.length === 0 && (
            <div className="text-center py-4 text-gray-400 text-sm">
              Sin zonas asignadas
            </div>
          )}
        </div>
      )}
    </div>
  );
};

interface ZonaRowProps {
  zona: ZonaDistribucion;
  isExpanded: boolean;
  onToggle: () => void;
}

const ZonaRow: React.FC<ZonaRowProps> = ({ zona, isExpanded, onToggle }) => {
  return (
    <div className="bg-white rounded border">
      {/* Header de zona */}
      <div
        className="flex items-center p-2 cursor-pointer hover:bg-blue-50 transition-colors"
        onClick={onToggle}
      >
        <button className="mr-2 text-gray-400">
          {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </button>
        <Map size={16} className="text-blue-500 mr-2" />
        <div className="flex-1">
          <span className="text-sm font-medium text-gray-700">{zona.nombre}</span>
          <span className="ml-2 text-xs text-gray-400">
            ({zona.municipios_count} municipios)
          </span>
        </div>
        <div className="text-right mr-3">
          <div className="text-sm font-medium text-gray-700">
            {formatPercent(zona.participacion_ventas)}
          </div>
          <div className="text-xs text-gray-500">
            {formatCurrency(zona.venta_proyectada)}
          </div>
        </div>
        <div className="w-20">
          <ProgressBar value={zona.participacion_ventas} color="bg-blue-500" />
        </div>
      </div>

      {/* Municipios expandidos */}
      {isExpanded && zona.municipios.length > 0 && (
        <div className="border-t bg-gray-50 p-2">
          {/* Validacion de municipios */}
          <div className="flex items-center justify-between mb-2 text-xs">
            <span className="text-gray-500">Suma participaciones:</span>
            <ValidationBadge
              suma={zona.validacion.suma_participaciones}
              esValido={zona.validacion.es_valido}
            />
          </div>

          {/* Lista de municipios */}
          <div className="space-y-1">
            {zona.municipios.map((municipio) => (
              <div
                key={municipio.id}
                className="flex items-center p-1.5 bg-white rounded text-xs"
              >
                <MapPin size={12} className="text-green-500 mr-2" />
                <div className="flex-1">
                  <span className="text-gray-700">{municipio.nombre}</span>
                  <span className="ml-1 text-gray-400">({municipio.departamento})</span>
                </div>
                <div className="text-right mr-2">
                  <span className="text-gray-600">
                    {formatPercent(municipio.participacion_ventas)}
                  </span>
                </div>
                <div className="text-right text-gray-500">
                  {formatCurrency(municipio.venta_proyectada)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
