'use client';

import React from 'react';
import { Calendar } from 'lucide-react';
import { MESES } from '@/lib/api';
import { useFilters } from '@/hooks/useFilters';

interface MonthSelectorProps {
  className?: string;
  showLabel?: boolean;
  size?: 'sm' | 'md';
}

/**
 * Selector de mes reutilizable que sincroniza con URL
 * Usa useFilters internamente para leer/escribir el mes
 */
export default function MonthSelector({
  className = '',
  showLabel = true,
  size = 'sm'
}: MonthSelectorProps) {
  const { filters, setMes } = useFilters();

  const sizeClasses = size === 'sm'
    ? 'text-xs px-2 py-1'
    : 'text-sm px-3 py-1.5';

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Calendar size={size === 'sm' ? 14 : 16} className="text-gray-500" />
      {showLabel && (
        <label className="text-xs text-gray-500">Mes:</label>
      )}
      <select
        value={filters.mes}
        onChange={(e) => setMes(e.target.value)}
        className={`${sizeClasses} border border-gray-300 rounded bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500`}
      >
        {MESES.map((mes) => (
          <option key={mes.value} value={mes.value}>
            {mes.label}
          </option>
        ))}
      </select>
    </div>
  );
}
