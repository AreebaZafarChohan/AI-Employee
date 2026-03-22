/**
 * Publish Thread Tool
 */

import { z } from 'zod';

const tweetSchema = z.object({
  content: z.string().min(1).max(280).describe('Tweet content'),
  media_ids: z.array(z.string()).optional().describe('Optional media IDs')
});

const inputSchema = z.object({
  tweets: z.array(tweetSchema).min(1).describe('Array of tweets for the thread')
});

export async function publishThread(params, twitterClient) {
  const validated = inputSchema.parse(params);

  try {
    const results = await twitterClient.publishThread(validated.tweets);

    const firstTweet = results[0];
    
    return {
      success: true,
      thread_id: firstTweet.data.id,
      tweet_count: results.length,
      tweets: results.map(r => ({
        tweet_id: r.data.id,
        text: r.data.text,
        created_at: r.data.created_at,
      })),
      thread_url: `https://twitter.com/i/web/status/${firstTweet.data.id}`,
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      thread_id: null,
    };
  }
}
