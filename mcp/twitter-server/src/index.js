#!/usr/bin/env node
/**
 * MCP Twitter Server
 * 
 * Provides Twitter API v2 integration via MCP protocol
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { config } from 'dotenv';
import { TwitterClient } from './client/twitter-client.js';
import { publishTweet } from './tools/publish-tweet.js';
import { publishThread } from './tools/publish-thread.js';
import { replyTweet } from './tools/reply-tweet.js';
import { retweet } from './tools/retweet.js';
import { getTwitterAnalytics } from './tools/get-twitter-analytics.js';
import { searchTweets } from './tools/search-tweets.js';

// Load environment variables
config();

// Configuration
const twitterConfig = {
  bearer_token: process.env.TWITTER_BEARER_TOKEN || '',
  api_key: process.env.TWITTER_API_KEY || '',
  api_secret: process.env.TWITTER_API_SECRET || '',
  access_token: process.env.TWITTER_ACCESS_TOKEN || '',
  access_token_secret: process.env.TWITTER_ACCESS_TOKEN_SECRET || '',
  timeout: parseInt(process.env.TWITTER_TIMEOUT || '30000')
};

// Initialize Twitter client
let twitterClient = null;

// Create MCP server
const server = new McpServer({
  name: 'twitter-server',
  version: '1.0.0',
  description: 'MCP server for Twitter API v2 integration'
});

// Register tools
server.tool(
  'publish_tweet',
  'Publish a tweet (max 280 characters)',
  {
    content: { type: 'string', minLength: 1, maxLength: 280, description: 'Tweet content' },
    media_ids: { type: 'array', items: { type: 'string' }, optional: true, description: 'Media IDs to attach' }
  },
  async (params) => {
    try {
      if (!twitterClient) {
        twitterClient = new TwitterClient(config);
      }
      const result = await publishTweet(params, twitterClient);
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
  'publish_thread',
  'Publish a thread of tweets',
  {
    tweets: {
      type: 'array',
      description: 'Array of tweets for the thread',
      items: {
        type: 'object',
        properties: {
          content: { type: 'string', minLength: 1, maxLength: 280 },
          media_ids: { type: 'array', items: { type: 'string' }, optional: true }
        },
        required: ['content']
      }
    }
  },
  async (params) => {
    try {
      if (!twitterClient) {
        twitterClient = new TwitterClient(config);
      }
      const result = await publishThread(params, twitterClient);
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
  'reply_tweet',
  'Reply to a tweet',
  {
    tweet_id: { type: 'string', description: 'Tweet ID to reply to' },
    content: { type: 'string', minLength: 1, maxLength: 280, description: 'Reply content' }
  },
  async (params) => {
    try {
      if (!twitterClient) {
        twitterClient = new TwitterClient(config);
      }
      const result = await replyTweet(params, twitterClient);
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
  'retweet',
  'Retweet a tweet',
  {
    tweet_id: { type: 'string', description: 'Tweet ID to retweet' }
  },
  async (params) => {
    try {
      if (!twitterClient) {
        twitterClient = new TwitterClient(config);
      }
      const result = await retweet(params, twitterClient);
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
  'get_twitter_analytics',
  'Get analytics for a tweet',
  {
    tweet_id: { type: 'string', description: 'Tweet ID to get analytics for' }
  },
  async (params) => {
    try {
      if (!twitterClient) {
        twitterClient = new TwitterClient(config);
      }
      const result = await getTwitterAnalytics(params, twitterClient);
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
  'search_tweets',
  'Search for tweets',
  {
    query: { type: 'string', description: 'Search query' },
    max_results: { type: 'number', default: 10, description: 'Max results (10-100)' },
    start_time: { type: 'string', optional: true, description: 'Start time (ISO 8601)' },
    end_time: { type: 'string', optional: true, description: 'End time (ISO 8601)' }
  },
  async (params) => {
    try {
      if (!twitterClient) {
        twitterClient = new TwitterClient(config);
      }
      const result = await searchTweets(params, twitterClient);
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
    console.error('Starting MCP Twitter Server...');
    
    if (!twitterConfig.bearer_token) {
      console.error('WARNING: TWITTER_BEARER_TOKEN not set');
    }
    
    const transport = new StdioServerTransport();
    await server.connect(transport);
    
    console.error('MCP Twitter Server running on stdio');
    console.error(`API Version: v2`);
    
    // Test connection
    try {
      twitterClient = new TwitterClient(config);
      const user = await twitterClient.getUserByUsername('twitter');
      console.error(`✓ Connected to Twitter API v2`);
    } catch (error) {
      console.error('✗ Failed to connect to Twitter:', error.message);
    }
  } catch (error) {
    console.error('Server error:', error);
    process.exit(1);
  }
}

main();
