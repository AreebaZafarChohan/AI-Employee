'use client';

import { Header } from '@/components/shared/header';
import { ErrorBoundary } from '@/components/shared/error-boundary';
import { VaultTable } from '@/components/vault/vault-table';
import { RiskBadge } from '@/components/vault/risk-badge';
import { StatusBadge } from '@/components/vault/status-badge';
import { useLinkedInPending } from '@/hooks/use-vault';
import { formatRelativeTime, truncateText } from '@/lib/utils';
import { Linkedin } from 'lucide-react';
import { motion } from 'framer-motion';

export default function LinkedInDashboardPage() {
  const { data, isLoading, isError } = useLinkedInPending();

  return (
    <div className="flex flex-col min-h-screen">
      <Header title="LinkedIn" />
      <main className="flex-1 bg-background">
        <div className="container mx-auto py-8 px-4">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <h1 className="text-4xl font-bold gradient-text flex items-center gap-3">
              <Linkedin className="h-8 w-8" />
              LinkedIn Dashboard
            </h1>
            <p className="text-muted-foreground mt-1 ml-11">
              DMs, mentions, and draft posts awaiting review.
            </p>
          </motion.div>

          <ErrorBoundary>
            <VaultTable
              title="Pending LinkedIn Items"
              icon={<Linkedin className="h-5 w-5 text-blue-400" />}
              items={data}
              isLoading={isLoading}
              isError={isError}
              emptyMessage="No pending LinkedIn items."
              columns={[
                {
                  key: 'from',
                  label: 'From',
                  render: (item) => (
                    <span className="font-medium">
                      {item.metadata.sender ?? item.metadata.from ?? '—'}
                    </span>
                  ),
                },
                {
                  key: 'title',
                  label: 'Title',
                  render: (item) => (
                    <span className="font-medium">{truncateText(item.title, 60)}</span>
                  ),
                },
                {
                  key: 'snippet',
                  label: 'Preview',
                  render: (item) => (
                    <span className="text-muted-foreground">
                      {truncateText(item.body_preview || item.metadata.snippet || '', 80)}
                    </span>
                  ),
                },
                {
                  key: 'risk',
                  label: 'Risk',
                  render: (item) => <RiskBadge level={item.risk_level} />,
                },
                {
                  key: 'time',
                  label: 'Time',
                  render: (item) => (
                    <span className="text-xs text-muted-foreground">
                      {formatRelativeTime(new Date(item.created_at))}
                    </span>
                  ),
                },
                {
                  key: 'status',
                  label: 'Status',
                  render: (item) => <StatusBadge status={item.status} />,
                },
              ]}
            />
          </ErrorBoundary>
        </div>
      </main>
    </div>
  );
}
