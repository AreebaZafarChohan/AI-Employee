/**
 * Publish Tweet Tool
 */

import { z } from 'zod';

const inputSchema = z.object({
  content: z.string().min(1).max(280).describe('Tweet content (max 280 characters)'),
  media_ids: z.array(z.string()).optional().describe('Optional media IDs to attach')
});

export async function publishTweet(params, twitterClient) {
  const validated = inputSchema.parse(params);

  try {
    const result = await twitterClient.publishTweet(
      validated.content,
      {
        media_ids: validated.media_ids,
      }
    );

    return {
      success: true,
      tweet_id: result.data.id,
      text: result.data.text,
      created_at: result.data.created_at,
      tweet_url: `https://twitter.com/i/web/status/${result.data.id}`,
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      tweet_id: null,
    };
  }
}
