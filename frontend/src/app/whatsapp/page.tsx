'use client';

import { useState, useEffect } from 'react';
import { Header } from '@/components/shared/header';
import { Sidebar } from '@/components/shared/sidebar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { whatsappApi, WhatsAppMessage, WhatsAppContact } from '@/lib/api';
import { formatRelativeTime, truncateText, cn } from '@/lib/utils';
import { 
  MessageCircle, 
  Send, 
  Users, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  RefreshCw,
  User,
  Search,
  Filter,
  MessageSquare,
  Smartphone
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { RiskBadge } from '@/components/vault/risk-badge';

export default function WhatsAppPage() {
  const [messages, setMessages] = useState<WhatsAppMessage[]>([]);
  const [contacts, setContacts] = useState<WhatsAppContact[]>([]);
  const [pendingMessages, setPendingMessages] = useState<WhatsAppMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<{ status: string; pendingMessages: number } | null>(null);
  const [selectedMessage, setSelectedMessage] = useState<WhatsAppMessage | null>(null);
  const [filter, setFilter] = useState<'all' | 'received' | 'pending'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Compose state
  const [composeRecipient, setComposeRecipient] = useState('');
  const [composeMessage, setComposeMessage] = useState('');
  const [composeSending, setComposeSending] = useState(false);
  const [composeResult, setComposeResult] = useState<{ success: boolean; message: string } | null>(null);

  // Approve/reject state
  const [replyContent, setReplyContent] = useState('');
  const [approvingId, setApprovingId] = useState<string | null>(null);

  const loadMessages = async () => {
    try {
      setLoading(true);
      const response = await whatsappApi.getMessages({ limit: 50 });
      // Backend returns { data: { data: [...], meta: {...} } }, axios unwraps outer data
      let msgs: WhatsAppMessage[] = [];
      if (Array.isArray(response)) {
        msgs = response;
      } else if (response?.data && Array.isArray(response.data)) {
        msgs = response.data;
      } else if (response?.data?.data && Array.isArray(response.data.data)) {
        msgs = response.data.data;
      }
      // Deduplicate by id
      const seen = new Set<string>();
      const unique = msgs.filter(m => {
        if (seen.has(m.id)) return false;
        seen.add(m.id);
        return true;
      });
      setMessages(unique);
    } catch (err) {
      console.error('Failed to load messages:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadContacts = async () => {
    try {
      const data = await whatsappApi.getContacts();
      let contactsData = data || [];
      
      setContacts(contactsData);
    } catch (err) {
      console.error('Failed to load contacts:', err);
    }
  };

  const loadPending = async () => {
    try {
      const data = await whatsappApi.getPendingMessages();
      let pending = data || [];
      
      setPendingMessages(pending);
    } catch (err) {
      console.error('Failed to load pending messages:', err);
    }
  };

  const loadStatus = async () => {
    try {
      const data = await whatsappApi.getStatus();
      setStatus(data);
    } catch (err) {
      console.error('Failed to load status:', err);
    }
  };

  useEffect(() => {
    loadMessages();
    loadContacts();
    loadPending();
    loadStatus();

    // Poll for new messages every 30 seconds
    const interval = setInterval(() => {
      loadMessages();
      loadPending();
      loadStatus();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const handleSendMessage = async () => {
    if (!composeRecipient.trim() || !composeMessage.trim()) return;
    setComposeSending(true);
    setComposeResult(null);
    try {
      await whatsappApi.sendMessage(composeRecipient.trim(), composeMessage.trim(), false);
      setComposeResult({ success: true, message: 'Message sent successfully!' });
      setComposeRecipient('');
      setComposeMessage('');
      loadMessages();
    } catch (err) {
      setComposeResult({ success: false, message: 'Failed to send message. Check console for details.' });
      console.error('Failed to send message:', err);
    } finally {
      setComposeSending(false);
    }
  };

  const handleApproveMessage = async (messageId: string) => {
    if (!replyContent && filter === 'pending') return;
    
    setApprovingId(messageId);
    try {
      await whatsappApi.approveMessage(messageId, replyContent || selectedMessage?.content || '');
      setReplyContent('');
      setSelectedMessage(null);
      loadPending();
      loadMessages();
    } catch (err) {
      console.error('Failed to approve message:', err);
    } finally {
      setApprovingId(null);
    }
  };

  const handleRejectMessage = async (messageId: string) => {
    if (!confirm('Reject this message?')) return;
    
    try {
      await whatsappApi.rejectMessage(messageId, 'User rejected');
      setSelectedMessage(null);
      loadPending();
    } catch (err) {
      console.error('Failed to reject message:', err);
    }
  };

  const allMessages = (() => {
    const seen = new Set<string>();
    const merged: WhatsAppMessage[] = [];
    for (const msg of [...messages, ...pendingMessages]) {
      if (!seen.has(msg.id)) {
        seen.add(msg.id);
        merged.push(msg);
      }
    }
    merged.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    return merged;
  })();

  const filteredMessages = allMessages.filter(msg => {
    const matchesFilter = 
      filter === 'all' || 
      (filter === 'received' && msg.status === 'received') || 
      (filter === 'pending' && msg.status === 'pending');
    
    const matchesSearch = 
      msg.from.toLowerCase().includes(searchQuery.toLowerCase()) || 
      msg.content.toLowerCase().includes(searchQuery.toLowerCase());
      
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <div className="ml-72 flex-1">
        <Header
          title="WhatsApp Dashboard"
          subtitle="Real-time messaging with approval workflow"
        />

        <main className="flex-1 bg-background">
          <div className="container mx-auto py-8 px-4">
            {/* Stats Bar */}
            <div className="grid gap-4 md:grid-cols-4 mb-8">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Messages</CardTitle>
                  <MessageSquare className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{messages.length}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Pending Approval</CardTitle>
                  <Clock className="h-4 w-4 text-orange-500" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{pendingMessages.length}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Contacts</CardTitle>
                  <Users className="h-4 w-4 text-blue-500" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{contacts.length}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Service Status</CardTitle>
                  <Smartphone className={cn(
                    "h-4 w-4",
                    status?.status === 'active' ? "text-green-500" : "text-muted-foreground"
                  )} />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold capitalize">{status?.status || 'Offline'}</div>
                </CardContent>
              </Card>
            </div>

            {/* Compose Message */}
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Send className="h-5 w-5" />
                  Compose Message
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col sm:flex-row gap-3">
                  <Input
                    placeholder="Recipient (name or phone number)"
                    value={composeRecipient}
                    onChange={(e) => setComposeRecipient(e.target.value)}
                    className="sm:w-64"
                  />
                  <Input
                    placeholder="Type your message..."
                    value={composeMessage}
                    onChange={(e) => setComposeMessage(e.target.value)}
                    className="flex-1"
                    onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                  />
                  <Button
                    onClick={handleSendMessage}
                    disabled={composeSending || !composeRecipient.trim() || !composeMessage.trim()}
                  >
                    {composeSending ? (
                      <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                      <Send className="h-4 w-4 mr-2" />
                    )}
                    Send
                  </Button>
                </div>
                {composeResult && (
                  <div className={cn(
                    'mt-3 p-3 rounded-lg text-sm flex items-center gap-2',
                    composeResult.success ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'
                  )}>
                    {composeResult.success ? <CheckCircle className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                    {composeResult.message}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Main Content Grid */}
            <div className="grid gap-6 lg:grid-cols-3">
              {/* Message List Column */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>Messages</CardTitle>
                    <div className="flex items-center gap-2">
                      <div className="relative">
                        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                          placeholder="Search messages..."
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          className="pl-8 w-64"
                        />
                      </div>
                      <Button variant="outline" size="icon" onClick={loadMessages}>
                        <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
                      </Button>
                    </div>
                  </div>

                  {/* Filters */}
                  <div className="flex gap-2 mt-4">
                    <Button
                      variant={filter === 'all' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setFilter('all')}
                    >
                      All
                    </Button>
                    <Button
                      variant={filter === 'received' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setFilter('received')}
                    >
                      Received
                    </Button>
                    <Button
                      variant={filter === 'pending' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setFilter('pending')}
                    >
                      Pending Approval
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {loading && messages.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground">Loading...</div>
                    ) : filteredMessages.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground">
                        <MessageCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>No messages found</p>
                      </div>
                    ) : (
                      filteredMessages.map((msg, index) => (
                        <motion.div
                          key={`${msg.id}-${index}`}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.03 }}
                          className={cn(
                            'p-4 rounded-lg border cursor-pointer transition-colors',
                            selectedMessage?.id === msg.id
                              ? 'bg-primary/10 border-primary'
                              : 'hover:bg-muted/50',
                            msg.status === 'pending' && 'border-orange-200 bg-orange-50/30'
                          )}
                          onClick={() => setSelectedMessage(msg)}
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-medium truncate">{msg.from}</span>
                                <RiskBadge level={msg.risk_level} />
                                {msg.status === 'pending' && (
                                  <Badge variant="outline" className="text-orange-600 border-orange-200 bg-orange-50">
                                    Pending
                                  </Badge>
                                )}
                              </div>
                              <p className="text-sm text-muted-foreground line-clamp-1">
                                {msg.content}
                              </p>
                            </div>
                            <div className="text-xs text-muted-foreground whitespace-nowrap">
                              {formatRelativeTime(new Date(msg.timestamp))}
                            </div>
                          </div>
                        </motion.div>
                      ))
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Message Details Column */}
              <Card>
                <CardHeader>
                  <CardTitle>
                    {selectedMessage ? 'Message Details' : 'Select a message'}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {selectedMessage ? (
                    <div className="space-y-4">
                      <div className="flex items-center gap-3 p-3 bg-muted/30 rounded-lg">
                        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                          <User className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <p className="font-medium">{selectedMessage.from}</p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(selectedMessage.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </div>

                      <div>
                        <p className="text-sm text-muted-foreground mb-2">Content</p>
                        <div className="p-4 bg-background border rounded-lg">
                          <p className="text-sm whitespace-pre-wrap">{selectedMessage.content}</p>
                        </div>
                      </div>

                      <div className="flex gap-2">
                        <Badge variant="outline">Type: {selectedMessage.type}</Badge>
                        <Badge variant="outline">Status: {selectedMessage.status}</Badge>
                      </div>

                      {selectedMessage.status === 'pending' ? (
                        <div className="pt-4 border-t space-y-4">
                          <div>
                            <label className="text-sm font-medium mb-2 block">
                              Edit Reply (Optional)
                            </label>
                            <textarea
                              className="w-full p-3 text-sm bg-background border rounded-lg focus:ring-2 focus:ring-primary outline-none min-h-[100px]"
                              placeholder="Add or edit the message content..."
                              value={replyContent || selectedMessage.content}
                              onChange={(e) => setReplyContent(e.target.value)}
                            />
                          </div>
                          <div className="flex gap-2">
                            <Button
                              onClick={() => handleApproveMessage(selectedMessage.id)}
                              className="flex-1 bg-green-600 hover:bg-green-700"
                              disabled={approvingId === selectedMessage.id}
                            >
                              <CheckCircle className="h-4 w-4 mr-2" />
                              Approve
                            </Button>
                            <Button
                              variant="outline"
                              onClick={() => handleRejectMessage(selectedMessage.id)}
                              className="flex-1 text-red-600 hover:bg-red-50"
                            >
                              <XCircle className="h-4 w-4 mr-2" />
                              Reject
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <div className="pt-4 border-t space-y-3">
                          <div>
                            <label className="text-sm font-medium mb-2 block">Reply</label>
                            <textarea
                              className="w-full p-3 text-sm bg-background border rounded-lg focus:ring-2 focus:ring-primary outline-none min-h-[80px]"
                              placeholder="Type your reply..."
                              value={replyContent}
                              onChange={(e) => setReplyContent(e.target.value)}
                            />
                          </div>
                          <Button className="w-full" onClick={async () => {
                            if (selectedMessage && replyContent.trim()) {
                              try {
                                setComposeSending(true);
                                await whatsappApi.sendMessage(selectedMessage.from, replyContent.trim(), false);
                                setReplyContent('');
                                setSelectedMessage(null);
                                loadMessages();
                                setComposeResult({ success: true, message: 'Reply sent!' });
                              } catch (err) {
                                console.error('Failed to send reply:', err);
                                setComposeResult({ success: false, message: 'Failed to send reply.' });
                              } finally {
                                setComposeSending(false);
                              }
                            }
                          }} disabled={!replyContent.trim() || composeSending}>
                            {composeSending ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Send className="h-4 w-4 mr-2" />}
                            Send Reply
                          </Button>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-12 text-muted-foreground">
                      <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-20" />
                      <p>Select a message from the list to view details and take actions.</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
