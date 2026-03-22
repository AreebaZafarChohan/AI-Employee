/**
 * Get Twitter Analytics Tool
 */

import { z } from 'zod';

const inputSchema = z.object({
  tweet_id: z.string().describe('Tweet ID to get analytics for')
});

export async function getTwitterAnalytics(params, twitterClient) {
  const validated = inputSchema.parse(params);

  try {
    const result = await twitterClient.getTweetMetrics(validated.tweet_id);

    const metrics = result.data;
    
    return {
      success: true,
      tweet_id: validated.tweet_id,
      metrics: {
        public: {
          impressions: metrics.public_metrics?.impression_count,
          likes: metrics.public_metrics?.like_count,
          retweets: metrics.public_metrics?.retweet_count,
          replies: metrics.public_metrics?.reply_count,
          quotes: metrics.public_metrics?.quote_count,
        },
        organic: metrics.organic_metrics ? {
          impressions: metrics.organic_metrics.impression_count,
          likes: metrics.organic_metrics.like_count,
          retweets: metrics.organic_metrics.retweet_count,
          replies: metrics.organic_metrics.reply_count,
        } : null,
        promoted: metrics.promoted_metrics ? {
          impressions: metrics.promoted_metrics.impression_count,
          likes: metrics.promoted_metrics.like_count,
          retweets: metrics.promoted_metrics.retweet_count,
          replies: metrics.promoted_metrics.reply_count,
        } : null,
      },
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      metrics: null,
    };
  }
}
