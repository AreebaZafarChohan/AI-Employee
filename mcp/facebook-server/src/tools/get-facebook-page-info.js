/**
 * Get Facebook Page Info Tool
 */

import { z } from 'zod';

const inputSchema = z.object({
  page_id: z.string().optional().describe('Facebook Page ID (defaults to configured page)')
});

export async function getFacebookPageInfo(params, facebookClient) {
  const validated = inputSchema.parse(params);

  try {
    const pageInfo = await facebookClient.getPageInfo(validated.page_id);

    return {
      success: true,
      page: {
        id: pageInfo.id,
        name: pageInfo.name,
        about: pageInfo.about,
        category: pageInfo.category,
        followers: pageInfo.followers_count,
        likes: pageInfo.likes,
        website: pageInfo.website,
        username: pageInfo.username,
      },
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      page: null,
    };
  }
}
