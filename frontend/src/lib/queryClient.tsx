'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Mantener datos en caché por 5 minutos
            staleTime: 5 * 60 * 1000,
            // Mantener en caché por 30 minutos
            gcTime: 30 * 60 * 1000,
            // No refetch automático al enfocar la ventana
            refetchOnWindowFocus: false,
            // Reintentar una vez en caso de error
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
