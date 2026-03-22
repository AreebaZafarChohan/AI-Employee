'use client';

import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Brain, Search } from 'lucide-react';
import { useMemorySearch, useMemoryDetail } from '@/hooks/use-memory';
import { MemorySearch } from '@/components/memory/memory-search';
import { MemoryResultList } from '@/components/memory/memory-result-list';
import { MemoryDetail } from '@/components/memory/memory-detail';
import { EmptyState } from '@/components/shared/empty-state';

export default function MemoryPage() {
  const [query, setQuery] = useState('');
  const [offset, setOffset] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { data, isLoading, isFetched } = useMemorySearch(query, 20, offset);
  const { data: detail } = useMemoryDetail(selectedId);

  const handleSearch = useCallback((q: string) => {
    setQuery(q);
    setOffset(0);
    setSelectedId(null);
  }, []);

  const hasResults = data && data.items.length > 0;
  const showEmpty = isFetched && !isLoading && !hasResults && query.trim().length > 0;
  const showHint = query.trim().length === 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex-1 p-6 space-y-6"
    >
      <h1 className="text-2xl font-bold">Memory Explorer</h1>

      <MemorySearch onSearch={handleSearch} isLoading={isLoading} />

      {showHint && (
        <EmptyState
          icon={Brain}
          title="Search agent memory"
          description="Try searching for topics like 'sales pipeline', 'weekly report', or 'client onboarding'."
        />
      )}

      {showEmpty && (
        <EmptyState
          icon={Search}
          title="No results found"
          description="Try different keywords or broaden your search. Suggestions: 'tasks', 'audit', 'briefing'."
        />
      )}

      {hasResults && (
        <MemoryResultList
          results={data.items}
          total={data.total}
          onSelect={setSelectedId}
          onPageChange={setOffset}
        />
      )}

      {detail && selectedId && (
        <MemoryDetail memory={detail} onClose={() => setSelectedId(null)} />
      )}
    </motion.div>
  );
}
