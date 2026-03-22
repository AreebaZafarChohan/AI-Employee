import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  Mail,
  MessageSquare,
  Linkedin,
  FileText,
  Settings,
  ChevronRight,
  Target,
  Zap,
  Bot,
  Goal,
  Brain,
  DollarSign,
  Wrench,
  Activity,
  Eye,
  Sparkles,
  ScrollText,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { useApprovalStore } from '@/store/approval-store';

const navigation = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
    description: 'Command Center',
    color: 'text-blue-500',
  },
  {
    name: 'AI Employee',
    href: '/ai-employee',
    icon: Bot,
    description: 'Autonomous Control',
    color: 'text-cyan-500',
  },
  {
    name: 'Gmail',
    href: '/gmail',
    icon: Mail,
    description: 'Email Management',
    color: 'text-red-500',
  },
  {
    name: 'WhatsApp',
    href: '/whatsapp',
    icon: MessageSquare,
    description: 'Messaging',
    color: 'text-green-500',
  },
  {
    name: 'LinkedIn',
    href: '/linkedin',
    icon: Linkedin,
    description: 'Professional Network',
    color: 'text-blue-600',
  },
  {
    name: 'Sales',
    href: '/sales',
    icon: Target,
    description: 'AI Sales Pipeline',
    color: 'text-purple-500',
  },
  {
    name: 'Files',
    href: '/files',
    icon: FileText,
    description: 'Document Manager',
    color: 'text-orange-500',
  },
  {
    name: 'AI Agent',
    href: '/ai-agent',
    icon: Sparkles,
    description: 'Generate & Post Content',
    color: 'text-violet-500',
  },
  {
    name: 'Watchers',
    href: '/watchers',
    icon: Eye,
    description: 'Service Monitoring',
    color: 'text-teal-500',
  },
  {
    name: 'Live Logs',
    href: '/live-logs',
    icon: ScrollText,
    description: 'Real-time Activity',
    color: 'text-pink-500',
  },
  {
    name: 'Agents',
    href: '/agents',
    icon: Bot,
    description: 'AI Agent Control',
    color: 'text-cyan-500',
  },
  {
    name: 'Goals',
    href: '/goals',
    icon: Goal,
    description: 'Strategic Goals',
    color: 'text-amber-500',
  },
  {
    name: 'Memory',
    href: '/memory',
    icon: Brain,
    description: 'AI Memory Explorer',
    color: 'text-pink-500',
  },
  {
    name: 'Costs',
    href: '/costs',
    icon: DollarSign,
    description: 'Usage & Costs',
    color: 'text-emerald-500',
  },
  {
    name: 'Tools',
    href: '/tools',
    icon: Wrench,
    description: 'Tool Monitor',
    color: 'text-indigo-500',
  },
  {
    name: 'Intelligence',
    href: '/intelligence',
    icon: Activity,
    description: 'System Intelligence',
    color: 'text-rose-500',
  },
];

const bottomNavigation = [
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings,
    color: 'text-slate-500',
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { stats } = useApprovalStore();

  return (
    <motion.aside 
      initial={{ x: -100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className="fixed left-4 top-4 bottom-4 w-64 glass rounded-3xl z-50 overflow-hidden flex flex-col shadow-2xl border-white/10 dark:bg-black/40 bg-white/40"
    >
      <div className="flex h-full flex-col">
        {/* Logo Section */}
        <div className="p-6">
          <Link href="/dashboard" className="flex items-center gap-3 group">
            <div className="relative">
              <div className="absolute inset-0 bg-primary/20 blur-lg rounded-full group-hover:bg-primary/40 transition-colors" />
              <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent shadow-lg group-hover:scale-110 transition-transform duration-300">
                <Zap className="h-5 w-5 text-white animate-pulse" />
              </div>
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight">AI Employee</h1>
              <div className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
                <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Active Agent</p>
              </div>
            </div>
          </Link>
        </div>

        {/* Main Navigation */}
        <nav className="flex-1 px-4 space-y-1 overflow-y-auto py-2 custom-scrollbar">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;

            return (
              <Link key={item.name} href={item.href}>
                <div
                  className={cn(
                    'group relative flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-all duration-300 mb-1 cursor-pointer overflow-hidden',
                    isActive
                      ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/20 scale-[1.02]'
                      : 'text-muted-foreground hover:bg-white/10 hover:text-foreground'
                  )}
                >
                  <Icon className={cn('h-5 w-5 relative z-10 transition-transform duration-300 group-hover:scale-110', !isActive && item.color)} />
                  <div className="relative z-10">
                    <p className="font-semibold leading-none">{item.name}</p>
                    <p className={cn('text-[10px] mt-0.5 opacity-70', isActive ? 'text-white' : 'text-muted-foreground')}>
                      {item.description}
                    </p>
                  </div>
                  {isActive && (
                    <motion.div 
                      layoutId="sidebar-active"
                      className="absolute inset-0 bg-gradient-to-r from-primary to-accent opacity-90"
                    />
                  )}
                </div>
              </Link>
            );
          })}
        </nav>

        {/* Stats Panel */}
        <div className="px-4 mb-4">
          <div className="rounded-2xl bg-black/5 dark:bg-white/5 p-4 border border-white/5">
            <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-3 px-1">Vault Status</p>
            <div className="space-y-2.5">
              {[
                { label: 'Pending', count: stats.pending, color: 'bg-orange-500' },
                { label: 'Approved', count: stats.approved, color: 'bg-green-500' },
                { label: 'Rejected', count: stats.rejected, color: 'bg-red-500' },
              ].map((s) => (
                <div key={s.label} className="flex items-center justify-between px-1">
                  <div className="flex items-center gap-2">
                    <div className={cn('h-1.5 w-1.5 rounded-full', s.color)} />
                    <span className="text-xs font-medium text-muted-foreground">{s.label}</span>
                  </div>
                  <span className="text-xs font-bold">{s.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer Navigation */}
        <div className="p-4 border-t border-white/5">
          {bottomNavigation.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;

            return (
              <Link key={item.name} href={item.href}>
                <div
                  className={cn(
                    'group flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-all cursor-pointer',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-white/10 hover:text-foreground'
                  )}
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.name}</span>
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </motion.aside>
  );
}
