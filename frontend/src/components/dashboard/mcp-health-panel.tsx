'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { Server } from 'lucide-react';
import { API_BASE_URL } from '@/lib/api-config';

interface McpServer {
  name: string;
  url: string;
  status: 'healthy' | 'unhealthy' | 'unknown';
  latencyMs: number | null;
  lastChecked: string;
  error?: string;
}

interface McpHealthData {
  servers: McpServer[];
  summary: { total: number; healthy: number; unhealthy: number };
}

export function McpHealthPanel() {
  const [data, setData] = useState<McpHealthData | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/system/mcp-health`);
        if (res.ok) {
          const json = await res.json();
          setData(json.data);
        }
      } catch { /* silent */ }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Server className="h-5 w-5" />
          MCP Server Health
          {data && (
            <Badge variant="outline" className="ml-auto text-xs">
              {data.summary.healthy}/{data.summary.total} online
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {!data ? (
          <p className="text-sm text-muted-foreground">Loading...</p>
        ) : (
          data.servers.map((server) => (
            <div
              key={server.name}
              className="flex items-center justify-between p-2 rounded-lg border"
            >
              <div className="flex items-center gap-2">
                <div
                  className={cn(
                    'h-2.5 w-2.5 rounded-full',
                    server.status === 'healthy'
                      ? 'bg-green-500'
                      : 'bg-red-500'
                  )}
                />
                <span className="text-sm font-medium">{server.name}</span>
              </div>
              <div className="flex items-center gap-2">
                {server.latencyMs !== null && (
                  <span className="text-xs text-muted-foreground">
                    {server.latencyMs}ms
                  </span>
                )}
                <Badge
                  variant="outline"
                  className={cn(
                    'text-xs capitalize',
                    server.status === 'healthy'
                      ? 'text-green-600 border-green-200'
                      : 'text-red-600 border-red-200'
                  )}
                >
                  {server.status}
                </Badge>
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
