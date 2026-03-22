'use client';

import { useEffect, useState } from 'react';
import { Header } from '@/components/shared/header';
import { Sidebar } from '@/components/shared/sidebar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { salesApi, type SalesLead, type PipelineStats } from '@/lib/api';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import {
  Users,
  TrendingUp,
  DollarSign,
  Calendar,
  Search,
  Plus,
  Send,
  FileText,
  Target,
  ArrowRight,
  ChevronRight,
} from 'lucide-react';

const STAGES = [
  { key: 'new', label: 'New Leads', color: 'bg-blue-500' },
  { key: 'contacted', label: 'Contacted', color: 'bg-yellow-500' },
  { key: 'responded', label: 'Responded', color: 'bg-purple-500' },
  { key: 'meeting', label: 'Meeting', color: 'bg-indigo-500' },
  { key: 'closed_won', label: 'Closed Won', color: 'bg-green-500' },
  { key: 'closed_lost', label: 'Closed Lost', color: 'bg-red-500' },
];

export default function SalesDashboardPage() {
  const [leads, setLeads] = useState<SalesLead[]>([]);
  const [stats, setStats] = useState<PipelineStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedLead, setSelectedLead] = useState<SalesLead | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeStageFilter, setActiveStageFilter] = useState<string | null>(null);
  const [discoveryKeywords, setDiscoveryKeywords] = useState('AI,SaaS');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [leadsRes, statsRes] = await Promise.all([
        salesApi.getLeads(),
        salesApi.getPipelineStats(),
      ]);
      setLeads(leadsRes);
      setStats(statsRes);
    } catch (error) {
      console.error('Failed to load sales data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDiscover = async () => {
    try {
      await salesApi.triggerDiscovery(discoveryKeywords);
      setTimeout(loadData, 2000);
    } catch (error) {
      console.error('Discovery failed:', error);
    }
  };

  const filteredLeads = leads.filter((lead) => {
    const matchesSearch =
      lead.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      lead.company?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStage = !activeStageFilter || lead.stage === activeStageFilter;
    return matchesSearch && matchesStage;
  });

  const getStageLeads = (stageKey: string) =>
    leads.filter((l) => l.stage === stageKey);

  const getScoreBadge = (score: number) => {
    if (score >= 80) return 'bg-green-600';
    if (score >= 60) return 'bg-yellow-600';
    if (score >= 40) return 'bg-orange-600';
    return 'bg-red-600';
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="ml-72 flex-1">
        <Header
          title="Sales Pipeline"
          subtitle="AI-powered lead management and outreach"
        />

        <main className="flex-1 bg-background">
          <div className="container mx-auto py-8 px-4">
            {/* Stats Bar */}
            <div className="grid gap-4 md:grid-cols-4 mb-8">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Leads</CardTitle>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats?.total_leads ?? 0}</div>
                  <p className="text-xs text-muted-foreground">
                    Avg score: {stats?.avg_score?.toFixed(0) ?? 0}
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {stats && stats.total_leads > 0
                      ? ((stats.by_stage?.closed_won ?? 0) / stats.total_leads * 100).toFixed(0)
                      : 0}%
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {stats?.by_stage?.closed_won ?? 0} closed won
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Revenue</CardTitle>
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    ${(stats?.total_revenue ?? 0).toLocaleString()}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    ${(stats?.pending_revenue ?? 0).toLocaleString()} pending
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Meetings</CardTitle>
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats?.by_stage?.meeting ?? 0}</div>
                  <p className="text-xs text-muted-foreground">Scheduled this week</p>
                </CardContent>
              </Card>
            </div>

            {/* Actions Bar */}
            <div className="flex items-center gap-4 mb-6">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search leads..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8"
                />
              </div>
              <div className="flex items-center gap-2">
                <Input
                  placeholder="Keywords"
                  value={discoveryKeywords}
                  onChange={(e) => setDiscoveryKeywords(e.target.value)}
                  className="w-40"
                />
                <Button onClick={handleDiscover}>
                  <Plus className="h-4 w-4 mr-2" />
                  Find Leads
                </Button>
              </div>
            </div>

            {/* Kanban Board */}
            <div className="grid gap-4 grid-cols-1 lg:grid-cols-6 mb-8">
              {STAGES.map((stage) => {
                const stageLeads = getStageLeads(stage.key);
                return (
                  <Card key={stage.key} className="min-h-[300px]">
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className={cn('w-2 h-2 rounded-full', stage.color)} />
                          <CardTitle className="text-xs font-medium">{stage.label}</CardTitle>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {stageLeads.length}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-2 px-2">
                      {stageLeads.map((lead, i) => (
                        <motion.div
                          key={lead.id}
                          initial={{ opacity: 0, y: 5 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: i * 0.05 }}
                          className={cn(
                            'p-2 rounded-md border cursor-pointer transition-colors text-xs',
                            selectedLead?.id === lead.id
                              ? 'bg-primary/10 border-primary'
                              : 'hover:bg-muted/50'
                          )}
                          onClick={() => setSelectedLead(lead)}
                        >
                          <p className="font-medium truncate">{lead.name}</p>
                          <p className="text-muted-foreground truncate">{lead.company}</p>
                          <div className="flex items-center justify-between mt-1">
                            <span className="text-muted-foreground">{lead.title}</span>
                            <Badge className={cn('text-[10px]', getScoreBadge(Number(lead.score)))}>
                              {lead.score}
                            </Badge>
                          </div>
                        </motion.div>
                      ))}
                      {stageLeads.length === 0 && (
                        <p className="text-xs text-muted-foreground text-center py-4">
                          No leads
                        </p>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {/* Lead Detail Panel + Lead List */}
            <div className="grid gap-6 lg:grid-cols-3">
              {/* Lead List */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>All Leads</CardTitle>
                    <div className="flex gap-1">
                      <Button
                        variant={activeStageFilter === null ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setActiveStageFilter(null)}
                      >
                        All
                      </Button>
                      {STAGES.slice(0, 4).map((s) => (
                        <Button
                          key={s.key}
                          variant={activeStageFilter === s.key ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => setActiveStageFilter(s.key)}
                        >
                          {s.label}
                        </Button>
                      ))}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {isLoading ? (
                    <div className="text-center py-8 text-muted-foreground">Loading...</div>
                  ) : filteredLeads.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No leads found. Click &quot;Find Leads&quot; to discover prospects.</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {filteredLeads.map((lead, index) => (
                        <motion.div
                          key={lead.id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.03 }}
                          className={cn(
                            'p-4 rounded-lg border cursor-pointer transition-colors',
                            selectedLead?.id === lead.id
                              ? 'bg-primary/10 border-primary'
                              : 'hover:bg-muted/50'
                          )}
                          onClick={() => setSelectedLead(lead)}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-medium">{lead.name}</span>
                                <Badge className={cn('text-xs', getScoreBadge(Number(lead.score)))}>
                                  Score: {lead.score}
                                </Badge>
                                <Badge variant="outline" className="text-xs">
                                  {lead.stage}
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground">
                                {lead.title} at {lead.company}
                              </p>
                            </div>
                            <ChevronRight className="h-4 w-4 text-muted-foreground" />
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Detail Panel */}
              <Card>
                <CardHeader>
                  <CardTitle>
                    {selectedLead ? 'Lead Details' : 'Select a lead'}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {selectedLead ? (
                    <div className="space-y-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Name</p>
                        <p className="font-medium">{selectedLead.name}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Title</p>
                        <p>{selectedLead.title} at {selectedLead.company}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Score</p>
                        <Badge className={cn(getScoreBadge(Number(selectedLead.score)))}>
                          {selectedLead.score}/100
                        </Badge>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Stage</p>
                        <Badge variant="outline">{selectedLead.stage}</Badge>
                      </div>
                      {selectedLead.linkedin_url && (
                        <div>
                          <p className="text-sm text-muted-foreground">LinkedIn</p>
                          <a
                            href={selectedLead.linkedin_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-blue-500 hover:underline"
                          >
                            View Profile
                          </a>
                        </div>
                      )}
                      {selectedLead.history && (
                        <div>
                          <p className="text-sm text-muted-foreground mb-1">History</p>
                          <p className="text-sm whitespace-pre-wrap">{selectedLead.history}</p>
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div className="space-y-2 pt-4 border-t">
                        <Button className="w-full" variant="default">
                          <Send className="h-4 w-4 mr-2" />
                          Generate DM
                        </Button>
                        <Button className="w-full" variant="outline">
                          <Calendar className="h-4 w-4 mr-2" />
                          Schedule Meeting
                        </Button>
                        <Button className="w-full" variant="outline">
                          <FileText className="h-4 w-4 mr-2" />
                          Generate Invoice
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>Select a lead to view details and take actions</p>
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
