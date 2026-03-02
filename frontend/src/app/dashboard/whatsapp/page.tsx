'use client';

import { Header } from '@/components/shared/header';
import { ErrorBoundary } from '@/components/shared/error-boundary';
import { VaultTable } from '@/components/vault/vault-table';
import { RiskBadge } from '@/components/vault/risk-badge';
import { StatusBadge } from '@/components/vault/status-badge';
import { useWhatsAppPending } from '@/hooks/use-vault';
import { formatRelativeTime, truncateText } from '@/lib/utils';
import { MessageCircle } from 'lucide-react';
import { motion } from 'framer-motion';

export default function WhatsAppDashboardPage() {
  const { data, isLoading, isError } = useWhatsAppPending();

  return (
    <div className="flex flex-col min-h-screen">
      <Header title="WhatsApp" />
      <main className="flex-1 bg-background">
        <div className="container mx-auto py-8 px-4">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <h1 className="text-4xl font-bold gradient-text flex items-center gap-3">
              <MessageCircle className="h-8 w-8" />
              WhatsApp Dashboard
            </h1>
            <p className="text-muted-foreground mt-1 ml-11">
              Pending WhatsApp messages awaiting review.
            </p>
          </motion.div>

          <ErrorBoundary>
            <VaultTable
              title="Pending WhatsApp Items"
              icon={<MessageCircle className="h-5 w-5 text-emerald-400" />}
              items={data}
              isLoading={isLoading}
              isError={isError}
              emptyMessage="No pending WhatsApp messages."
              columns={[
                {
                  key: 'sender',
                  label: 'Sender',
                  render: (item) => (
                    <span className="font-medium">
                      {item.metadata.sender ?? '—'}
                    </span>
                  ),
                },
                {
                  key: 'message_preview',
                  label: 'Message Preview',
                  render: (item) => (
                    <span className="text-muted-foreground">
                      {truncateText(item.metadata.message_preview ?? item.body_preview, 80)}
                    </span>
                  ),
                },
                {
                  key: 'risk',
                  label: 'Risk Level',
                  render: (item) => <RiskBadge level={item.risk_level} />,
                },
                {
                  key: 'time',
                  label: 'Received',
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
