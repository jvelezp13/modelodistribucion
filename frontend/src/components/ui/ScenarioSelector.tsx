import React from 'react';
import { Escenario } from '@/lib/api';

interface ScenarioSelectorProps {
    escenarios: Escenario[];
    selectedId: number | null;
    onSelect: (id: number) => void;
    isLoading: boolean;
}

export function ScenarioSelector({ escenarios, selectedId, onSelect, isLoading }: ScenarioSelectorProps) {
    return (
        <div className="flex items-center gap-3 bg-white p-2 rounded-lg border border-gray-200 shadow-sm">
            <label htmlFor="scenario-select" className="text-sm font-medium text-gray-700 whitespace-nowrap">
                Escenario:
            </label>
            <select
                id="scenario-select"
                value={selectedId || ''}
                onChange={(e) => onSelect(Number(e.target.value))}
                disabled={isLoading}
                className="block w-full min-w-[200px] rounded-md border-gray-300 py-1.5 pl-3 pr-8 text-sm focus:border-primary-500 focus:outline-none focus:ring-primary-500 disabled:opacity-50"
            >
                {escenarios.map((escenario) => (
                    <option key={escenario.id} value={escenario.id}>
                        {escenario.nombre} ({escenario.anio}) {escenario.activo ? '(Activo)' : ''}
                    </option>
                ))}
            </select>
        </div>
    );
}
