# Social Post Generator - Usage Patterns

Practical code examples and workflow patterns for the `social_post_generator` skill.

---

## Pattern 1: Multi-Platform Product Launch Campaign

**Use Case:** Launch new feature across all social platforms simultaneously

**Code Example:**

```javascript
const { generateSocialPost } = require('./social_post_generator');

async function launchProductCampaign(productDetails) {
  const campaign = await generateSocialPost({
    campaign_type: "product_launch",
    platforms: ["linkedin", "twitter", "facebook"],
    content: {
      product_name: productDetails.name,
      value_proposition: productDetails.value_prop,
      key_features: productDetails.features,
      launch_date: productDetails.launch_date,
      special_offer: productDetails.offer,
      customer_pain_point: productDetails.pain_point,
      target_result: productDetails.benefit
    },
    target_audience: {
      primary: "B2B SaaS companies",
      secondary: "Product managers and founders",
      persona: productDetails.persona
    },
    tone: "professional",
    cta: {
      type: "sign_up",
      text: "Get early access",
      url: `https://company.com/launch/${productDetails.slug}`,
      urgency: "high"
    },
    hashtags: {
      branded: [`#${productDetails.name.replace(/\s/g, '')}`, "#CompanyName"],
      industry: productDetails.industry_tags,
      trending: []
    },
    ab_testing: {
      enabled: true,
      variations_count: 3,
      test_variables: ["headline", "cta_text", "emoji_usage"]
    },
    metadata: {
      agent: "lex",
      campaign_id: `launch_${productDetails.slug}`,
      session_id: process.env.SOCIAL_SESSION_ID
    }
  });

  if (campaign.success) {
    console.log(`✅ Campaign created: ${campaign.file_path}`);
    console.log(`📊 Total variations: ${campaign.variations_count}`);
    console.log(`📱 Platforms: ${campaign.platforms.join(', ')}`);
    return campaign;
  } else {
    console.error(`❌ Campaign failed: ${campaign.error}`);
    return null;
  }
}

// Usage
await launchProductCampaign({
  name: "AI Analytics Pro",
  slug: "ai-analytics",
  value_prop: "Get insights in seconds, not hours",
  features: [
    "Natural language queries",
    "Predictive analytics",
    "Real-time alerts",
    "Custom dashboards"
  ],
  launch_date: "2025-03-01",
  offer: "50% off first 3 months",
  pain_point: "Data teams waste 60% of time on manual analysis",
  benefit: "Reduce analysis time by 80%",
  persona: "Data analysts at mid-size companies",
  industry_tags: ["#DataScience", "#Analytics", "#AI", "#B2BSaaS"]
});
```

**Output:**
```
✅ Campaign created: Social_Posts/20250204-153022-product-launch-ai-analytics-pro.md
📊 Total variations: 9 (3 per platform)
📱 Platforms: linkedin, twitter, facebook
```

---

## Pattern 2: Weekly Content Promotion Schedule

**Use Case:** Automate weekly blog post promotion

**Code Example:**

```javascript
async function promoteWeeklyContent(blogPosts) {
  const campaigns = [];

  for (const post of blogPosts) {
    const campaign = await generateSocialPost({
      campaign_type: "content_promotion",
      platforms: ["linkedin", "twitter"],
      content: {
        content_type: "blog_post",
        title: post.title,
        summary: post.excerpt,
        reading_time: post.reading_time,
        target_reader: post.audience,
        key_takeaways: post.takeaways,
        author: post.author,
        published_date: post.date
      },
      tone: "informative",
      cta: {
        type: "learn_more",
        text: "Read the full post",
        url: post.url
      },
      hashtags: {
        industry: post.tags.slice(0, 5) // Max 5 hashtags
      },
      ab_testing: {
        enabled: true,
        variations_count: 2
      }
    });

    if (campaign.success) {
      campaigns.push(campaign);
      console.log(`✅ Created promotion for: ${post.title}`);
    }
  }

  console.log(`\n📊 Weekly Content Summary:`);
  console.log(`   Posts promoted: ${campaigns.length}`);
  console.log(`   Total variations: ${campaigns.length * 2 * 2}`); // 2 variations × 2 platforms

  return campaigns;
}

// Usage
const weeklyPosts = [
  {
    title: "10 SaaS Metrics That Actually Matter",
    excerpt: "Stop tracking vanity metrics. Focus on these 10 KPIs instead.",
    reading_time: "8 min",
    audience: "SaaS founders and product managers",
    takeaways: [
      "MRR vs ARR breakdown",
      "Customer acquisition cost optimization",
      "Churn rate analysis"
    ],
    author: "Sarah Chen, VP of Product",
    date: "2025-02-04",
    url: "https://blog.company.com/saas-metrics",
    tags: ["#SaaS", "#Metrics", "#ProductManagement", "#Growth"]
  },
  // More posts...
];

await promoteWeeklyContent(weeklyPosts);
```

---

## Pattern 3: Event Countdown Series

**Use Case:** Build anticipation with countdown posts

**Code Example:**

```javascript
async function createEventCountdown(eventDetails, daysBeforeEvent) {
  const countdownPosts = [];

  for (const day of daysBeforeEvent) {
    let urgency, message;

    if (day === 7) {
      urgency = "low";
      message = "1 week until";
    } else if (day === 3) {
      urgency = "medium";
      message = "Only 3 days left!";
    } else if (day === 1) {
      urgency = "high";
      message = "Tomorrow! Last chance to register";
    }

    const post = await generateSocialPost({
      campaign_type: "event_promotion",
      platforms: ["linkedin", "twitter"],
      content: {
        event_name: eventDetails.name,
        event_type: eventDetails.type,
        event_date: eventDetails.date,
        countdown_message: message,
        days_remaining: day,
        speakers: eventDetails.speakers,
        topics: eventDetails.topics,
        value_proposition: eventDetails.value
      },
      tone: "enthusiastic",
      cta: {
        type: "register",
        text: day === 1 ? "Register now (last chance!)" : "Save your spot",
        url: eventDetails.registration_url,
        urgency: urgency
      },
      hashtags: {
        branded: [`#${eventDetails.hashtag}`],
        industry: eventDetails.industry_tags
      },
      ab_testing: {
        enabled: day === 7, // Only A/B test first post
        variations_count: day === 7 ? 2 : 1
      },
      metadata: {
        campaign_series: "event_countdown",
        event_id: eventDetails.id,
        countdown_day: day
      }
    });

    countdownPosts.push(post);
    console.log(`✅ Created ${day}-day countdown post`);
  }

  return countdownPosts;
}

// Usage
await createEventCountdown(
  {
    id: "saas-summit-2025",
    name: "SaaS Growth Summit 2025",
    type: "virtual_conference",
    date: "2025-03-15T10:00:00-08:00",
    hashtag: "SaaSGrowth2025",
    speakers: ["Sarah Chen", "Marcus Johnson", "Dr. Emily Park"],
    topics: ["Scaling from $1M to $10M", "PLG strategies", "AI in SaaS"],
    value: "Learn from founders who scaled 10+ SaaS companies",
    registration_url: "https://company.com/summit",
    industry_tags: ["#SaaS", "#StartupGrowth", "#B2B"]
  },
  [7, 3, 1] // Post 7 days, 3 days, 1 day before event
);
```

---

## Pattern 4: A/B Test Analysis & Iteration

**Use Case:** Analyze A/B test results and generate improved variations

**Code Example:**

```javascript
async function analyzeAndIterate(previousCampaignId, results) {
  // Analyze which variation performed best
  const winningVariation = results.variations.reduce((best, current) => {
    return current.ctr > best.ctr ? current : best;
  });

  console.log(`📊 A/B Test Results:`);
  console.log(`   Winner: Variation ${winningVariation.id}`);
  console.log(`   CTR: ${winningVariation.ctr}%`);
  console.log(`   Engagement: ${winningVariation.engagement_rate}%`);

  // Identify winning elements
  const winningElements = {
    headline_style: winningVariation.headline_style,
    cta_text: winningVariation.cta_text,
    emoji_usage: winningVariation.emoji_usage,
    format: winningVariation.format
  };

  // Generate new campaign with winning elements
  const improvedCampaign = await generateSocialPost({
    campaign_type: results.campaign_type,
    platforms: results.platforms,
    content: {
      ...results.content,
      optimize_for: winningElements.headline_style
    },
    tone: results.tone,
    cta: {
      ...results.cta,
      text: winningElements.cta_text // Use winning CTA
    },
    ab_testing: {
      enabled: true,
      variations_count: 3,
      test_variables: ["format", "hook"], // Test new variables
      previous_winner: winningElements
    },
    metadata: {
      previous_campaign: previousCampaignId,
      iteration: results.iteration + 1,
      learning: `${winningElements.headline_style} headlines perform best`
    }
  });

  console.log(`✅ Generated improved campaign based on learnings`);
  return improvedCampaign;
}

// Usage
const testResults = {
  campaign_id: "SOCIAL-20250204-001",
  campaign_type: "product_launch",
  platforms: ["linkedin"],
  iteration: 1,
  variations: [
    {
      id: "A",
      headline_style: "feature_focus",
      cta_text: "Get early access",
      emoji_usage: "minimal",
      format: "bullets",
      ctr: 3.2,
      engagement_rate: 4.5
    },
    {
      id: "B",
      headline_style: "pain_point",
      cta_text: "Start free trial",
      emoji_usage: "moderate",
      format: "narrative",
      ctr: 5.8, // Winner!
      engagement_rate: 6.2
    },
    {
      id: "C",
      headline_style: "social_proof",
      cta_text: "Join 500+ companies",
      emoji_usage: "strategic",
      format: "bullets",
      ctr: 4.1,
      engagement_rate: 5.0
    }
  ]
};

await analyzeAndIterate("SOCIAL-20250204-001", testResults);
```

---

## Pattern 5: Batch Campaign Generation

**Use Case:** Generate multiple campaigns in parallel

**Code Example:**

```javascript
async function generateMultipleCampaigns(campaigns) {
  console.log(`📱 Generating ${campaigns.length} campaigns in parallel...`);

  const startTime = Date.now();

  // Generate all campaigns in parallel
  const campaignPromises = campaigns.map(campaign =>
    generateSocialPost(campaign).catch(error => ({
      success: false,
      error: error.message,
      campaign_name: campaign.content.name || campaign.campaign_type
    }))
  );

  const results = await Promise.all(campaignPromises);

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
  const successful = results.filter(r => r.success).length;

  console.log(`\n📊 Batch Generation Summary:`);
  console.log(`   ✅ Successful: ${successful}/${results.length}`);
  console.log(`   ❌ Failed: ${results.length - successful}/${results.length}`);
  console.log(`   ⏱️ Time: ${elapsed}s (avg ${(elapsed / results.length).toFixed(2)}s per campaign)`);

  return results;
}

// Usage: Generate month's worth of content
const monthlyCampaigns = [
  // Week 1: Product launch
  {
    campaign_type: "product_launch",
    platforms: ["linkedin", "twitter"],
    content: { /* ... */ },
    scheduled_date: "2025-03-01"
  },
  // Week 2: Thought leadership
  {
    campaign_type: "thought_leadership",
    platforms: ["linkedin"],
    content: { /* ... */ },
    scheduled_date: "2025-03-08"
  },
  // Week 3: Customer testimonial
  {
    campaign_type: "testimonial",
    platforms: ["linkedin", "facebook"],
    content: { /* ... */ },
    scheduled_date: "2025-03-15"
  },
  // Week 4: Webinar promotion
  {
    campaign_type: "event_promotion",
    platforms: ["linkedin", "twitter", "facebook"],
    content: { /* ... */ },
    scheduled_date: "2025-03-22"
  }
];

await generateMultipleCampaigns(monthlyCampaigns);
```

---

## Pattern 6: Platform-Specific Optimization

**Use Case:** Generate highly optimized content for each platform separately

**Code Example:**

```javascript
async function generatePlatformOptimizedPosts(baseContent) {
  const platforms = {
    linkedin: {
      tone: "professional",
      format: "detailed",
      length: "long_form", // 1500-1800 chars
      hashtags: 5,
      emoji: "strategic"
    },
    twitter: {
      tone: "casual",
      format: "concise",
      length: "max_280",
      hashtags: 2,
      emoji: "moderate"
    },
    facebook: {
      tone: "conversational",
      format: "storytelling",
      length: "medium", // 600-800 chars
      hashtags: 2,
      emoji: "enthusiastic"
    }
  };

  const posts = {};

  for (const [platform, settings] of Object.entries(platforms)) {
    console.log(`\n📱 Optimizing for ${platform}...`);

    const post = await generateSocialPost({
      campaign_type: baseContent.campaign_type,
      platforms: [platform], // One platform at a time
      content: {
        ...baseContent,
        optimize_for: platform,
        preferred_length: settings.length
      },
      tone: settings.tone,
      cta: baseContent.cta,
      hashtags: {
        ...baseContent.hashtags,
        max_count: settings.hashtags
      },
      formatting: {
        style: settings.format,
        emoji_usage: settings.emoji
      },
      ab_testing: {
        enabled: true,
        variations_count: 2
      },
      metadata: {
        optimization_strategy: "platform_specific",
        target_platform: platform
      }
    });

    posts[platform] = post;
    console.log(`   ✅ ${platform} post created`);
  }

  return posts;
}

// Usage
const baseContent = {
  campaign_type: "product_launch",
  product_name: "Analytics Dashboard",
  value_proposition: "Get insights in seconds",
  key_features: ["AI-powered", "Real-time", "Custom alerts"],
  cta: {
    type: "sign_up",
    text: "Start free trial",
    url: "https://company.com/trial"
  },
  hashtags: {
    branded: ["#AnalyticsPro"],
    industry: ["#DataScience", "#Analytics", "#AI"]
  }
};

const optimizedPosts = await generatePlatformOptimizedPosts(baseContent);
```

---

## Pattern 7: Compliance Check Integration

**Use Case:** Validate posts against company policies before approval

**Code Example:**

```javascript
const { checkPolicyCompliance } = require('../compliance/company_handbook_enforcer');

async function createCompliantSocialPost(postDetails) {
  // Generate post
  const post = await generateSocialPost(postDetails);

  if (!post.success) {
    return post;
  }

  // Check each variation for compliance
  const complianceResults = [];

  for (const platform of post.platforms) {
    for (const variation of post.variations[platform]) {
      const compliance = await checkPolicyCompliance({
        type: "social_media",
        platform: platform,
        content: variation.content,
        hashtags: variation.hashtags,
        cta_url: variation.cta.url
      });

      if (compliance.violations.length > 0) {
        console.warn(`⚠️ Compliance issues in ${platform} Variation ${variation.id}:`);
        compliance.violations.forEach(v => {
          console.warn(`   - ${v.policy}: ${v.reasoning}`);
        });

        complianceResults.push({
          platform,
          variation_id: variation.id,
          requires_review: true,
          violations: compliance.violations
        });
      } else {
        complianceResults.push({
          platform,
          variation_id: variation.id,
          requires_review: false,
          violations: []
        });
      }
    }
  }

  // Flag post for review if any violations
  const requiresReview = complianceResults.some(r => r.requires_review);

  if (requiresReview) {
    console.log(`\n📋 Post flagged for compliance review`);
    post.requires_approval = true;
    post.compliance_issues = complianceResults;
  } else {
    console.log(`\n✅ All variations pass compliance checks`);
  }

  return post;
}

// Usage
await createCompliantSocialPost({
  campaign_type: "company_news",
  platforms: ["linkedin", "twitter"],
  content: {
    news_type: "acquisition",
    acquired_company: "TechStartup Inc",
    acquisition_terms: "undisclosed" // Avoid specific financials
  },
  tone: "professional",
  cta: {
    type: "learn_more",
    url: "https://company.com/news/acquisition"
  }
});
```

---

## Pattern 8: Seasonal Campaign Templates

**Use Case:** Pre-configured templates for recurring seasonal campaigns

**Code Example:**

```javascript
const seasonalTemplates = {
  black_friday: {
    campaign_type: "brand_awareness",
    tone: "enthusiastic",
    emoji_usage: "high",
    urgency: "critical",
    cta_type: "sign_up",
    hashtags: ["#BlackFriday", "#CyberMonday", "#Deals"]
  },
  year_end_review: {
    campaign_type: "company_news",
    tone: "professional",
    emoji_usage: "moderate",
    urgency: "low",
    cta_type: "learn_more",
    hashtags: ["#YearInReview", "#CompanyGrowth"]
  },
  new_year: {
    campaign_type: "engagement",
    tone: "enthusiastic",
    emoji_usage: "high",
    urgency: "low",
    cta_type: "engagement",
    hashtags: ["#NewYear", "#Goals2025"]
  }
};

async function launchSeasonalCampaign(season, customContent) {
  const template = seasonalTemplates[season];

  if (!template) {
    throw new Error(`Unknown season: ${season}`);
  }

  console.log(`🎯 Launching ${season} campaign...`);

  const campaign = await generateSocialPost({
    campaign_type: template.campaign_type,
    platforms: ["linkedin", "twitter", "facebook"],
    content: {
      ...customContent,
      seasonal_theme: season
    },
    tone: template.tone,
    cta: {
      type: template.cta_type,
      text: customContent.cta_text,
      url: customContent.cta_url,
      urgency: template.urgency
    },
    hashtags: {
      branded: customContent.branded_hashtags,
      industry: customContent.industry_hashtags,
      seasonal: template.hashtags
    },
    formatting: {
      emoji_usage: template.emoji_usage
    },
    ab_testing: {
      enabled: true,
      variations_count: 3
    },
    metadata: {
      campaign_template: season,
      seasonal: true
    }
  });

  console.log(`✅ ${season} campaign created`);
  return campaign;
}

// Usage
await launchSeasonalCampaign("black_friday", {
  branded_hashtags: ["#CompanyDeals"],
  industry_hashtags: ["#SaaS", "#CloudStorage"],
  cta_text: "Get 50% off",
  cta_url: "https://company.com/black-friday",
  offer_details: "50% off all plans - 48 hours only",
  value_highlight: "Biggest discount of the year"
});
```

---

## Best Practices

### 1. Always Validate Character Limits

```javascript
// ✅ Good: Validate before generation
if (content.length > 280 && platforms.includes('twitter')) {
  console.warn('Content too long for Twitter');
  // Truncate or split into thread
}
```

### 2. Use Branded Hashtags Consistently

```javascript
// ✅ Good: Centralized brand hashtags
const BRAND_HASHTAGS = {
  primary: "#CompanyName",
  product: "#ProductName",
  category: "#SaaSPlatform"
};

hashtags: {
  branded: [BRAND_HASHTAGS.primary, BRAND_HASHTAGS.product]
}
```

### 3. Track Campaign Performance

```javascript
// ✅ Good: Include tracking metadata
metadata: {
  campaign_id: generateCampaignId(),
  tracking_code: "CAMP-2025-Q1-001",
  budget_allocated: 5000,
  target_impressions: 100000
}
```

### 4. Schedule Posts at Optimal Times

```javascript
// ✅ Good: Use platform-specific timing
const optimalTimes = {
  linkedin: "2025-03-01T09:00:00-08:00", // Tuesday 9 AM PST
  twitter: "2025-03-01T12:00:00-08:00",  // Tuesday 12 PM PST
  facebook: "2025-03-01T14:00:00-08:00"  // Tuesday 2 PM PST
};
```

---

## Performance Optimization

### Parallel Generation for Speed

```javascript
// ✅ Efficient: Generate multiple campaigns in parallel
const campaigns = await Promise.all([
  generateSocialPost(campaign1),
  generateSocialPost(campaign2),
  generateSocialPost(campaign3)
]);

console.log(`Generated ${campaigns.length} campaigns in ${elapsed}s`);
```

### Reuse Successful Elements

```javascript
// ✅ Smart: Learn from past successes
const successfulElements = {
  headline_style: "pain_point",
  cta_text: "Start free trial",
  emoji_placement: "end_of_sentence"
};

// Apply to new campaigns
content: {
  ...newContent,
  optimize_with: successfulElements
}
```

---

These patterns demonstrate production-ready workflows for the social_post_generator skill! 🚀
