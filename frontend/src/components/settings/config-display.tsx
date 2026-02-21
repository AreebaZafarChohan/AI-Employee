'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { motion } from 'framer-motion';
import { Settings, Bell, Palette, Shield, Database, Clock, Zap, User } from 'lucide-react';

interface ConfigItem {
  category: string;
  icon: React.ReactNode;
  gradient: string;
  items: Array<{ label: string; value: string | boolean }>;
}

export function ConfigDisplay() {
  const configItems: ConfigItem[] = [
    {
      category: 'General',
      icon: <Settings className="h-6 w-6" />,
      gradient: 'from-blue-400 to-cyan-500',
      items: [
        { label: 'Theme', value: 'System' },
        { label: 'Language', value: 'English' },
        { label: 'Timezone', value: 'UTC' },
      ],
    },
    {
      category: 'Notifications',
      icon: <Bell className="h-6 w-6" />,
      gradient: 'from-orange-400 to-red-500',
      items: [
        { label: 'Email Notifications', value: true },
        { label: 'Push Notifications', value: false },
        { label: 'Sound Alerts', value: true },
      ],
    },
    {
      category: 'Appearance',
      icon: <Palette className="h-6 w-6" />,
      gradient: 'from-purple-400 to-pink-500',
      items: [
        { label: 'Color Scheme', value: 'Blue' },
        { label: 'Font Size', value: 'Medium' },
        { label: 'Compact Mode', value: false },
      ],
    },
    {
      category: 'Privacy & Security',
      icon: <Shield className="h-6 w-6" />,
      gradient: 'from-green-400 to-emerald-500',
      items: [
        { label: 'Two-Factor Auth', value: false },
        { label: 'Session Timeout', value: '30 minutes' },
        { label: 'Data Encryption', value: true },
      ],
    },
    {
      category: 'Data Management',
      icon: <Database className="h-6 w-6" />,
      gradient: 'from-indigo-400 to-blue-500',
      items: [
        { label: 'Auto-Save', value: true },
        { label: 'Backup Frequency', value: 'Daily' },
        { label: 'Retention Period', value: '30 days' },
      ],
    },
    {
      category: 'Performance',
      icon: <Zap className="h-6 w-6" />,
      gradient: 'from-yellow-400 to-orange-500',
      items: [
        { label: 'Animation Speed', value: 'Normal' },
        { label: 'Data Refresh', value: 'Automatic' },
        { label: 'Cache Mode', value: 'Enabled' },
      ],
    },
  ];

  return (
    <Card className="border-0 glass shadow-xl overflow-hidden h-full">
      <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 to-pink-500/5" />
      <CardHeader className="relative z-10">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-gradient-to-br from-orange-400 to-pink-500 shadow-lg">
            <Settings className="h-6 w-6 text-white" />
          </div>
          <div>
            <CardTitle className="text-xl">Configuration Settings</CardTitle>
            <CardDescription>
              Current system configuration and preferences
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="relative z-10">
        <ScrollArea className="h-[450px] pr-2">
          <div className="space-y-6">
            {configItems.map((config, index) => (
              <motion.div
                key={config.category}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                className="space-y-3"
              >
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  className="flex items-center gap-3"
                >
                  <div className={cn('flex h-10 w-10 items-center justify-center rounded-xl shadow-lg bg-gradient-to-br flex-shrink-0', config.gradient)}>
                    <div className="text-white">
                      {config.icon}
                    </div>
                  </div>
                  <h4 className="font-bold text-lg">{config.category}</h4>
                </motion.div>
                <div className="space-y-2 pl-14">
                  {config.items.map((item, itemIndex) => (
                    <motion.div
                      key={item.label}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.2 + index * 0.1 + itemIndex * 0.05 }}
                      whileHover={{ x: 5 }}
                      className="flex items-center justify-between p-3 rounded-xl bg-muted/50 hover:bg-gradient-to-r hover:from-primary/10 hover:to-accent/10 transition-all duration-300 cursor-pointer group"
                    >
                      <span className="text-sm font-medium group-hover:text-primary transition-colors">{item.label}</span>
                      {typeof item.value === 'boolean' ? (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          transition={{ type: 'spring', delay: 0.3 + index * 0.1 }}
                        >
                          <Badge
                            variant={item.value ? 'default' : 'secondary'}
                            className={cn(
                              'border-0 bg-gradient-to-r text-white shadow-lg',
                              item.value ? 'from-green-400 to-emerald-500' : 'from-gray-400 to-gray-600'
                            )}
                          >
                            {item.value ? 'Enabled' : 'Disabled'}
                          </Badge>
                        </motion.div>
                      ) : (
                        <motion.span
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          className="text-sm font-semibold gradient-text"
                        >
                          {item.value}
                        </motion.span>
                      )}
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

function cn(...classes: any[]) {
  return classes.filter(Boolean).join(' ');
}
