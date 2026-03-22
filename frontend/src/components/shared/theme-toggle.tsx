'use client';

import * as React from 'react';
import { Moon, Sun, Laptop } from 'lucide-react';
import { useTheme } from 'next-themes';
import { Button } from '@/components/ui/button';
import { motion, AnimatePresence } from 'framer-motion';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div className="w-10 h-10" />;
  }

  const cycleTheme = () => {
    if (theme === 'light') setTheme('dark');
    else if (theme === 'dark') setTheme('system');
    else setTheme('light');
  };

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={cycleTheme}
      className="relative w-10 h-10 rounded-full bg-background/50 backdrop-blur-md border border-white/10 hover:bg-primary/20 transition-all duration-300 shadow-lg group"
    >
      <AnimatePresence mode="wait" initial={false}>
        {theme === 'light' && (
          <motion.div
            key="sun"
            initial={{ y: 20, opacity: 0, rotate: -90 }}
            animate={{ y: 0, opacity: 1, rotate: 0 }}
            exit={{ y: -20, opacity: 0, rotate: 90 }}
            transition={{ duration: 0.2 }}
          >
            <Sun className="h-[1.2rem] w-[1.2rem] text-orange-500 group-hover:scale-110 transition-transform" />
          </motion.div>
        )}
        {theme === 'dark' && (
          <motion.div
            key="moon"
            initial={{ y: 20, opacity: 0, rotate: -90 }}
            animate={{ y: 0, opacity: 1, rotate: 0 }}
            exit={{ y: -20, opacity: 0, rotate: 90 }}
            transition={{ duration: 0.2 }}
          >
            <Moon className="h-[1.2rem] w-[1.2rem] text-blue-400 group-hover:scale-110 transition-transform" />
          </motion.div>
        )}
        {theme === 'system' && (
          <motion.div
            key="system"
            initial={{ y: 20, opacity: 0, rotate: -90 }}
            animate={{ y: 0, opacity: 1, rotate: 0 }}
            exit={{ y: -20, opacity: 0, rotate: 90 }}
            transition={{ duration: 0.2 }}
          >
            <Laptop className="h-[1.2rem] w-[1.2rem] text-primary group-hover:scale-110 transition-transform" />
          </motion.div>
        )}
      </AnimatePresence>
      <span className="sr-only">Toggle theme</span>
    </Button>
  );
}
