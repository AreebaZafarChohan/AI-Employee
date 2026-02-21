'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AiStatus, AI_STATUS_VARIANTS } from '@/data/types/ai-status';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import { Cpu, Loader2, CheckCircle2, Sparkles } from 'lucide-react';

interface AiStatusCardProps {
  status: AiStatus;
  className?: string;
}

export function AiStatusCard({ status, className }: AiStatusCardProps) {
  const variant = AI_STATUS_VARIANTS[status.type];
  
  const getStatusConfig = () => {
    switch (status.type) {
      case 'Idle':
        return {
          icon: <CheckCircle2 className="h-10 w-10" />,
          gradient: 'from-green-400 to-emerald-500',
          bgGradient: 'from-green-500/10 to-emerald-500/10',
          glow: 'shadow-green-500/20',
          message: 'Ready for new tasks',
        };
      case 'Thinking':
        return {
          icon: <Loader2 className="h-10 w-10" />,
          gradient: 'from-blue-400 to-cyan-500',
          bgGradient: 'from-blue-500/10 to-cyan-500/10',
          glow: 'shadow-blue-500/20',
          message: status.message || 'Processing...',
        };
      case 'Planning':
        return {
          icon: <Cpu className="h-10 w-10" />,
          gradient: 'from-purple-400 to-pink-500',
          bgGradient: 'from-purple-500/10 to-pink-500/10',
          glow: 'shadow-purple-500/20',
          message: status.message || 'Creating plan...',
        };
    }
  };

  const config = getStatusConfig();

  return (
    <Card className={cn('overflow-hidden border-0 glass glow transition-all duration-500', config.glow, className)}>
      <div className={cn('absolute inset-0 bg-gradient-to-br opacity-50', config.bgGradient)} />
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 relative z-10">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          AI Status
        </CardTitle>
        <Badge
          variant={variant === 'default' ? 'secondary' : variant === 'processing' ? 'processing' : 'default'}
          className={cn('border-0 bg-gradient-to-r text-white shadow-lg', config.gradient)}
        >
          {status.type}
        </Badge>
      </CardHeader>
      <CardContent className="relative z-10">
        <motion.div
          className="flex items-center space-x-6"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <motion.div
            className={cn('p-4 rounded-2xl bg-gradient-to-br shadow-xl', config.gradient)}
            animate={{
              rotate: status.type === 'Thinking' ? 360 : 0,
              scale: status.type === 'Planning' ? [1, 1.1, 1] : 1,
            }}
            transition={{
              rotate: { duration: 2, repeat: Infinity, ease: 'linear' },
              scale: { duration: 1.5, repeat: Infinity, ease: 'easeInOut' },
            }}
          >
            <div className="text-white">
              {config.icon}
            </div>
          </motion.div>
          <div className="space-y-2">
            <motion.p
              key={status.type}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="text-2xl font-bold gradient-text"
            >
              {config.message}
            </motion.p>
            <p className="text-xs text-muted-foreground flex items-center gap-2">
              <span className="inline-block w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              Last updated: {new Date(status.updatedAt).toLocaleTimeString()}
              {status.startedAt && (
                <span className="text-muted-foreground/60">
                  • Started: {new Date(status.startedAt).toLocaleTimeString()}
                </span>
              )}
            </p>
          </div>
        </motion.div>
      </CardContent>
    </Card>
  );
}
