#!/usr/bin/env node
/**
 * MCP Facebook Server
 * 
 * Provides Facebook Graph API integration via MCP protocol
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { config } from 'dotenv';
import { FacebookClient } from './client/facebook-client.js';
import { publishFacebookPost } from './tools/publish-facebook-post.js';
import { scheduleFacebookPost } from './tools/schedule-facebook-post.js';
import { getFacebookPageInfo } from './tools/get-facebook-page-info.js';
import { getFacebookInsights } from './tools/get-facebook-insights.js';
import { replyFacebookComment } from './tools/reply-facebook-comment.js';

// Load environment variables
config();

// Configuration
const facebookConfig = {
  access_token: process.env.FACEBOOK_ACCESS_TOKEN || '',
  page_id: process.env.FACEBOOK_PAGE_ID || 'me',
  api_version: process.env.FACEBOOK_API_VERSION || 'v18.0',
  timeout: parseInt(process.env.FACEBOOK_TIMEOUT || '30000')
};

// Initialize Facebook client
let facebookClient = null;

// Create MCP server
const server = new McpServer({
  name: 'facebook-server',
  version: '1.0.0',
  description: 'MCP server for Facebook Graph API integration'
});

// Register tools
server.tool(
  'publish_facebook_post',
  'Publish a post to Facebook Page',
  {
    content: { type: 'string', description: 'Post content/message' },
    link: { type: 'string', optional: true, description: 'Optional link to share' },
    photo: { type: 'string', optional: true, description: 'Optional photo URL' },
    scheduled_at: { type: 'string', optional: true, description: 'Optional scheduled time (ISO 8601)' }
  },
  async (params) => {
    try {
      if (!facebookClient) {
        facebookClient = new FacebookClient(facebookConfig);
      }
      const result = await publishFacebookPost(params, facebookClient);
      return {
        content: [{ type: 'text', text: JSON.stringify(result, null, 2) }]
      };
    } catch (error) {
      return {
        content: [{ type: 'text', text: JSON.stringify({ success: false, error: error.message }) }],
        isError: true
      };
    }
  }
);

server.tool(
  'schedule_facebook_post',
  'Schedule a post for later publishing',
  {
    content: { type: 'string', description: 'Post content/message' },
    scheduled_at: { type: 'string', description: 'Scheduled time (ISO 8601)' },
    link: { type: 'string', optional: true, description: 'Optional link' },
    photo: { type: 'string', optional: true, description: 'Optional photo URL' }
  },
  async (params) => {
    try {
      if (!facebookClient) {
        facebookClient = new FacebookClient(facebookConfig);
      }
      const result = await scheduleFacebookPost(params, facebookClient);
      return {
        content: [{ type: 'text', text: JSON.stringify(result, null, 2) }]
      };
    } catch (error) {
      return {
        content: [{ type: 'text', text: JSON.stringify({ success: false, error: error.message }) }],
        isError: true
      };
    }
  }
);

server.tool(
  'get_facebook_page_info',
  'Get Facebook Page information',
  {
    page_id: { type: 'string', optional: true, description: 'Facebook Page ID' }
  },
  async (params) => {
    try {
      if (!facebookClient) {
        facebookClient = new FacebookClient(facebookConfig);
      }
      const result = await getFacebookPageInfo(params, facebookClient);
      return {
        content: [{ type: 'text', text: JSON.stringify(result, null, 2) }]
      };
    } catch (error) {
      return {
        content: [{ type: 'text', text: JSON.stringify({ success: false, error: error.message }) }],
        isError: true
      };
    }
  }
);

server.tool(
  'get_facebook_insights',
  'Get Facebook Page insights and analytics',
  {
    metrics: { type: 'array', items: { type: 'string' }, optional: true, description: 'Metrics to fetch' },
    since: { type: 'string', optional: true, description: 'Start date (YYYY-MM-DD)' },
    until: { type: 'string', optional: true, description: 'End date (YYYY-MM-DD)' }
  },
  async (params) => {
    try {
      if (!facebookClient) {
        facebookClient = new FacebookClient(facebookConfig);
      }
      const result = await getFacebookInsights(params, facebookClient);
      return {
        content: [{ type: 'text', text: JSON.stringify(result, null, 2) }]
      };
    } catch (error) {
      return {
        content: [{ type: 'text', text: JSON.stringify({ success: false, error: error.message }) }],
        isError: true
      };
    }
  }
);

server.tool(
  'reply_facebook_comment',
  'Reply to a Facebook comment',
  {
    comment_id: { type: 'string', description: 'Comment ID to reply to' },
    message: { type: 'string', description: 'Reply message' }
  },
  async (params) => {
    try {
      if (!facebookClient) {
        facebookClient = new FacebookClient(facebookConfig);
      }
      const result = await replyFacebookComment(params, facebookClient);
      return {
        content: [{ type: 'text', text: JSON.stringify(result, null, 2) }]
      };
    } catch (error) {
      return {
        content: [{ type: 'text', text: JSON.stringify({ success: false, error: error.message }) }],
        isError: true
      };
    }
  }
);

// Start server
async function main() {
  try {
    console.error('Starting MCP Facebook Server...');

    if (!facebookConfig.access_token) {
      console.error('WARNING: FACEBOOK_ACCESS_TOKEN not set');
    }

    const transport = new StdioServerTransport();
    await server.connect(transport);

    console.error('MCP Facebook Server running on stdio');
    console.error(`Page ID: ${facebookConfig.page_id}`);
    console.error(`API Version: ${facebookConfig.api_version}`);

    // Test connection
    try {
      facebookClient = new FacebookClient(facebookConfig);
      const pageInfo = await facebookClient.getPageInfo();
      console.error(`✓ Connected to Facebook Page: ${pageInfo.name}`);
    } catch (error) {
      console.error('✗ Failed to connect to Facebook:', error.message);
    }
  } catch (error) {
    console.error('Server error:', error);
    process.exit(1);
  }
}

main();
