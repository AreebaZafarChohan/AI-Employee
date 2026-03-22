'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sidebar } from '@/components/shared/sidebar';
import { Header } from '@/components/shared/header';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Bot, Send, Sparkles, Loader2, CheckCircle, XCircle, Clock, 
  AlertCircle, Zap, Shield, FileText, Share2, Mail, MessageSquare,
  Twitter, Linkedin, Facebook, Instagram, RefreshCw, Eye
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { 
  useSendCommand, 
  useVaultItems, 
  useApproveFile, 
  useRejectFile,
  useVaultCounts
} from '@/hooks/use-ai-employee';

const PLATFORM_ICONS: Record<string, any> = {
  twitter: Twitter,
  linkedin: Linkedin,
  facebook: Facebook,
  instagram: Instagram,
  whatsapp: MessageSquare,
  email: Mail,
};

const PLATFORM_COLORS: Record<string, string> = {
  twitter: 'text-sky-500',
  linkedin: 'text-blue-600',
  facebook: 'text-blue-500',
  instagram: 'text-pink-500',
  whatsapp: 'text-green-500',
  email: 'text-red-500',
};

export default function AiEmployeePage() {
  const [command, setCommand] = useState('');
  const [activeTab, setActiveTab] = useState('pending');
  
  const sendCommandMutation = useSendCommand();
  const approveMutation = useApproveFile();
  const rejectMutation = useRejectFile();
  
  const { data: pendingItems, isLoading: loadingPending } = useVaultItems('pending');
  const { data: needsActionItems, isLoading: loadingNeedsAction } = useVaultItems('needs-action');
  const { data: doneItems, isLoading: loadingDone } = useVaultItems('done');
  const { data: counts } = useVaultCounts();

  const handleSendCommand = () => {
    if (!command.trim()) return;
    sendCommandMutation.mutate({ command }, {
      onSuccess: () => setCommand(''),
    });
  };

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="ml-72 flex-1 flex flex-col">
        <Header title="AI Employee" subtitle="Autonomous Agent Control Center" />
        
        <main className="flex-1 p-8 space-y-8">
          {/* Command Center */}
          <section className="max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="relative"
            >
              <div className="absolute -inset-1 bg-gradient-to-r from-primary to-accent rounded-3xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
              <Card className="relative border-white/10 shadow-2xl overflow-hidden">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center">
                        <Zap className="h-6 w-6 text-primary" />
                      </div>
                      <div>
                        <CardTitle>AI Command Center</CardTitle>
                        <CardDescription>Instruct your AI Employee using natural language</CardDescription>
                      </div>
                    </div>
                    <Badge variant="outline" className="gap-2 px-3 py-1">
                      <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                      Agent Online
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-4">
                    <div className="relative flex-1">
                      <Bot className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                      <Input
                        value={command}
                        onChange={(e) => setCommand(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSendCommand()}
                        placeholder="e.g. LinkedIn aur Twitter par AI automation ke baare mein post karo..."
                        className="pl-12 h-14 text-lg rounded-2xl bg-muted/50 border-white/5 focus-visible:ring-primary/50"
                      />
                    </div>
                    <Button 
                      onClick={handleSendCommand}
                      disabled={!command.trim() || sendCommandMutation.isPending}
                      className="h-14 px-8 rounded-2xl bg-gradient-to-r from-primary to-accent hover:opacity-90 transition-opacity gap-2"
                    >
                      {sendCommandMutation.isPending ? (
                        <Loader2 className="h-5 w-5 animate-spin" />
                      ) : (
                        <Send className="h-5 w-5" />
                      )}
                      Execute
                    </Button>
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    <p className="text-xs text-muted-foreground mr-2 mt-1">Suggestions:</p>
                    <Badge 
                      variant="secondary" 
                      className="cursor-pointer hover:bg-primary/20 transition-colors"
                      onClick={() => setCommand("Generate social media posts about our new AI features")}
                    >
                      "Social media posts about AI features"
                    </Badge>
                    <Badge 
                      variant="secondary" 
                      className="cursor-pointer hover:bg-primary/20 transition-colors"
                      onClick={() => setCommand("Write a LinkedIn post about future of AI Agents")}
                    >
                      "LinkedIn post about AI Agents"
                    </Badge>
                    <Badge 
                      variant="secondary" 
                      className="cursor-pointer hover:bg-primary/20 transition-colors"
                      onClick={() => setCommand("Draft an email reply to latest inquiry")}
                    >
                      "Draft email reply"
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </section>

          {/* Workflow Status */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <div className="lg:col-span-3">
              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <div className="flex items-center justify-between mb-4">
                  <TabsList className="bg-muted/50 p-1 rounded-xl">
                    <TabsTrigger value="pending" className="rounded-lg px-6">
                      Pending Approval
                      <Badge className="ml-2 bg-orange-500">{counts?.pending || 0}</Badge>
                    </TabsTrigger>
                    <TabsTrigger value="active" className="rounded-lg px-6">
                      Active Tasks
                      <Badge className="ml-2 bg-blue-500">{counts?.['needs-action'] || 0}</Badge>
                    </TabsTrigger>
                    <TabsTrigger value="done" className="rounded-lg px-6">
                      Completed
                      <Badge className="ml-2 bg-green-500">{counts?.done || 0}</Badge>
                    </TabsTrigger>
                  </TabsList>
                  
                  <Button variant="ghost" size="sm" className="gap-2" onClick={() => window.location.reload()}>
                    <RefreshCw className="h-4 w-4" />
                    Refresh
                  </Button>
                </div>

                <AnimatePresence mode="wait">
                  <TabsContent value="pending" className="mt-0 focus-visible:outline-none focus-visible:ring-0">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {loadingPending ? (
                        Array(4).fill(0).map((_, i) => (
                          <Card key={i} className="animate-pulse bg-muted/50 h-64 border-white/5 rounded-2xl" />
                        ))
                      ) : !pendingItems?.length ? (
                        <div className="col-span-full py-20 flex flex-col items-center justify-center text-muted-foreground bg-muted/20 rounded-3xl border border-dashed border-white/10">
                          <CheckCircle className="h-12 w-12 mb-4 opacity-20" />
                          <p>No items pending approval</p>
                        </div>
                      ) : (
                        pendingItems.map((item) => (
                          <ApprovalCard key={item.filename} item={item} />
                        ))
                      )}
                    </div>
                  </TabsContent>

                  <TabsContent value="active" className="mt-0 focus-visible:outline-none focus-visible:ring-0">
                    <div className="space-y-4">
                      {loadingNeedsAction ? (
                        Array(3).fill(0).map((_, i) => (
                          <Card key={i} className="animate-pulse bg-muted/50 h-32 border-white/5 rounded-2xl" />
                        ))
                      ) : !needsActionItems?.length ? (
                        <div className="py-20 flex flex-col items-center justify-center text-muted-foreground bg-muted/20 rounded-3xl border border-dashed border-white/10">
                          <Bot className="h-12 w-12 mb-4 opacity-20" />
                          <p>No active autonomous tasks</p>
                        </div>
                      ) : (
                        needsActionItems.map((item) => (
                          <TaskCard key={item.filename} item={item} />
                        ))
                      )}
                    </div>
                  </TabsContent>

                  <TabsContent value="done" className="mt-0 focus-visible:outline-none focus-visible:ring-0">
                    <div className="space-y-4">
                      {loadingDone ? (
                        Array(5).fill(0).map((_, i) => (
                          <Card key={i} className="animate-pulse bg-muted/50 h-24 border-white/5 rounded-2xl" />
                        ))
                      ) : !doneItems?.length ? (
                        <div className="py-20 flex flex-col items-center justify-center text-muted-foreground bg-muted/20 rounded-3xl border border-dashed border-white/10">
                          <FileText className="h-12 w-12 mb-4 opacity-20" />
                          <p>No completed items found</p>
                        </div>
                      ) : (
                        doneItems.map((item) => (
                          <DoneItemCard key={item.filename} item={item} />
                        ))
                      )}
                    </div>
                  </TabsContent>
                </AnimatePresence>
              </Tabs>
            </div>

            {/* Sidebar Stats */}
            <div className="space-y-6">
              <Card className="border-white/10 bg-muted/30">
                <CardHeader>
                  <CardTitle className="text-sm uppercase tracking-wider font-bold text-muted-foreground">System Health</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <HealthItem label="Gemini Engine" status="online" />
                  <HealthItem label="Ralph Reasoning Loop" status="online" />
                  <HealthItem label="MCP Server" status="online" />
                  <HealthItem label="Social Watcher" status="online" />
                </CardContent>
              </Card>

              <Card className="border-white/10 bg-muted/30">
                <CardHeader>
                  <CardTitle className="text-sm uppercase tracking-wider font-bold text-muted-foreground">Auto-Execution</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium">Low-risk auto-approve</span>
                    <Badge variant="outline" className="text-green-500 border-green-500/50">ON</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium">Weekly AI Audit</span>
                    <Badge variant="outline" className="text-blue-500 border-blue-500/50">Mon 9 AM</Badge>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

function ApprovalCard({ item }: { item: any }) {
  const approveMutation = useApproveFile();
  const rejectMutation = useRejectFile();
  const platform = (item.platform || item.channel || 'twitter').toLowerCase();
  const Icon = PLATFORM_ICONS[platform] || FileText;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
    >
      <Card className="border-white/10 overflow-hidden group hover:shadow-xl transition-all duration-300 rounded-2xl flex flex-col h-full">
        <div className={cn("h-1 w-full bg-gradient-to-r", 
          platform === 'linkedin' ? "from-blue-600 to-blue-400" :
          platform === 'twitter' ? "from-sky-400 to-sky-600" :
          platform === 'instagram' ? "from-pink-500 to-purple-600" :
          "from-primary to-accent"
        )} />
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className={cn("p-2 rounded-lg bg-muted/50", PLATFORM_COLORS[platform])}>
                <Icon className="h-5 w-5" />
              </div>
              <div>
                <CardTitle className="text-base capitalize">{platform} Post</CardTitle>
                <CardDescription className="text-[10px]">{new Date(item.createdAt).toLocaleString()}</CardDescription>
              </div>
            </div>
            <Badge variant="outline" className="capitalize">{item.risk_level || 'medium'} Risk</Badge>
          </div>
        </CardHeader>
        <CardContent className="flex-1 space-y-4">
          <div className="p-4 rounded-xl bg-muted/50 text-sm leading-relaxed line-clamp-6 whitespace-pre-wrap font-medium">
            {item.content?.split('## Content\n\n')[1]?.split('---')[0] || item.content}
          </div>
          
          <div className="flex gap-2 pt-2 mt-auto">
            <Button 
              size="sm" 
              className="flex-1 bg-green-600 hover:bg-green-700 rounded-xl"
              onClick={() => approveMutation.mutate({ filename: item.filename })}
              disabled={approveMutation.isPending || rejectMutation.isPending}
            >
              {approveMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4 mr-2" />}
              Approve
            </Button>
            <Button 
              size="sm" 
              variant="outline" 
              className="flex-1 rounded-xl hover:bg-red-500/10 hover:text-red-500"
              onClick={() => rejectMutation.mutate({ filename: item.filename })}
              disabled={approveMutation.isPending || rejectMutation.isPending}
            >
              <XCircle className="h-4 w-4 mr-2" />
              Reject
            </Button>
            <Button size="icon" variant="ghost" className="rounded-xl">
              <Eye className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function TaskCard({ item }: { item: any }) {
  return (
    <Card className="border-white/10 bg-muted/20 rounded-2xl p-4 flex items-center justify-between group hover:bg-muted/30 transition-colors">
      <div className="flex items-center gap-4">
        <div className="h-10 w-10 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-500">
          <RefreshCw className="h-5 w-5 animate-spin-slow" />
        </div>
        <div>
          <h4 className="font-semibold text-sm">{item.title || "Autonomous Reasoning"}</h4>
          <p className="text-xs text-muted-foreground line-clamp-1">{item.command || "Processing multi-platform content generation..."}</p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <div className="text-right">
          <Badge className="bg-blue-600 mb-1">Working</Badge>
          <p className="text-[10px] text-muted-foreground">{new Date(item.createdAt).toLocaleTimeString()}</p>
        </div>
        <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:translate-x-1 transition-transform" />
      </div>
    </Card>
  );
}

function DoneItemCard({ item }: { item: any }) {
  const platform = (item.platform || item.channel || 'twitter').toLowerCase();
  const Icon = PLATFORM_ICONS[platform] || FileText;

  return (
    <Card className="border-white/10 bg-muted/10 rounded-2xl p-4 flex items-center justify-between group hover:bg-muted/20 transition-colors">
      <div className="flex items-center gap-4">
        <div className={cn("h-10 w-10 rounded-xl flex items-center justify-center bg-muted/50", PLATFORM_COLORS[platform])}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <h4 className="font-semibold text-sm capitalize">{platform} Post Published</h4>
          <p className="text-xs text-muted-foreground line-clamp-1">{item.topic || item.title}</p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <div className="text-right">
          <div className="flex items-center gap-1 text-green-500 mb-1">
            <CheckCircle className="h-3 w-3" />
            <span className="text-[10px] font-bold uppercase">Success</span>
          </div>
          <p className="text-[10px] text-muted-foreground">{new Date(item.createdAt).toLocaleDateString()}</p>
        </div>
        <Button size="icon" variant="ghost" className="rounded-xl">
          <Share2 className="h-4 w-4" />
        </Button>
      </div>
    </Card>
  );
}

function HealthItem({ label, status }: { label: string, status: 'online' | 'offline' | 'error' }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs font-medium">{label}</span>
      <div className="flex items-center gap-1.5">
        <span className={cn("h-1.5 w-1.5 rounded-full animate-pulse", 
          status === 'online' ? 'bg-green-500' : status === 'offline' ? 'bg-slate-500' : 'bg-red-500'
        )} />
        <span className="text-[10px] font-bold uppercase tracking-wider">{status}</span>
      </div>
    </div>
  );
}

function ChevronRight({ className }: { className?: string }) {
  return (
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
      className={className}
    >
      <path d="m9 18 6-6-6-6"/>
    </svg>
  );
}
