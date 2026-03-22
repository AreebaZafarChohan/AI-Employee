import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Tasks
  getPendingTasks: () => apiClient.get('/tasks/pending'),
  getNeedsActionTasks: () => apiClient.get('/tasks/needs-action'),
  getDoneTasks: () => apiClient.get('/tasks/done'),
  
  // Vault
  getCounts: () => apiClient.get('/vault/counts'),
  approve: (filename: string) => apiClient.post('/vault/approve', { filename }),
  reject: (filename: string) => apiClient.post('/vault/reject', { filename }),
  
  // Agent
  sendCommand: (command: string) => apiClient.post('/agent/command', { command }),
};
