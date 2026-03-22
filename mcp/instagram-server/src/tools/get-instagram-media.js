/**
 * Get Instagram Media Tool
 */

import { z } from 'zod';

const inputSchema = z.object({
  limit: z.number().default(10).describe('Number of media items to fetch')
});

export async function getInstagramMedia(params, instagramClient) {
  const validated = inputSchema.parse(params);

  try {
    const media = await instagramClient.getMedia(validated.limit);

    // Format media data
    const formattedMedia = media.data?.map(item => ({
      id: item.id,
      caption: item.caption,
      media_type: item.media_type,
      media_url: item.media_url,
      permalink: item.permalink,
      timestamp: item.timestamp,
      like_count: item.like_count,
      comments_count: item.comments_count,
    })) || [];

    return {
      success: true,
      media: formattedMedia,
      count: formattedMedia.length,
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      media: [],
    };
  }
}
