'use client';

import { Inter } from 'next/font/google';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from '@/components/ui/toaster';
import '@/styles/globals.css';
import { makeQueryClient } from '@/hooks/use-api-client';

const inter = Inter({ subsets: ['latin'] });

// Create a new QueryClient for each client render
// In a real app, you might want to persist this across renders
let queryClient: ReturnType<typeof makeQueryClient> | null = null;

function getQueryClient() {
  if (typeof window === 'undefined') {
    // Server: always create a new query client
    return makeQueryClient();
  } else {
    // Browser: make a new query client if we don't already have one
    if (!queryClient) {
      queryClient = makeQueryClient();
    }
    return queryClient;
  }
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const queryClient = getQueryClient();

  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <QueryClientProvider client={queryClient}>
          {children}
          <Toaster />
          <ReactQueryDevtools initialIsOpen={false} />
        </QueryClientProvider>
      </body>
    </html>
  );
}
