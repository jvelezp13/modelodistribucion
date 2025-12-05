'use client';

import { useState, useEffect } from 'react';
import { apiClient, SimulacionResult, Escenario } from '@/lib/api';
// formatearMoneda y formatearPorcentaje se usan en PyGDetallado
import { LoadingOverlay } from '@/components/ui/LoadingSpinner';
import { RefreshCw, Play, AlertCircle } from 'lucide-react';
import Sidebar from '@/components/Sidebar';
import PyGDetallado from '@/components/PyGDetallado';
import PyGZonas from '@/components/PyGZonas';
import PyGMunicipios from '@/components/PyGMunicipios';
import LejaniasComercial from '@/components/LejaniasComercial';
import LejaniasLogistica from '@/components/LejaniasLogistica';

type ViewType = 'pyg' | 'pyg-zonas' | 'pyg-municipios' | 'lejanias-comercial' | 'lejanias-logistica';

export default function DashboardPage() {
  const [marcasDisponibles, setMarcasDisponibles] = useState<string[]>([]);
  const [marcasSeleccionadas, setMarcasSeleccionadas] = useState<string[]>([]);
  const [escenarios, setEscenarios] = useState<Escenario[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<number | null>(null);
  const [resultado, setResultado] = useState<SimulacionResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMarcas, setIsLoadingMarcas] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<ViewType>('pyg');
  const [selectedMarcaPyG, setSelectedMarcaPyG] = useState<string | null>(null);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [selectedZonaId, setSelectedZonaId] = useState<number | null>(null);
  const [selectedZonaNombre, setSelectedZonaNombre] = useState<string | null>(null);

  useEffect(() => {
    cargarDatosIniciales();
  }, []);

  const cargarDatosIniciales = async () => {
    setIsLoadingMarcas(true);
    setError(null);
    try {
      const [marcas, listaEscenarios] = await Promise.all([
        apiClient.listarMarcas(),
        apiClient.listarEscenarios()
      ]);

      setMarcasDisponibles(marcas);
      setMarcasSeleccionadas(marcas);
      setEscenarios(listaEscenarios);

      if (listaEscenarios.length > 0) {
        const activo = listaEscenarios.find(e => e.activo) || listaEscenarios[0];
        setSelectedScenarioId(activo.id);
      }
    } catch (err) {
      setError('Error al cargar datos iniciales');
      console.error(err);
    } finally {
      setIsLoadingMarcas(false);
    }
  };

  const ejecutarSimulacion = async () => {
    if (marcasSeleccionadas.length === 0) {
      setError('Debe seleccionar al menos una marca');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const result = await apiClient.ejecutarSimulacion(marcasSeleccionadas, selectedScenarioId || undefined);
      setResultado(result);
    } catch (err) {
      setError('Error al ejecutar la simulación');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const recargarDatos = async () => {
    setResultado(null);
    setRefreshKey(prev => prev + 1);
    await cargarDatosIniciales();
  };

  if (isLoadingMarcas) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <LoadingOverlay message="Cargando sistema..." />
      </div>
    );
  }

  const escenarioActual = escenarios.find(e => e.id === selectedScenarioId);

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
        {/* Compact Header */}
        <header className="bg-white border-b border-gray-200 h-12 flex items-center justify-between px-4">
          <div className="flex items-center gap-4">
            <h1 className="text-sm font-semibold text-gray-800">
              Sistema DxV
            </h1>
            {escenarioActual && (
              <span className="text-xs text-gray-500">
                {escenarioActual.nombre} ({escenarioActual.anio})
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Scenario Selector */}
            {escenarios.length > 0 && (
              <select
                value={selectedScenarioId || ''}
                onChange={(e) => setSelectedScenarioId(Number(e.target.value))}
                disabled={isLoading}
                className="text-xs px-2 py-1 border border-gray-300 rounded bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                {escenarios.map((esc) => (
                  <option key={esc.id} value={esc.id}>
                    {esc.nombre} - {esc.anio} {esc.activo && '(Activo)'}
                  </option>
                ))}
              </select>
            )}

            <button
              onClick={recargarDatos}
              className="flex items-center gap-1 px-2 py-1 text-xs text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-colors"
              title="Recargar"
            >
              <RefreshCw size={14} />
              <span>Recargar</span>
            </button>
          </div>
        </header>

        {/* Control Panel */}
        <div className="bg-white border-b border-gray-200 px-4 py-2">
          <div className="flex items-center gap-3">
            {/* Marca Selector */}
            <div className="flex-1">
              <select
                multiple
                value={marcasSeleccionadas}
                onChange={(e) => {
                  const values = Array.from(e.target.selectedOptions, option => option.value);
                  setMarcasSeleccionadas(values);
                }}
                className="w-full text-xs px-2 py-1 border border-gray-300 rounded bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
                size={Math.min(marcasDisponibles.length, 3)}
              >
                {marcasDisponibles.map((marca) => (
                  <option key={marca} value={marca}>
                    {marca}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={ejecutarSimulacion}
              disabled={marcasSeleccionadas.length === 0 || isLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed rounded transition-colors"
            >
              <Play size={14} />
              {isLoading ? 'Simulando...' : 'Ejecutar Simulación'}
            </button>
          </div>

          {error && (
            <div className="mt-2 flex items-center gap-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
              <AlertCircle size={14} />
              {error}
            </div>
          )}
        </div>

        {/* Main Content Area */}
        <div className="p-4">
          {/* Vista P&G - Requiere simulación */}
          {activeView === 'pyg' && (
            <>
              {isLoading ? (
                <div className="flex items-center justify-center h-64">
                  <LoadingOverlay message="Ejecutando simulación..." />
                </div>
              ) : resultado ? (
                <div>
                  {resultado.marcas.length > 1 && (
                    <div className="mb-3 bg-white border border-gray-200 rounded p-2">
                      <label className="text-xs font-medium text-gray-700 block mb-1">
                        Selecciona una marca:
                      </label>
                      <select
                        value={selectedMarcaPyG || resultado.marcas[0]?.marca_id || ''}
                        onChange={(e) => setSelectedMarcaPyG(e.target.value)}
                        className="w-full text-xs px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        {resultado.marcas.map((marca) => (
                          <option key={marca.marca_id} value={marca.marca_id}>
                            {marca.nombre}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  {(() => {
                    const marcaSeleccionada = resultado.marcas.find(
                      m => m.marca_id === (selectedMarcaPyG || resultado.marcas[0]?.marca_id)
                    );

                    return marcaSeleccionada ? (
                      <PyGDetallado marca={marcaSeleccionada} escenarioId={selectedScenarioId!} />
                    ) : (
                      <div className="bg-white border border-gray-200 rounded p-8 text-center">
                        <p className="text-sm text-gray-600">No se pudo cargar el P&G detallado</p>
                      </div>
                    );
                  })()}
                </div>
              ) : (
                <div className="bg-white border border-gray-200 rounded p-12 text-center">
                  <p className="text-sm text-gray-600">
                    Selecciona las marcas y ejecuta la simulación para ver los resultados
                  </p>
                </div>
              )}
            </>
          )}

          {/* Vista Lejanías Comerciales */}
          {activeView === 'lejanias-comercial' && (
            <>
              {resultado ? (
                <>
                  {/* Selector de marca si hay múltiples */}
                  {resultado.marcas.length > 1 && (
                    <div className="mb-3 bg-white border border-gray-200 rounded p-2">
                      <label className="text-xs font-medium text-gray-700 block mb-1">
                        Selecciona una marca:
                      </label>
                      <select
                        value={selectedMarcaPyG || resultado.marcas[0]?.marca_id || ''}
                        onChange={(e) => setSelectedMarcaPyG(e.target.value)}
                        className="w-full text-xs px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        {resultado.marcas.map((marca) => (
                          <option key={marca.marca_id} value={marca.marca_id}>
                            {marca.nombre}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                  <LejaniasComercial
                    key={`lejanias-comercial-${refreshKey}`}
                    escenarioId={selectedScenarioId!}
                    marcaId={selectedMarcaPyG || resultado.marcas[0]?.marca_id}
                  />
                </>
              ) : (
                <div className="bg-white border border-gray-200 rounded p-12 text-center">
                  <p className="text-sm text-gray-600">
                    Selecciona las marcas y ejecuta la simulación para ver los resultados
                  </p>
                </div>
              )}
            </>
          )}

          {/* Vista Lejanías Logísticas */}
          {activeView === 'lejanias-logistica' && (
            <>
              {resultado ? (
                <>
                  {/* Selector de marca si hay múltiples */}
                  {resultado.marcas.length > 1 && (
                    <div className="mb-3 bg-white border border-gray-200 rounded p-2">
                      <label className="text-xs font-medium text-gray-700 block mb-1">
                        Selecciona una marca:
                      </label>
                      <select
                        value={selectedMarcaPyG || resultado.marcas[0]?.marca_id || ''}
                        onChange={(e) => setSelectedMarcaPyG(e.target.value)}
                        className="w-full text-xs px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        {resultado.marcas.map((marca) => (
                          <option key={marca.marca_id} value={marca.marca_id}>
                            {marca.nombre}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                  <LejaniasLogistica
                    key={`lejanias-logistica-${refreshKey}`}
                    escenarioId={selectedScenarioId!}
                    marcaId={selectedMarcaPyG || resultado.marcas[0]?.marca_id}
                  />
                </>
              ) : (
                <div className="bg-white border border-gray-200 rounded p-12 text-center">
                  <p className="text-sm text-gray-600">
                    Selecciona las marcas y ejecuta la simulación para ver los resultados
                  </p>
                </div>
              )}
            </>
          )}

          {/* Vista P&G por Zonas */}
          {activeView === 'pyg-zonas' && (
            <>
              {resultado ? (
                <>
                  {/* Selector de marca si hay múltiples */}
                  {resultado.marcas.length > 1 && (
                    <div className="mb-3 bg-white border border-gray-200 rounded p-2">
                      <label className="text-xs font-medium text-gray-700 block mb-1">
                        Selecciona una marca:
                      </label>
                      <select
                        value={selectedMarcaPyG || resultado.marcas[0]?.marca_id || ''}
                        onChange={(e) => setSelectedMarcaPyG(e.target.value)}
                        className="w-full text-xs px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        {resultado.marcas.map((marca) => (
                          <option key={marca.marca_id} value={marca.marca_id}>
                            {marca.nombre}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                  <PyGZonas
                    key={`pyg-zonas-${refreshKey}`}
                    escenarioId={selectedScenarioId!}
                    marcaId={selectedMarcaPyG || resultado.marcas[0]?.marca_id}
                    onZonaSelect={(zonaId, zonaNombre) => {
                      setSelectedZonaId(zonaId);
                      setSelectedZonaNombre(zonaNombre);
                      setActiveView('pyg-municipios');
                    }}
                  />
                </>
              ) : (
                <div className="bg-white border border-gray-200 rounded p-12 text-center">
                  <p className="text-sm text-gray-600">
                    Selecciona las marcas y ejecuta la simulación para ver los resultados
                  </p>
                </div>
              )}
            </>
          )}

          {/* Vista P&G por Municipios */}
          {activeView === 'pyg-municipios' && (
            <>
              {resultado ? (
                <>
                  {/* Selector de marca si hay múltiples */}
                  {resultado.marcas.length > 1 && (
                    <div className="mb-3 bg-white border border-gray-200 rounded p-2">
                      <label className="text-xs font-medium text-gray-700 block mb-1">
                        Selecciona una marca:
                      </label>
                      <select
                        value={selectedMarcaPyG || resultado.marcas[0]?.marca_id || ''}
                        onChange={(e) => {
                          setSelectedMarcaPyG(e.target.value);
                          setSelectedZonaId(null);
                          setSelectedZonaNombre(null);
                        }}
                        className="w-full text-xs px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        {resultado.marcas.map((marca) => (
                          <option key={marca.marca_id} value={marca.marca_id}>
                            {marca.nombre}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  {selectedZonaId ? (
                    <PyGMunicipios
                      key={`pyg-municipios-${selectedZonaId}-${refreshKey}`}
                      escenarioId={selectedScenarioId!}
                      zonaId={selectedZonaId}
                      zonaNombre={selectedZonaNombre || undefined}
                      marcaId={selectedMarcaPyG || resultado.marcas[0]?.marca_id}
                      onBack={() => {
                        setSelectedZonaId(null);
                        setSelectedZonaNombre(null);
                        setActiveView('pyg-zonas');
                      }}
                    />
                  ) : (
                    <PyGZonas
                      key={`pyg-zonas-selector-${refreshKey}`}
                      escenarioId={selectedScenarioId!}
                      marcaId={selectedMarcaPyG || resultado.marcas[0]?.marca_id}
                      onZonaSelect={(zonaId, zonaNombre) => {
                        setSelectedZonaId(zonaId);
                        setSelectedZonaNombre(zonaNombre);
                      }}
                    />
                  )}
                </>
              ) : (
                <div className="bg-white border border-gray-200 rounded p-12 text-center">
                  <p className="text-sm text-gray-600">
                    Selecciona las marcas y ejecuta la simulación para ver los resultados
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
