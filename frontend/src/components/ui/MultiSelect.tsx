'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { X } from 'lucide-react';

interface MultiSelectProps {
  options: string[];
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
  label?: string;
}

export function MultiSelect({
  options,
  value,
  onChange,
  placeholder = 'Seleccionar...',
  label,
}: MultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false);

  const toggleOption = (option: string) => {
    if (value.includes(option)) {
      onChange(value.filter((v) => v !== option));
    } else {
      onChange([...value, option]);
    }
  };

  const removeOption = (option: string) => {
    onChange(value.filter((v) => v !== option));
  };

  return (
    <div className="relative">
      {label && (
        <label className="block text-sm font-medium text-secondary-700 mb-2">
          {label}
        </label>
      )}

      <div className="relative">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className={cn(
            'w-full px-4 py-3 text-left bg-white border border-secondary-300 rounded-lg',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'transition-all duration-200 hover:border-secondary-400',
            'min-h-[48px]'
          )}
        >
          <div className="flex flex-wrap gap-2">
            {value.length === 0 ? (
              <span className="text-secondary-400">{placeholder}</span>
            ) : (
              value.map((item) => (
                <span
                  key={item}
                  className="inline-flex items-center gap-1 px-2 py-1 bg-primary-100 text-primary-700 rounded text-sm font-medium"
                >
                  {item.toUpperCase()}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeOption(item);
                    }}
                    className="hover:bg-primary-200 rounded-full p-0.5 transition-colors"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))
            )}
          </div>
        </button>

        {isOpen && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setIsOpen(false)}
            />
            <div className="absolute z-20 w-full mt-2 bg-white border border-secondary-200 rounded-lg shadow-large max-h-60 overflow-auto">
              {options.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => toggleOption(option)}
                  className={cn(
                    'w-full px-4 py-3 text-left hover:bg-primary-50 transition-colors',
                    value.includes(option) && 'bg-primary-50 text-primary-700 font-medium'
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span>{option.toUpperCase()}</span>
                    {value.includes(option) && (
                      <span className="text-primary-600">✓</span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
