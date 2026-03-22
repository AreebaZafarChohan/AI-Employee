import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';
import { Card3D } from '@/components/shared/card-3d';

interface StatsCardProps {
  title: string;
  value: number | string;
  icon: LucideIcon;
  trend?: {
    value: number;
    label: string;
    isPositive: boolean;
  };
  color: 'purple' | 'blue' | 'green' | 'orange' | 'red';
  className?: string;
}

const COLOR_VARIANTS = {
  purple: 'from-purple-500/20 to-indigo-500/20 text-purple-500 border-purple-500/20',
  blue: 'from-blue-500/20 to-cyan-500/20 text-blue-500 border-blue-500/20',
  green: 'from-green-500/20 to-emerald-500/20 text-green-500 border-green-500/20',
  orange: 'from-orange-500/20 to-amber-500/20 text-orange-500 border-orange-500/20',
  red: 'from-red-500/20 to-rose-500/20 text-red-500 border-red-500/20',
};

export function StatsCard({
  title,
  value,
  icon: Icon,
  trend,
  color,
  className,
}: StatsCardProps) {
  const colorClass = COLOR_VARIANTS[color];

  return (
    <Card3D>
      <Card className={cn(
        'relative overflow-hidden border-white/10 bg-background/50 backdrop-blur-md transition-all duration-300 group hover:border-primary/50',
        className
      )}>
        {/* Background Gradient Glow */}
        <div className={cn(
          'absolute -right-10 -top-10 h-32 w-32 rounded-full bg-gradient-to-br blur-3xl opacity-20 group-hover:opacity-40 transition-opacity',
          colorClass
        )} />
        
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 relative z-10">
          <CardTitle className="text-sm font-medium text-muted-foreground group-hover:text-foreground transition-colors">
            {title}
          </CardTitle>
          <div className={cn(
            'p-2.5 rounded-xl bg-gradient-to-br border shadow-inner transition-transform duration-300 group-hover:scale-110 group-hover:rotate-6',
            colorClass
          )}>
            <Icon className="h-4 w-4" />
          </div>
        </CardHeader>
        
        <CardContent className="relative z-10">
          <motion.div 
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            className="text-3xl font-bold tracking-tight"
          >
            {value}
          </motion.div>
          {trend && (
            <div className="flex items-center gap-1.5 mt-2">
              <span className={cn(
                'flex items-center text-xs font-bold px-1.5 py-0.5 rounded-full',
                trend.isPositive ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'
              )}>
                {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
              </span>
              <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
                {trend.label}
              </span>
            </div>
          )}
        </CardContent>
      </Card>
    </Card3D>
  );
}
