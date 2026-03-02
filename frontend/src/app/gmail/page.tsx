/**
 * Gmail Dashboard Page
 * Inbox management with AI classification and approval workflow
 */

'use client';

import { useEffect, useState } from 'react';
import { Header } from '@/components/shared/header';
import { Sidebar } from '@/components/shared/sidebar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { gmailApi, type GmailMessage } from '@/lib/api';
import { useApprovalStore } from '@/store/approval-store';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import {
  Inbox,
  Send,
  Archive,
  AlertCircle,
  Search,
  Filter,
  CheckCircle,
  XCircle,
  Eye,
  Paperclip,
} from 'lucide-react';

export default function GmailDashboardPage() {
  const [messages, setMessages] = useState<GmailMessage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedMessage, setSelectedMessage] = useState<GmailMessage | null>(null);
  const [filter, setFilter] = useState<'all' | 'unread' | 'important'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const { addItem: addApproval } = useApprovalStore();

  useEffect(() => {
    loadMessages();
  }, [filter]);

  const loadMessages = async () => {
    setIsLoading(true);
    try {
      const response = await gmailApi.getInbox({
        unread: filter === 'unread',
      });
      setMessages(response.data);
    } catch (error) {
      console.error('Failed to load messages:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async (message: GmailMessage) => {
    // Create approval item for this message
    addApproval({
      id: `approval-${message.id}`,
      type: 'gmail',
      status: 'pending',
      riskLevel: message.labels.includes('IMPORTANT') ? 'medium' : 'low',
      title: `Email: ${message.subject}`,
      description: message.snippet,
      sender: message.from,
      createdAt: message.receivedAt,
      metadata: { messageId: message.id, threadId: message.threadId },
    });

    // Show success feedback
    setSelectedMessage(null);
  };

  const handleReject = async (message: GmailMessage) => {
    // Archive or mark as read
    console.log('Rejecting message:', message.id);
    setSelectedMessage(null);
  };

  const filteredMessages = messages.filter((msg) => {
    const matchesSearch =
      msg.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
      msg.from.toLowerCase().includes(searchQuery.toLowerCase()) ||
      msg.snippet.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div className="ml-72 flex-1">
        <Header
          title="Gmail Dashboard"
          subtitle="AI-powered inbox management"
          onBack={() => (window.location.href = '/dashboard')}
        />

        <main className="flex-1 bg-background">
          <div className="container mx-auto py-8 px-4">
            {/* Stats Bar */}
            <div className="grid gap-4 md:grid-cols-4 mb-8">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Messages</CardTitle>
                <Inbox className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{messages.length}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Unread</CardTitle>
                <AlertCircle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {messages.filter((m) => m.labels.includes('UNREAD')).length}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Important</CardTitle>
                <AlertCircle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {messages.filter((m) => m.labels.includes('IMPORTANT')).length}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">With Attachments</CardTitle>
                <Paperclip className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {messages.filter((m) => m.hasAttachment).length}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Message List */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Inbox</CardTitle>
                  <div className="flex items-center gap-2">
                    <div className="relative">
                      <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                      <Input
                        placeholder="Search emails..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-8 w-64"
                      />
                    </div>
                    <Button variant="outline" size="icon">
                      <Filter className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {/* Filter Tabs */}
                <div className="flex gap-2 mt-4">
                  <Button
                    variant={filter === 'all' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setFilter('all')}
                  >
                    All
                  </Button>
                  <Button
                    variant={filter === 'unread' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setFilter('unread')}
                  >
                    Unread
                  </Button>
                  <Button
                    variant={filter === 'important' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setFilter('important')}
                  >
                    Important
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="text-center py-8 text-muted-foreground">Loading...</div>
                ) : filteredMessages.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Inbox className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No messages found</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {filteredMessages.map((message, index) => (
                      <motion.div
                        key={message.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.03 }}
                        className={cn(
                          'p-4 rounded-lg border cursor-pointer transition-colors',
                          selectedMessage?.id === message.id
                            ? 'bg-primary/10 border-primary'
                            : 'hover:bg-muted/50',
                          !message.labels.includes('READ') && 'bg-muted/30'
                        )}
                        onClick={() => setSelectedMessage(message)}
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium truncate">{message.from}</span>
                              {message.labels.includes('IMPORTANT') && (
                                <Badge variant="outline" className="text-xs">
                                  Important
                                </Badge>
                              )}
                              {message.hasAttachment && (
                                <Paperclip className="h-3 w-3 text-muted-foreground" />
                              )}
                            </div>
                            <p className="text-sm font-medium truncate">{message.subject}</p>
                            <p className="text-sm text-muted-foreground line-clamp-2">
                              {message.snippet}
                            </p>
                          </div>
                          <div className="text-xs text-muted-foreground whitespace-nowrap">
                            {new Date(message.receivedAt).toLocaleTimeString([], {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Message Detail / Actions */}
            <Card>
              <CardHeader>
                <CardTitle>
                  {selectedMessage ? 'Message Details' : 'Select a message'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {selectedMessage ? (
                  <div className="space-y-4">
                    <div>
                      <p className="text-sm text-muted-foreground">From</p>
                      <p className="font-medium">{selectedMessage.from}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Subject</p>
                      <p className="font-medium">{selectedMessage.subject}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Received</p>
                      <p>
                        {new Date(selectedMessage.receivedAt).toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground mb-2">Labels</p>
                      <div className="flex flex-wrap gap-1">
                        {selectedMessage.labels.map((label) => (
                          <Badge key={label} variant="outline" className="text-xs">
                            {label}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div className="pt-4 border-t">
                      <p className="text-sm text-muted-foreground mb-2">Preview</p>
                      <p className="text-sm">{selectedMessage.snippet}</p>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-2 pt-4 border-t">
                      <Button
                        onClick={() => handleApprove(selectedMessage)}
                        className="flex-1 bg-green-600 hover:bg-green-700"
                      >
                        <CheckCircle className="h-4 w-4 mr-2" />
                        Approve
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => handleReject(selectedMessage)}
                        className="flex-1"
                      >
                        <XCircle className="h-4 w-4 mr-2" />
                        Reject
                      </Button>
                    </div>
                    <Button variant="outline" className="w-full">
                      <Eye className="h-4 w-4 mr-2" />
                      View Full Message
                    </Button>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <Inbox className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Select a message to view details</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
