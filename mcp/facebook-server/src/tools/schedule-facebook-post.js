/**
 * Schedule Facebook Post Tool
 */

import { z } from 'zod';

const inputSchema = z.object({
  content: z.string().describe('Post content/message'),
  scheduled_at: z.string().describe('Scheduled time (ISO 8601)'),
  link: z.string().optional().describe('Optional link to share'),
  photo: z.string().optional().describe('Optional photo URL')
});

export async function scheduleFacebookPost(params, facebookClient) {
  const validated = inputSchema.parse(params);

  try {
    // Validate scheduled time is in future
    const scheduledTime = new Date(validated.scheduled_at);
    if (scheduledTime <= new Date()) {
      return {
        success: false,
        error: 'Scheduled time must be in the future',
        post_id: null,
      };
    }

    const result = await facebookClient.schedulePost(
      validated.content,
      validated.scheduled_at,
      {
        link: validated.link,
        photo: validated.photo,
      }
    );

    return {
      success: true,
      post_id: result.id,
      scheduled_time: validated.scheduled_at,
      message: 'Post scheduled successfully',
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      post_id: null,
    };
  }
}
