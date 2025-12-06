'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient, PyGZonasResponse, PyGMunicipiosResponse, DiagnosticoPersonalResponse, ComparacionPyGResponse } from '@/lib/api';

/**
 * Hook para obtener P&G por zonas con caché
 */
export function usePyGZonas(escenarioId: number | null, marcaId: string | null) {
  return useQuery({
    queryKey: ['pyg-zonas', escenarioId, marcaId],
    queryFn: () => apiClient.obtenerPyGZonas(escenarioId!, marcaId!),
    enabled: !!escenarioId && !!marcaId,
    staleTime: 5 * 60 * 1000, // 5 minutos
  });
}

/**
 * Hook para obtener diagnóstico de personal con caché
 */
export function useDiagnosticoPersonal(escenarioId: number | null, marcaId: string | null) {
  return useQuery({
    queryKey: ['diagnostico-personal', escenarioId, marcaId],
    queryFn: () => apiClient.obtenerDiagnosticoPersonal(escenarioId!, marcaId!),
    enabled: !!escenarioId && !!marcaId,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook para obtener comparación P&G con caché
 */
export function useComparacionPyG(escenarioId: number | null, marcaId: string | null) {
  return useQuery({
    queryKey: ['comparacion-pyg', escenarioId, marcaId],
    queryFn: () => apiClient.obtenerComparacionPyG(escenarioId!, marcaId!),
    enabled: !!escenarioId && !!marcaId,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook para obtener P&G por municipios de una zona con caché
 */
export function usePyGMunicipios(zonaId: number | null, escenarioId: number | null, marcaId: string | null) {
  return useQuery({
    queryKey: ['pyg-municipios', zonaId, escenarioId, marcaId],
    queryFn: () => apiClient.obtenerPyGMunicipios(zonaId!, escenarioId!, marcaId!),
    enabled: !!zonaId && !!escenarioId && !!marcaId,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook combinado para cargar todos los datos de P&G Zonas
 * Usa queries paralelas con caché compartido
 */
export function usePyGZonasData(escenarioId: number | null, marcaId: string | null) {
  const zonasQuery = usePyGZonas(escenarioId, marcaId);
  const diagnosticoQuery = useDiagnosticoPersonal(escenarioId, marcaId);
  const comparacionQuery = useComparacionPyG(escenarioId, marcaId);

  return {
    data: zonasQuery.data,
    diagnostico: diagnosticoQuery.data,
    comparacion: comparacionQuery.data,
    isLoading: zonasQuery.isLoading || diagnosticoQuery.isLoading || comparacionQuery.isLoading,
    error: zonasQuery.error || diagnosticoQuery.error || comparacionQuery.error,
    refetch: () => {
      zonasQuery.refetch();
      diagnosticoQuery.refetch();
      comparacionQuery.refetch();
    }
  };
}
