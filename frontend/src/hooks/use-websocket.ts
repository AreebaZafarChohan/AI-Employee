'use client';

import { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { getWebSocketClient, type ConnectionState } from '@/lib/websocket-client';
import React from 'react';

interface WebSocketContextValue {
  connectionState: ConnectionState;
  subscribe: (event: string, handler: (data: unknown) => void) => void;
  unsubscribe: (event: string, handler: (data: unknown) => void) => void;
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const clientRef = useRef(getWebSocketClient());

  useEffect(() => {
    const client = clientRef.current;
    const unsub = client.onStateChange(setConnectionState);
    client.connect();
    return () => {
      unsub();
      client.disconnect();
    };
  }, []);

  const subscribe = useCallback((event: string, handler: (data: unknown) => void) => {
    clientRef.current.subscribe(event, handler);
  }, []);

  const unsubscribe = useCallback((event: string, handler: (data: unknown) => void) => {
    clientRef.current.unsubscribe(event, handler);
  }, []);

  return React.createElement(
    WebSocketContext.Provider,
    { value: { connectionState, subscribe, unsubscribe } },
    children
  );
}

export function useWebSocket() {
  const ctx = useContext(WebSocketContext);
  if (!ctx) throw new Error('useWebSocket must be used within WebSocketProvider');
  return ctx;
}
