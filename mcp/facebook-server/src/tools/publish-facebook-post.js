/**
 * Publish Facebook Post Tool
 */

import { z } from 'zod';

const inputSchema = z.object({
  content: z.string().describe('Post content/message'),
  link: z.string().optional().describe('Optional link to share'),
  photo: z.string().optional().describe('Optional photo URL'),
  scheduled_at: z.string().optional().describe('Optional scheduled time (ISO 8601)')
});

export async function publishFacebookPost(params, facebookClient) {
  const validated = inputSchema.parse(params);

  try {
    const result = await facebookClient.publishPost(
      validated.content,
      {
        link: validated.link,
        photo: validated.photo,
        scheduled_at: validated.scheduled_at,
      }
    );

    return {
      success: true,
      post_id: result.id,
      message: validated.scheduled_at ? 'Post scheduled successfully' : 'Post published successfully',
      post_url: `https://facebook.com/${result.id}`,
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      post_id: null,
    };
  }
}
