/**
 * Simple Backend API for Demo
 * Provides mock endpoints without database
 */

const express = require('express');
const cors = require('cors');
const http = require('http');
const WebSocket = require('ws');

const app = express();
const PORT = process.env.PORT || 8000;

app.use(cors());
app.use(express.json());

// Mock data
const mockGoals = [];
const mockTasks = [];
const mockPlans = [];
const mockApprovals = [];
const mockAuditLogs = [];
const mockMcpHealth = {
  email: { status: 'connected', lastCheck: new Date().toISOString() },
  whatsapp: { status: 'connected', lastCheck: new Date().toISOString() },
  linkedin: { status: 'connected', lastCheck: new Date().toISOString() },
};

// Health endpoint
app.get('/api/v1/system/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// MCP Health endpoint
app.get('/api/v1/system/mcp-health', (req, res) => {
  res.json(mockMcpHealth);
});

// Goals endpoints
app.get('/api/v1/goals', (req, res) => {
  res.json({ data: mockGoals, total: mockGoals.length });
});

app.post('/api/v1/goals', (req, res) => {
  const { title, description, priority } = req.body;
  const goal = {
    id: `goal-${Date.now()}`,
    title,
    description,
    priority: priority || 1,
    status: 'PENDING_PLAN',
    createdAt: new Date().toISOString(),
  };
  mockGoals.push(goal);
  res.status(201).json(goal);
});

// Tasks endpoints
app.get('/api/v1/tasks', (req, res) => {
  res.json({ data: mockTasks, total: mockTasks.length });
});

app.post('/api/v1/tasks', (req, res) => {
  const { title, description, status } = req.body;
  const task = {
    id: `task-${Date.now()}`,
    title,
    description,
    status: status || 'Pending',
    createdAt: new Date().toISOString(),
  };
  mockTasks.push(task);
  res.status(201).json(task);
});

// Plans endpoints
app.get('/api/v1/plans', (req, res) => {
  res.json({ data: mockPlans, total: mockPlans.length });
});

// Watcher endpoints
app.get('/api/v1/watcher/status', (req, res) => {
  res.json({
    status: 'running',
    lastSync: new Date().toISOString(),
    queueSize: 0,
    processingSpeed: 10,
  });
});

// Vault endpoints - Multiple path patterns
app.get('/api/v1/vault/pending', (req, res) => {
  res.json({ data: [] });
});

app.get('/api/v1/vault/approved', (req, res) => {
  res.json({ data: [] });
});

app.get('/api/v1/vault/needs-action', (req, res) => {
  res.json({ data: [], total: 0 });
});

app.get('/vault/needs-action', (req, res) => {
  res.json({ data: [], total: 0 });
});

// Activity log
app.get('/api/v1/activity-logs', (req, res) => {
  res.json({ data: [], total: 0 });
});

// Audit logs
app.get('/api/v1/audit-logs', (req, res) => {
  const limit = parseInt(req.query.limit) || 50;
  res.json({ data: mockAuditLogs.slice(0, limit), total: mockAuditLogs.length });
});

// System state
app.get('/api/v1/system/state', (req, res) => {
  res.json({
    status: 'idle',
    lastActivityAt: new Date().toISOString(),
    currentTaskId: null,
  });
});

// Approvals endpoints
app.get('/api/v1/approvals/pending', (req, res) => {
  res.json({ data: mockApprovals, total: mockApprovals.length });
});

app.post('/api/v1/approvals/:id/approve', (req, res) => {
  res.json({ success: true, id: req.params.id });
});

app.post('/api/v1/approvals/:id/reject', (req, res) => {
  res.json({ success: true, id: req.params.id });
});

// Files endpoints
app.get('/api/v1/files/pending', (req, res) => {
  res.json({ data: [], total: 0 });
});

// Agent endpoints
app.get('/api/v1/agents', (req, res) => {
  res.json({
    data: [
      { id: 'local-executive', name: 'Local Executive', status: 'active', role: 'executor' },
      { id: 'cloud-executive', name: 'Cloud Executive', status: 'active', role: 'planner' },
    ],
  });
});

// Memory endpoints
app.get('/api/v1/memory/records', (req, res) => {
  res.json({ data: [], total: 0 });
});

// Intelligence endpoints
app.get('/api/v1/intelligence/summary', (req, res) => {
  res.json({
    summary: 'System operating normally',
    insights: [],
    recommendations: [],
  });
});

// Costs endpoints
app.get('/api/v1/costs/threshold', (req, res) => {
  res.json({ threshold: 10.00, current: 0.50 });
});

// Tools endpoints
app.get('/api/v1/tools', (req, res) => {
  res.json({
    data: [
      { id: 'email', name: 'Email', enabled: true },
      { id: 'whatsapp', name: 'WhatsApp', enabled: true },
      { id: 'linkedin', name: 'LinkedIn', enabled: true },
    ],
  });
});

// Settings endpoints
app.get('/api/v1/settings', (req, res) => {
  res.json({
    vaultPath: '../AI-Employee-Vault',
    autonomyTier: 'silver',
    dryRun: false,
  });
});

// Catch-all for unknown API routes - return empty data instead of 404
app.use('/api/v1/*', (req, res) => {
  console.log(`⚠️ Unknown endpoint: ${req.path}`);
  res.json({ data: [], total: 0, message: 'Endpoint not implemented' });
});

// Create HTTP server
const server = http.createServer(app);

// Create WebSocket server
const wss = new WebSocket.Server({ server, path: '/ws' });

wss.on('connection', (ws) => {
  console.log('🔌 WebSocket client connected');
  
  ws.on('message', (message) => {
    console.log('📩 Received:', message.toString());
    // Echo back
    ws.send(JSON.stringify({ type: 'ack', message: 'Received' }));
  });
  
  ws.on('close', () => {
    console.log('🔌 WebSocket client disconnected');
  });
  
  ws.on('error', (error) => {
    console.error('❌ WebSocket error:', error);
  });
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`✅ Simple API Server running on http://0.0.0.0:${PORT}`);
  console.log(`📊 Health: http://localhost:${PORT}/api/v1/system/health`);
  console.log(`🔌 WebSocket: ws://localhost:${PORT}/ws`);
});
