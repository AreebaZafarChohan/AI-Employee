---
name: social_post_generator
description: Draft social media posts (LinkedIn, Twitter/X, Facebook) aligned with business goals. Includes CTAs, hashtags, audience targeting, and A/B testing variations.
---

# Social Post Generator

## Purpose

This skill generates professional, engaging social media posts tailored to specific platforms (LinkedIn, Twitter/X, Facebook) and business objectives. It produces platform-optimized content with appropriate CTAs, hashtags, audience tone, and multiple variations for A/B testing.

The skill is designed for marketing teams, social media managers, and business professionals who need consistent, high-quality social content aligned with brand voice and campaign goals.

## When to Use This Skill

Use `social_post_generator` when:

- **Product launches**: Announcing new products, features, or services
- **Content promotion**: Sharing blog posts, videos, podcasts, or resources
- **Thought leadership**: Posting industry insights, opinions, or expertise
- **Company news**: Announcing milestones, awards, partnerships, or team updates
- **Event promotion**: Marketing webinars, conferences, or community events
- **Engagement campaigns**: Creating conversation starters or community building posts
- **Customer testimonials**: Sharing success stories or case studies
- **Brand awareness**: Building visibility and recognition in target markets
- **Lead generation**: Driving traffic to landing pages or lead magnets

Do NOT use this skill when:

- **Crisis communications**: Sensitive issues requiring legal/PR review
- **Financial disclosures**: Regulated announcements requiring compliance approval
- **Personal employee posts**: Individual employee content (not company branded)
- **Customer service responses**: Direct replies to customer inquiries or complaints
- **Real-time news reactions**: Time-sensitive responses requiring immediate human judgment

## Impact Analysis Workflow

### 1. Environment Variable Strategy

**Build-Time vs Runtime Variables:**

This skill operates at runtime only. No build-time variables required.

**Runtime variables:**
```bash
# Required
VAULT_PATH="/absolute/path/to/vault"
SOCIAL_POSTS_PATH="$VAULT_PATH/Social_Posts"  # Auto-created if missing

# Required: Brand configuration
SOCIAL_BRAND_NAME="Your Company Name"
SOCIAL_BRAND_VOICE="professional"              # professional | conversational | playful | authoritative
SOCIAL_TARGET_AUDIENCE="B2B decision makers"   # Primary audience description

# Optional: Platform defaults
SOCIAL_DEFAULT_PLATFORMS="linkedin,twitter"    # Comma-separated list
SOCIAL_LINKEDIN_ENABLED="true"
SOCIAL_TWITTER_ENABLED="true"
SOCIAL_FACEBOOK_ENABLED="true"

# Optional: Content configuration
SOCIAL_DEFAULT_TONE="professional"             # professional | casual | enthusiastic | informative
SOCIAL_MAX_HASHTAGS_LINKEDIN="5"
SOCIAL_MAX_HASHTAGS_TWITTER="3"
SOCIAL_MAX_HASHTAGS_FACEBOOK="3"
SOCIAL_INCLUDE_EMOJI="true"
SOCIAL_AB_VARIATIONS_COUNT="3"                 # Number of A/B test variations to generate

# Optional: CTA configuration
SOCIAL_DEFAULT_CTA_TYPE="learn_more"           # learn_more | sign_up | download | register | contact
SOCIAL_CTA_URL_BASE="https://yourcompany.com"

# Optional: Compliance
SOCIAL_REQUIRE_APPROVAL="false"                # Require approval before posting
SOCIAL_INCLUDE_DISCLAIMER="false"              # Add legal disclaimer
SOCIAL_DISCLAIMER_TEXT=""                      # Custom disclaimer text

# Optional: Hashtag strategy
SOCIAL_BRANDED_HASHTAGS="#YourBrand,#YourProduct"  # Comma-separated branded hashtags
SOCIAL_AUTO_HASHTAGS="true"                    # Auto-generate relevant hashtags

# Optional: Audit trail
SOCIAL_AUDIT_LOG_PATH="$VAULT_PATH/Audit_Logs"
SOCIAL_SESSION_ID=""                           # Current agent session ID
```

**Secrets Management:**

- This skill does NOT post to social media (draft only)
- No social media API credentials required
- May reference URLs (not sensitive)
- Never log post content to system logs

**Variable Discovery Process:**
```bash
# Check social media configuration
cat .env | grep SOCIAL_

# Verify Social_Posts folder exists
test -d "$VAULT_PATH/Social_Posts" && echo "OK" || mkdir -p "$VAULT_PATH/Social_Posts"

# Count draft posts
find "$VAULT_PATH/Social_Posts" -name '*.md' | wc -l
```

### 2. Network & Topology Implications

**Port Discovery:**

No network ports required. This skill operates on local filesystem only.

**Dependency Topology:**

```
Social Post Generator
  ├── Vault State Manager (file writes to Social_Posts/)
  │   └── Filesystem (Social_Posts/ folder)
  └── Optional: Content Templates
      └── Filesystem (Social_Templates/ folder)
```

**Topology Notes:**
- Primary operation: local file writes (no external dependencies)
- No social media API integration (draft only)
- No database dependencies
- Stateless operation (each post is independent)

**Docker/K8s Implications:**

When containerizing agents that use this skill:
- Mount vault as read-write volume: `-v /host/vault:/vault:rw`
- Ensure `Social_Posts/` folder is writable
- No network access required
- No persistent storage needed beyond vault mount

### 3. Auth / CORS / Security Impact

**Authentication Pattern Analysis:**

- No authentication for filesystem access (local only)
- No social media API authentication (draft only)
- Agent authorization: all agents have write access to Social_Posts/ (per AGENTS.md §4)

**Security Considerations:**

| Risk | Mitigation |
|------|-----------|
| **Brand damage** | Require approval for sensitive topics |
| **Link hijacking** | Validate all URLs before including |
| **Inappropriate content** | Content moderation checks |
| **Hashtag spam** | Limit hashtag count per platform |
| **Competitor mentions** | Flag competitor brand names for review |
| **Sensitive information** | Never include confidential data |

**Validation Rules:**

Before creating any social post:
```javascript
function validateSocialPost(post) {
  // Required fields check
  if (!post.content || post.content.length === 0) {
    throw new Error("Post content cannot be empty");
  }

  // Platform-specific length validation
  if (post.platform === 'twitter' && post.content.length > 280) {
    throw new Error("Twitter post exceeds 280 character limit");
  }

  if (post.platform === 'linkedin' && post.content.length > 3000) {
    throw new Error("LinkedIn post exceeds 3000 character limit");
  }

  // CTA validation
  if (post.cta && post.cta.url) {
    if (!post.cta.url.startsWith('http')) {
      throw new Error("CTA URL must be a valid HTTP/HTTPS URL");
    }
  }

  // Hashtag validation
  const hashtagCount = (post.content.match(/#\w+/g) || []).length;
  if (post.platform === 'twitter' && hashtagCount > 3) {
    throw new Error("Twitter posts should have max 3 hashtags");
  }

  return true;
}
```

---

## Usage Patterns

### Pattern 1: Product Launch Announcement

**Use Case:** Announcing new product launch across multiple platforms

**Input:**
```javascript
const { generateSocialPost } = require('./social_post_generator');

const postDraft = await generateSocialPost({
  campaign_type: "product_launch",
  platforms: ["linkedin", "twitter", "facebook"],
  content: {
    product_name: "CloudSync Pro",
    value_proposition: "Seamlessly sync your files across all devices with military-grade encryption",
    key_features: [
      "End-to-end encryption",
      "10TB storage",
      "Real-time collaboration",
      "99.99% uptime SLA"
    ],
    launch_date: "2025-02-15",
    special_offer: "50% off for first 100 customers"
  },
  target_audience: {
    primary: "B2B decision makers",
    secondary: "IT professionals",
    persona: "CTOs and engineering managers at mid-size companies"
  },
  tone: "professional",
  cta: {
    type: "sign_up",
    text: "Get early access",
    url: "https://company.com/cloudsync-launch",
    urgency: "high"
  },
  hashtags: {
    branded: ["#CloudSyncPro", "#SecureCloud"],
    industry: ["#CloudStorage", "#DataSecurity", "#B2BSaaS"],
    trending: []
  },
  ab_testing: {
    enabled: true,
    variations_count: 3,
    test_variables: ["headline", "cta_text", "emoji_usage"]
  },
  metadata: {
    agent: "lex",
    session_id: "session_abc123",
    timestamp: "2025-02-04T14:30:22Z"
  }
});

console.log(`Social post drafts created: ${postDraft.file_path}`);
console.log(`Variations: ${postDraft.variations_count}`);
```

**Output File:** `Social_Posts/20250204-143022-product-launch-cloudsync-pro.md`

**File Content:**
```markdown
---
draft_id: SOCIAL-20250204-143022-ABC123
created_at: 2025-02-04T14:30:22Z
status: draft
campaign_type: product_launch
platforms: ["linkedin", "twitter", "facebook"]
tone: professional
ab_testing_enabled: true
variations_count: 3
requires_approval: false
---

# Social Post Draft: Product Launch - CloudSync Pro

**Draft ID:** SOCIAL-20250204-143022-ABC123
**Created:** 2025-02-04 14:30:22 UTC
**Status:** 📝 Draft
**Campaign Type:** Product Launch

---

## Campaign Overview

**Product:** CloudSync Pro
**Launch Date:** February 15, 2025
**Target Audience:** B2B decision makers, IT professionals
**Primary Persona:** CTOs and engineering managers at mid-size companies

**Value Proposition:**
Seamlessly sync your files across all devices with military-grade encryption

**Key Features:**
- End-to-end encryption
- 10TB storage
- Real-time collaboration
- 99.99% uptime SLA

**Special Offer:** 50% off for first 100 customers

---

## LinkedIn Post Variations

### Variation A (Professional - Feature Focus)

Introducing CloudSync Pro 🚀

Your data deserves military-grade protection. CloudSync Pro delivers enterprise-level file synchronization with end-to-end encryption, 10TB storage, and 99.99% uptime SLA.

Built for teams that take security seriously:
✅ End-to-end encryption
✅ Real-time collaboration
✅ 10TB storage included
✅ 99.99% uptime guarantee

🎯 Early Access Special: 50% off for first 100 customers

Ready to elevate your team's productivity while keeping data secure?

👉 Get early access: https://company.com/cloudsync-launch

#CloudSyncPro #CloudStorage #DataSecurity #B2BSaaS #SecureCloud

---

### Variation B (Professional - Pain Point Focus)

Tired of choosing between convenience and security? 🔐

CloudSync Pro solves the file sync dilemma. Collaborate seamlessly across all devices without compromising on data protection.

What makes us different:
• Military-grade end-to-end encryption
• 10TB storage (no more "delete old files" alerts)
• Real-time collaboration for distributed teams
• 99.99% uptime SLA you can trust

Launching February 15 - Early bird special: 50% off for first 100 signups

Join forward-thinking CTOs who prioritize both security and productivity.

Get early access → https://company.com/cloudsync-launch

#CloudSyncPro #DataSecurity #CloudStorage #B2BSaaS #SecureCloud

---

### Variation C (Professional - Social Proof Focus)

After 2 years of development and beta testing with 50+ enterprise teams, CloudSync Pro is ready. 🎉

The feedback? "Finally, a cloud sync solution that doesn't force us to compromise on security."

Why teams love CloudSync Pro:
- End-to-end encryption (your data, your keys)
- 10TB storage per team
- Real-time collaboration without lag
- 99.99% uptime (backed by SLA)

Launching February 15. Early access: 50% off for first 100 customers.

See why CTOs at mid-size companies are making the switch.

👉 https://company.com/cloudsync-launch

#CloudSyncPro #SecureCloud #CloudStorage #DataSecurity #B2BSaaS

---

## Twitter/X Post Variations

### Variation A (280 chars - Feature Focus)

Introducing CloudSync Pro 🚀

✅ Military-grade encryption
✅ 10TB storage
✅ Real-time collaboration
✅ 99.99% uptime

Launch special: 50% off for first 100!

Get early access 👉 company.com/cloudsync-launch

#CloudSyncPro #DataSecurity #CloudStorage

---

### Variation B (280 chars - Pain Point Focus)

Stop choosing between convenience & security 🔐

CloudSync Pro = seamless sync + military-grade encryption + 10TB storage

Launching Feb 15. Early bird: 50% off (first 100)

Join the waitlist → company.com/cloudsync-launch

#CloudSyncPro #SecureCloud

---

### Variation C (280 chars - Urgency Focus)

⚡ CloudSync Pro launches Feb 15

First 100 customers get 50% OFF
- End-to-end encryption
- 10TB storage
- 99.99% uptime SLA

Secure your spot now 👉 company.com/cloudsync-launch

#CloudSyncPro #DataSecurity

---

## Facebook Post Variations

### Variation A (Conversational - Storytelling)

We've been working on something special. 🚀

For the past 2 years, our team has been building CloudSync Pro - the file sync solution we wish existed when we were struggling with the "convenience vs. security" dilemma.

Here's what we built:
🔐 Military-grade end-to-end encryption
📦 10TB storage (yes, really)
⚡ Real-time collaboration
✅ 99.99% uptime SLA

Launching February 15, and we're celebrating with a special offer: 50% off for our first 100 customers.

If you're a CTO, engineering manager, or IT professional tired of compromising on security for the sake of convenience, this is for you.

Get early access here: https://company.com/cloudsync-launch

#CloudSyncPro #CloudStorage #DataSecurity

---

### Variation B (Conversational - Community Focus)

Big news for our community! 🎉

CloudSync Pro is launching February 15, and we couldn't be more excited.

After months of beta testing with amazing teams, we're ready to share what we've built:
- End-to-end encryption (because your data deserves protection)
- 10TB storage (no more "storage almost full" nightmares)
- Real-time collaboration (work together, stay secure)
- 99.99% uptime SLA (we've got your back)

To celebrate, we're offering 50% off for our first 100 customers.

Ready to experience cloud sync that doesn't compromise on security?

👉 Get early access: https://company.com/cloudsync-launch

Join the CloudSync Pro community!

#CloudSyncPro #SecureCloud #CloudStorage

---

### Variation C (Conversational - Value Focus)

Let's talk about cloud storage. 💭

Most solutions force you to choose: convenience OR security. Not both.

That's why we built CloudSync Pro.

Here's what you get:
✨ Seamless sync across all devices
🔐 Military-grade encryption (end-to-end)
📦 10TB storage included
👥 Real-time team collaboration
⏰ 99.99% uptime guarantee

Perfect for teams that refuse to compromise on data security.

Launching February 15 with a special offer: 50% off for first 100 customers.

Are you in?

Get early access → https://company.com/cloudsync-launch

#CloudSyncPro #CloudStorage #DataSecurity #B2BSaaS

---

## A/B Testing Strategy

**Test Variables:**
- **Headline Style:** Feature focus vs. Pain point vs. Social proof
- **CTA Text:** "Get early access" vs. "Join the waitlist" vs. "Secure your spot"
- **Emoji Usage:** Minimal (1-2) vs. Moderate (3-5) vs. Strategic (key points only)

**Recommended Distribution:**
- LinkedIn: Equal split across 3 variations (33% each)
- Twitter: Equal split across 3 variations (33% each)
- Facebook: Equal split across 3 variations (33% each)

**Success Metrics to Track:**
- Click-through rate (CTR) on CTA link
- Engagement rate (likes, comments, shares)
- Conversion rate (sign-ups from traffic)
- Cost per acquisition (if using paid promotion)

**Minimum Test Duration:** 7 days or 1,000 impressions per variation

---

## Platform-Specific Optimization

### LinkedIn
- **Character Count:** 1,200-1,800 (optimal for engagement)
- **Hashtags:** 3-5 relevant hashtags
- **Posting Time:** Tuesday-Thursday, 7-9 AM or 12-1 PM (timezone adjusted)
- **Format:** Professional tone, bullet points, clear value proposition
- **Visual:** Recommended - product screenshot or infographic

### Twitter/X
- **Character Count:** 240-280 (use full space)
- **Hashtags:** 1-3 hashtags max
- **Posting Time:** Monday-Friday, 8-10 AM or 6-9 PM
- **Format:** Concise, punchy, emoji for visual interest
- **Visual:** Recommended - product image or video

### Facebook
- **Character Count:** 400-800 (optimal for engagement)
- **Hashtags:** 1-3 hashtags (less important on Facebook)
- **Posting Time:** Wednesday-Friday, 1-3 PM
- **Format:** Conversational, storytelling, community focus
- **Visual:** Required - engaging image or video

---

## CTA Analysis

**Primary CTA:** Get early access
**URL:** https://company.com/cloudsync-launch
**Type:** Sign-up (pre-launch)
**Urgency:** High (limited spots: first 100 customers)

**CTA Variations:**
1. "Get early access" (neutral, informative)
2. "Join the waitlist" (FOMO, exclusivity)
3. "Secure your spot" (urgency, action-oriented)

**Tracking:**
- Use UTM parameters: `?utm_source={platform}&utm_medium=social&utm_campaign=cloudsync_launch`
- Example: `https://company.com/cloudsync-launch?utm_source=linkedin&utm_medium=social&utm_campaign=cloudsync_launch&utm_content=variation_a`

---

## Hashtag Strategy

**Branded Hashtags:**
- #CloudSyncPro (primary brand hashtag)
- #SecureCloud (product category)

**Industry Hashtags:**
- #CloudStorage (broad category)
- #DataSecurity (key benefit)
- #B2BSaaS (target market)

**Trending Hashtags:** None currently relevant

**Usage Guidelines:**
- LinkedIn: Use all 5 hashtags at end of post
- Twitter: Use 2-3 hashtags integrated into copy
- Facebook: Use 2-3 hashtags, less critical for reach

---

## Compliance & Approval

**Requires Approval:** No (standard product launch)
**Legal Review Required:** No
**Disclaimer Required:** No

**Compliance Checklist:**
- [ ] No unsubstantiated claims
- [ ] Feature descriptions accurate
- [ ] Pricing clearly stated
- [ ] No competitor disparagement
- [ ] Brand guidelines followed

---

## Visual Asset Recommendations

**Required Images:**
1. **Product Hero Shot** (1200x627px for LinkedIn/Facebook)
   - CloudSync Pro dashboard screenshot
   - Highlight key features visually

2. **Twitter Card** (1200x675px)
   - Product logo + tagline
   - Launch date and offer

3. **Alternative Options:**
   - Video demo (15-30 seconds)
   - Infographic (security features comparison)
   - Customer testimonial graphic

**Design Guidelines:**
- Use brand colors
- Include logo
- Clear, readable text overlays
- Mobile-optimized (60% of views are mobile)

---

## Metadata

- **Agent:** lex (Local Executive Agent)
- **Session ID:** session_abc123
- **Campaign Type:** product_launch
- **Product:** CloudSync Pro
- **Launch Date:** 2025-02-15
- **Target Audience:** B2B decision makers, IT professionals
- **Platforms:** LinkedIn, Twitter, Facebook
- **A/B Testing:** Enabled (3 variations per platform)
- **Total Variations:** 9 posts (3 per platform)

---

## Next Steps

### Immediate Actions (Before Posting)

- [ ] Review all 9 variations for brand voice consistency
- [ ] Verify CTA URL is live and tracking properly
- [ ] Prepare visual assets (3 images)
- [ ] Schedule posts across platforms (use tool like Hootsuite/Buffer)
- [ ] Set up UTM tracking for each variation
- [ ] Notify sales team of launch timing

### During Campaign (Feb 15-22)

- [ ] Monitor engagement metrics daily
- [ ] Respond to comments within 2 hours
- [ ] Track click-through rates by variation
- [ ] Adjust budget allocation to winning variations (if using paid)
- [ ] Share user-generated content

### Post-Campaign (After Feb 22)

- [ ] Analyze A/B test results
- [ ] Document winning variations
- [ ] Calculate ROI and cost per acquisition
- [ ] Create follow-up campaign for non-converters
- [ ] Share learnings with marketing team

---

## Approval Workflow

**Status:** Draft
**Review Required:** No (standard product launch)

If approval is required:
1. Update YAML frontmatter: `requires_approval: true`
2. Assign reviewer: `reviewer: marketing_manager@company.com`
3. Set approval deadline: `approval_deadline: 2025-02-10T00:00:00Z`

---

## Audit Trail

- **Draft ID:** SOCIAL-20250204-143022-ABC123
- **Created By:** lex
- **Created At:** 2025-02-04T14:30:22Z
- **Session ID:** session_abc123
- **Skill Version:** social_post_generator v1.0.0

---

**Generated by Social Post Generator Skill v1.0.0**
```

---

## Key Guarantees

1. **Platform Optimization**: Posts tailored to character limits and best practices for each platform
2. **A/B Testing**: Multiple variations with different angles for testing
3. **CTA Integration**: Clear calls-to-action with tracking capabilities
4. **Hashtag Strategy**: Platform-appropriate hashtag selection and placement
5. **Audience Targeting**: Tone and messaging aligned with target persona
6. **Brand Consistency**: Maintains brand voice across all variations
7. **Compliance Ready**: Built-in compliance checklist and approval workflow
8. **Actionable Metadata**: Complete tracking and next steps

---

## Output Schema

**Social Post File:**
- **Location:** `Social_Posts/`
- **Naming:** `YYYYMMDD-HHMMSS-<campaign-type>-<brief-slug>.md`
- **Format:** Markdown with YAML frontmatter

**Frontmatter Fields:**
```yaml
draft_id: "SOCIAL-YYYYMMDD-HHMMSS-HASH"
created_at: "ISO8601 timestamp"
status: "draft | approved | scheduled | posted"
campaign_type: "product_launch | content_promotion | thought_leadership | etc"
platforms: ["linkedin", "twitter", "facebook"]
tone: "professional | casual | enthusiastic | informative"
ab_testing_enabled: true | false
variations_count: 3
requires_approval: true | false
approved_by: null
approved_at: null
scheduled_date: null
posted_at: null
```

---

## Supported Campaign Types

| Campaign Type | Use Case | Best Platform |
|---------------|----------|---------------|
| `product_launch` | New product announcements | LinkedIn, Twitter |
| `content_promotion` | Blog, video, podcast shares | LinkedIn, Facebook |
| `thought_leadership` | Industry insights, opinions | LinkedIn |
| `company_news` | Milestones, awards, partnerships | All platforms |
| `event_promotion` | Webinars, conferences | LinkedIn, Facebook |
| `engagement` | Polls, questions, discussions | Twitter, LinkedIn |
| `testimonial` | Customer success stories | LinkedIn, Facebook |
| `brand_awareness` | Visibility campaigns | All platforms |
| `lead_generation` | Landing page promotions | LinkedIn |

---

## Integration Points

**Upstream Skills:**
- `company_handbook_enforcer` → Validates brand guidelines compliance
- `approval_request_creator` → Creates approval requests for sensitive campaigns

**Downstream Skills:**
- `vault_state_manager` → Stores post drafts and tracks status
- `dashboard_writer` → Displays campaign metrics

**External Tools:**
- Social media scheduling tools (Hootsuite, Buffer, etc.)
- Analytics platforms (Google Analytics, social platform insights)

---

## Error Handling

**Common Errors:**

1. **Character Limit Exceeded:**
   ```
   Error: Twitter post exceeds 280 character limit (current: 315)
   Solution: Use shorter variation or split into thread
   ```

2. **Missing CTA URL:**
   ```
   Error: CTA specified but URL is missing
   Solution: Provide valid CTA URL or remove CTA
   ```

3. **Invalid Platform:**
   ```
   Error: Platform 'instagram' not supported
   Solution: Use supported platforms: linkedin, twitter, facebook
   ```

4. **Too Many Hashtags:**
   ```
   Warning: Twitter post has 5 hashtags (recommended max: 3)
   Solution: Reduce hashtag count for better engagement
   ```

---

## Configuration Examples

### Minimal Configuration:
```bash
VAULT_PATH="/path/to/vault"
SOCIAL_BRAND_NAME="Acme Corp"
SOCIAL_BRAND_VOICE="professional"
```

### With Brand Customization:
```bash
VAULT_PATH="/path/to/vault"
SOCIAL_BRAND_NAME="Acme Corp"
SOCIAL_BRAND_VOICE="conversational"
SOCIAL_TARGET_AUDIENCE="Small business owners"
SOCIAL_DEFAULT_PLATFORMS="linkedin,twitter"
SOCIAL_INCLUDE_EMOJI="true"
SOCIAL_BRANDED_HASHTAGS="#AcmeCorp,#AcmeSolutions"
```

### Production Setup:
```bash
VAULT_PATH="/path/to/vault"
SOCIAL_BRAND_NAME="Acme Corp"
SOCIAL_BRAND_VOICE="professional"
SOCIAL_TARGET_AUDIENCE="B2B decision makers"
SOCIAL_REQUIRE_APPROVAL="true"
SOCIAL_AB_VARIATIONS_COUNT="3"
SOCIAL_AUDIT_LOG_PATH="$VAULT_PATH/Audit_Logs"
SOCIAL_AUTO_HASHTAGS="true"
```

---

## Testing Checklist

Before deploying this skill:

- [ ] Verify `Social_Posts/` folder exists and is writable
- [ ] Test post generation for all platforms
- [ ] Verify character limits are enforced
- [ ] Test A/B variation generation
- [ ] Verify hashtag generation and limits
- [ ] Test CTA integration and URL validation
- [ ] Verify tone adaptation across audiences
- [ ] Test with different campaign types
- [ ] Verify compliance checklist inclusion
- [ ] Test audit log entries created

---

## Version History

- **v1.0.0** (2025-02-04): Initial release
  - Support for LinkedIn, Twitter/X, Facebook
  - A/B testing with multiple variations
  - CTA integration with tracking
  - Hashtag strategy per platform
  - Tone adaptation
  - Compliance workflow
  - Platform-specific optimization
