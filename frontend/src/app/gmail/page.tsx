'use client';

import { useEffect, useState } from 'react';
import { Header } from '@/components/shared/header';
import { Sidebar } from '@/components/shared/sidebar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { gmailApi, type GmailMessage } from '@/lib/api';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Inbox,
  Send,
  AlertCircle,
  Search,
  RefreshCw,
  Plus,
  User,
  Type,
  Sparkles,
  FileText,
  CheckCircle,
  XCircle,
  Activity,
  Filter
} from 'lucide-react';

export default function GmailDashboardPage() {
  const [messages, setMessages] = useState<GmailMessage[]>([]);
  const [drafts, setDrafts] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedMessage, setSelectedMessage] = useState<GmailMessage | null>(null);
  const [selectedDraft, setSelectedDraft] = useState<any | null>(null);
  
  // Tabs
  const [activeView, setActiveView] = useState<'inbox' | 'compose' | 'drafts'>('inbox');
  const [composeMode, setComposeMode] = useState<'manual' | 'ai'>('manual');
  
  // Filter/Search
  const [filterType, setFilterType] = useState<'all' | 'unread' | 'important'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [badgeCounts, setBadgeCounts] = useState({ all: 0, unread: 0, important: 0 });

  // Form states
  const [composeTo, setComposeTo] = useState('');
  const [composeSubject, setComposeSubject] = useState('');
  const [composeTopic, setComposeTopic] = useState('');
  const [composeBody, setComposeBody] = useState('');
  const [replyInstructions, setReplyInstructions] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    loadData();
    // Fetch badge counts only once on mount (not on every filter change)
    fetchBadgeCounts();
  }, [filterType, activeView]);

  const fetchBadgeCounts = async () => {
    try {
      const response = await gmailApi.getCounts();
      const counts = response?.counts ?? { all: 0, unread: 0, important: 0 };
      console.log('Badge counts:', counts);
      setBadgeCounts(counts);
    } catch (err) {
      console.error('Failed to fetch badge counts:', err);
    }
  };

  const loadData = async () => {
    setIsLoading(true);
    try {
      if (activeView === 'inbox') {
        const response = await gmailApi.getInbox({ filter_type: filterType, limit: 50 });
        const msgs = response?.data?.data || response?.data || [];
        setMessages(msgs);
      } else if (activeView === 'drafts') {
        const response = await (gmailApi as any).getDrafts();
        console.log('Drafts response:', response);
        setDrafts(response?.data || []);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAICompose = async () => {
    if (!composeTo || !composeTopic) return;
    setIsProcessing(true);
    try {
      await (gmailApi as any).generateAICompose({ to: composeTo, topic: composeTopic });
      alert('AI Draft generated and saved in Vault (Needs Approval)!');
      // Reset compose form instead of redirecting
      setComposeTopic('');
      loadData(); // Refresh drafts count
    } catch (err) {
      alert('AI generation failed. Check backend.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAIReply = async () => {
    if (!selectedMessage || !replyInstructions) return;
    setIsProcessing(true);
    try {
      await (gmailApi as any).generateAIReply({ 
        message_id: selectedMessage.id, 
        instructions: replyInstructions 
      });
      alert('AI Reply generated and saved in Vault (Needs Approval)!');
      setReplyInstructions('');
      loadData(); // Refresh drafts count
    } catch (err) {
      alert('AI reply generation failed.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleApproveDraft = async (draft: any) => {
    setIsProcessing(true);
    try {
      await (gmailApi as any).approveDraft(draft.filename, draft.body);
      alert('Draft approved, sent, and moved to Done!');
      setSelectedDraft(null); // Close detail view
      loadData();
    } catch (err) {
      alert('Failed to send draft');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-muted/30">
      <Sidebar />
      <div className="ml-72 flex-1">
        <Header title="Gmail AI Dashboard" subtitle="Manage your emails with Yaram Kazmi (AI)" />

        <main className="flex-1 p-8">
          {/* Top Stats Cards */}
          <div className="grid gap-4 md:grid-cols-5 mb-8">
            <Card className={cn("cursor-pointer transition-all hover:shadow-md", activeView === 'inbox' && "ring-2 ring-primary")} onClick={() => setActiveView('inbox')}>
              <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
                <CardTitle className="text-xs font-medium">Inbox</CardTitle>
                <Inbox className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent><div className="text-2xl font-bold">{messages.length}</div></CardContent>
            </Card>
            <Card className={cn("cursor-pointer transition-all hover:shadow-md", activeView === 'drafts' && "ring-2 ring-primary")} onClick={() => setActiveView('drafts')}>
              <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
                <CardTitle className="text-xs font-medium">AI Drafts</CardTitle>
                <FileText className="h-4 w-4 text-orange-500" />
              </CardHeader>
              <CardContent><div className="text-2xl font-bold">{drafts.length}</div></CardContent>
            </Card>
            <Card className={cn("cursor-pointer transition-all hover:shadow-md", activeView === 'compose' && "ring-2 ring-primary")} onClick={() => setActiveView('compose')}>
              <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
                <CardTitle className="text-xs font-medium">Compose</CardTitle>
                <Plus className="h-4 w-4 text-blue-500" />
              </CardHeader>
              <CardContent><div className="text-sm font-medium text-muted-foreground">New Message</div></CardContent>
            </Card>
            <Card className="bg-primary/5 border-primary/20">
              <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
                <CardTitle className="text-xs font-medium text-primary">Agent Status</CardTitle>
                <Sparkles className="h-4 w-4 text-primary animate-pulse" />
              </CardHeader>
              <CardContent><div className="text-sm font-bold text-primary flex items-center gap-1">Yaram Kazmi Active</div></CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-300 shadow-sm">
              <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
                <CardTitle className="text-xs font-medium text-green-700">System Status</CardTitle>
                <div className="relative">
                  <Activity className="h-4 w-4 text-green-600" />
                  <span className="absolute -top-1 -right-1 h-2.5 w-2.5 bg-green-500 rounded-full animate-pulse border-2 border-white"></span>
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-sm font-bold text-green-700 flex items-center gap-1.5">
                  <span className="inline-block w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                  Email Online
                </div>
                <p className="text-[10px] text-green-600 mt-0.5">All systems operational</p>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            {/* Left Column: Inbox/Draft List */}
            <Card className="lg:col-span-2 shadow-sm border-muted">
              <CardHeader className="pb-3 border-b">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <CardTitle className="text-lg">
                      {activeView === 'inbox' ? 'Inbox' : activeView === 'drafts' ? 'Pending AI Drafts' : 'Compose Email'}
                    </CardTitle>
                    {activeView === 'inbox' && (
                      <div className="flex items-center bg-muted/50 p-1 rounded-md gap-1">
                        <Button variant={filterType === 'all' ? 'default' : 'ghost'} size="sm" className="h-7 text-xs px-2 gap-1.5" onClick={() => setFilterType('all')}>
                          All <Badge className={cn("h-4 min-w-4 px-1 text-[9px]", filterType === 'all' ? "bg-white/20 text-white" : "bg-muted-foreground text-white")}>{badgeCounts.all}</Badge>
                        </Button>
                        <Button variant={filterType === 'unread' ? 'default' : 'ghost'} size="sm" className="h-7 text-xs px-2 gap-1.5" onClick={() => setFilterType('unread')}>
                          Unread <Badge className={cn("h-4 min-w-4 px-1 text-[9px]", filterType === 'unread' ? "bg-white/20 text-white" : "bg-blue-500 text-white")}>{badgeCounts.unread}</Badge>
                        </Button>
                        <Button variant={filterType === 'important' ? 'default' : 'ghost'} size="sm" className="h-7 text-xs px-2 gap-1.5" onClick={() => setFilterType('important')}>
                          Important <Badge className={cn("h-4 min-w-4 px-1 text-[9px]", filterType === 'important' ? "bg-white/20 text-white" : "bg-red-500 text-white")}>{badgeCounts.important}</Badge>
                        </Button>
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                     <div className="relative">
                        <Search className="absolute left-2 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
                        <Input placeholder="Search..." className="h-8 pl-8 w-48 text-xs bg-muted/20" value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
                     </div>
                     <Button variant="outline" size="icon" className="h-8 w-8" onClick={loadData} disabled={isLoading}>
                       <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
                     </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                {isLoading ? (
                  <div className="flex flex-col items-center justify-center py-20 gap-3">
                    <div className="h-8 w-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
                    <p className="text-xs text-muted-foreground">Loading your emails...</p>
                  </div>
                ) : activeView === 'inbox' && (
                  <div className="divide-y max-h-[600px] overflow-y-auto">
                    {messages.length === 0 ? (
                      <div className="p-20 text-center text-muted-foreground">No messages found</div>
                    ) : messages.map(m => (
                      <div key={m.id} onClick={() => setSelectedMessage(m)} className={cn("p-4 flex flex-col gap-1 cursor-pointer transition-colors hover:bg-muted/50", selectedMessage?.id === m.id && "bg-primary/5 border-l-4 border-l-primary")}>
                        <div className="flex justify-between items-start">
                          <p className="text-xs font-bold text-foreground/80">{m.from}</p>
                          <p className="text-[10px] text-muted-foreground">{m.receivedAt || 'Recently'}</p>
                        </div>
                        <p className="text-sm font-semibold truncate">{m.subject}</p>
                        <p className="text-xs text-muted-foreground line-clamp-1">{m.snippet}</p>
                        <div className="flex gap-1 mt-1">
                          {m.labels.slice(0, 3).map(l => (
                            <Badge key={l} variant="outline" className="text-[9px] h-4 py-0 uppercase">{l}</Badge>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {activeView === 'drafts' && (
                  <div className="divide-y max-h-[600px] overflow-y-auto">
                    {drafts.length === 0 ? (
                      <div className="p-20 text-center text-muted-foreground">No pending AI drafts in Needs_Action</div>
                    ) : drafts.map(d => (
                      <div key={d.filename} onClick={() => setSelectedDraft(d)} className={cn("p-4 flex flex-col gap-1 cursor-pointer transition-colors hover:bg-muted/50", selectedDraft?.filename === d.filename && "bg-orange-50/50 border-l-4 border-l-orange-500")}>
                        <div className="flex justify-between items-start">
                           <p className="text-xs font-bold text-foreground/80">To: {d.to}</p>
                           <Badge className="text-[9px] bg-orange-100 text-orange-600 border-none hover:bg-orange-200">NEEDS APPROVAL</Badge>
                        </div>
                        <p className="text-sm font-semibold truncate">{d.subject}</p>
                        <p className="text-xs text-muted-foreground line-clamp-1 italic">Generated by Yaram Kazmi</p>
                      </div>
                    ))}
                  </div>
                )}
                {activeView === 'compose' && (
                  <div className="p-6 space-y-4">
                    <div className="flex gap-2 p-1 bg-muted rounded-lg w-fit">
                      <Button variant={composeMode === 'manual' ? 'secondary' : 'ghost'} size="sm" onClick={() => setComposeMode('manual')} className="text-xs">Manual Mode</Button>
                      <Button variant={composeMode === 'ai' ? 'secondary' : 'ghost'} size="sm" onClick={() => setComposeMode('ai')} className="text-xs gap-1.5"><Sparkles className="h-3.5 w-3.5" /> AI Powered</Button>
                    </div>
                    <div className="grid gap-4">
                      <div className="space-y-2">
                        <label className="text-[10px] font-bold uppercase text-muted-foreground">Recipient</label>
                        <Input placeholder="email@example.com" value={composeTo} onChange={e => setComposeTo(e.target.value)} />
                      </div>
                      {composeMode === 'manual' ? (
                        <>
                          <div className="space-y-2">
                            <label className="text-[10px] font-bold uppercase text-muted-foreground">Subject</label>
                            <Input placeholder="Message Subject" value={composeSubject} onChange={e => setComposeSubject(e.target.value)} />
                          </div>
                          <div className="space-y-2">
                            <label className="text-[10px] font-bold uppercase text-muted-foreground">Body</label>
                            <textarea className="w-full h-48 p-3 border rounded-lg text-sm bg-background resize-none focus:ring-2 focus:ring-primary outline-none" placeholder="Write your message here..." value={composeBody} onChange={e => setComposeBody(e.target.value)} />
                          </div>
                          <Button className="w-full h-10" disabled={isProcessing || !composeTo}>Send Now</Button>
                        </>
                      ) : (
                        <>
                          <div className="space-y-2">
                            <label className="text-[10px] font-bold uppercase text-muted-foreground">AI Topic / Instructions</label>
                            <textarea className="w-full h-32 p-3 border rounded-lg text-sm bg-background resize-none focus:ring-2 focus:ring-purple-500 outline-none" placeholder="Explain what the email should be about (e.g., 'Request for pricing for 10 units of Widget X')..." value={composeTopic} onChange={e => setComposeTopic(e.target.value)} />
                          </div>
                          <Button className="w-full h-11 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-lg" onClick={handleAICompose} disabled={isProcessing || !composeTo || !composeTopic}>
                            {isProcessing ? (
                               <><RefreshCw className="h-4 w-4 mr-2 animate-spin" /> Yaram is writing...</>
                            ) : (
                               <><Sparkles className="h-4 w-4 mr-2" /> Draft with Yaram Kazmi</>
                            )}
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Right Column: Action Center */}
            <Card className="min-h-[600px] shadow-sm border-muted overflow-hidden flex flex-col">
              <CardHeader className="border-b bg-muted/10 py-4">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                  <Activity className="h-3.5 w-3.5" /> Action Center
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto p-0">
                <AnimatePresence mode="wait">
                  {activeView === 'drafts' && selectedDraft ? (
                    <motion.div key="draft-view" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-6 space-y-6">
                      <div className="space-y-1">
                        <Badge className="bg-orange-500 hover:bg-orange-600 border-none px-2 py-0.5 rounded text-[9px]">DRAFT REVIEW</Badge>
                        <h3 className="font-bold text-sm truncate">{selectedDraft.subject}</h3>
                        <p className="text-[10px] text-muted-foreground font-medium uppercase">To: {selectedDraft.to}</p>
                      </div>
                      
                      <div className="space-y-2">
                        <label className="text-[10px] font-bold uppercase text-muted-foreground flex justify-between">
                           Edit Draft Content
                           <span className="text-[9px] font-normal lowercase">Markdown supported</span>
                        </label>
                        <textarea className="w-full h-80 p-3 bg-muted/30 border rounded-lg text-xs leading-relaxed outline-none focus:ring-1 focus:ring-orange-500 resize-none font-mono" value={selectedDraft.body} onChange={e => setSelectedDraft({...selectedDraft, body: e.target.value})} />
                      </div>

                      <div className="flex flex-col gap-2">
                        <Button className="w-full bg-green-600 hover:bg-green-700 text-sm font-bold h-11" onClick={() => handleApproveDraft(selectedDraft)} disabled={isProcessing}>
                          <CheckCircle className="h-4 w-4 mr-2" /> Approve & Send Now
                        </Button>
                        <Button variant="ghost" className="text-xs text-muted-foreground" onClick={() => setSelectedDraft(null)}>Close Review</Button>
                      </div>
                    </motion.div>
                  ) : activeView === 'inbox' && selectedMessage ? (
                    <motion.div key="inbox-view" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-6 space-y-6">
                      <div className="space-y-2 border-b pb-4">
                        <h3 className="font-bold text-sm leading-tight">{selectedMessage.subject}</h3>
                        <div className="flex items-center justify-between">
                           <span className="text-[10px] font-medium text-muted-foreground">From: {selectedMessage.from}</span>
                           <Badge variant="secondary" className="text-[9px] h-4">INBOX</Badge>
                        </div>
                      </div>

                      <div className="p-4 bg-muted/20 rounded-lg border border-muted/50">
                        <p className="text-xs leading-relaxed whitespace-pre-wrap text-foreground/80">{selectedMessage.snippet}...</p>
                        <Button variant="link" className="text-[10px] h-fit p-0 mt-2 text-primary font-bold">View Full Thread</Button>
                      </div>

                      <div className="space-y-4 pt-4 bg-primary/5 p-4 rounded-xl border border-primary/10">
                        <div className="flex items-center justify-between">
                          <p className="text-[10px] font-bold text-primary flex items-center gap-1"><Sparkles className="h-3.5 w-3.5" /> AI Reply Instructions</p>
                          <Badge className="bg-primary text-white text-[8px] h-3.5">POWERED BY GEMINI</Badge>
                        </div>
                        <textarea className="w-full h-24 p-3 text-xs border border-primary/20 rounded-lg bg-background outline-none focus:ring-2 focus:ring-primary shadow-inner" placeholder="E.g. 'Tell them I am interested but ask for a discount'..." value={replyInstructions} onChange={e => setReplyInstructions(e.target.value)} />
                        <Button className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-xs font-bold h-10 shadow-md" onClick={handleAIReply} disabled={isProcessing || !replyInstructions}>
                          {isProcessing ? (
                             <><RefreshCw className="h-4 w-4 mr-2 animate-spin" /> Yaram is drafting...</>
                          ) : (
                             <><Sparkles className="h-4 w-4 mr-2" /> Generate AI Reply</>
                          )}
                        </Button>
                        <p className="text-[9px] text-center text-muted-foreground/60 italic">AI replies are saved to drafts for your approval</p>
                      </div>
                    </motion.div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-full py-20 px-8 text-center space-y-4">
                      <div className="h-16 w-16 bg-muted/30 rounded-full flex items-center justify-center">
                        <Inbox className="h-8 w-8 text-muted-foreground/30" />
                      </div>
                      <div className="space-y-2">
                        <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Workspace Empty</p>
                        <p className="text-[11px] text-muted-foreground italic leading-relaxed">Select an email or draft from the left panel to begin managing with Yaram Kazmi.</p>
                      </div>
                    </div>
                  )}
                </AnimatePresence>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
}
