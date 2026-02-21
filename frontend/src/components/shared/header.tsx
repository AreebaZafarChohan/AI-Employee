'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Sun, Moon, Bell, User, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { STORAGE_KEYS } from '@/lib/constants';

interface HeaderProps {
  title?: string;
}

export function Header({ title }: HeaderProps) {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const savedTheme = localStorage.getItem(STORAGE_KEYS.THEME);
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
      setIsDarkMode(true);
      document.documentElement.classList.add('dark');
    }

    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const toggleTheme = () => {
    const newMode = !isDarkMode;
    setIsDarkMode(newMode);
    localStorage.setItem(STORAGE_KEYS.THEME, newMode ? 'dark' : 'light');
    
    if (newMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.3 }}
      className={cn(
        'sticky top-0 z-30 flex h-20 items-center justify-between px-6 transition-all duration-300',
        isScrolled ? 'glass shadow-lg' : 'bg-transparent'
      )}
    >
      <div className="flex items-center gap-4">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', duration: 0.5 }}
          className="flex items-center gap-2"
        >
          <div className="p-2 rounded-xl bg-gradient-to-br from-primary to-accent shadow-lg">
            <Zap className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold gradient-text">{title}</h1>
            <p className="text-xs text-muted-foreground">Welcome back!</p>
          </div>
        </motion.div>
      </div>

      <div className="flex items-center gap-3">
        {/* Theme Toggle with animation */}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          className="relative overflow-hidden hover:bg-primary/10 transition-all duration-300 hover:scale-110"
          aria-label="Toggle theme"
        >
          <motion.div
            initial={false}
            animate={{ rotate: isDarkMode ? 180 : 0 }}
            transition={{ duration: 0.3 }}
          >
            <Sun
              className={cn(
                'h-5 w-5 absolute transition-all duration-300',
                isDarkMode ? 'rotate-90 scale-0 opacity-0' : 'rotate-0 scale-100 opacity-100'
              )}
            />
          </motion.div>
          <motion.div
            initial={false}
            animate={{ rotate: isDarkMode ? 0 : -180 }}
            transition={{ duration: 0.3 }}
          >
            <Moon
              className={cn(
                'h-5 w-5 absolute transition-all duration-300',
                !isDarkMode ? 'rotate-90 scale-0 opacity-0' : 'rotate-0 scale-100 opacity-100'
              )}
            />
          </motion.div>
        </Button>

        {/* Notifications with pulse effect */}
        <Button variant="ghost" size="icon" className="relative hover:bg-primary/10 transition-all duration-300 hover:scale-110" aria-label="Notifications">
          <Bell className="h-5 w-5" />
          <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-red-500 animate-pulse" />
        </Button>

        {/* User Menu with gradient border */}
        <Button variant="ghost" size="icon" className="relative overflow-hidden hover:bg-primary/10 transition-all duration-300 hover:scale-110" aria-label="User menu">
          <div className="absolute inset-0 bg-gradient-to-r from-primary/20 to-accent/20 opacity-0 hover:opacity-100 transition-opacity duration-300" />
          <User className="h-5 w-5 relative z-10" />
        </Button>
      </div>
    </motion.header>
  );
}
