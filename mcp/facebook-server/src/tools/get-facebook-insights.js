/**
 * Get Facebook Insights Tool
 */

import { z } from 'zod';

const inputSchema = z.object({
  metrics: z.array(z.string()).optional().describe('Metrics to fetch'),
  since: z.string().optional().describe('Start date (YYYY-MM-DD)'),
  until: z.string().optional().describe('End date (YYYY-MM-DD)')
});

export async function getFacebookInsights(params, facebookClient) {
  const validated = inputSchema.parse(params);

  try {
    const insights = await facebookClient.getInsights(
      validated.metrics?.join(','),
      validated.since,
      validated.until
    );

    // Format insights data
    const formattedInsights = insights.data?.map(insight => ({
      name: insight.name,
      period: insight.period,
      value: insight.values?.[0]?.value || 0,
      title: insight.title,
      description: insight.description,
    })) || [];

    return {
      success: true,
      insights: formattedInsights,
      period: {
        since: validated.since,
        until: validated.until,
      },
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      insights: [],
    };
  }
}
