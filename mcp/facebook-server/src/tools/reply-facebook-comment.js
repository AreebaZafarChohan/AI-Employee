/**
 * Reply to Facebook Comment Tool
 */

import { z } from 'zod';

const inputSchema = z.object({
  comment_id: z.string().describe('Comment ID to reply to'),
  message: z.string().describe('Reply message')
});

export async function replyFacebookComment(params, facebookClient) {
  const validated = inputSchema.parse(params);

  try {
    const result = await facebookClient.replyToComment(
      validated.comment_id,
      validated.message
    );

    return {
      success: true,
      comment_id: result.id,
      message: 'Reply posted successfully',
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      comment_id: null,
    };
  }
}
