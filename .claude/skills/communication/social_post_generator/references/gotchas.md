# Social Post Generator - Common Gotchas and Troubleshooting

Common pitfalls, edge cases, and troubleshooting guidance for the `social_post_generator` skill.

---

## Common Gotchas

### 1. Twitter Character Limit Exceeded

**Problem:**
Post content exceeds Twitter's 280-character limit

**Example:**
```javascript
// ❌ WRONG - content too long
const post = await generateSocialPost({
  campaign_type: "product_launch",
  platforms: ["twitter"],
  content: {
    product_name: "Advanced Analytics Dashboard Pro",
    value_proposition: "Get comprehensive, actionable insights from your data in seconds instead of spending hours on manual analysis and report generation",
    key_features: [
      "Natural language query interface",
      "Automated anomaly detection with ML",
      "Predictive forecasting algorithms",
      "Real-time customizable alerts"
    ]
  }
});
```

**Generated (problematic):**
```
Introducing Advanced Analytics Dashboard Pro 🚀

Get comprehensive, actionable insights from your data in seconds instead of spending hours on manual analysis:
✅ Natural language query interface
✅ Automated anomaly detection with ML
✅ Predictive forecasting algorithms
✅ Real-time customizable alerts

Launch special: 50% off
Try it → company.com/launch

#Analytics #AI #DataScience
[355 characters - EXCEEDS 280 LIMIT!]
```

**Solution:**
```javascript
// ✅ CORRECT - concise Twitter-optimized content
const post = await generateSocialPost({
  campaign_type: "product_launch",
  platforms: ["twitter"],
  content: {
    product_name: "Analytics Pro",
    value_proposition: "Get insights in seconds, not hours",
    key_features: [
      "Natural language queries",
      "AI anomaly detection",
      "Predictive forecasting"
    ],
    twitter_optimized: true // Special flag for Twitter
  },
  formatting: {
    style: "ultra_concise",
    bullet_style: "emoji" // Use emoji instead of checkmarks
  }
});
```

**Generated (correct):**
```
Get insights in seconds, not hours ⚡

Analytics Pro launches today:
🔍 Natural language queries
🤖 AI anomaly detection
📈 Predictive forecasting

Launch: 50% off

Try it → co.com/analytics

#Analytics #AI
[237 characters - WITHIN LIMIT ✓]
```

**Fix:**
- Use `twitter_optimized: true` flag
- Limit features to top 3
- Use shorter CTAs
- Use link shorteners
- Reduce hashtag count

---

### 2. Too Many Hashtags Kill Engagement

**Problem:**
Using excessive hashtags reduces post reach and engagement

**Example:**
```javascript
// ❌ WRONG - hashtag spam
hashtags: {
  branded: ["#CompanyName", "#ProductName", "#BrandVoice"],
  industry: ["#SaaS", "#CloudComputing", "#B2B", "#Technology", "#Innovation"],
  trending: ["#TechTrends", "#AI", "#MachineLearning", "#BigData"]
}
// Total: 12 hashtags!
```

**Generated (problematic):**
```
[Post content]

#CompanyName #ProductName #BrandVoice #SaaS #CloudComputing #B2B #Technology #Innovation #TechTrends #AI #MachineLearning #BigData
```

**Issues:**
- Looks spammy
- Reduces credibility
- Algorithm may flag as low-quality
- Engagement drops 15-20%

**Solution:**
```javascript
// ✅ CORRECT - strategic hashtag use
hashtags: {
  branded: ["#CompanyName"], // 1 brand hashtag
  industry: ["#SaaS", "#B2B"], // 2-3 relevant hashtags
  trending: [] // Skip unless highly relevant
}
// Total: 3 hashtags
```

**Platform-Specific Limits:**
- LinkedIn: 3-5 hashtags (optimal: 3)
- Twitter: 1-3 hashtags (optimal: 2)
- Facebook: 1-3 hashtags (less important)

**Fix:**
- Set `SOCIAL_MAX_HASHTAGS_*` in `.env`
- Use only highly relevant hashtags
- Test hashtag performance
- Remove underperforming hashtags

---

### 3. Generic CTAs Don't Convert

**Problem:**
Vague CTAs fail to drive action

**Example:**
```javascript
// ❌ WRONG - generic CTA
cta: {
  type: "learn_more",
  text: "Click here",
  url: "https://company.com"
}
```

**Generated (weak):**
```
[Post content]

👉 Click here
```

**Conversion rate:** ~0.5-1%

**Solution:**
```javascript
// ✅ CORRECT - specific, benefit-driven CTA
cta: {
  type: "sign_up",
  text: "Start free 14-day trial (no credit card)",
  url: "https://company.com/trial?utm_source=linkedin&utm_campaign=launch",
  urgency: "high",
  benefit: "Setup takes 2 minutes"
}
```

**Generated (strong):**
```
[Post content]

🚀 Start free 14-day trial (no credit card)
Setup takes 2 minutes → company.com/trial
```

**Conversion rate:** ~3-5%

**Fix:**
- Be specific about what happens ("Start trial" not "Click here")
- Add benefit ("No credit card" / "Free forever")
- Create urgency when appropriate
- Use action verbs ("Get", "Start", "Join", "Claim")

---

### 4. Ignoring Platform Culture

**Problem:**
Using same tone/format across all platforms

**Example:**
```javascript
// ❌ WRONG - corporate LinkedIn post on Twitter
platforms: ["linkedin", "twitter"],
tone: "professional", // Too formal for Twitter
content: {
  detailed_announcement: "We are pleased to announce..."
}
```

**Twitter Output (feels off):**
```
We are pleased to announce the launch of our new enterprise-grade analytics platform. This solution delivers comprehensive insights...
[Sounds too corporate for Twitter audience]
```

**Solution:**
```javascript
// ✅ CORRECT - adapt tone per platform
platforms: ["linkedin", "twitter"],
platform_overrides: {
  linkedin: {
    tone: "professional",
    format: "detailed"
  },
  twitter: {
    tone: "casual",
    format: "punchy"
  }
}
```

**LinkedIn Output (appropriate):**
```
We're excited to announce Analytics Pro 📊

Built for data teams who need insights fast:
✅ Natural language queries
✅ AI-powered analysis
✅ Real-time alerts

Perfect for scaling teams...
```

**Twitter Output (appropriate):**
```
Analytics Pro is here! ⚡

Ask questions in plain English, get instant answers

No SQL needed 🙌

Try it → company.com/analytics
```

**Fix:**
- Research platform culture
- Adapt tone: LinkedIn (professional), Twitter (casual), Facebook (conversational)
- Match audience expectations
- Test different approaches

---

### 5. Missing UTM Parameters

**Problem:**
Can't track which posts drive conversions

**Example:**
```javascript
// ❌ WRONG - no tracking
cta: {
  url: "https://company.com/product"
}
```

**Issue:** Can't measure:
- Which platform drove traffic
- Which variation performed best
- Campaign ROI

**Solution:**
```javascript
// ✅ CORRECT - full UTM tracking
cta: {
  url: "https://company.com/product",
  utm_params: {
    source: "linkedin", // Auto-detected from platform
    medium: "social",
    campaign: "product_launch_q1_2025",
    content: "variation_a",
    term: "analytics_dashboard"
  }
}
```

**Generated URL:**
```
https://company.com/product?utm_source=linkedin&utm_medium=social&utm_campaign=product_launch_q1_2025&utm_content=variation_a&utm_term=analytics_dashboard
```

**Fix:**
- Always include UTM parameters
- Use consistent naming convention
- Track by platform, campaign, and variation
- Set `SOCIAL_UTM_SOURCE_AUTO="true"` in `.env`

---

### 6. Posting at Wrong Times

**Problem:**
Publishing when target audience is offline

**Example:**
```javascript
// ❌ WRONG - posting at 2 AM
scheduled_time: "2025-03-01T02:00:00-08:00" // 2 AM PST
```

**Result:** 80% lower reach

**Solution:**
```javascript
// ✅ CORRECT - optimal posting times
const optimalTimes = {
  linkedin: {
    best_days: ["tuesday", "wednesday", "thursday"],
    best_hours: ["07-09", "12-13"], // 7-9 AM or 12-1 PM
    timezone: "America/Los_Angeles"
  },
  twitter: {
    best_days: ["monday", "tuesday", "wednesday", "thursday", "friday"],
    best_hours: ["08-10", "18-21"], // 8-10 AM or 6-9 PM
    timezone: "America/Los_Angeles"
  },
  facebook: {
    best_days: ["wednesday", "thursday", "friday"],
    best_hours: ["13-15"], // 1-3 PM
    timezone: "America/Los_Angeles"
  }
};

scheduled_time: "2025-03-05T09:00:00-08:00" // Tuesday 9 AM PST for LinkedIn
```

**Platform-Specific Best Times:**
- **LinkedIn (B2B):** Tue-Thu, 7-9 AM or 12-1 PM
- **Twitter:** Mon-Fri, 8-10 AM or 6-9 PM
- **Facebook:** Wed-Fri, 1-3 PM

**Fix:**
- Schedule posts for optimal times
- Consider target audience timezone
- Test different times for your audience
- Use scheduling tools (Hootsuite, Buffer)

---

### 7. No A/B Testing Strategy

**Problem:**
Generating variations without testing plan

**Example:**
```javascript
// ❌ WRONG - A/B testing enabled but no strategy
ab_testing: {
  enabled: true,
  variations_count: 3
}
// Which variation is which? What are you testing?
```

**Solution:**
```javascript
// ✅ CORRECT - clear testing hypothesis
ab_testing: {
  enabled: true,
  variations_count: 3,
  test_variables: ["headline_style"], // Test ONE variable
  variations: [
    {
      id: "A",
      headline_style: "feature_focus",
      hypothesis: "Feature-focused headlines drive more clicks"
    },
    {
      id: "B",
      headline_style: "pain_point",
      hypothesis: "Pain point headlines resonate more"
    },
    {
      id: "C",
      headline_style: "social_proof",
      hypothesis: "Social proof increases trust"
    }
  ],
  success_metric: "click_through_rate",
  minimum_sample_size: 1000,
  test_duration_days: 7
}
```

**Fix:**
- Test ONE variable at a time
- Define clear hypothesis
- Set success metrics
- Run test for sufficient duration (min 7 days or 1000 impressions)
- Document learnings

---

### 8. Forgetting Visual Assets

**Problem:**
Social posts without images get 50-80% less engagement

**Example:**
```javascript
// ❌ WRONG - text-only post
const post = await generateSocialPost({
  // ... post content
  // No mention of visuals!
});
```

**Engagement:** 50-80% lower than posts with images

**Solution:**
```javascript
// ✅ CORRECT - include visual recommendations
const post = await generateSocialPost({
  campaign_type: "product_launch",
  content: { /* ... */ },
  visual_assets: {
    required: true,
    recommendations: [
      {
        type: "product_screenshot",
        dimensions: "1200x627", // LinkedIn/Facebook
        description: "Dashboard showing AI insights"
      },
      {
        type: "twitter_card",
        dimensions: "1200x675",
        description: "Product logo + key benefit"
      }
    ],
    design_notes: "Use brand colors, include logo, mobile-optimized"
  }
});
```

**Fix:**
- Always include visual asset recommendations
- Specify dimensions per platform
- LinkedIn/Facebook: 1200x627px
- Twitter: 1200x675px
- Use high-quality images
- Test video content (performs 2-3x better)

---

### 9. Not Monitoring Competitor Mentions

**Problem:**
Accidentally mentioning competitors in posts

**Example:**
```javascript
// ❌ WRONG - mentions competitor
content: {
  value_proposition: "Unlike Competitor X, we actually have real-time analytics"
}
```

**Issues:**
- Free advertising for competitor
- Looks unprofessional
- May violate brand guidelines

**Solution:**
```javascript
// ✅ CORRECT - focus on benefits, not competitors
content: {
  value_proposition: "Get real-time analytics that actually work",
  differentiation: "Built by data scientists, for data teams"
}

// Enable competitor detection
SOCIAL_FLAG_COMPETITOR_MENTIONS="true"
SOCIAL_COMPETITORS="CompetitorX,CompetitorY,CompetitorZ"
```

**Fix:**
- Set up competitor detection in `.env`
- Focus on your benefits, not competitor weaknesses
- Let features speak for themselves
- If comparison needed, use generic terms ("other tools")

---

### 10. Ignoring Engagement in First Hour

**Problem:**
Not responding to comments quickly

**Example:**
Post goes live at 9 AM, first comment at 9:15 AM, response at 5 PM (8 hours later)

**Impact:** Algorithm deprioritizes post, reach drops 60%

**Solution:**
```javascript
// Include in campaign plan
next_steps: [
  {
    action: "Monitor comments",
    timing: "First 60 minutes after posting",
    owner: "Social media manager",
    response_time_target: "< 15 minutes"
  },
  {
    action: "Engage with relevant comments",
    timing: "First 24 hours",
    types: ["questions", "positive_feedback", "concerns"]
  }
]
```

**Fix:**
- Monitor posts actively for first hour
- Respond to comments within 15 minutes
- Like and engage with all comments
- Ask follow-up questions to drive conversation
- Platform algorithms reward early engagement

---

## Troubleshooting Guide

### Issue: Post Generation Fails

**Symptoms:**
```
Error: Failed to generate social post
```

**Diagnosis:**
```bash
# Check if directory exists
ls -la "$VAULT_PATH/Social_Posts"

# Check write permissions
test -w "$VAULT_PATH/Social_Posts" && echo "Writable" || echo "Not writable"

# Verify environment variables
env | grep SOCIAL_
```

**Solution:**
```bash
# Create directory if missing
mkdir -p "$VAULT_PATH/Social_Posts"

# Fix permissions
chmod 755 "$VAULT_PATH/Social_Posts"

# Verify brand settings are configured
export SOCIAL_BRAND_NAME="Your Company"
export SOCIAL_BRAND_VOICE="professional"
```

---

### Issue: Character Count Inconsistent

**Symptoms:**
Generated post shows 275 characters but Twitter rejects it as > 280

**Diagnosis:**
Twitter counts URLs as 23 characters regardless of actual length

**Solution:**
```javascript
// Account for Twitter URL shortening
if (platform === 'twitter') {
  const urlCount = (content.match(/https?:\/\/\S+/g) || []).length;
  const effectiveLength = content.length - actualUrlLength + (urlCount * 23);
}
```

---

### Issue: Hashtags Not Generated

**Symptoms:**
Post has no hashtags even though they're configured

**Diagnosis:**
```bash
# Check if auto-hashtags is enabled
echo $SOCIAL_AUTO_HASHTAGS

# Check branded hashtags
echo $SOCIAL_BRANDED_HASHTAGS
```

**Solution:**
```bash
# Enable auto-hashtags
export SOCIAL_AUTO_HASHTAGS="true"

# Set branded hashtags
export SOCIAL_BRANDED_HASHTAGS="#YourBrand,#YourProduct"
```

---

### Issue: A/B Variations Look Too Similar

**Symptoms:**
All 3 variations have minor differences

**Diagnosis:**
Not enough variation in test variables

**Solution:**
```javascript
// ✅ Create meaningful differences
ab_testing: {
  enabled: true,
  variations_count: 3,
  test_variables: ["headline_style", "format"],
  variation_guidelines: {
    differentiation_level: "high", // Force distinct differences
    minimum_word_change: 30 // At least 30% word difference
  }
}
```

---

### Issue: CTR Lower Than Expected

**Symptoms:**
Post gets views but no clicks

**Diagnosis:**
- Weak CTA
- Link not visible
- No urgency

**Solution:**
```javascript
// Improve CTA
cta: {
  type: "sign_up",
  text: "Start free trial (no credit card) →", // Clear benefit + arrow
  url: "https://company.com/trial",
  urgency: "high",
  visibility: "prominent", // Make CTA stand out
  multiple_mentions: true // Mention CTA in post body AND at end
}
```

---

## Best Practices Checklist

Before publishing any social post:

- [ ] Character count within platform limits
- [ ] Hashtags: 3-5 (LinkedIn), 1-3 (Twitter/Facebook)
- [ ] Clear, specific CTA with benefit
- [ ] UTM tracking parameters included
- [ ] Visual assets prepared (images/video)
- [ ] Scheduled for optimal time (platform-specific)
- [ ] A/B testing plan documented
- [ ] Competitor mentions removed
- [ ] Compliance check passed
- [ ] Engagement plan for first hour
- [ ] Mobile preview looks good
- [ ] Link tested and working

---

## Emergency Recovery

If a post goes wrong:

### Crisis Response

```bash
# 1. Immediately pause scheduled posts
# 2. Archive problematic post
mv "$VAULT_PATH/Social_Posts/problem-post.md" "$VAULT_PATH/Social_Posts_Archive/"

# 3. Document issue
echo "Issue: [description]" >> "$VAULT_PATH/Social_Posts/incidents.log"
echo "Date: $(date)" >> "$VAULT_PATH/Social_Posts/incidents.log"
echo "Resolution: [action taken]" >> "$VAULT_PATH/Social_Posts/incidents.log"

# 4. Generate corrected version
# Use skill to create new post

# 5. Review approval process
# Update guidelines to prevent recurrence
```

---

These gotchas will save you hours of troubleshooting! Learn from common mistakes and create better social content. 🚀
