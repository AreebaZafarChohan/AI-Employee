/**
 * Search Tweets Tool
 */

import { z } from 'zod';

const inputSchema = z.object({
  query: z.string().describe('Search query'),
  max_results: z.number().default(10).describe('Max results (10-100)'),
  start_time: z.string().optional().describe('Start time (ISO 8601)'),
  end_time: z.string().optional().describe('End time (ISO 8601)')
});

export async function searchTweets(params, twitterClient) {
  const validated = inputSchema.parse(params);

  try {
    const result = await twitterClient.searchTweets(validated.query, {
      max_results: validated.max_results,
      start_time: validated.start_time,
      end_time: validated.end_time,
    });

    const tweets = result.data?.map(tweet => ({
      id: tweet.id,
      text: tweet.text,
      created_at: tweet.created_at,
      author_id: tweet.author_id,
      metrics: tweet.public_metrics,
    })) || [];

    return {
      success: true,
      query: validated.query,
      count: tweets.length,
      tweets,
      meta: result.meta,
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      tweets: [],
    };
  }
}
