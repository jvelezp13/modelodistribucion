import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility to merge Tailwind classes
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Formatea un número como moneda colombiana
 */
export function formatearMoneda(valor: number): string {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(valor);
}

/**
 * Formatea un número como porcentaje
 */
export function formatearPorcentaje(valor: number): string {
  return `${valor.toFixed(1)}%`;
}

/**
 * Formatea un número grande de forma compacta (K, M, B)
 */
export function formatearNumeroCompacto(valor: number): string {
  if (valor >= 1_000_000_000) {
    return `${(valor / 1_000_000_000).toFixed(1)}B`;
  } else if (valor >= 1_000_000) {
    return `${(valor / 1_000_000).toFixed(1)}M`;
  } else if (valor >= 1_000) {
    return `${(valor / 1_000).toFixed(1)}K`;
  }
  return valor.toString();
}
