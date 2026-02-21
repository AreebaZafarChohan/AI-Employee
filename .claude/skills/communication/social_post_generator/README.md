# Social Post Generator Skill

Professional social media post drafting for LinkedIn, Twitter/X, and Facebook with A/B testing variations.

## Quick Start

```javascript
const { generateSocialPost } = require('./social_post_generator');

const post = await generateSocialPost({
  campaign_type: "product_launch",
  platforms: ["linkedin", "twitter"],
  content: {
    product_name: "CloudSync Pro",
    value_proposition: "Seamlessly sync your files with military-grade encryption",
    key_features: ["End-to-end encryption", "10TB storage", "Real-time collaboration"]
  },
  tone: "professional",
  cta: {
    type: "sign_up",
    text: "Get early access",
    url: "https://company.com/product-launch"
  },
  ab_testing: {
    enabled: true,
    variations_count: 3
  }
});

console.log(`Posts created: ${post.file_path}`);
console.log(`Variations: ${post.variations_count}`);
```

## Features

- ✅ **Multi-Platform Support**: LinkedIn, Twitter/X, Facebook
- ✅ **A/B Testing**: Generate 2-5 variations per platform
- ✅ **Platform Optimization**: Character limits, hashtag best practices
- ✅ **CTA Integration**: Clear calls-to-action with tracking
- ✅ **Hashtag Strategy**: Branded, industry, and trending hashtags
- ✅ **Tone Adaptation**: Professional, casual, enthusiastic, informative
- ✅ **Compliance Workflow**: Built-in approval and review process
- ✅ **Analytics Ready**: UTM tracking and success metrics

## Installation

1. **Set up environment variables:**

```bash
cp .claude/skills/communication/social_post_generator/assets/.env.example .env
```

2. **Configure brand settings:**

```bash
export VAULT_PATH="/path/to/vault"
export SOCIAL_BRAND_NAME="Your Company"
export SOCIAL_BRAND_VOICE="professional"
export SOCIAL_TARGET_AUDIENCE="B2B decision makers"
```

3. **Create required directories:**

```bash
mkdir -p "$VAULT_PATH/Social_Posts"
```

## Usage

### Product Launch

```javascript
await generateSocialPost({
  campaign_type: "product_launch",
  platforms: ["linkedin", "twitter", "facebook"],
  content: {
    product_name: "New Product X",
    value_proposition: "Solve problem Y with feature Z",
    launch_date: "2025-03-01",
    special_offer: "20% off early birds"
  },
  tone: "enthusiastic",
  cta: {
    type: "sign_up",
    url: "https://company.com/launch"
  }
});
```

### Content Promotion

```javascript
await generateSocialPost({
  campaign_type: "content_promotion",
  platforms: ["linkedin"],
  content: {
    content_type: "blog_post",
    title: "5 Ways to Improve Your SaaS Onboarding",
    summary: "Learn proven strategies to reduce churn...",
    reading_time: "5 min"
  },
  tone: "informative",
  cta: {
    type: "learn_more",
    url: "https://blog.company.com/saas-onboarding"
  }
});
```

### Thought Leadership

```javascript
await generateSocialPost({
  campaign_type: "thought_leadership",
  platforms: ["linkedin", "twitter"],
  content: {
    topic: "Future of AI in Customer Service",
    key_insights: [
      "AI augments, not replaces human agents",
      "Personalization at scale is now possible",
      "Data privacy remains critical"
    ],
    opinion: "controversial but data-backed"
  },
  tone: "professional",
  ab_testing: {
    enabled: true,
    variations_count: 2
  }
});
```

### Event Promotion

```javascript
await generateSocialPost({
  campaign_type: "event_promotion",
  platforms: ["linkedin", "facebook"],
  content: {
    event_name: "SaaS Growth Summit 2025",
    event_date: "2025-04-15",
    event_type: "webinar",
    speakers: ["Sarah Johnson, CEO", "Mike Chen, Growth Expert"],
    topics: ["Scaling to $10M ARR", "PLG strategies"]
  },
  tone: "enthusiastic",
  cta: {
    type: "register",
    text: "Reserve your spot",
    url: "https://company.com/summit"
  }
});
```

## Supported Platforms

### LinkedIn
- **Character Limit:** 3,000 (optimal: 1,200-1,800)
- **Hashtags:** 3-5 hashtags
- **Best For:** B2B, thought leadership, professional content
- **Tone:** Professional, informative

### Twitter/X
- **Character Limit:** 280
- **Hashtags:** 1-3 hashtags
- **Best For:** News, quick updates, engagement
- **Tone:** Concise, punchy, conversational

### Facebook
- **Character Limit:** 63,206 (optimal: 400-800)
- **Hashtags:** 1-3 hashtags (less important)
- **Best For:** Community building, storytelling
- **Tone:** Conversational, personal

## Campaign Types

| Type | Use Case | Best Platforms |
|------|----------|----------------|
| `product_launch` | New product announcements | LinkedIn, Twitter |
| `content_promotion` | Blog, video, podcast | LinkedIn, Facebook |
| `thought_leadership` | Industry insights | LinkedIn |
| `company_news` | Milestones, awards | All platforms |
| `event_promotion` | Webinars, conferences | LinkedIn, Facebook |
| `engagement` | Polls, discussions | Twitter, LinkedIn |
| `testimonial` | Customer stories | LinkedIn, Facebook |
| `brand_awareness` | Visibility campaigns | All platforms |
| `lead_generation` | Landing pages | LinkedIn |

## Tone Options

### Professional
- Formal language
- Bullet points and structure
- Data-driven
- **Best for:** B2B, executive audience

### Casual
- Conversational language
- Personal voice
- Relatable examples
- **Best for:** B2C, younger audience

### Enthusiastic
- Energetic language
- Exclamation points
- Celebratory tone
- **Best for:** Launches, celebrations

### Informative
- Educational focus
- Clear explanations
- Actionable insights
- **Best for:** Thought leadership, content

## A/B Testing

Generate multiple variations to test:

**Test Variables:**
- Headlines (feature vs. benefit vs. pain point)
- CTA text ("Learn more" vs. "Get started" vs. "Try now")
- Emoji usage (minimal vs. moderate vs. strategic)
- Format (bullets vs. paragraphs vs. questions)
- Hook (statistic vs. question vs. story)

**Example:**
```javascript
ab_testing: {
  enabled: true,
  variations_count: 3,
  test_variables: ["headline", "cta_text", "emoji_usage"]
}
```

## CTA Best Practices

### CTA Types

| Type | Use Case | Example Text |
|------|----------|--------------|
| `learn_more` | Educational content | "Read the full guide" |
| `sign_up` | Account creation | "Start free trial" |
| `download` | Resource downloads | "Download the ebook" |
| `register` | Event registration | "Save your seat" |
| `contact` | Sales inquiries | "Talk to an expert" |

### URL Tracking

Always include UTM parameters:
```
https://company.com/page?utm_source=linkedin&utm_medium=social&utm_campaign=product_launch&utm_content=variation_a
```

## Hashtag Strategy

### Branded Hashtags
Your company/product hashtags:
```javascript
hashtags: {
  branded: ["#YourBrand", "#YourProduct"]
}
```

### Industry Hashtags
Relevant category hashtags:
```javascript
hashtags: {
  industry: ["#SaaS", "#B2B", "#CloudComputing"]
}
```

### Platform Guidelines
- **LinkedIn:** 3-5 hashtags at end of post
- **Twitter:** 1-3 hashtags integrated into copy
- **Facebook:** 1-3 hashtags (optional)

## Output Structure

Each draft is saved as:

```markdown
---
draft_id: SOCIAL-20250204-143022-ABC123
status: draft
campaign_type: product_launch
platforms: ["linkedin", "twitter"]
variations_count: 3
---

# Social Post Draft: Product Launch

## LinkedIn Post Variations
### Variation A
[Post content]

### Variation B
[Post content]

### Variation C
[Post content]

## Twitter/X Post Variations
[3 variations]

## A/B Testing Strategy
[Test plan]

## Platform-Specific Optimization
[Platform details]

## CTA Analysis
[CTA details]

## Metadata
[Tracking info]
```

## Configuration

### Basic Setup

```bash
VAULT_PATH="/path/to/vault"
SOCIAL_BRAND_NAME="Acme Corp"
SOCIAL_BRAND_VOICE="professional"
```

### With A/B Testing

```bash
SOCIAL_AB_VARIATIONS_COUNT="3"
SOCIAL_DEFAULT_PLATFORMS="linkedin,twitter"
SOCIAL_INCLUDE_EMOJI="true"
```

### Production Setup

```bash
VAULT_PATH="/path/to/vault"
SOCIAL_BRAND_NAME="Acme Corp"
SOCIAL_BRAND_VOICE="professional"
SOCIAL_TARGET_AUDIENCE="B2B decision makers"
SOCIAL_REQUIRE_APPROVAL="true"
SOCIAL_AUDIT_LOG_PATH="$VAULT_PATH/Audit_Logs"
SOCIAL_BRANDED_HASHTAGS="#AcmeCorp,#AcmeProducts"
```

## Best Practices

### 1. Platform-Specific Content

```javascript
// ❌ Same content for all platforms
platforms: ["linkedin", "twitter", "facebook"]
content: { generic_message: "Check out our product" }

// ✅ Platform-optimized
platforms: ["linkedin"]  // Professional audience
tone: "professional"
content: { detailed_features: [...] }

platforms: ["twitter"]  // Quick updates
tone: "casual"
content: { concise_hook: "..." }
```

### 2. Clear CTAs

```javascript
// ❌ Vague CTA
cta: { text: "Click here" }

// ✅ Specific, action-oriented
cta: {
  type: "sign_up",
  text: "Start your free trial",
  url: "https://company.com/trial",
  urgency: "high"
}
```

### 3. Relevant Hashtags

```javascript
// ❌ Too many generic hashtags
hashtags: ["#business", "#success", "#motivation", "#entrepreneur", "#marketing"]

// ✅ Targeted, relevant
hashtags: {
  branded: ["#YourProduct"],
  industry: ["#SaaS", "#B2BSales"]
}
```

### 4. A/B Test Systematically

```javascript
// ✅ Test one variable at a time
ab_testing: {
  enabled: true,
  variations_count: 3,
  test_variables: ["headline"]  // Focus on headline first
}
```

## Troubleshooting

### Post Too Long

```bash
# Check character count per platform
LinkedIn: Max 3,000 (optimal 1,200-1,800)
Twitter: Max 280
Facebook: Max 63,206 (optimal 400-800)
```

### No Variations Generated

```javascript
// Ensure A/B testing is enabled
ab_testing: {
  enabled: true,  // Must be true
  variations_count: 3
}
```

### Hashtags Not Appearing

```bash
# Configure branded hashtags
export SOCIAL_BRANDED_HASHTAGS="#Brand1,#Brand2"

# Enable auto hashtags
export SOCIAL_AUTO_HASHTAGS="true"
```

## Integration

### With Company Handbook Enforcer

```javascript
const post = await generateSocialPost({ ... });
const compliance = await checkPolicyCompliance({
  type: "social_media",
  content: post.content
});
```

### With Approval Request Creator

```javascript
if (campaign_type === "executive_announcement") {
  await createApprovalRequest({
    action: { type: "social_post", details: post }
  });
}
```

## Documentation

- **SKILL.md** - Complete technical documentation
- **EXAMPLES.md** - Real-world campaign examples
- **patterns.md** - Usage patterns and best practices
- **gotchas.md** - Common pitfalls and solutions
- **impact-checklist.md** - Deployment guide

## Support

For issues or questions:
- Check **references/gotchas.md** for common problems
- Review **EXAMPLES.md** for real-world scenarios
- Consult **references/patterns.md** for best practices

## Version

**v1.0.0** - Initial release (2025-02-04)

---

**Ready to create engaging social media content!** 🚀
