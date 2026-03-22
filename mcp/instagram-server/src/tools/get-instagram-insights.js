/**
 * Get Instagram Insights Tool
 */

import { z } from 'zod';

const inputSchema = z.object({
  metrics: z.array(z.string()).optional().describe('Metrics to fetch'),
  period: z.enum(['day', 'week', 'month', 'lifetime']).default('day').describe('Time period')
});

export async function getInstagramInsights(params, instagramClient) {
  const validated = inputSchema.parse(params);

  try {
    const insights = await instagramClient.getAccountInsights(
      validated.metrics?.join(','),
      validated.period
    );

    // Format insights data
    const formattedInsights = insights.data?.map(insight => ({
      name: insight.name,
      period: insight.period,
      value: insight.values?.[0]?.value || 0,
      title: insight.title,
    })) || [];

    return {
      success: true,
      insights: formattedInsights,
      period: validated.period,
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      insights: [],
    };
  }
}
