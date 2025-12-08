'use client';

import { useState, useEffect, useMemo } from 'react';
import { apiClient, Escenario, Operacion, MarcaBasica } from '@/lib/api';
import { LoadingOverlay } from '@/components/ui/LoadingSpinner';
import { RefreshCw, AlertCircle, Check } from 'lucide-react';
import Sidebar from '@/components/Sidebar';
import PyGDetallado from '@/components/PyGDetallado';
import PyGZonas from '@/components/PyGZonas';
import LejaniasComercial from '@/components/LejaniasComercial';
import LejaniasLogistica from '@/components/LejaniasLogistica';

type ViewType = 'pyg' | 'pyg-zonas' | 'lejanias-comercial' | 'lejanias-logistica';

export default function DashboardPage() {
  // Datos base
  const [escenarios, setEscenarios] = useState<Escenario[]>([]);
  const [operaciones, setOperaciones] = useState<Operacion[]>([]);
  const [marcas, setMarcas] = useState<MarcaBasica[]>([]);

  // Filtros seleccionados
  const [selectedScenarioId, setSelectedScenarioId] = useState<number | null>(null);
  const [selectedOperacionIds, setSelectedOperacionIds] = useState<number[]>([]);
  const [selectedMarcaIds, setSelectedMarcaIds] = useState<string[]>([]);

  // UI State
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<ViewType>('pyg');
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
    if (selectedScenarioId) {
      cargarOperaciones(selectedScenarioId);
    }
  }, [selectedScenarioId]);

  // Cargar marcas cuando cambian las operaciones seleccionadas
  useEffect(() => {
    if (selectedScenarioId) {
      cargarMarcas(selectedScenarioId, selectedOperacionIds);
    }
  }, [selectedScenarioId, selectedOperacionIds]);

  const cargarDatosIniciales = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const listaEscenarios = await apiClient.listarEscenarios();
      setEscenarios(listaEscenarios);

      if (listaEscenarios.length > 0) {
        const activo = listaEscenarios.find(e => e.activo) || listaEscenarios[0];
        setSelectedScenarioId(activo.id);
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
      setOperaciones(response.operaciones);
      // Seleccionar todas las operaciones por defecto
      setSelectedOperacionIds(response.operaciones.map(o => o.id));
    } catch (err) {
      console.error('Error cargando operaciones:', err);
      setOperaciones([]);
      setSelectedOperacionIds([]);
    }
  };

  const cargarMarcas = async (escenarioId: number, operacionIds: number[]) => {
    try {
      const response = await apiClient.obtenerMarcasPorOperaciones(
        escenarioId,
        operacionIds.length > 0 ? operacionIds : undefined
      );
      setMarcas(response.marcas);
      // Seleccionar todas las marcas por defecto
      setSelectedMarcaIds(response.marcas.map(m => m.marca_id));
    } catch (err) {
      console.error('Error cargando marcas:', err);
      setMarcas([]);
      setSelectedMarcaIds([]);
    }
  };

  const recargarDatos = async () => {
    setRefreshKey(prev => prev + 1);
    if (selectedScenarioId) {
      await cargarOperaciones(selectedScenarioId);
    }
  };

  // Toggle operación
  const toggleOperacion = (operacionId: number) => {
    setSelectedOperacionIds(prev => {
      if (prev.includes(operacionId)) {
        return prev.filter(id => id !== operacionId);
      } else {
        return [...prev, operacionId];
      }
    });
  };

  // Toggle todas las operaciones
  const toggleAllOperaciones = () => {
    if (selectedOperacionIds.length === operaciones.length) {
      setSelectedOperacionIds([]);
    } else {
      setSelectedOperacionIds(operaciones.map(o => o.id));
    }
  };

  // Toggle marca
  const toggleMarca = (marcaId: string) => {
    setSelectedMarcaIds(prev => {
      if (prev.includes(marcaId)) {
        return prev.filter(id => id !== marcaId);
      } else {
        return [...prev, marcaId];
      }
    });
  };

  // Toggle todas las marcas
  const toggleAllMarcas = () => {
    if (selectedMarcaIds.length === marcas.length) {
      setSelectedMarcaIds([]);
    } else {
      setSelectedMarcaIds(marcas.map(m => m.marca_id));
    }
  };

  // Labels para dropdowns
  const operacionesLabel = useMemo(() => {
    if (selectedOperacionIds.length === 0) return 'Ninguna';
    if (selectedOperacionIds.length === operaciones.length) return 'Todas';
    if (selectedOperacionIds.length === 1) {
      const op = operaciones.find(o => o.id === selectedOperacionIds[0]);
      return op?.nombre || '1 seleccionada';
    }
    return `${selectedOperacionIds.length} seleccionadas`;
  }, [selectedOperacionIds, operaciones]);

  const marcasLabel = useMemo(() => {
    if (selectedMarcaIds.length === 0) return 'Ninguna';
    if (selectedMarcaIds.length === marcas.length) return 'Todas';
    if (selectedMarcaIds.length === 1) {
      const marca = marcas.find(m => m.marca_id === selectedMarcaIds[0]);
      return marca?.nombre || '1 seleccionada';
    }
    return `${selectedMarcaIds.length} seleccionadas`;
  }, [selectedMarcaIds, marcas]);

  // Verificar si hay datos para mostrar
  const tieneSeleccion = selectedScenarioId && selectedMarcaIds.length > 0;

  // Primera marca seleccionada (para vistas que necesitan una sola)
  const primeraMarcaId = selectedMarcaIds[0] || null;

  const escenarioActual = escenarios.find(e => e.id === selectedScenarioId);

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
        activeView={activeView}
        onViewChange={(view) => setActiveView(view as ViewType)}
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
                  value={selectedScenarioId || ''}
                  onChange={(e) => setSelectedScenarioId(Number(e.target.value))}
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
                        {selectedOperacionIds.length === operaciones.length ? 'Deseleccionar todas' : 'Seleccionar todas'}
                      </button>
                    </div>
                    <div className="max-h-48 overflow-y-auto">
                      {operaciones.map((op) => (
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

              {/* Marcas (multi-select dropdown) */}
              <div className="relative">
                <label className="text-xs text-gray-500 mr-2">Marcas:</label>
                <button
                  onClick={() => {
                    setMarcaDropdownOpen(!marcaDropdownOpen);
                    setOperacionDropdownOpen(false);
                  }}
                  className="text-xs px-3 py-1.5 border border-gray-300 rounded bg-white text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-1 focus:ring-blue-500 min-w-[120px] text-left"
                >
                  {marcasLabel}
                  <span className="float-right ml-2">▼</span>
                </button>
                {marcaDropdownOpen && (
                  <div className="absolute z-50 mt-1 w-56 bg-white border border-gray-200 rounded-lg shadow-lg">
                    <div className="p-2 border-b border-gray-100">
                      <button
                        onClick={toggleAllMarcas}
                        className="text-xs text-blue-600 hover:text-blue-800"
                      >
                        {selectedMarcaIds.length === marcas.length ? 'Deseleccionar todas' : 'Seleccionar todas'}
                      </button>
                    </div>
                    <div className="max-h-48 overflow-y-auto">
                      {marcas.map((marca) => (
                        <label
                          key={marca.marca_id}
                          className="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={selectedMarcaIds.includes(marca.marca_id)}
                            onChange={() => toggleMarca(marca.marca_id)}
                            className="rounded text-blue-600 focus:ring-blue-500"
                          />
                          <span className="text-xs text-gray-700">{marca.nombre}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}
              </div>

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
                Selecciona al menos una marca para ver los resultados
              </p>
            </div>
          ) : (
            <>
              {/* Indicador de selección actual */}
              {selectedMarcaIds.length > 1 && (
                <div className="mb-3 bg-blue-50 border border-blue-200 rounded p-2">
                  <p className="text-xs text-blue-700">
                    <strong>Nota:</strong> Tienes {selectedMarcaIds.length} marcas seleccionadas.
                    Las vistas muestran datos de la primera marca ({marcas.find(m => m.marca_id === primeraMarcaId)?.nombre}).
                    Selecciona una sola marca para ver sus datos específicos.
                  </p>
                </div>
              )}

              {/* Vista P&G Detallado */}
              {activeView === 'pyg' && primeraMarcaId && (
                <PyGDetallado
                  key={`pyg-${primeraMarcaId}-${refreshKey}`}
                  escenarioId={selectedScenarioId!}
                  marcaId={primeraMarcaId}
                  operacionIds={selectedOperacionIds}
                />
              )}

              {/* Vista P&G por Zonas */}
              {activeView === 'pyg-zonas' && primeraMarcaId && (
                <PyGZonas
                  key={`pyg-zonas-${primeraMarcaId}-${refreshKey}`}
                  escenarioId={selectedScenarioId!}
                  marcaId={primeraMarcaId}
                />
              )}

              {/* Vista Lejanías Comerciales */}
              {activeView === 'lejanias-comercial' && primeraMarcaId && (
                <LejaniasComercial
                  key={`lejanias-comercial-${primeraMarcaId}-${refreshKey}`}
                  escenarioId={selectedScenarioId!}
                  marcaId={primeraMarcaId}
                />
              )}

              {/* Vista Lejanías Logísticas */}
              {activeView === 'lejanias-logistica' && primeraMarcaId && (
                <LejaniasLogistica
                  key={`lejanias-logistica-${primeraMarcaId}-${refreshKey}`}
                  escenarioId={selectedScenarioId!}
                  marcaId={primeraMarcaId}
                />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
