'use client';

import { useEffect, useState } from 'react';
import { Header } from '@/components/shared/header';
import { Sidebar } from '@/components/shared/sidebar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { linkedinApi, type LinkedInMessage, type LinkedInPost } from '@/lib/api';
import { useApprovalStore } from '@/store/approval-store';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import {
  Linkedin,
  Users,
  MessageSquare,
  FileText,
  CheckCircle,
  Search,
  Calendar,
  TrendingUp,
} from 'lucide-react';

export default function LinkedInDashboardPage() {
  const [messages, setMessages] = useState<LinkedInMessage[]>([]);
  const [posts, setPosts] = useState<LinkedInPost[]>([]);
  const [connections, setConnections] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedMessage, setSelectedMessage] = useState<LinkedInMessage | null>(null);
  const [activeTab, setActiveTab] = useState<'messages' | 'posts'>('messages');
  const [status, setStatus] = useState<{ status: string; pendingActions: number; lastSync: string } | null>(null);
  const { addItem: addApproval } = useApprovalStore();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [messagesData, postsData, connectionsData, statusData] = await Promise.all([
        linkedinApi.getMessages() as Promise<LinkedInMessage[]>,
        linkedinApi.getPosts() as Promise<LinkedInPost[]>,
        linkedinApi.getConnections() as Promise<any[]>,
        linkedinApi.getStatus() as Promise<any>,
      ]);
      setMessages(messagesData);
      setPosts(postsData);
      setConnections(connectionsData.length);
      setStatus(statusData);
    } catch (error) {
      console.error('Failed to load LinkedIn data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApproveMessage = async (message: LinkedInMessage) => {
    addApproval({
      id: `approval-${message.id}`,
      type: 'linkedin',
      status: 'pending',
      riskLevel: (message.riskLevel as any) || 'medium',
      title: `LinkedIn Message: ${message.from.name}`,
      description: message.content,
      sender: message.from.name,
      createdAt: message.timestamp,
      metadata: { messageId: message.id, type: 'message' },
    });

    setSelectedMessage(null);
  };

  const handleApprovePost = async (post: LinkedInPost) => {
    addApproval({
      id: `approval-${post.id}`,
      type: 'linkedin',
      status: 'pending',
      riskLevel: post.riskLevel as any,
      title: `LinkedIn Post`,
      description: post.content.substring(0, 100),
      createdAt: post.createdAt,
      metadata: { postId: post.id, type: 'post', scheduledFor: post.scheduledFor },
    });
  };

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div className="ml-72 flex-1">
        <Header
          title="LinkedIn Dashboard"
          subtitle="AI-powered LinkedIn engagement management"
        />

        <main className="flex-1 bg-background">
          <div className="container mx-auto py-8 px-4">
            {/* Stats Bar */}
            <div className="grid gap-4 md:grid-cols-4 mb-8">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Connections</CardTitle>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{connections}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Messages</CardTitle>
                  <MessageSquare className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{messages.length}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Scheduled Posts</CardTitle>
                  <FileText className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{posts.length}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Status</CardTitle>
                  <CheckCircle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <Badge variant={status?.status === 'active' ? 'default' : 'destructive'}>
                    {status?.status || 'unknown'}
                  </Badge>
                </CardContent>
              </Card>
            </div>

            {/* Tab Navigation */}
            <div className="flex gap-4 mb-6">
              <Button
                variant={activeTab === 'messages' ? 'default' : 'outline'}
                onClick={() => setActiveTab('messages')}
                className="flex items-center gap-2"
              >
                <MessageSquare className="h-4 w-4" />
                Messages
              </Button>
              <Button
                variant={activeTab === 'posts' ? 'default' : 'outline'}
                onClick={() => setActiveTab('posts')}
                className="flex items-center gap-2"
              >
                <FileText className="h-4 w-4" />
                Scheduled Posts
              </Button>
            </div>

            {/* Main Content */}
            <div className="grid gap-6 lg:grid-cols-3">
              {/* List */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>
                      {activeTab === 'messages' ? 'Messages' : 'Scheduled Posts'}
                    </CardTitle>
                    <Button variant="outline" size="icon">
                      <Search className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {isLoading ? (
                    <div className="text-center py-8 text-muted-foreground">Loading...</div>
                  ) : activeTab === 'messages' ? (
                    messages.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground">
                        <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>No messages found</p>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {messages.map((message, index) => (
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
                              !message.read && 'bg-muted/30'
                            )}
                            onClick={() => setSelectedMessage(message)}
                          >
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="font-medium truncate">{message.from.name}</span>
                                  {!message.read && (
                                    <Badge variant="outline" className="text-xs">
                                      New
                                    </Badge>
                                  )}
                                </div>
                                <p className="text-sm text-muted-foreground line-clamp-2">
                                  {message.content}
                                </p>
                              </div>
                              <div className="text-xs text-muted-foreground whitespace-nowrap">
                                {new Date(message.timestamp).toLocaleDateString()}
                              </div>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    )
                  ) : posts.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No scheduled posts</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {posts.map((post, index) => (
                        <motion.div
                          key={post.id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.03 }}
                          className="p-4 rounded-lg border hover:bg-muted/50 cursor-pointer transition-colors"
                          onClick={() => handleApprovePost(post)}
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1 min-w-0">
                              <p className="text-sm text-muted-foreground line-clamp-2">
                                {post.content}
                              </p>
                              <div className="flex items-center gap-4 mt-2">
                                <Badge variant="outline">{post.status}</Badge>
                                <span className="text-xs text-muted-foreground flex items-center gap-1">
                                  <Calendar className="h-3 w-3" />
                                  {new Date(post.scheduledFor).toLocaleDateString()}
                                </span>
                              </div>
                            </div>
                            <Badge variant={post.riskLevel === 'high' ? 'destructive' : 'outline'}>
                              {post.riskLevel}
                            </Badge>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Detail / Actions */}
              <Card>
                <CardHeader>
                  <CardTitle>
                    {activeTab === 'messages'
                      ? selectedMessage
                        ? 'Message Details'
                        : 'Select a message'
                      : 'Post Actions'}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {activeTab === 'messages' ? (
                    selectedMessage ? (
                      <div className="space-y-4">
                        <div>
                          <p className="text-sm text-muted-foreground">From</p>
                          <p className="font-medium">{selectedMessage.from.name}</p>
                          <p className="text-sm text-muted-foreground">{selectedMessage.from.headline}</p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Received</p>
                          <p>
                            {new Date(selectedMessage.timestamp).toLocaleString()}
                          </p>
                        </div>
                        <div className="pt-4 border-t">
                          <p className="text-sm text-muted-foreground mb-2">Message</p>
                          <p className="text-sm">{selectedMessage.content}</p>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex gap-2 pt-4 border-t">
                          <Button
                            onClick={() => handleApproveMessage(selectedMessage)}
                            className="flex-1 bg-green-600 hover:bg-green-700"
                          >
                            <CheckCircle className="h-4 w-4 mr-2" />
                            Approve
                          </Button>
                          <Button variant="outline" className="flex-1">
                            Reject
                          </Button>
                        </div>
                        <Button variant="outline" className="w-full">
                          <Linkedin className="h-4 w-4 mr-2" />
                          Reply via LinkedIn
                        </Button>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-muted-foreground">
                        <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>Select a message to view details</p>
                      </div>
                    )
                  ) : (
                    <div className="space-y-4">
                      <div className="text-center py-8 text-muted-foreground">
                        <TrendingUp className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>Select a post to take action</p>
                      </div>
                      <Button variant="outline" className="w-full">
                        <Calendar className="h-4 w-4 mr-2" />
                        Reschedule Post
                      </Button>
                      <Button variant="outline" className="w-full">
                        <FileText className="h-4 w-4 mr-2" />
                        Edit Content
                      </Button>
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
