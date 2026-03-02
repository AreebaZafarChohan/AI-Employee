/**
 * Approval Card Component
 * Displays pending approval items with approve/reject actions
 */

'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { useApprovalStore } from '@/store/approval-store';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import {
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Mail,
  MessageSquare,
  Linkedin,
  FileText,
  DollarSign,
  FileImage,
} from 'lucide-react';

interface ApprovalCardProps {
  approval: ReturnType<typeof useApprovalStore.getState>['items'][0];
  className?: string;
}

const TYPE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  gmail: Mail,
  whatsapp: MessageSquare,
  linkedin: Linkedin,
  file: FileText,
  payment: DollarSign,
  post: FileImage,
};

const RISK_COLORS = {
  low: 'text-green-600 bg-green-100 dark:bg-green-900/30 border-green-200',
  medium: 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30 border-yellow-200',
  high: 'text-orange-600 bg-orange-100 dark:bg-orange-900/30 border-orange-200',
  critical: 'text-red-600 bg-red-100 dark:bg-red-900/30 border-red-200',
};

const STATUS_COLORS = {
  pending: 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30',
  approved: 'text-green-600 bg-green-100 dark:bg-green-900/30',
  rejected: 'text-red-600 bg-red-100 dark:bg-red-900/30',
};

export function ApprovalCard({ approval, className }: ApprovalCardProps) {
  const { approveItem, rejectItem } = useApprovalStore();
  const [isApproving, setIsApproving] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);
  const [showRejectReason, setShowRejectReason] = useState(false);
  const [rejectReason, setRejectReason] = useState('');

  const TypeIcon = TYPE_ICONS[approval.type] || FileText;

  const handleApprove = async () => {
    setIsApproving(true);
    try {
      await approveItem(approval.id);
    } finally {
      setIsApproving(false);
    }
  };

  const handleReject = async () => {
    if (showRejectReason && !rejectReason.trim()) return;
    
    setIsRejecting(true);
    try {
      await rejectItem(approval.id, rejectReason || undefined);
      setShowRejectReason(false);
      setRejectReason('');
    } finally {
      setIsRejecting(false);
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / 3600000);
    
    if (hours < 1) return 'Just now';
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      layout
    >
      <Card className={cn('overflow-hidden transition-all duration-300 hover:shadow-lg', className)}>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-3">
              <div className={cn('p-2 rounded-lg', RISK_COLORS[approval.riskLevel])}>
                <TypeIcon className="h-5 w-5" />
              </div>
              <div>
                <CardTitle className="text-base">{approval.title}</CardTitle>
                <p className="text-sm text-muted-foreground">{approval.description}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge
                variant="outline"
                className={cn('capitalize', STATUS_COLORS[approval.status])}
              >
                {approval.status}
              </Badge>
              <Badge
                variant="outline"
                className={cn('capitalize border', RISK_COLORS[approval.riskLevel])}
              >
                {approval.riskLevel} risk
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Metadata */}
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            {approval.sender && (
              <div className="flex items-center gap-1">
                <Mail className="h-4 w-4" />
                <span>{approval.sender}</span>
              </div>
            )}
            <div className="flex items-center gap-1">
              <Clock className="h-4 w-4" />
              <span>{formatTimeAgo(approval.createdAt)}</span>
            </div>
            {approval.expiresAt && (
              <div className="flex items-center gap-1">
                <AlertTriangle className="h-4 w-4" />
                <span>Expires in {Math.floor((new Date(approval.expiresAt).getTime() - Date.now()) / 3600000)}h</span>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          {approval.status === 'pending' && (
            <div className="flex gap-2 pt-3 border-t">
              <Button
                onClick={handleApprove}
                disabled={isApproving || isRejecting}
                className="flex-1 bg-green-600 hover:bg-green-700"
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                {isApproving ? 'Approving...' : 'Approve'}
              </Button>
              {showRejectReason ? (
                <div className="flex-1 flex gap-2">
                  <Textarea
                    value={rejectReason}
                    onChange={(e) => setRejectReason(e.target.value)}
                    placeholder="Reason for rejection..."
                    className="flex-1 min-h-[40px]"
                    autoFocus
                  />
                  <Button
                    variant="destructive"
                    onClick={handleReject}
                    disabled={isApproving || isRejecting || !rejectReason.trim()}
                  >
                    Confirm
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowRejectReason(false);
                      setRejectReason('');
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              ) : (
                <>
                  <Button
                    variant="outline"
                    onClick={() => setShowRejectReason(true)}
                    disabled={isApproving || isRejecting}
                    className="flex-1"
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    Reject
                  </Button>
                </>
              )}
            </div>
          )}

          {/* Status Display for non-pending */}
          {approval.status !== 'pending' && (
            <div className={cn('p-3 rounded-md', STATUS_COLORS[approval.status])}>
              <p className="text-sm font-medium">
                {approval.status === 'approved' ? '✓ Approved' : '✗ Rejected'}
              </p>
              {approval.status === 'rejected' && (
                <p className="text-sm mt-1">
                  {approval.metadata?.rejectReason || 'No reason provided'}
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
