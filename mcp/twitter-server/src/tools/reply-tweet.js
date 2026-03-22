/**
 * Reply to Tweet Tool
 */

import { z } from 'zod';

const inputSchema = z.object({
  tweet_id: z.string().describe('Tweet ID to reply to'),
  content: z.string().min(1).max(280).describe('Reply content')
});

export async function replyTweet(params, twitterClient) {
  const validated = inputSchema.parse(params);

  try {
    const result = await twitterClient.replyToTweet(
      validated.tweet_id,
      validated.content
    );

    return {
      success: true,
      tweet_id: result.data.id,
      in_reply_to: validated.tweet_id,
      text: result.data.text,
      created_at: result.data.created_at,
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      tweet_id: null,
    };
  }
}
