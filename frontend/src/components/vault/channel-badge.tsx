'use client';

import { Badge } from '@/components/ui/badge';
import { MessageCircle, Mail, Linkedin, FileText, CircleDot } from 'lucide-react';
import type { VaultChannel } from '@/types/vault';

const channelConfig: Record<VaultChannel, { label: string; className: string; Icon: React.ElementType }> = {
  whatsapp: {
    label: 'WhatsApp',
    className: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    Icon: MessageCircle,
  },
  gmail: {
    label: 'Gmail',
    className: 'bg-red-500/20 text-red-400 border-red-500/30',
    Icon: Mail,
  },
  linkedin: {
    label: 'LinkedIn',
    className: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    Icon: Linkedin,
  },
  plan: {
    label: 'Plan',
    className: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    Icon: FileText,
  },
  general: {
    label: 'General',
    className: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
    Icon: CircleDot,
  },
};

interface ChannelBadgeProps {
  channel: VaultChannel;
}

export function ChannelBadge({ channel }: ChannelBadgeProps) {
  const config = channelConfig[channel] ?? channelConfig.general;
  const { Icon } = config;
  return (
    <Badge variant="outline" className={`${config.className} gap-1`}>
      <Icon className="h-3 w-3" />
      {config.label}
    </Badge>
  );
}
