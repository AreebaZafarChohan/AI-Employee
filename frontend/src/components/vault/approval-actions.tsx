'use client';

import { Button } from '@/components/ui/button';
import { Check, X, Loader2 } from 'lucide-react';
import { useApproveFile, useRejectFile } from '@/hooks/use-vault';

interface ApprovalActionsProps {
  filename: string;
  size?: 'sm' | 'default';
}

export function ApprovalActions({ filename, size = 'sm' }: ApprovalActionsProps) {
  const approve = useApproveFile();
  const reject = useRejectFile();
  const isLoading = approve.isPending || reject.isPending;

  return (
    <div className="flex items-center gap-2">
      <Button
        size={size}
        onClick={() => approve.mutate(filename)}
        disabled={isLoading}
        className="bg-green-600 hover:bg-green-700 text-white"
      >
        {approve.isPending ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Check className="h-4 w-4" />
        )}
        <span className="ml-1">Approve</span>
      </Button>
      <Button
        size={size}
        variant="destructive"
        onClick={() => reject.mutate(filename)}
        disabled={isLoading}
      >
        {reject.isPending ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <X className="h-4 w-4" />
        )}
        <span className="ml-1">Reject</span>
      </Button>
    </div>
  );
}
