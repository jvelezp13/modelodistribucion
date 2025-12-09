'use client';

import { useState, useEffect, useMemo, Suspense } from 'react';
import { apiClient, Escenario, Operacion, MarcaBasica } from '@/lib/api';
import { LoadingOverlay } from '@/components/ui/LoadingSpinner';
import { RefreshCw, AlertCircle } from 'lucide-react';
import Sidebar from '@/components/Sidebar';
import MonthSelector from '@/components/MonthSelector';
import PyGDetallado from '@/components/PyGDetallado';
import PyGZonas from '@/components/PyGZonas';
import LejaniasComercial from '@/components/LejaniasComercial';
import LejaniasLogistica from '@/components/LejaniasLogistica';
import DistribucionVentas from '@/components/DistribucionVentas';
import { useFilters, ViewType } from '@/hooks/useFilters';

// Componente interno que usa useFilters (requiere Suspense)
function DashboardContent() {
  const { filters, setEscenario, setMarca, setVista, updateFilters } = useFilters();

  // Datos base cargados desde API
  const [escenarios, setEscenarios] = useState<Escenario[]>([]);
  const [operacionesList, setOperacionesList] = useState<Operacion[]>([]);
  const [marcas, setMarcas] = useState<MarcaBasica[]>([]);

  // UI State
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  // Dropdowns abiertos
  const [operacionDropdownOpen, setOperacionDropdownOpen] = useState(false);
  const [marcaDropdownOpen, setMarcaDropdownOpen] = useState(false);

  // Cargar datos iniciales
  useEffect(() => {
    cargarDatosIniciales();
  }, []);

  // Cargar operaciones cuando cambia el escenario
  useEffect(() => {
    if (filters.escenarioId) {
      cargarOperaciones(filters.escenarioId);
    }
  }, [filters.escenarioId]);

  // Cargar marcas cuando cambian las operaciones
  useEffect(() => {
    if (filters.escenarioId && operacionesList.length > 0) {
      // Si hay operaciones en URL, usarlas; si no, usar todas las disponibles
      const idsToUse = filters.operacionIds.length > 0
        ? filters.operacionIds
        : operacionesList.map(o => o.id);
      cargarMarcas(filters.escenarioId, idsToUse);
    }
  }, [filters.escenarioId, filters.operacionIds, operacionesList]);

  const cargarDatosIniciales = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const listaEscenarios = await apiClient.listarEscenarios();
      setEscenarios(listaEscenarios);

      // Si no hay escenario en URL, establecer el primero activo
      if (listaEscenarios.length > 0 && !filters.escenarioId) {
        const activo = listaEscenarios.find(e => e.activo) || listaEscenarios[0];
        setEscenario(activo.id);
      }
    } catch (err) {
      setError('Error al cargar escenarios');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const cargarOperaciones = async (escenarioId: number) => {
    try {
      const response = await apiClient.obtenerOperaciones(escenarioId);
      setOperacionesList(response.operaciones);

      // Si no hay operaciones en URL, seleccionar todas por defecto
      if (filters.operacionIds.length === 0 && response.operaciones.length > 0) {
        setOperaciones_URL(response.operaciones.map(o => o.id));
      }
    } catch (err) {
      console.error('Error cargando operaciones:', err);
      setOperacionesList([]);
    }
  };

  const setOperaciones_URL = (ids: number[]) => {
    updateFilters({ operacionIds: ids });
  };

  const cargarMarcas = async (escenarioId: number, operacionIds: number[]) => {
    try {
      const response = await apiClient.obtenerMarcasPorOperaciones(
        escenarioId,
        operacionIds.length > 0 ? operacionIds : undefined
      );
      setMarcas(response.marcas);

      // Si no hay marca en URL, seleccionar la primera
      if (!filters.marcaId && response.marcas.length > 0) {
        setMarca(response.marcas[0].marca_id);
      }
    } catch (err) {
      console.error('Error cargando marcas:', err);
      setMarcas([]);
    }
  };

  const recargarDatos = async () => {
    setRefreshKey(prev => prev + 1);
    if (filters.escenarioId) {
      await cargarOperaciones(filters.escenarioId);
    }
  };

  // Toggle operación
  const toggleOperacion = (operacionId: number) => {
    const currentIds = filters.operacionIds.length > 0
      ? filters.operacionIds
      : operacionesList.map(o => o.id);

    const newIds = currentIds.includes(operacionId)
      ? currentIds.filter(id => id !== operacionId)
      : [...currentIds, operacionId];

    updateFilters({ operacionIds: newIds });
  };

  // Toggle todas las operaciones
  const toggleAllOperaciones = () => {
    const allIds = operacionesList.map(o => o.id);
    const currentIds = filters.operacionIds.length > 0
      ? filters.operacionIds
      : allIds;

    if (currentIds.length === allIds.length) {
      updateFilters({ operacionIds: [] });
    } else {
      updateFilters({ operacionIds: allIds });
    }
  };

  // IDs de operaciones efectivos (para UI)
  const selectedOperacionIds = filters.operacionIds.length > 0
    ? filters.operacionIds
    : operacionesList.map(o => o.id);

  // Labels para dropdowns
  const operacionesLabel = useMemo(() => {
    if (selectedOperacionIds.length === 0) return 'Ninguna';
    if (selectedOperacionIds.length === operacionesList.length) return 'Todas';
    if (selectedOperacionIds.length === 1) {
      const op = operacionesList.find(o => o.id === selectedOperacionIds[0]);
      return op?.nombre || '1 seleccionada';
    }
    return `${selectedOperacionIds.length} seleccionadas`;
  }, [selectedOperacionIds, operacionesList]);

  const marcasLabel = useMemo(() => {
    if (!filters.marcaId) return 'Ninguna';
    const marca = marcas.find(m => m.marca_id === filters.marcaId);
    return marca?.nombre || filters.marcaId;
  }, [filters.marcaId, marcas]);

  // Verificar si hay datos para mostrar
  const tieneSeleccion = filters.escenarioId && filters.marcaId;

  const escenarioActual = escenarios.find(e => e.id === filters.escenarioId);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <LoadingOverlay message="Cargando sistema..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar
        isCollapsed={isSidebarCollapsed}
        onToggle={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        activeView={filters.vista}
        onViewChange={(view) => setVista(view as ViewType)}
      />

      {/* Main Content */}
      <div
        className={`transition-all duration-300 ${isSidebarCollapsed ? 'ml-16' : 'ml-56'}`}
      >
        {/* Header con filtros */}
        <header className="bg-white border-b border-gray-200 px-4 py-3">
          <div className="flex items-center justify-between gap-4">
            {/* Título */}
            <div className="flex items-center gap-3">
              <h1 className="text-sm font-semibold text-gray-800">
                Sistema DxV
              </h1>
              {escenarioActual && (
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                  {escenarioActual.nombre} ({escenarioActual.anio})
                </span>
              )}
            </div>

            {/* Filtros */}
            <div className="flex items-center gap-3">
              {/* Escenario */}
              <div className="flex items-center gap-2">
                <label className="text-xs text-gray-500">Escenario:</label>
                <select
                  value={filters.escenarioId || ''}
                  onChange={(e) => setEscenario(Number(e.target.value))}
                  className="text-xs px-2 py-1.5 border border-gray-300 rounded bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {escenarios.map((esc) => (
                    <option key={esc.id} value={esc.id}>
                      {esc.nombre} - {esc.anio} {esc.activo && '(Activo)'}
                    </option>
                  ))}
                </select>
              </div>

              {/* Operaciones (multi-select dropdown) */}
              <div className="relative">
                <label className="text-xs text-gray-500 mr-2">Operaciones:</label>
                <button
                  onClick={() => {
                    setOperacionDropdownOpen(!operacionDropdownOpen);
                    setMarcaDropdownOpen(false);
                  }}
                  className="text-xs px-3 py-1.5 border border-gray-300 rounded bg-white text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-1 focus:ring-blue-500 min-w-[120px] text-left"
                >
                  {operacionesLabel}
                  <span className="float-right ml-2">▼</span>
                </button>
                {operacionDropdownOpen && (
                  <div className="absolute z-50 mt-1 w-56 bg-white border border-gray-200 rounded-lg shadow-lg">
                    <div className="p-2 border-b border-gray-100">
                      <button
                        onClick={toggleAllOperaciones}
                        className="text-xs text-blue-600 hover:text-blue-800"
                      >
                        {selectedOperacionIds.length === operacionesList.length ? 'Deseleccionar todas' : 'Seleccionar todas'}
                      </button>
                    </div>
                    <div className="max-h-48 overflow-y-auto">
                      {operacionesList.map((op) => (
                        <label
                          key={op.id}
                          className="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={selectedOperacionIds.includes(op.id)}
                            onChange={() => toggleOperacion(op.id)}
                            className="rounded text-blue-600 focus:ring-blue-500"
                          />
                          <span className="text-xs text-gray-700">{op.nombre}</span>
                          <span
                            className="w-3 h-3 rounded-full ml-auto"
                            style={{ backgroundColor: op.color }}
                          />
                        </label>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Marcas (single select) */}
              <div className="flex items-center gap-2">
                <label className="text-xs text-gray-500">Marca:</label>
                <select
                  value={filters.marcaId || ''}
                  onChange={(e) => setMarca(e.target.value || null)}
                  className="text-xs px-2 py-1.5 border border-gray-300 rounded bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500 min-w-[120px]"
                >
                  <option value="">Seleccionar...</option>
                  {marcas.map((marca) => (
                    <option key={marca.marca_id} value={marca.marca_id}>
                      {marca.nombre}
                    </option>
                  ))}
                </select>
              </div>

              {/* Mes */}
              <MonthSelector showLabel={true} size="sm" />

              {/* Recargar */}
              <button
                onClick={recargarDatos}
                className="flex items-center gap-1 px-2 py-1.5 text-xs text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-colors"
                title="Recargar datos"
              >
                <RefreshCw size={14} />
              </button>
            </div>
          </div>

          {error && (
            <div className="mt-2 flex items-center gap-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
              <AlertCircle size={14} />
              {error}
            </div>
          )}
        </header>

        {/* Click outside to close dropdowns */}
        {(operacionDropdownOpen || marcaDropdownOpen) && (
          <div
            className="fixed inset-0 z-40"
            onClick={() => {
              setOperacionDropdownOpen(false);
              setMarcaDropdownOpen(false);
            }}
          />
        )}

        {/* Main Content Area */}
        <div className="p-4">
          {!tieneSeleccion ? (
            <div className="bg-white border border-gray-200 rounded p-12 text-center">
              <p className="text-sm text-gray-600">
                Selecciona un escenario y una marca para ver los resultados
              </p>
            </div>
          ) : (
            <>
              {/* Vista Distribucion de Ventas */}
              {filters.vista === 'distribucion' && (
                <DistribucionVentas
                  key={`distribucion-${filters.marcaId}-${refreshKey}`}
                />
              )}

              {/* Vista P&G Detallado */}
              {filters.vista === 'pyg' && (
                <PyGDetallado
                  key={`pyg-${filters.marcaId}-${refreshKey}`}
                />
              )}

              {/* Vista P&G por Zonas */}
              {filters.vista === 'pyg-zonas' && (
                <PyGZonas
                  key={`pyg-zonas-${filters.marcaId}-${refreshKey}`}
                />
              )}

              {/* Vista Lejanías Comerciales */}
              {filters.vista === 'lejanias-comercial' && (
                <LejaniasComercial
                  key={`lejanias-comercial-${filters.marcaId}-${refreshKey}`}
                />
              )}

              {/* Vista Lejanías Logísticas */}
              {filters.vista === 'lejanias-logistica' && (
                <LejaniasLogistica
                  key={`lejanias-logistica-${filters.marcaId}-${refreshKey}`}
                />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// Página principal con Suspense para useSearchParams
export default function DashboardPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <LoadingOverlay message="Cargando sistema..." />
      </div>
    }>
      <DashboardContent />
    </Suspense>
  );
}
