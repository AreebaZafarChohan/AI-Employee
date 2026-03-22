'use client';

import { useEffect, useState } from 'react';
import { Header } from '@/components/shared/header';
import { Sidebar } from '@/components/shared/sidebar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { filesApi, type FileItem } from '@/lib/api';
import { useApprovalStore } from '@/store/approval-store';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import {
  File,
  Folder,
  CheckCircle,
  XCircle,
  Search,
  Filter,
  Clock,
  Archive,
  AlertCircle,
  FileText,
} from 'lucide-react';

export default function FilesDashboardPage() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [stats, setStats] = useState<{ total: number; byFolder: Record<string, number> } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<'all' | 'email' | 'whatsapp' | 'linkedin' | 'file'>('all');
  const { addItem: addApproval } = useApprovalStore();

  useEffect(() => {
    loadFiles();
    loadStats();
  }, [typeFilter]);

  const loadStats = async () => {
    try {
      const data = await filesApi.getStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to load file stats:', error);
    }
  };

  const loadFiles = async () => {
    setIsLoading(true);
    try {
      const data = await filesApi.getPending() as FileItem[];
      let filtered = data;
      
      if (typeFilter !== 'all') {
        filtered = data.filter(f => f.type === typeFilter);
      }
      
      setFiles(filtered);
    } catch (error) {
      console.error('Failed to load files:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async (file: FileItem) => {
    try {
      await filesApi.approve(file.path);
      addApproval({
        id: `approval-${file.id}`,
        type: 'file',
        status: 'approved',
        riskLevel: file.riskLevel || 'medium',
        title: `File Approved: ${file.name}`,
        description: file.path,
        createdAt: new Date().toISOString(),
        metadata: { fileId: file.id, path: file.path },
      });
      loadFiles();
      loadStats();
      setSelectedFile(null);
    } catch (error) {
      console.error('Failed to approve file:', error);
    }
  };

  const handleReject = async (file: FileItem) => {
    const reason = prompt('Enter rejection reason:');
    if (reason) {
      try {
        await filesApi.reject(file.path, reason);
        addApproval({
          id: `approval-${file.id}`,
          type: 'file',
          status: 'rejected',
          riskLevel: file.riskLevel || 'medium',
          title: `File Rejected: ${file.name}`,
          description: reason,
          createdAt: new Date().toISOString(),
          metadata: { fileId: file.id, reason },
        });
        loadFiles();
        loadStats();
        setSelectedFile(null);
      } catch (error) {
        console.error('Failed to reject file:', error);
      }
    }
  };

  const filteredFiles = (files ?? []).filter((file) => {
    const matchesSearch =
      file.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      file.path.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div className="ml-72 flex-1">
        <Header
          title="Files Dashboard"
          subtitle="AI-powered file approval management"
        />

        <main className="flex-1 bg-background">
          <div className="container mx-auto py-8 px-4">
            {/* Stats Bar */}
            <div className="grid gap-4 md:grid-cols-5 mb-8">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Files</CardTitle>
                  <File className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats?.total || 0}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Pending</CardTitle>
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats?.byFolder?.Pending_Approval || 0}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Approved</CardTitle>
                  <CheckCircle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats?.byFolder?.Approved || 0}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Rejected</CardTitle>
                  <XCircle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats?.byFolder?.Rejected || 0}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Needs Action</CardTitle>
                  <AlertCircle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats?.byFolder?.Needs_Action || 0}</div>
                </CardContent>
              </Card>
            </div>

            {/* Main Content */}
            <div className="grid gap-6 lg:grid-cols-3">
              {/* File List */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>Pending Files</CardTitle>
                    <div className="flex items-center gap-2">
                      <div className="relative">
                        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                          placeholder="Search files..."
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
                      variant={typeFilter === 'all' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setTypeFilter('all')}
                    >
                      All
                    </Button>
                    <Button
                      variant={typeFilter === 'email' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setTypeFilter('email')}
                    >
                      Email
                    </Button>
                    <Button
                      variant={typeFilter === 'whatsapp' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setTypeFilter('whatsapp')}
                    >
                      WhatsApp
                    </Button>
                    <Button
                      variant={typeFilter === 'linkedin' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setTypeFilter('linkedin')}
                    >
                      LinkedIn
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {isLoading ? (
                    <div className="text-center py-8 text-muted-foreground">Loading...</div>
                  ) : filteredFiles.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Folder className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No files found</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {filteredFiles.map((file, index) => (
                        <motion.div
                          key={file.id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.03 }}
                          className={cn(
                            'p-4 rounded-lg border cursor-pointer transition-colors',
                            selectedFile?.id === file.id
                              ? 'bg-primary/10 border-primary'
                              : 'hover:bg-muted/50'
                          )}
                          onClick={() => setSelectedFile(file)}
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <FileText className="h-4 w-4 text-muted-foreground" />
                                <span className="font-medium truncate">{file.name}</span>
                              </div>
                              <p className="text-sm text-muted-foreground truncate">{file.path}</p>
                              <div className="flex items-center gap-2 mt-2">
                                <Badge variant="outline">{file.type}</Badge>
                                <span className="text-xs text-muted-foreground">
                                  {(file.size / 1024).toFixed(1)} KB
                                </span>
                              </div>
                            </div>
                            <Badge
                              variant={
                                file.riskLevel === 'high'
                                  ? 'destructive'
                                  : file.riskLevel === 'medium'
                                  ? 'secondary'
                                  : 'outline'
                              }
                            >
                              {file.riskLevel}
                            </Badge>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* File Detail / Actions */}
              <Card>
                <CardHeader>
                  <CardTitle>
                    {selectedFile ? 'File Details' : 'Select a file'}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {selectedFile ? (
                    <div className="space-y-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Name</p>
                        <p className="font-medium">{selectedFile.name}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Path</p>
                        <p className="text-sm font-mono">{selectedFile.path}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Type</p>
                        <Badge variant="outline">{selectedFile.type}</Badge>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Size</p>
                        <p>{(selectedFile.size / 1024).toFixed(2)} KB</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Risk Level</p>
                        <Badge
                          variant={
                            selectedFile.riskLevel === 'high'
                              ? 'destructive'
                              : selectedFile.riskLevel === 'medium'
                              ? 'secondary'
                              : 'outline'
                          }
                        >
                          {selectedFile.riskLevel || 'unknown'}
                        </Badge>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Modified</p>
                        <p>{new Date(selectedFile.modifiedAt).toLocaleString()}</p>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex gap-2 pt-4 border-t">
                        <Button
                          onClick={() => handleApprove(selectedFile)}
                          className="flex-1 bg-green-600 hover:bg-green-700"
                        >
                          <CheckCircle className="h-4 w-4 mr-2" />
                          Approve
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => handleReject(selectedFile)}
                          className="flex-1"
                        >
                          <XCircle className="h-4 w-4 mr-2" />
                          Reject
                        </Button>
                      </div>
                      <Button variant="outline" className="w-full">
                        <Archive className="h-4 w-4 mr-2" />
                        View Full Content
                      </Button>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <Folder className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>Select a file to view details</p>
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
