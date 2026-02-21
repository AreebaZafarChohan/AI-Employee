'use client';

import { EnvironmentInfo } from '@/components/settings/environment-info';
import { ConfigDisplay } from '@/components/settings/config-display';
import { Header } from '@/components/shared/header';

export default function SettingsPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header title="Settings" />
      <main className="flex-1 bg-background p-8">
        <div className="container mx-auto">
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-2">Settings</h1>
            <p className="text-muted-foreground">
              View system information and configuration settings
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <EnvironmentInfo />
            <ConfigDisplay />
          </div>
        </div>
      </main>
    </div>
  );
}
