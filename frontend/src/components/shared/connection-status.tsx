'use client';

import { useWebSocket } from '@/hooks/use-websocket';
import { Wifi, WifiOff } from 'lucide-react';

export function ConnectionStatus() {
  const { connectionState } = useWebSocket();

  if (connectionState === 'connected') return null;

  const config = {
    connecting: { text: 'Connecting...', bg: 'bg-yellow-500/90', icon: Wifi },
    disconnected: { text: 'Disconnected — Reconnecting...', bg: 'bg-red-500/90', icon: WifiOff },
    error: { text: 'Connection error — Retrying...', bg: 'bg-red-500/90', icon: WifiOff },
  }[connectionState];

  const Icon = config.icon;

  return (
    <div className={`fixed top-0 left-0 right-0 z-[100] ${config.bg} text-white text-center py-1.5 text-sm font-medium flex items-center justify-center gap-2`}>
      <Icon className="h-4 w-4" />
      {config.text}
    </div>
  );
}
