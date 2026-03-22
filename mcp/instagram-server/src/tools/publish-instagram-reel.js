/**
 * Publish Instagram Reel Tool
 */

import { z } from 'zod';

const inputSchema = z.object({
  caption: z.string().describe('Reel caption'),
  video_url: z.string().describe('Reel video URL'),
  thumbnail_url: z.string().optional().describe('Optional thumbnail URL')
});

export async function publishInstagramReel(params, instagramClient) {
  const validated = inputSchema.parse(params);

  try {
    // Reels are published as VIDEO media type
    const result = await instagramClient.publishPost(
      validated.caption,
      validated.video_url,
      'VIDEO'
    );

    return {
      success: true,
      reel_id: result.id,
      status: result.status,
      message: 'Reel published successfully',
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      reel_id: null,
    };
  }
}
