'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { APP_NAME, APP_VERSION } from '@/lib/constants';
import { motion } from 'framer-motion';
import { Cpu, MemoryStick, HardDrive, Globe, Shield, Wifi } from 'lucide-react';

export function EnvironmentInfo() {
  const environment = {
    appName: APP_NAME,
    version: APP_VERSION,
    platform: typeof navigator !== 'undefined' ? navigator.platform : 'Unknown',
    browser: typeof navigator !== 'undefined' ? navigator.userAgent.split(' ')[0] : 'Unknown',
    screenResolution: typeof window !== 'undefined' ? `${window.screen.width}x${window.screen.height}` : 'Unknown',
    language: typeof navigator !== 'undefined' ? navigator.language : 'Unknown',
  };

  const infoItems = [
    {
      icon: <Cpu className="h-6 w-6" />,
      label: 'Application',
      value: `${environment.appName} v${environment.version}`,
      gradient: 'from-blue-400 to-cyan-500',
    },
    {
      icon: <Globe className="h-6 w-6" />,
      label: 'Browser',
      value: environment.browser,
      gradient: 'from-purple-400 to-pink-500',
    },
    {
      icon: <MemoryStick className="h-6 w-6" />,
      label: 'Platform',
      value: environment.platform,
      gradient: 'from-orange-400 to-red-500',
    },
    {
      icon: <HardDrive className="h-6 w-6" />,
      label: 'Screen Resolution',
      value: environment.screenResolution,
      gradient: 'from-green-400 to-emerald-500',
    },
    {
      icon: <Shield className="h-6 w-6" />,
      label: 'Language',
      value: environment.language,
      gradient: 'from-indigo-400 to-blue-500',
    },
    {
      icon: <Wifi className="h-6 w-6" />,
      label: 'Connection Status',
      value: 'Online',
      gradient: 'from-green-400 to-teal-500',
    },
  ];

  return (
    <Card className="border-0 glass shadow-xl overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5" />
      <CardHeader className="relative z-10">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-gradient-to-br from-blue-400 to-purple-500 shadow-lg">
            <Cpu className="h-6 w-6 text-white" />
          </div>
          <div>
            <CardTitle className="text-xl">Environment Information</CardTitle>
            <CardDescription>
              Details about your current session and system
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="relative z-10">
        <div className="grid gap-4">
          {infoItems.map((item, index) => (
            <motion.div
              key={item.label}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              whileHover={{ scale: 1.02, x: 5 }}
              className="group"
            >
              <div className="flex items-center gap-4 p-4 rounded-xl bg-muted/50 group-hover:bg-gradient-to-r group-hover:from-primary/10 group-hover:to-accent/10 transition-all duration-300">
                <motion.div
                  whileHover={{ rotate: 360, scale: 1.1 }}
                  transition={{ duration: 0.5 }}
                  className={cn('flex h-12 w-12 items-center justify-center rounded-xl shadow-lg bg-gradient-to-br flex-shrink-0', item.gradient)}
                >
                  <div className="text-white">
                    {item.icon}
                  </div>
                </motion.div>
                <div className="flex-1">
                  <p className="text-sm font-medium mb-1">{item.label}</p>
                  <p className="text-lg font-semibold gradient-text">{item.value}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function cn(...classes: any[]) {
  return classes.filter(Boolean).join(' ');
}
