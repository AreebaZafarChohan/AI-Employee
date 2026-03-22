/**
 * Retweet Tool
 */

import { z } from 'zod';

const inputSchema = z.object({
  tweet_id: z.string().describe('Tweet ID to retweet')
});

export async function retweet(params, twitterClient) {
  const validated = inputSchema.parse(params);

  try {
    const result = await twitterClient.retweet(validated.tweet_id);

    return {
      success: true,
      retweeted: true,
      tweet_id: validated.tweet_id,
      message: 'Tweet retweeted successfully',
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      retweeted: false,
    };
  }
}
