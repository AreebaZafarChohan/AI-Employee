'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Bot, FileText } from 'lucide-react';
import { Pagination } from '@/components/shared/pagination';
import type { MemoryItem } from '@/hooks/use-memory';

interface MemoryResultListProps {
  results: MemoryItem[];
  total: number;
  onSelect: (id: string) => void;
  onPageChange: (offset: number) => void;
}

export function MemoryResultList({ results, total, onSelect, onPageChange }: MemoryResultListProps) {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const sorted = [...results].sort((a, b) => b.similarityScore - a.similarityScore);

  function handlePageChange(newPage: number) {
    setPage(newPage);
    onPageChange((newPage - 1) * pageSize);
  }

  function handlePageSizeChange(size: number) {
    setPageSize(size);
    setPage(1);
    onPageChange(0);
  }

  return (
    <motion.div
      className="flex flex-col gap-2"
      variants={{ hidden: {}, show: { transition: { staggerChildren: 0.04 } } }}
      initial="hidden"
      animate="show"
    >
      {sorted.map((item) => (
        <motion.button
          variants={{ hidden: { opacity: 0, y: 8 }, show: { opacity: 1, y: 0 } }}
          key={item.id}
          onClick={() => onSelect(item.id)}
          className="w-full text-left rounded-lg border p-4 hover:bg-muted/50 transition-colors"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <p className="text-sm line-clamp-2">{item.content}</p>
              <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <FileText className="h-3 w-3" />
                  {item.source}
                </span>
                <span className="flex items-center gap-1">
                  <Bot className="h-3 w-3" />
                  {item.agentName}
                </span>
              </div>
            </div>
            <span className="shrink-0 rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
              {(item.similarityScore * 100).toFixed(0)}%
            </span>
          </div>
        </motion.button>
      ))}

      <Pagination
        page={page}
        pageSize={pageSize}
        total={total}
        onPageChange={handlePageChange}
        onPageSizeChange={handlePageSizeChange}
      />
    </motion.div>
  );
}
