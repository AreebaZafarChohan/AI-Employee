'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.push('/dashboard');
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold gradient-text mb-4">AI Employee</h1>
        <p className="text-muted-foreground">Redirecting to dashboard...</p>
      </div>
    </div>
  );
}
