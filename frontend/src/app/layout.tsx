'use client';

import { Inter } from 'next/font/google';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from '@/components/ui/toaster';
import '@/styles/globals.css';
import { makeQueryClient } from '@/hooks/use-api-client';
import { ThemeProvider } from '@/components/shared/theme-provider';
import { WebSocketProvider } from '@/hooks/use-websocket';
import { ConnectionStatus } from '@/components/shared/connection-status';

const inter = Inter({ subsets: ['latin'] });

// Create a new QueryClient for each client render
let queryClient: ReturnType<typeof makeQueryClient> | null = null;

function getQueryClient() {
  if (typeof window === 'undefined') {
    return makeQueryClient();
  } else {
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
      <body className={`${inter.className} min-h-screen bg-background antialiased overflow-x-hidden`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <QueryClientProvider client={queryClient}>
            <WebSocketProvider>
            <ConnectionStatus />
            <div className="relative flex min-h-screen flex-col">
              {/* Background Glows */}
              <div className="fixed inset-0 z-[-1] overflow-hidden pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-primary/20 blur-[120px] animate-pulse" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-accent/20 blur-[120px] animate-pulse" style={{ animationDelay: '2s' }} />
              </div>
              
              <div className="relative z-10">
                {children}
              </div>
            </div>
            <Toaster />
            <ReactQueryDevtools initialIsOpen={false} />
            </WebSocketProvider>
          </QueryClientProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
