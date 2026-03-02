/**
 * Main Navigation Sidebar
 * Left sidebar navigation for all services
 */

'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  Mail,
  MessageSquare,
  Linkedin,
  FileText,
  Settings,
  ChevronRight,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { useApprovalStore } from '@/store/approval-store';

const navigation = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
    description: 'Command Center',
  },
  {
    name: 'Gmail',
    href: '/gmail',
    icon: Mail,
    description: 'Email Management',
  },
  {
    name: 'WhatsApp',
    href: '/whatsapp',
    icon: MessageSquare,
    description: 'Messaging',
  },
  {
    name: 'LinkedIn',
    href: '/linkedin',
    icon: Linkedin,
    description: 'Professional Network',
  },
  {
    name: 'Files',
    href: '/files',
    icon: FileText,
    description: 'Document Manager',
  },
];

const bottomNavigation = [
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings,
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { stats } = useApprovalStore();

  return (
    <div className="fixed left-0 top-0 h-screen w-72 border-r bg-gradient-to-b from-slate-900 to-slate-800 text-white z-50 shadow-2xl">
      <div className="flex h-full flex-col">
        {/* Logo Section */}
        <div className="flex h-20 items-center gap-3 border-b border-slate-700 px-6 bg-slate-800/50">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-purple-600 to-blue-600 shadow-lg">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-5 w-5 text-white"
            >
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
              AI Employee
            </h1>
            <p className="text-xs text-slate-400">Orchestration Dashboard</p>
          </div>
        </div>

        {/* Main Navigation */}
        <nav className="flex-1 space-y-1 px-3 py-6 overflow-y-auto">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;

            return (
              <Link key={item.name} href={item.href} passHref>
                <div
                  className={cn(
                    'group flex items-center justify-between rounded-lg px-3 py-3 text-sm font-medium transition-all mb-1 cursor-pointer',
                    isActive
                      ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-md'
                      : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                  )}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={cn('h-5 w-5', isActive ? 'text-white' : 'text-slate-400 group-hover:text-white')} />
                    <div>
                      <p className="font-medium">{item.name}</p>
                      <p className={cn('text-xs', isActive ? 'text-white/70' : 'text-slate-500')}>
                        {item.description}
                      </p>
                    </div>
                  </div>
                  {isActive && <ChevronRight className="h-4 w-4 opacity-70" />}
                </div>
              </Link>
            );
          })}
        </nav>

        {/* Pending Approvals Widget */}
        <div className="mx-3 mb-4 rounded-lg border border-slate-700 bg-slate-800/50 p-4">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-sm font-semibold text-white">Approvals</p>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="text-purple-400"
            >
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Pending</span>
              <Badge className="bg-yellow-600 text-white hover:bg-yellow-700">
                {stats.pending}
              </Badge>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Approved</span>
              <Badge className="bg-green-600 text-white hover:bg-green-700">
                {stats.approved}
              </Badge>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Rejected</span>
              <Badge className="bg-red-600 text-white hover:bg-red-700">
                {stats.rejected}
              </Badge>
            </div>
          </div>
        </div>

        {/* Bottom Navigation */}
        <div className="border-t border-slate-700 px-3 py-4 bg-slate-800/30">
          {bottomNavigation.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;

            return (
              <Link key={item.name} href={item.href} passHref>
                <div
                  className={cn(
                    'group flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition-all cursor-pointer',
                    isActive
                      ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-md'
                      : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                  )}
                >
                  <Icon className={cn('h-5 w-5', isActive ? 'text-white' : 'text-slate-400 group-hover:text-white')} />
                  <span>{item.name}</span>
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
