/**
 * Publish Instagram Post Tool
 */

import { z } from 'zod';

const inputSchema = z.object({
  caption: z.string().describe('Post caption'),
  media_url: z.string().describe('Media URL (image or video)'),
  media_type: z.enum(['IMAGE', 'VIDEO', 'CAROUSEL']).default('IMAGE').describe('Media type')
});

export async function publishInstagramPost(params, instagramClient) {
  const validated = inputSchema.parse(params);

  try {
    const result = await instagramClient.publishPost(
      validated.caption,
      validated.media_url,
      validated.media_type
    );

    return {
      success: true,
      post_id: result.id,
      status: result.status,
      message: 'Post published successfully',
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      post_id: null,
    };
  }
}
