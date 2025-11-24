'use client';

import { useState, useEffect } from 'react';
import { apiClient, SimulacionResult } from '@/lib/api';
import { formatearMoneda, formatearPorcentaje } from '@/lib/utils';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { MetricCard } from '@/components/ui/MetricCard';
import { LoadingOverlay } from '@/components/ui/LoadingSpinner';
import { MultiSelect } from '@/components/ui/MultiSelect';
import { TrendingUp, DollarSign, Users, PieChart, RefreshCw, Play } from 'lucide-react';

export default function DashboardPage() {
  const [marcasDisponibles, setMarcasDisponibles] = useState<string[]>([]);
  const [marcasSeleccionadas, setMarcasSeleccionadas] = useState<string[]>([]);
  const [resultado, setResultado] = useState<SimulacionResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMarcas, setIsLoadingMarcas] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'consolidado' | 'marcas' | 'detalles'>('consolidado');

  // Cargar marcas disponibles al montar el componente
  useEffect(() => {
    cargarMarcas();
  }, []);

  const cargarMarcas = async () => {
    setIsLoadingMarcas(true);
    setError(null);
    try {
      const marcas = await apiClient.listarMarcas();
      setMarcasDisponibles(marcas);
      // Seleccionar todas las marcas por defecto
      setMarcasSeleccionadas(marcas);
    } catch (err) {
      setError('Error al cargar las marcas disponibles');
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
      const result = await apiClient.ejecutarSimulacion(marcasSeleccionadas);
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
    await cargarMarcas();
  };

  if (isLoadingMarcas) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingOverlay message="Cargando sistema..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white border-b border-secondary-200 shadow-soft">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-primary-600 to-primary-500 bg-clip-text text-transparent">
                Sistema de Distribución Multimarcas
              </h1>
              <p className="mt-1 text-secondary-600">
                Modelo de Distribución y Ventas (DxV) - Simulación y Optimización
              </p>
            </div>
            <Button
              variant="outline"
              onClick={recargarDatos}
              className="gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Recargar Datos
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Panel de control */}
        <Card variant="bordered" className="mb-8">
          <CardContent className="py-6">
            <div className="flex flex-col md:flex-row gap-4 items-end">
              <div className="flex-1">
                <MultiSelect
                  label="Marcas a Simular"
                  options={marcasDisponibles}
                  value={marcasSeleccionadas}
                  onChange={setMarcasSeleccionadas}
                  placeholder="Selecciona las marcas..."
                />
              </div>
              <Button
                onClick={ejecutarSimulacion}
                isLoading={isLoading}
                disabled={marcasSeleccionadas.length === 0}
                size="lg"
                className="gap-2 md:min-w-[200px]"
              >
                <Play className="h-5 w-5" />
                Ejecutar Simulación
              </Button>
            </div>

            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                {error}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Contenido principal */}
        {isLoading ? (
          <LoadingOverlay message="Ejecutando simulación..." />
        ) : resultado ? (
          <>
            {/* Tabs */}
            <div className="mb-6 border-b border-secondary-200">
              <nav className="flex gap-8">
                {[
                  { id: 'consolidado', label: '📊 Resumen General', icon: PieChart },
                  { id: 'marcas', label: '📈 Por Marca', icon: TrendingUp },
                  { id: 'detalles', label: '🔍 Detalles', icon: Users },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`
                      px-4 py-3 font-semibold border-b-2 transition-all duration-200
                      ${activeTab === tab.id
                        ? 'border-primary-500 text-primary-600'
                        : 'border-transparent text-secondary-600 hover:text-secondary-900 hover:border-secondary-300'
                      }
                    `}
                  >
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>

            {/* Tab Content */}
            {activeTab === 'consolidado' && (
              <div className="space-y-8">
                {/* Métricas principales */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <MetricCard
                    label="Ventas Mensuales (Sell Out)"
                    value={formatearMoneda(resultado.consolidado.total_ventas_mensuales ?? 0)}
                    subtitle={resultado.consolidado.total_descuentos_mensuales ?
                      `Ingresos Extra: ${formatearMoneda(resultado.consolidado.total_descuentos_mensuales)}` :
                      `${formatearMoneda(resultado.consolidado.total_ventas_anuales)} anuales`
                    }
                    icon={<DollarSign className="h-6 w-6" />}
                    variant="success"
                  />
                  <MetricCard
                    label="Costos Mensuales"
                    value={formatearMoneda(resultado.consolidado.total_costos_mensuales)}
                    subtitle={`${formatearMoneda(resultado.consolidado.total_costos_anuales)} anuales`}
                    icon={<TrendingUp className="h-6 w-6" />}
                    variant="warning"
                  />
                  <MetricCard
                    label="Margen Consolidado"
                    value={formatearPorcentaje(resultado.consolidado.margen_consolidado * 100)}
                    subtitle="Incluye Descuentos como Ingreso"
                    variant={resultado.consolidado.margen_consolidado > 0.1 ? 'success' : 'danger'}
                    icon={<PieChart className="h-6 w-6" />}
                  />
                  <MetricCard
                    label="Total Empleados"
                    value={resultado.consolidado.total_empleados}
                    icon={<Users className="h-6 w-6" />}
                    variant="primary"
                  />
                </div>

                {/* Desglose de costos */}
                <Card variant="elevated">
                  <CardHeader>
                    <CardTitle>Desglose de Costos por Categoría</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {[
                        { label: 'Comercial', valor: resultado.consolidado.costo_comercial_total, color: 'bg-blue-500' },
                        { label: 'Logística', valor: resultado.consolidado.costo_logistico_total, color: 'bg-green-500' },
                        { label: 'Administrativa', valor: resultado.consolidado.costo_administrativo_total, color: 'bg-purple-500' },
                      ].map((categoria) => {
                        const porcentaje = (categoria.valor / resultado.consolidado.total_costos_mensuales) * 100;
                        return (
                          <div key={categoria.label}>
                            <div className="flex justify-between items-center mb-2">
                              <span className="font-medium text-secondary-700">{categoria.label}</span>
                              <span className="text-secondary-900 font-semibold">
                                {formatearMoneda(categoria.valor)} ({formatearPorcentaje(porcentaje)})
                              </span>
                            </div>
                            <div className="w-full bg-secondary-100 rounded-full h-3">
                              <div
                                className={`${categoria.color} h-3 rounded-full transition-all duration-500`}
                                style={{ width: `${porcentaje}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>

                {/* Comparación entre marcas */}
                <Card variant="elevated">
                  <CardHeader>
                    <CardTitle>Comparación entre Marcas</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-secondary-200">
                            <th className="text-left py-3 px-4 font-semibold text-secondary-700">Marca</th>
                            <th className="text-right py-3 px-4 font-semibold text-secondary-700">Sell Out</th>
                            <th className="text-right py-3 px-4 font-semibold text-secondary-700">Ingresos Extra</th>
                            <th className="text-right py-3 px-4 font-semibold text-secondary-700">Costos</th>
                            <th className="text-right py-3 px-4 font-semibold text-secondary-700">Margen Neto %</th>
                            <th className="text-right py-3 px-4 font-semibold text-secondary-700">Empleados</th>
                          </tr>
                        </thead>
                        <tbody>
                          {resultado.marcas.map((marca) => {
                            const tieneDescuentos = (marca.porcentaje_descuento_total ?? 0) > 0;
                            const totalIngresosExtra = (marca.descuento_pie_factura ?? 0) + (marca.rebate ?? 0) + (marca.descuento_financiero ?? 0);
                            return (
                              <tr key={marca.marca_id} className="border-b border-secondary-100 hover:bg-primary-50 transition-colors">
                                <td className="py-3 px-4 font-medium text-secondary-900">{marca.nombre}</td>
                                <td className="py-3 px-4 text-right text-secondary-900 font-semibold">
                                  {formatearMoneda(marca.ventas_mensuales)}
                                </td>
                                <td className="py-3 px-4 text-right">
                                  {tieneDescuentos ? (
                                    <span className="text-success font-medium">
                                      +{formatearMoneda(totalIngresosExtra)}
                                    </span>
                                  ) : (
                                    <span className="text-secondary-400">-</span>
                                  )}
                                </td>
                                <td className="py-3 px-4 text-right text-warning">{formatearMoneda(marca.costo_total)}</td>
                                <td className="py-3 px-4 text-right">
                                  <span className={`font-semibold ${marca.margen_porcentaje > 10 ? 'text-success' : 'text-danger'}`}>
                                    {formatearPorcentaje(marca.margen_porcentaje)}
                                  </span>
                                </td>
                                <td className="py-3 px-4 text-right text-secondary-900">{marca.total_empleados}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {activeTab === 'marcas' && (
              <div className="space-y-8">
                {resultado.marcas.map((marca) => (
                  <Card key={marca.marca_id} variant="elevated">
                    <CardHeader>
                      <CardTitle>🏢 {marca.nombre}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {/* Métricas de la marca */}
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                        <MetricCard
                          label="Ventas Mensuales (Sell Out)"
                          value={formatearMoneda(marca.ventas_mensuales)}
                          subtitle={(marca.porcentaje_descuento_total ?? 0) > 0 ?
                            `Ingresos Extra: ${formatearMoneda((marca.descuento_pie_factura ?? 0) + (marca.rebate ?? 0) + (marca.descuento_financiero ?? 0))}` :
                            undefined
                          }
                          variant="success"
                        />
                        <MetricCard
                          label="Costo Total"
                          value={formatearMoneda(marca.costo_total)}
                          variant="warning"
                        />
                        <MetricCard
                          label="Margen Neto"
                          value={formatearPorcentaje(marca.margen_porcentaje)}
                          subtitle="Incluye Descuentos como Ingreso"
                          variant={marca.margen_porcentaje > 10 ? 'success' : 'danger'}
                        />
                        <MetricCard
                          label="Empleados"
                          value={marca.total_empleados}
                          variant="primary"
                        />
                      </div>

                      {/* Desglose de costos */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <h4 className="font-semibold text-secondary-900 mb-3">Desglose de Costos</h4>
                          <div className="space-y-2">
                            {[
                              { label: 'Comercial', valor: marca.costo_comercial },
                              { label: 'Logística', valor: marca.costo_logistico },
                              { label: 'Administrativa', valor: marca.costo_administrativo },
                            ].map((cat) => {
                              const pct = (cat.valor / marca.costo_total) * 100;
                              return (
                                <div key={cat.label} className="flex justify-between text-sm">
                                  <span className="text-secondary-600">{cat.label}:</span>
                                  <span className="font-medium text-secondary-900">
                                    {formatearMoneda(cat.valor)} ({formatearPorcentaje(pct)})
                                  </span>
                                </div>
                              );
                            })}
                          </div>
                        </div>

                        <div>
                          <h4 className="font-semibold text-secondary-900 mb-3">Recursos</h4>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-secondary-600">Rubros Individuales:</span>
                              <span className="font-medium text-secondary-900">{marca.rubros_individuales.length}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-secondary-600">Rubros Compartidos:</span>
                              <span className="font-medium text-secondary-900">{marca.rubros_compartidos_asignados.length}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-secondary-600">Empleados Comerciales:</span>
                              <span className="font-medium text-secondary-900">{marca.empleados_comerciales}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-secondary-600">Empleados Logísticos:</span>
                              <span className="font-medium text-secondary-900">{marca.empleados_logisticos}</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Rubros individuales */}
                      {marca.rubros_individuales.length > 0 && (
                        <div className="mt-6">
                          <h4 className="font-semibold text-secondary-900 mb-3">Detalle de Rubros Individuales</h4>
                          <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                              <thead>
                                <tr className="border-b border-secondary-200">
                                  <th className="text-left py-2 px-3 font-semibold text-secondary-700">Nombre</th>
                                  <th className="text-left py-2 px-3 font-semibold text-secondary-700">Categoría</th>
                                  <th className="text-left py-2 px-3 font-semibold text-secondary-700">Tipo</th>
                                  <th className="text-right py-2 px-3 font-semibold text-secondary-700">Cantidad</th>
                                  <th className="text-right py-2 px-3 font-semibold text-secondary-700">Costo Total</th>
                                </tr>
                              </thead>
                              <tbody>
                                {marca.rubros_individuales.map((rubro) => (
                                  <tr key={rubro.id} className="border-b border-secondary-100 hover:bg-primary-50">
                                    <td className="py-2 px-3">{rubro.nombre}</td>
                                    <td className="py-2 px-3 capitalize">{rubro.categoria}</td>
                                    <td className="py-2 px-3">{rubro.tipo}</td>
                                    <td className="py-2 px-3 text-right">{rubro.cantidad || '-'}</td>
                                    <td className="py-2 px-3 text-right font-medium">{formatearMoneda(rubro.valor_total)}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {activeTab === 'detalles' && (
              <div className="space-y-6">
                <Card variant="elevated">
                  <CardHeader>
                    <CardTitle>🔄 Rubros Compartidos</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-secondary-600 mb-4">
                      Total de rubros compartidos: <span className="font-semibold">{resultado.rubros_compartidos.length}</span>
                    </p>
                    {resultado.rubros_compartidos.length > 0 && (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-secondary-200">
                              <th className="text-left py-2 px-3 font-semibold text-secondary-700">ID</th>
                              <th className="text-left py-2 px-3 font-semibold text-secondary-700">Nombre</th>
                              <th className="text-left py-2 px-3 font-semibold text-secondary-700">Categoría</th>
                              <th className="text-left py-2 px-3 font-semibold text-secondary-700">Criterio Prorrateo</th>
                              <th className="text-right py-2 px-3 font-semibold text-secondary-700">Valor Total</th>
                            </tr>
                          </thead>
                          <tbody>
                            {resultado.rubros_compartidos.map((rubro) => (
                              <tr key={rubro.id} className="border-b border-secondary-100 hover:bg-primary-50">
                                <td className="py-2 px-3 text-secondary-600">{rubro.id}</td>
                                <td className="py-2 px-3">{rubro.nombre}</td>
                                <td className="py-2 px-3 capitalize">{rubro.categoria}</td>
                                <td className="py-2 px-3">{rubro.criterio_prorrateo || 'N/A'}</td>
                                <td className="py-2 px-3 text-right font-medium">{formatearMoneda(rubro.valor_total)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card variant="elevated">
                  <CardHeader>
                    <CardTitle>⚙️ Metadata</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className="bg-secondary-50 p-4 rounded-lg text-xs overflow-auto">
                      {JSON.stringify(resultado.metadata, null, 2)}
                    </pre>
                  </CardContent>
                </Card>
              </div>
            )}
          </>
        ) : (
          <Card variant="bordered">
            <CardContent className="py-12 text-center">
              <PieChart className="h-16 w-16 mx-auto text-secondary-300 mb-4" />
              <p className="text-secondary-600 text-lg">
                Selecciona las marcas y haz clic en <strong>Ejecutar Simulación</strong> para ver los resultados
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
