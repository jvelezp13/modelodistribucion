import { Card } from './Card';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'default';
}

export function MetricCard({
  label,
  value,
  subtitle,
  icon,
  trend,
  trendValue,
  variant = 'default',
}: MetricCardProps) {
  const variantColors = {
    primary: 'border-l-primary-500',
    success: 'border-l-success',
    warning: 'border-l-warning',
    danger: 'border-l-danger',
    default: 'border-l-secondary-300',
  };

  return (
    <Card variant="elevated" className={cn('border-l-4', variantColors[variant])}>
      <div className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-secondary-600 uppercase tracking-wide">
              {label}
            </p>
            <p className="mt-2 text-3xl font-bold text-secondary-900">
              {value}
            </p>
            {subtitle && (
              <p className="mt-1 text-sm text-secondary-500">
                {subtitle}
              </p>
            )}
            {trendValue && (
              <div className="mt-2 flex items-center gap-1">
                {trend === 'up' && (
                  <span className="text-success text-sm">↑ {trendValue}</span>
                )}
                {trend === 'down' && (
                  <span className="text-danger text-sm">↓ {trendValue}</span>
                )}
                {trend === 'neutral' && (
                  <span className="text-secondary-500 text-sm">→ {trendValue}</span>
                )}
              </div>
            )}
          </div>
          {icon && (
            <div className="ml-4 p-3 bg-primary-50 rounded-lg text-primary-600">
              {icon}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
