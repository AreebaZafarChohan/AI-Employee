import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Bell, User, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { ThemeToggle } from './theme-toggle';

interface HeaderProps {
  title?: string;
  subtitle?: string;
}

export function Header({ title, subtitle }: HeaderProps) {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.3 }}
      className={cn(
        'sticky top-0 z-30 flex h-20 items-center justify-between px-6 transition-all duration-300',
        isScrolled ? 'bg-background/80 backdrop-blur-md border-b border-white/10 shadow-lg' : 'bg-transparent'
      )}
    >
      <div className="flex items-center gap-4">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', duration: 0.5 }}
          className="flex items-center gap-2"
        >
          <div className="p-2 rounded-xl bg-gradient-to-br from-primary to-accent shadow-lg shadow-primary/20">
            <Zap className="h-5 w-5 text-white animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/70">{title}</h1>
            {subtitle && <p className="text-xs text-muted-foreground font-medium">{subtitle}</p>}
          </div>
        </motion.div>
      </div>

      <div className="flex items-center gap-4">
        <ThemeToggle />

        {/* Notifications with pulse effect */}
        <Button variant="ghost" size="icon" className="relative hover:bg-primary/10 transition-all duration-300 hover:scale-110 rounded-full border border-white/5" aria-label="Notifications">
          <Bell className="h-5 w-5" />
          <span className="absolute top-2.5 right-2.5 h-2 w-2 rounded-full bg-red-500 animate-ping" />
          <span className="absolute top-2.5 right-2.5 h-2 w-2 rounded-full bg-red-500" />
        </Button>

        {/* User Menu with gradient border */}
        <Button variant="ghost" size="icon" className="relative overflow-hidden hover:bg-primary/10 transition-all duration-300 hover:scale-110 rounded-full border border-white/5" aria-label="User menu">
          <User className="h-5 w-5 relative z-10" />
        </Button>
      </div>
    </motion.header>
  );
}
