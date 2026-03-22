'use client';

import { X, Bot, FileText, Calendar, Hash } from 'lucide-react';
import type { MemoryItem } from '@/hooks/use-memory';

interface MemoryDetailProps {
  memory: MemoryItem;
  onClose: () => void;
}

export function MemoryDetail({ memory, onClose }: MemoryDetailProps) {
  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md border-l bg-background shadow-xl flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-5 py-4">
        <h2 className="text-lg font-semibold">Memory Detail</h2>
        <button
          onClick={onClose}
          className="rounded-md p-1.5 hover:bg-muted transition-colors"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">
        {/* Similarity score */}
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary">
            {(memory.similarityScore * 100).toFixed(0)}% match
          </span>
        </div>

        {/* Content */}
        <div>
          <h3 className="text-sm font-medium text-muted-foreground mb-1">Content</h3>
          <p className="text-sm whitespace-pre-wrap">{memory.content}</p>
        </div>

        {/* Meta */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="flex items-center gap-2 text-muted-foreground">
            <FileText className="h-4 w-4" />
            <div>
              <p className="text-xs text-muted-foreground">Source</p>
              <p className="text-foreground">{memory.source}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Bot className="h-4 w-4" />
            <div>
              <p className="text-xs text-muted-foreground">Agent</p>
              <p className="text-foreground">{memory.agentName}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Calendar className="h-4 w-4" />
            <div>
              <p className="text-xs text-muted-foreground">Created</p>
              <p className="text-foreground">
                {new Date(memory.createdAt).toLocaleDateString()}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Hash className="h-4 w-4" />
            <div>
              <p className="text-xs text-muted-foreground">ID</p>
              <p className="text-foreground font-mono text-xs truncate">{memory.id}</p>
            </div>
          </div>
        </div>

        {/* Metadata */}
        {memory.metadata && Object.keys(memory.metadata).length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Metadata</h3>
            <div className="rounded-lg border bg-muted/30 p-3">
              <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                {JSON.stringify(memory.metadata, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
