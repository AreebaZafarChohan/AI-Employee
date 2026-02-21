'use client';

import { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { ROUTES } from '@/lib/constants';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  LayoutDashboard, 
  Inbox, 
  FileText, 
  Settings,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
  Sparkles
} from 'lucide-react';
import { Button } from '@/components/ui/button';

const navItems = [
  {
    title: 'Dashboard',
    href: ROUTES.DASHBOARD,
    icon: LayoutDashboard,
    gradient: 'from-blue-500 to-cyan-500',
  },
  {
    title: 'Needs Action',
    href: ROUTES.NEEDS_ACTION,
    icon: Inbox,
    gradient: 'from-orange-500 to-red-500',
  },
  {
    title: 'Plans',
    href: ROUTES.PLANS,
    icon: FileText,
    gradient: 'from-purple-500 to-pink-500',
  },
  {
    title: 'Settings',
    href: ROUTES.SETTINGS,
    icon: Settings,
    gradient: 'from-green-500 to-emerald-500',
  },
];

interface SidebarProps {
  className?: string;
}

export function Sidebar({ className }: SidebarProps) {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const toggleSidebar = () => setIsCollapsed(!isCollapsed);
  const toggleMobile = () => setIsMobileOpen(!isMobileOpen);

  return (
    <>
      {/* Mobile Overlay */}
      <AnimatePresence>
        {isMobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-40 lg:hidden backdrop-blur-sm"
            onClick={() => setIsMobileOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Mobile Menu Button */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed top-4 left-4 z-50 lg:hidden glass"
        onClick={toggleMobile}
      >
        <Menu className="h-5 w-5" />
      </Button>

      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{
          width: isCollapsed ? 80 : 280,
          x: isMobile && !isMobileOpen ? -280 : 0,
        }}
        className={cn(
          'fixed top-0 left-0 h-full glass z-50 lg:z-0',
          'transition-all duration-300 ease-in-out',
          className
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo Section */}
          <div className={cn(
            'flex items-center justify-between p-6 border-b border-white/10',
            isCollapsed && 'justify-center'
          )}>
            <AnimatePresence>
              {!isCollapsed && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex items-center gap-2"
                >
                  <Sparkles className="h-6 w-6 text-primary" />
                  <span className="font-bold text-xl gradient-text">AI Employee</span>
                </motion.div>
              )}
            </AnimatePresence>
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleSidebar}
              className="hidden lg:flex hover:bg-primary/10"
            >
              {isCollapsed ? (
                <ChevronRight className="h-4 w-4" />
              ) : (
                <ChevronLeft className="h-4 w-4" />
              )}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleMobile}
              className="lg:hidden"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 py-6 space-y-2 px-3">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.title}
                  href={item.href}
                  onClick={() => setIsMobileOpen(false)}
                  className={cn(
                    'relative group flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300',
                    'hover:bg-primary/10 hover:scale-105',
                    isActive && 'bg-gradient-to-r from-primary/20 to-accent/20 shadow-lg',
                    isCollapsed && 'justify-center'
                  )}
                >
                  {isActive && (
                    <motion.div
                      layoutId="activeNav"
                      className="absolute inset-0 bg-gradient-to-r from-primary/10 to-accent/10 rounded-xl"
                      transition={{ type: 'spring', duration: 0.5 }}
                    />
                  )}
                  <div className={cn(
                    'relative z-10 p-2 rounded-lg bg-gradient-to-br transition-all duration-300 group-hover:scale-110',
                    isActive ? `bg-gradient-to-br ${item.gradient}` : 'bg-muted'
                  )}>
                    <item.icon className={cn(
                      'h-5 w-5 flex-shrink-0',
                      isActive ? 'text-white' : 'text-muted-foreground group-hover:text-primary'
                    )} />
                  </div>
                  <AnimatePresence>
                    {!isCollapsed && (
                      <motion.span
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className={cn(
                          'relative z-10 font-medium whitespace-nowrap',
                          isActive ? 'text-primary' : 'text-foreground'
                        )}
                      >
                        {item.title}
                      </motion.span>
                    )}
                  </AnimatePresence>
                  {isActive && !isCollapsed && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="relative z-10 ml-auto"
                    >
                      <Sparkles className="h-4 w-4 text-primary" />
                    </motion.div>
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className={cn(
            'p-4 border-t border-white/10',
            isCollapsed && 'text-center'
          )}>
            <AnimatePresence>
              {!isCollapsed && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="space-y-2"
                >
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                    <span>Bronze Tier v1.0.0</span>
                  </div>
                  <div className="text-xs text-muted-foreground/60">
                    © 2026 AI Employee
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </motion.aside>
    </>
  );
}
