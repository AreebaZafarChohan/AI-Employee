'use client';

import { Header } from '@/components/shared/header';
import { ErrorBoundary } from '@/components/shared/error-boundary';
import { VaultTable } from '@/components/vault/vault-table';
import { RiskBadge } from '@/components/vault/risk-badge';
import { StatusBadge } from '@/components/vault/status-badge';
import { useGmailPending } from '@/hooks/use-vault';
import { formatRelativeTime, truncateText } from '@/lib/utils';
import { Mail } from 'lucide-react';
import { motion } from 'framer-motion';

export default function GmailDashboardPage() {
  const { data, isLoading, isError } = useGmailPending();

  return (
    <div className="flex flex-col min-h-screen">
      <Header title="Gmail" />
      <main className="flex-1 bg-background">
        <div className="container mx-auto py-8 px-4">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <h1 className="text-4xl font-bold gradient-text flex items-center gap-3">
              <Mail className="h-8 w-8" />
              Gmail Dashboard
            </h1>
            <p className="text-muted-foreground mt-1 ml-11">
              Pending email items awaiting review.
            </p>
          </motion.div>

          <ErrorBoundary>
            <VaultTable
              title="Pending Gmail Items"
              icon={<Mail className="h-5 w-5 text-red-400" />}
              items={data}
              isLoading={isLoading}
              isError={isError}
              emptyMessage="No pending email items."
              columns={[
                {
                  key: 'from',
                  label: 'From',
                  render: (item) => (
                    <span className="font-medium">
                      {item.metadata.from ?? item.metadata.sender ?? '—'}
                    </span>
                  ),
                },
                {
                  key: 'subject',
                  label: 'Subject',
                  render: (item) => (
                    <span className="font-medium">
                      {truncateText(item.metadata.subject ?? item.title, 60)}
                    </span>
                  ),
                },
                {
                  key: 'snippet',
                  label: 'Snippet',
                  render: (item) => (
                    <span className="text-muted-foreground">
                      {truncateText(item.metadata.snippet ?? item.body_preview, 80)}
                    </span>
                  ),
                },
                {
                  key: 'risk',
                  label: 'Risk',
                  render: (item) => <RiskBadge level={item.risk_level} />,
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
