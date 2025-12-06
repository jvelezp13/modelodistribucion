'use client';

import React from 'react';
import {
  FileText,
  ChevronLeft,
  ChevronRight,
  MapPin,
  Truck,
  Map
} from 'lucide-react';

interface SidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
  activeView: string;
  onViewChange: (view: string) => void;
}

interface NavItem {
  id: string;
  label: string;
  icon: React.ElementType;
}

const navItems: NavItem[] = [
  { id: 'pyg', label: 'P&G Detallado', icon: FileText },
  { id: 'pyg-zonas', label: 'P&G Zonas y Municipios', icon: Map },
  { id: 'lejanias-comercial', label: 'Lejanías Comerciales', icon: MapPin },
  { id: 'lejanias-logistica', label: 'Lejanías Logísticas', icon: Truck },
];

export default function Sidebar({ isCollapsed, onToggle, activeView, onViewChange }: SidebarProps) {
  return (
    <div
      className={`
        fixed left-0 top-0 h-full bg-gray-900 text-gray-100
        transition-all duration-300 ease-in-out z-50
        ${isCollapsed ? 'w-16' : 'w-56'}
      `}
    >
      {/* Header */}
      <div className="h-12 border-b border-gray-800 flex items-center justify-between px-3">
        {!isCollapsed && (
          <span className="text-sm font-semibold text-gray-300">DxV Sistema</span>
        )}
        <button
          onClick={onToggle}
          className="p-1.5 hover:bg-gray-800 rounded transition-colors ml-auto"
          title={isCollapsed ? 'Expandir' : 'Colapsar'}
        >
          {isCollapsed ? (
            <ChevronRight size={16} className="text-gray-400" />
          ) : (
            <ChevronLeft size={16} className="text-gray-400" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="py-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={`
                w-full flex items-center gap-3 px-3 py-2.5 text-sm
                transition-colors
                ${isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }
              `}
              title={isCollapsed ? item.label : undefined}
            >
              <Icon size={18} className="flex-shrink-0" />
              {!isCollapsed && (
                <span className="truncate">{item.label}</span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer info */}
      {!isCollapsed && (
        <div className="absolute bottom-0 left-0 right-0 p-3 border-t border-gray-800">
          <div className="text-xs text-gray-500">
            <div>Modelo Distribución</div>
            <div className="text-gray-600">v2.0</div>
          </div>
        </div>
      )}
    </div>
  );
}
