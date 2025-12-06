import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { QueryProvider } from '@/lib/queryClient';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Sistema DxV Multimarcas',
  description: 'Modelo de Distribución y Ventas - Simulación y Optimización',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body className={inter.className}>
        <QueryProvider>
          <div className="min-h-screen bg-gradient-to-br from-white via-primary-50/30 to-white">
            {children}
          </div>
        </QueryProvider>
      </body>
    </html>
  );
}
