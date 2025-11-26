'use client';

import { useState, useEffect } from 'react';
import { apiClient, SimulacionResult, Escenario } from '@/lib/api';
import { formatearMoneda, formatearPorcentaje } from '@/lib/utils';
import { LoadingOverlay } from '@/components/ui/LoadingSpinner';
import { RefreshCw, Play, AlertCircle } from 'lucide-react';
import Sidebar from '@/components/Sidebar';
import PyGDetallado from '@/components/PyGDetallado';

export default function DashboardPage() {
  const [marcasDisponibles, setMarcasDisponibles] = useState<string[]>([]);
  const [marcasSeleccionadas, setMarcasSeleccionadas] = useState<string[]>([]);
  const [escenarios, setEscenarios] = useState<Escenario[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<number | null>(null);
  const [resultado, setResultado] = useState<SimulacionResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMarcas, setIsLoadingMarcas] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<'consolidado' | 'marcas' | 'pyg' | 'detalles'>('consolidado');
  const [selectedMarcaPyG, setSelectedMarcaPyG] = useState<string | null>(null);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

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
        onViewChange={(view) => setActiveView(view as any)}
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
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <LoadingOverlay message="Ejecutando simulación..." />
            </div>
          ) : resultado ? (
            <>
              {/* Consolidado View */}
              {activeView === 'consolidado' && (
                <div className="space-y-4">
                  {/* Compact Metrics */}
                  <div className="grid grid-cols-4 gap-3">
                    <div className="bg-white border border-gray-200 rounded p-3">
                      <div className="text-xs text-gray-500 mb-1">Ventas Mensuales</div>
                      <div className="text-lg font-semibold text-gray-900">
                        {formatearMoneda(resultado.consolidado.total_ventas_mensuales ?? 0)}
                      </div>
                      {resultado.consolidado.total_descuentos_mensuales && (
                        <div className="text-xs text-green-600 mt-1">
                          +{formatearMoneda(resultado.consolidado.total_descuentos_mensuales)} ingresos extra
                        </div>
                      )}
                    </div>

                    <div className="bg-white border border-gray-200 rounded p-3">
                      <div className="text-xs text-gray-500 mb-1">Costos Mensuales</div>
                      <div className="text-lg font-semibold text-gray-900">
                        {formatearMoneda(resultado.consolidado.total_costos_mensuales)}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {formatearMoneda(resultado.consolidado.total_costos_anuales)} anuales
                      </div>
                    </div>

                    <div className="bg-white border border-gray-200 rounded p-3">
                      <div className="text-xs text-gray-500 mb-1">Margen Consolidado</div>
                      <div className={`text-lg font-semibold ${resultado.consolidado.margen_consolidado > 0.1 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatearPorcentaje(resultado.consolidado.margen_consolidado * 100)}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">Incluye descuentos</div>
                    </div>

                    <div className="bg-white border border-gray-200 rounded p-3">
                      <div className="text-xs text-gray-500 mb-1">Total Empleados</div>
                      <div className="text-lg font-semibold text-gray-900">
                        {resultado.consolidado.total_empleados}
                      </div>
                    </div>
                  </div>

                  {/* Cost Breakdown Bars */}
                  <div className="bg-white border border-gray-200 rounded p-3">
                    <div className="text-sm font-semibold text-gray-700 mb-3">Desglose de Costos</div>
                    <div className="space-y-2">
                      {[
                        { label: 'Comercial', valor: resultado.consolidado.costo_comercial_total, color: 'bg-blue-500' },
                        { label: 'Logística', valor: resultado.consolidado.costo_logistico_total, color: 'bg-green-500' },
                        { label: 'Administrativa', valor: resultado.consolidado.costo_administrativo_total, color: 'bg-purple-500' },
                      ].map((cat) => {
                        const pct = (cat.valor / resultado.consolidado.total_costos_mensuales) * 100;
                        return (
                          <div key={cat.label}>
                            <div className="flex justify-between items-center text-xs mb-1">
                              <span className="text-gray-600">{cat.label}</span>
                              <span className="text-gray-900 font-medium">
                                {formatearMoneda(cat.valor)} ({formatearPorcentaje(pct)})
                              </span>
                            </div>
                            <div className="w-full bg-gray-100 rounded-full h-2">
                              <div
                                className={`${cat.color} h-2 rounded-full`}
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Compact Table */}
                  <div className="bg-white border border-gray-200 rounded">
                    <div className="px-3 py-2 border-b border-gray-200">
                      <div className="text-sm font-semibold text-gray-700">Comparación entre Marcas</div>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="border-b border-gray-200 bg-gray-50">
                            <th className="text-left py-2 px-3 font-medium text-gray-700">Marca</th>
                            <th className="text-right py-2 px-3 font-medium text-gray-700">Sell Out</th>
                            <th className="text-right py-2 px-3 font-medium text-gray-700">Ingresos Extra</th>
                            <th className="text-right py-2 px-3 font-medium text-gray-700">Costos</th>
                            <th className="text-right py-2 px-3 font-medium text-gray-700">Margen %</th>
                            <th className="text-right py-2 px-3 font-medium text-gray-700">Empleados</th>
                          </tr>
                        </thead>
                        <tbody>
                          {resultado.marcas.map((marca) => {
                            const totalIngresosExtra = (marca.descuento_pie_factura ?? 0) + (marca.rebate ?? 0) + (marca.descuento_financiero ?? 0);
                            return (
                              <tr key={marca.marca_id} className="border-b border-gray-100 hover:bg-gray-50">
                                <td className="py-2 px-3 font-medium text-gray-900">{marca.nombre}</td>
                                <td className="py-2 px-3 text-right text-gray-900">
                                  {formatearMoneda(marca.ventas_mensuales)}
                                </td>
                                <td className="py-2 px-3 text-right">
                                  {totalIngresosExtra > 0 ? (
                                    <span className="text-green-600 font-medium">
                                      +{formatearMoneda(totalIngresosExtra)}
                                    </span>
                                  ) : (
                                    <span className="text-gray-400">-</span>
                                  )}
                                </td>
                                <td className="py-2 px-3 text-right text-gray-900">{formatearMoneda(marca.costo_total)}</td>
                                <td className="py-2 px-3 text-right">
                                  <span className={`font-medium ${marca.margen_porcentaje > 10 ? 'text-green-600' : 'text-red-600'}`}>
                                    {formatearPorcentaje(marca.margen_porcentaje)}
                                  </span>
                                </td>
                                <td className="py-2 px-3 text-right text-gray-900">{marca.total_empleados}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* Marcas View */}
              {activeView === 'marcas' && (
                <div className="space-y-4">
                  {resultado.marcas.map((marca) => (
                    <div key={marca.marca_id} className="bg-white border border-gray-200 rounded">
                      <div className="px-3 py-2 border-b border-gray-200 bg-gray-50">
                        <div className="text-sm font-semibold text-gray-800">{marca.nombre}</div>
                      </div>

                      <div className="p-3">
                        {/* Compact Metrics */}
                        <div className="grid grid-cols-4 gap-3 mb-3">
                          <div>
                            <div className="text-xs text-gray-500">Ventas</div>
                            <div className="text-sm font-semibold text-gray-900">{formatearMoneda(marca.ventas_mensuales)}</div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500">Costos</div>
                            <div className="text-sm font-semibold text-gray-900">{formatearMoneda(marca.costo_total)}</div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500">Margen</div>
                            <div className={`text-sm font-semibold ${marca.margen_porcentaje > 10 ? 'text-green-600' : 'text-red-600'}`}>
                              {formatearPorcentaje(marca.margen_porcentaje)}
                            </div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500">Empleados</div>
                            <div className="text-sm font-semibold text-gray-900">{marca.total_empleados}</div>
                          </div>
                        </div>

                        {/* Rubros Table */}
                        {marca.rubros_individuales.length > 0 && (
                          <div className="mt-3">
                            <div className="text-xs font-medium text-gray-700 mb-2">Rubros Individuales</div>
                            <div className="overflow-x-auto">
                              <table className="w-full text-xs">
                                <thead>
                                  <tr className="border-b border-gray-200 bg-gray-50">
                                    <th className="text-left py-1.5 px-2 font-medium text-gray-700">Nombre</th>
                                    <th className="text-left py-1.5 px-2 font-medium text-gray-700">Categoría</th>
                                    <th className="text-left py-1.5 px-2 font-medium text-gray-700">Tipo</th>
                                    <th className="text-right py-1.5 px-2 font-medium text-gray-700">Cant.</th>
                                    <th className="text-right py-1.5 px-2 font-medium text-gray-700">Costo Total</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {marca.rubros_individuales.map((rubro) => (
                                    <tr key={rubro.id} className="border-b border-gray-100 hover:bg-gray-50">
                                      <td className="py-1.5 px-2 text-gray-900">{rubro.nombre}</td>
                                      <td className="py-1.5 px-2 text-gray-600 capitalize">{rubro.categoria}</td>
                                      <td className="py-1.5 px-2 text-gray-600">{rubro.tipo}</td>
                                      <td className="py-1.5 px-2 text-right text-gray-600">{rubro.cantidad || '-'}</td>
                                      <td className="py-1.5 px-2 text-right text-gray-900 font-medium">{formatearMoneda(rubro.valor_total)}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* P&G View */}
              {activeView === 'pyg' && (
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
                      <PyGDetallado marca={marcaSeleccionada} />
                    ) : (
                      <div className="bg-white border border-gray-200 rounded p-8 text-center">
                        <p className="text-sm text-gray-600">No se pudo cargar el P&G detallado</p>
                      </div>
                    );
                  })()}
                </div>
              )}

              {/* Detalles View */}
              {activeView === 'detalles' && (
                <div className="bg-white border border-gray-200 rounded">
                  <div className="px-3 py-2 border-b border-gray-200">
                    <div className="text-sm font-semibold text-gray-700">
                      Rubros Compartidos ({resultado.rubros_compartidos.length})
                    </div>
                  </div>
                  {resultado.rubros_compartidos.length > 0 && (
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="border-b border-gray-200 bg-gray-50">
                            <th className="text-left py-2 px-3 font-medium text-gray-700">ID</th>
                            <th className="text-left py-2 px-3 font-medium text-gray-700">Nombre</th>
                            <th className="text-left py-2 px-3 font-medium text-gray-700">Categoría</th>
                            <th className="text-left py-2 px-3 font-medium text-gray-700">Prorrateo</th>
                            <th className="text-right py-2 px-3 font-medium text-gray-700">Valor</th>
                          </tr>
                        </thead>
                        <tbody>
                          {resultado.rubros_compartidos.map((rubro) => (
                            <tr key={rubro.id} className="border-b border-gray-100 hover:bg-gray-50">
                              <td className="py-2 px-3 text-gray-600">{rubro.id}</td>
                              <td className="py-2 px-3 text-gray-900">{rubro.nombre}</td>
                              <td className="py-2 px-3 text-gray-600 capitalize">{rubro.categoria}</td>
                              <td className="py-2 px-3 text-gray-600">{rubro.criterio_prorrateo || 'N/A'}</td>
                              <td className="py-2 px-3 text-right text-gray-900 font-medium">{formatearMoneda(rubro.valor_total)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="bg-white border border-gray-200 rounded p-12 text-center">
              <p className="text-sm text-gray-600">
                Selecciona las marcas y ejecuta la simulación para ver los resultados
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
