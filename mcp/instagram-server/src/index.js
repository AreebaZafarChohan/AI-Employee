#!/usr/bin/env node
/**
 * MCP Instagram Server
 * 
 * Provides Instagram Graph API integration via MCP protocol
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { config } from 'dotenv';
import { InstagramClient } from './client/instagram-client.js';
import { publishInstagramPost } from './tools/publish-instagram-post.js';
import { publishInstagramStory } from './tools/publish-instagram-story.js';
import { publishInstagramReel } from './tools/publish-instagram-reel.js';
import { getInstagramInsights } from './tools/get-instagram-insights.js';
import { getInstagramMedia } from './tools/get-instagram-media.js';

// Load environment variables
config();

// Configuration
const instagramConfig = {
  access_token: process.env.INSTAGRAM_ACCESS_TOKEN || '',
  business_account_id: process.env.INSTAGRAM_BUSINESS_ACCOUNT_ID || '',
  api_version: process.env.INSTAGRAM_API_VERSION || 'v18.0',
  timeout: parseInt(process.env.INSTAGRAM_TIMEOUT || '30000')
};

// Initialize Instagram client
let instagramClient = null;

// Create MCP server
const server = new McpServer({
  name: 'instagram-server',
  version: '1.0.0',
  description: 'MCP server for Instagram Graph API integration'
});

// Register tools
server.tool(
  'publish_instagram_post',
  'Publish a post to Instagram',
  {
    caption: { type: 'string', description: 'Post caption' },
    media_url: { type: 'string', description: 'Media URL (image or video)' },
    media_type: { type: 'string', enum: ['IMAGE', 'VIDEO', 'CAROUSEL'], default: 'IMAGE', description: 'Media type' }
  },
  async (params) => {
    try {
      if (!instagramClient) {
        instagramClient = new InstagramClient(instagramConfig);
      }
      const result = await publishInstagramPost(params, instagramClient);
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
  'publish_instagram_story',
  'Publish a story to Instagram',
  {
    media_url: { type: 'string', description: 'Story media URL' },
    media_type: { type: 'string', enum: ['IMAGE', 'VIDEO'], default: 'IMAGE', description: 'Media type' }
  },
  async (params) => {
    try {
      if (!instagramClient) {
        instagramClient = new InstagramClient(instagramConfig);
      }
      const result = await publishInstagramStory(params, instagramClient);
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
  'publish_instagram_reel',
  'Publish a reel to Instagram',
  {
    caption: { type: 'string', description: 'Reel caption' },
    video_url: { type: 'string', description: 'Reel video URL' },
    thumbnail_url: { type: 'string', optional: true, description: 'Optional thumbnail URL' }
  },
  async (params) => {
    try {
      if (!instagramClient) {
        instagramClient = new InstagramClient(instagramConfig);
      }
      const result = await publishInstagramReel(params, instagramClient);
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
  'get_instagram_insights',
  'Get Instagram account insights',
  {
    metrics: { type: 'array', items: { type: 'string' }, optional: true, description: 'Metrics to fetch' },
    period: { type: 'string', enum: ['day', 'week', 'month', 'lifetime'], default: 'day', description: 'Time period' }
  },
  async (params) => {
    try {
      if (!instagramClient) {
        instagramClient = new InstagramClient(instagramConfig);
      }
      const result = await getInstagramInsights(params, instagramClient);
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
  'get_instagram_media',
  'Get recent Instagram media',
  {
    limit: { type: 'number', default: 10, description: 'Number of media items to fetch' }
  },
  async (params) => {
    try {
      if (!instagramClient) {
        instagramClient = new InstagramClient(instagramConfig);
      }
      const result = await getInstagramMedia(params, instagramClient);
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
    console.error('Starting MCP Instagram Server...');
    
    if (!instagramConfig.access_token) {
      console.error('WARNING: INSTAGRAM_ACCESS_TOKEN not set');
    }

    if (!instagramConfig.business_account_id) {
      console.error('WARNING: INSTAGRAM_BUSINESS_ACCOUNT_ID not set');
    }

    const transport = new StdioServerTransport();
    await server.connect(transport);

    console.error('MCP Instagram Server running on stdio');
    console.error(`Business Account ID: ${instagramConfig.business_account_id}`);
    console.error(`API Version: ${instagramConfig.api_version}`);
    
    // Test connection
    try {
      instagramClient = new InstagramClient(instagramConfig);
      const accountInfo = await instagramClient.getAccountInfo();
      console.error(`✓ Connected to Instagram Account: ${accountInfo.username}`);
    } catch (error) {
      console.error('✗ Failed to connect to Instagram:', error.message);
    }
  } catch (error) {
    console.error('Server error:', error);
    process.exit(1);
  }
}

main();
