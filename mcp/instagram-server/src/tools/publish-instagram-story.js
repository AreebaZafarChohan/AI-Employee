/**
 * Publish Instagram Story Tool
 */

import { z } from 'zod';

const inputSchema = z.object({
  media_url: z.string().describe('Story media URL (image or video)'),
  media_type: z.enum(['IMAGE', 'VIDEO']).default('IMAGE').describe('Media type')
});

export async function publishInstagramStory(params, instagramClient) {
  const validated = inputSchema.parse(params);

  try {
    // Stories use the same API but with different parameters
    const result = await instagramClient.publishPost(
      '', // Stories typically don't have captions
      validated.media_url,
      validated.media_type
    );

    return {
      success: true,
      story_id: result.id,
      status: result.status,
      message: 'Story published successfully',
      expires_in: '24 hours',
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      story_id: null,
    };
  }
}
