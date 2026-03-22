'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Sidebar } from '@/components/shared/sidebar';
import { Header } from '@/components/shared/header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Bot, Send, RefreshCw, CheckCircle, XCircle, Clock,
  Twitter, Linkedin, Facebook, Instagram, MessageSquare, Mail,
  Sparkles, Loader2, Copy, Check,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAgentStatus, useGenerateContent, usePostContent, usePostHistory } from '@/hooks/use-ai-agent';

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

export default function AiAgentPage() {
  const [platform, setPlatform] = useState('twitter');
  const [topic, setTopic] = useState('');
  const [generatedContent, setGeneratedContent] = useState('');
  const [copied, setCopied] = useState(false);

  const { data: status } = useAgentStatus();
  const generateMutation = useGenerateContent();
  const postMutation = usePostContent();
  const { data: history } = usePostHistory(30);

  const handleGenerate = () => {
    if (!topic.trim()) return;
    generateMutation.mutate({ platform, topic }, {
      onSuccess: (data) => setGeneratedContent(data.content),
    });
  };

  const handlePost = () => {
    if (!generatedContent) return;
    postMutation.mutate({ platform, content: generatedContent }, {
      onSuccess: () => {
        setGeneratedContent('');
        setTopic('');
      },
    });
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(generatedContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="ml-72 flex-1 flex flex-col">
        <Header title="AI Agent" subtitle="Generate & Post Social Content" />
        <main className="flex-1 bg-background">
          <div className="container mx-auto py-8 px-4 space-y-6">
            {/* Status Bar */}
            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
              <Card>
                <CardContent className="py-4">
                  <div className="flex items-center gap-6 flex-wrap">
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-5 w-5 text-purple-500" />
                      <span className="text-sm font-medium">AI Providers:</span>
                      <Badge variant={status?.gemini === 'ready' ? 'default' : 'outline'} className={status?.gemini === 'ready' ? 'bg-green-600' : ''}>
                        Gemini {status?.gemini === 'ready' ? '✓' : '✗'}
                      </Badge>
                      <Badge variant={status?.grok === 'ready' ? 'default' : 'outline'} className={status?.grok === 'ready' ? 'bg-blue-600' : ''}>
                        Grok {status?.grok === 'ready' ? '✓' : '✗'}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-medium">Platforms:</span>
                      {status?.platforms && Object.entries(status.platforms).map(([p, s]) => {
                        const Icon = PLATFORM_ICONS[p] || Bot;
                        return (
                          <Badge key={p} variant="outline" className="gap-1">
                            <Icon className={cn('h-3 w-3', PLATFORM_COLORS[p])} />
                            {p} {s === 'ready' ? '✓' : s === 'available' ? '~' : '✗'}
                          </Badge>
                        );
                      })}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            <div className="grid gap-6 lg:grid-cols-3">
              {/* Left: Generator */}
              <div className="lg:col-span-2 space-y-6">
                {/* Platform Selector */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Bot className="h-5 w-5 text-cyan-500" />
                      Generate Content
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Platform Pills */}
                    <div className="flex gap-2 flex-wrap">
                      {(status?.supported || ['twitter', 'linkedin', 'facebook', 'instagram', 'whatsapp', 'email']).map((p) => {
                        const Icon = PLATFORM_ICONS[p] || Bot;
                        return (
                          <Button
                            key={p}
                            size="sm"
                            variant={platform === p ? 'default' : 'outline'}
                            onClick={() => setPlatform(p)}
                            className="gap-1.5 capitalize"
                          >
                            <Icon className={cn('h-4 w-4', platform !== p && PLATFORM_COLORS[p])} />
                            {p}
                          </Button>
                        );
                      })}
                    </div>

                    {/* Topic Input */}
                    <div className="flex gap-2">
                      <Input
                        placeholder="Topic likhein... e.g. AI aur future of work"
                        value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
                        className="flex-1"
                      />
                      <Button onClick={handleGenerate} disabled={!topic.trim() || generateMutation.isPending}>
                        {generateMutation.isPending ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Sparkles className="h-4 w-4" />
                        )}
                        Generate
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* Generated Content Preview */}
                {(generatedContent || generateMutation.isPending) && (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                    <Card className="border-primary/30">
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <CardTitle className="flex items-center gap-2 text-lg">
                            {(() => { const Icon = PLATFORM_ICONS[platform] || Bot; return <Icon className={cn('h-5 w-5', PLATFORM_COLORS[platform])} />; })()}
                            {platform.charAt(0).toUpperCase() + platform.slice(1)} Draft
                          </CardTitle>
                          <div className="flex gap-2">
                            <Badge variant="outline">{generatedContent.length} chars</Badge>
                            {generateMutation.data?.provider && (
                              <Badge className="bg-purple-600">via {generateMutation.data.provider}</Badge>
                            )}
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {generateMutation.isPending ? (
                          <div className="flex items-center gap-3 py-8 justify-center text-muted-foreground">
                            <Loader2 className="h-5 w-5 animate-spin" />
                            Generating content...
                          </div>
                        ) : (
                          <>
                            <div className="rounded-xl bg-muted/50 p-4 font-medium text-base leading-relaxed whitespace-pre-wrap">
                              {generatedContent}
                            </div>
                            <div className="flex gap-2 justify-end">
                              <Button size="sm" variant="outline" onClick={handleCopy}>
                                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                                {copied ? 'Copied!' : 'Copy'}
                              </Button>
                              <Button size="sm" variant="outline" onClick={handleGenerate} disabled={generateMutation.isPending}>
                                <RefreshCw className="h-4 w-4" /> Regenerate
                              </Button>
                              <Button size="sm" onClick={handlePost} disabled={postMutation.isPending}>
                                {postMutation.isPending ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Send className="h-4 w-4" />
                                )}
                                Post to {platform.charAt(0).toUpperCase() + platform.slice(1)}
                              </Button>
                            </div>
                          </>
                        )}
                      </CardContent>
                    </Card>
                  </motion.div>
                )}

                {/* Post Result */}
                {postMutation.isSuccess && (
                  <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
                    <Card className={postMutation.data?.posted ? 'border-green-500/50 bg-green-500/5' : 'border-orange-500/50 bg-orange-500/5'}>
                      <CardContent className="py-4 flex items-center gap-3">
                        {postMutation.data?.posted ? (
                          <>
                            <CheckCircle className="h-6 w-6 text-green-500" />
                            <div>
                              <p className="font-semibold text-green-700 dark:text-green-400">Posted successfully!</p>
                              <p className="text-sm text-muted-foreground">
                                Saved to {postMutation.data.savedTo} via {postMutation.data.method}
                              </p>
                            </div>
                          </>
                        ) : (
                          <>
                            <Clock className="h-6 w-6 text-orange-500" />
                            <div>
                              <p className="font-semibold text-orange-700 dark:text-orange-400">Saved for approval</p>
                              <p className="text-sm text-muted-foreground">
                                Content saved to Pending_Approval/. {postMutation.data?.error || ''}
                              </p>
                            </div>
                          </>
                        )}
                      </CardContent>
                    </Card>
                  </motion.div>
                )}

                {postMutation.isError && (
                  <Card className="border-red-500/50 bg-red-500/5">
                    <CardContent className="py-4 flex items-center gap-3">
                      <XCircle className="h-6 w-6 text-red-500" />
                      <p className="font-semibold text-red-700 dark:text-red-400">
                        Error: {postMutation.error?.message}
                      </p>
                    </CardContent>
                  </Card>
                )}
              </div>

              {/* Right: Post History */}
              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Clock className="h-5 w-5 text-orange-500" />
                      Post History
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 max-h-[600px] overflow-y-auto">
                    {!history?.length ? (
                      <p className="text-sm text-muted-foreground text-center py-4">No posts yet</p>
                    ) : (
                      history.map((item) => {
                        const Icon = PLATFORM_ICONS[item.platform] || Bot;
                        return (
                          <div key={item.filename} className="rounded-lg border p-3 space-y-2">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <Icon className={cn('h-4 w-4', PLATFORM_COLORS[item.platform])} />
                                <span className="text-sm font-medium capitalize">{item.platform}</span>
                              </div>
                              <Badge variant={item.status === 'done' ? 'default' : 'outline'}
                                className={item.status === 'done' ? 'bg-green-600' : ''}>
                                {item.status}
                              </Badge>
                            </div>
                            <p className="text-xs text-muted-foreground line-clamp-3">
                              {item.content_preview}
                            </p>
                            <p className="text-[10px] text-muted-foreground">
                              {new Date(item.created_at).toLocaleString()}
                            </p>
                          </div>
                        );
                      })
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
