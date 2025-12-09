'use client';

import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { useMemo, useCallback, useTransition } from 'react';
import { getMesActual } from '@/lib/api';

export type ViewType = 'distribucion' | 'pyg' | 'pyg-zonas' | 'lejanias-comercial' | 'lejanias-logistica';

export interface Filters {
  escenarioId: number | null;
  operacionIds: number[];
  marcaId: string | null;
  mes: string;
  vista: ViewType;
}

export interface UseFiltersReturn {
  filters: Filters;
  setEscenario: (id: number | null) => void;
  setOperaciones: (ids: number[]) => void;
  setMarca: (id: string | null) => void;
  setMes: (mes: string) => void;
  setVista: (vista: ViewType) => void;
  updateFilters: (updates: Partial<Filters>) => void;
  isPending: boolean;
}

/**
 * Hook centralizado para manejar filtros sincronizados con URL
 *
 * URL Schema:
 * ?escenario=1&operaciones=1,2,3&marca=MARCA01&mes=enero&vista=pyg-zonas
 */
export function useFilters(): UseFiltersReturn {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const [isPending, startTransition] = useTransition();

  // Leer filtros desde URL con defaults
  const filters = useMemo<Filters>(() => {
    const escenarioParam = searchParams.get('escenario');
    const operacionesParam = searchParams.get('operaciones');
    const marcaParam = searchParams.get('marca');
    const mesParam = searchParams.get('mes');
    const vistaParam = searchParams.get('vista');

    return {
      escenarioId: escenarioParam ? Number(escenarioParam) : null,
      operacionIds: operacionesParam
        ? operacionesParam.split(',').map(Number).filter(n => !isNaN(n))
        : [],
      marcaId: marcaParam || null,
      mes: mesParam || getMesActual(),
      vista: (vistaParam as ViewType) || 'distribucion',
    };
  }, [searchParams]);

  // Función base para actualizar URL
  const updateURL = useCallback((updates: Record<string, string | null>) => {
    startTransition(() => {
      const params = new URLSearchParams(searchParams.toString());

      Object.entries(updates).forEach(([key, value]) => {
        if (value === null || value === '') {
          params.delete(key);
        } else {
          params.set(key, value);
        }
      });

      const queryString = params.toString();
      const newURL = queryString ? `${pathname}?${queryString}` : pathname;
      router.push(newURL, { scroll: false });
    });
  }, [searchParams, router, pathname]);

  // Setters individuales
  const setEscenario = useCallback((id: number | null) => {
    // Al cambiar escenario, limpiar operaciones y marca (se recargarán)
    updateURL({
      escenario: id?.toString() ?? null,
      operaciones: null,
      marca: null,
    });
  }, [updateURL]);

  const setOperaciones = useCallback((ids: number[]) => {
    updateURL({
      operaciones: ids.length > 0 ? ids.join(',') : null,
    });
  }, [updateURL]);

  const setMarca = useCallback((id: string | null) => {
    updateURL({
      marca: id,
    });
  }, [updateURL]);

  const setMes = useCallback((mes: string) => {
    updateURL({
      mes: mes,
    });
  }, [updateURL]);

  const setVista = useCallback((vista: ViewType) => {
    updateURL({
      vista: vista,
    });
  }, [updateURL]);

  // Actualización múltiple
  const updateFilters = useCallback((updates: Partial<Filters>) => {
    const urlUpdates: Record<string, string | null> = {};

    if ('escenarioId' in updates) {
      urlUpdates.escenario = updates.escenarioId?.toString() ?? null;
    }
    if ('operacionIds' in updates) {
      urlUpdates.operaciones = updates.operacionIds?.length
        ? updates.operacionIds.join(',')
        : null;
    }
    if ('marcaId' in updates) {
      urlUpdates.marca = updates.marcaId ?? null;
    }
    if ('mes' in updates) {
      urlUpdates.mes = updates.mes ?? null;
    }
    if ('vista' in updates) {
      urlUpdates.vista = updates.vista ?? null;
    }

    updateURL(urlUpdates);
  }, [updateURL]);

  return {
    filters,
    setEscenario,
    setOperaciones,
    setMarca,
    setMes,
    setVista,
    updateFilters,
    isPending,
  };
}

/**
 * Hook para obtener solo el mes actual (sin necesidad de URL)
 * Útil para componentes que solo necesitan el mes sin otros filtros
 */
export function useMesActual(): string {
  const searchParams = useSearchParams();
  return searchParams.get('mes') || getMesActual();
}
