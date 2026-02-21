'use client';

import { useState } from 'react';
import { NeedsActionList } from '@/components/needs-action/needs-action-list';
import { NeedsActionDetailPanel } from '@/components/needs-action/needs-action-detail-panel';
import { Header } from '@/components/shared/header';
import { NeedsActionItem } from '@/data/types/needs-action';
import { motion } from 'framer-motion';

export default function NeedsActionPage() {
  const [selectedItem, setSelectedItem] = useState<NeedsActionItem | null>(null);
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  const handleItemSelected = (item: NeedsActionItem) => {
    setSelectedItem(item);
    setIsPanelOpen(true);
  };

  const handleClosePanel = () => {
    setIsPanelOpen(false);
    setTimeout(() => setSelectedItem(null), 300);
  };

  const handleGeneratePlan = (itemId: string) => {
    // Mock handler - will be connected to backend in Silver tier
    console.log('Generating plan for item:', itemId);
    alert(`Plan generation initiated for item: ${itemId}\n\n(This is a mock action - will be connected to backend in Silver tier)`);
    handleClosePanel();
  };

  return (
    <div className="flex flex-col min-h-screen">
      <Header title="Needs Action" />
      <main className="flex-1 bg-background">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="container mx-auto py-8 px-4"
        >
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-2">Action Items</h1>
            <p className="text-muted-foreground">
              Review and respond to items requiring your attention
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* List View - Full width on mobile, 2/3 on desktop */}
            <div className="lg:col-span-2">
              <NeedsActionList
                selectedId={selectedItem?.id}
                onItemSelected={handleItemSelected}
              />
            </div>

            {/* Detail View - Hidden on mobile, shown as panel on desktop */}
            <div className="hidden lg:block lg:col-span-1">
              {selectedItem && (
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <NeedsActionDetailPanel
                    item={selectedItem}
                    isOpen={true}
                    onClose={handleClosePanel}
                    onGeneratePlan={handleGeneratePlan}
                  />
                </motion.div>
              )}
            </div>
          </div>
        </motion.div>

        {/* Mobile detail panel (overlay) */}
        {selectedItem && (
          <NeedsActionDetailPanel
            item={selectedItem}
            isOpen={isPanelOpen}
            onClose={handleClosePanel}
            onGeneratePlan={handleGeneratePlan}
          />
        )}
      </main>
    </div>
  );
}
