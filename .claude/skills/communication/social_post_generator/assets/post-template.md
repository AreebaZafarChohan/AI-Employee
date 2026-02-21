---
draft_id: "{{DRAFT_ID}}"
created_at: "{{CREATED_AT}}"
status: "{{STATUS}}"
campaign_type: "{{CAMPAIGN_TYPE}}"
platforms: {{PLATFORMS_ARRAY}}
tone: "{{TONE}}"
ab_testing_enabled: {{AB_TESTING_ENABLED}}
variations_count: {{VARIATIONS_COUNT}}
requires_approval: {{REQUIRES_APPROVAL}}
approved_by: null
approved_at: null
scheduled_date: null
posted_at: null
---

# Social Post Draft: {{CAMPAIGN_TITLE}}

**Draft ID:** {{DRAFT_ID}}
**Created:** {{CREATED_AT}}
**Status:** {{STATUS_EMOJI}} {{STATUS}}
**Campaign Type:** {{CAMPAIGN_TYPE}}

---

## Campaign Overview

{{CAMPAIGN_OVERVIEW}}

**Target Audience:** {{TARGET_AUDIENCE}}
**Platforms:** {{PLATFORMS_LIST}}
**Tone:** {{TONE}}

---

{{#each PLATFORMS}}
## {{PLATFORM_NAME}} Post Variations

{{#each VARIATIONS}}
### Variation {{VARIATION_ID}} ({{VARIATION_STYLE}})

{{VARIATION_CONTENT}}

**Character Count:** {{CHAR_COUNT}} / {{PLATFORM_MAX}}
**Hashtags:** {{HASHTAG_COUNT}}
**CTA:** {{CTA_TEXT}}

---

{{/each}}
{{/each}}

## A/B Testing Strategy

**Test Variables:**
{{#each TEST_VARIABLES}}
- {{this}}
{{/each}}

**Recommended Distribution:**
{{#each PLATFORMS}}
- {{this}}: Equal split across {{VARIATIONS_COUNT}} variations
{{/each}}

**Success Metrics to Track:**
- Click-through rate (CTR) on CTA link
- Engagement rate (likes, comments, shares)
- Conversion rate (actions from traffic)
- Cost per acquisition (if using paid promotion)

**Minimum Test Duration:** {{TEST_DURATION}} days or {{MINIMUM_IMPRESSIONS}} impressions per variation

---

## Platform-Specific Optimization

{{#each PLATFORMS}}
### {{PLATFORM_NAME}}
- **Character Count:** {{OPTIMAL_LENGTH}}
- **Hashtags:** {{HASHTAG_RANGE}}
- **Posting Time:** {{BEST_TIMES}}
- **Format:** {{FORMAT_STYLE}}
{{#if VISUAL_REQUIRED}}
- **Visual:** {{VISUAL_TYPE}} ({{VISUAL_DIMENSIONS}})
{{/if}}

{{/each}}

---

## CTA Analysis

**Primary CTA:** {{CTA_TEXT}}
**URL:** {{CTA_URL}}
**Type:** {{CTA_TYPE}}
**Urgency:** {{URGENCY_LEVEL}}

**CTA Variations:**
{{#each CTA_VARIATIONS}}
{{INDEX}}. "{{this.text}}" ({{this.style}})
{{/each}}

**Tracking:**
- Use UTM parameters: `?utm_source={{PLATFORM}}&utm_medium=social&utm_campaign={{CAMPAIGN_ID}}`
- Example: `{{CTA_URL}}?utm_source={{PLATFORM}}&utm_medium=social&utm_campaign={{CAMPAIGN_ID}}&utm_content={{VARIATION_ID}}`

---

## Hashtag Strategy

**Branded Hashtags:**
{{#each BRANDED_HASHTAGS}}
- {{this}}
{{/each}}

**Industry Hashtags:**
{{#each INDUSTRY_HASHTAGS}}
- {{this}}
{{/each}}

{{#if TRENDING_HASHTAGS}}
**Trending Hashtags:**
{{#each TRENDING_HASHTAGS}}
- {{this}}
{{/each}}
{{/if}}

**Usage Guidelines:**
- LinkedIn: Use all {{LINKEDIN_HASHTAG_COUNT}} hashtags at end of post
- Twitter: Use {{TWITTER_HASHTAG_COUNT}} hashtags integrated into copy
- Facebook: Use {{FACEBOOK_HASHTAG_COUNT}} hashtags

---

## Compliance & Approval

**Requires Approval:** {{REQUIRES_APPROVAL}}
{{#if COMPLIANCE_ISSUES}}
**Compliance Issues:**
{{#each COMPLIANCE_ISSUES}}
- {{this.policy}}: {{this.issue}}
{{/each}}
{{/if}}

**Compliance Checklist:**
- [ ] No unsubstantiated claims
- [ ] Feature descriptions accurate
- [ ] No competitor disparagement
- [ ] Brand guidelines followed
- [ ] Legal disclaimer added (if required)
- [ ] Sensitive topics flagged

---

## Visual Asset Recommendations

**Required Images:**
{{#each VISUAL_ASSETS}}
{{INDEX}}. **{{this.name}}** ({{this.dimensions}})
   - {{this.description}}
{{/each}}

**Design Guidelines:**
- Use brand colors
- Include logo
- Clear, readable text overlays
- Mobile-optimized (60% of views are mobile)

---

## Metadata

- **Agent:** {{AGENT_NAME}}
- **Session ID:** {{SESSION_ID}}
- **Campaign Type:** {{CAMPAIGN_TYPE}}
{{#if PRODUCT_NAME}}
- **Product:** {{PRODUCT_NAME}}
{{/if}}
{{#if LAUNCH_DATE}}
- **Launch Date:** {{LAUNCH_DATE}}
{{/if}}
- **Target Audience:** {{TARGET_AUDIENCE}}
- **Platforms:** {{PLATFORMS_LIST}}
- **A/B Testing:** {{AB_TESTING_STATUS}}
- **Total Variations:** {{TOTAL_VARIATIONS}}

---

## Next Steps

### Immediate Actions (Before Posting)

- [ ] Review all {{TOTAL_VARIATIONS}} variations for brand voice consistency
- [ ] Verify CTA URL is live and tracking properly
- [ ] Prepare visual assets ({{VISUAL_ASSET_COUNT}} images/videos)
- [ ] Schedule posts across platforms (use tool like Hootsuite/Buffer)
- [ ] Set up UTM tracking for each variation
{{#if STAKEHOLDER_NOTIFY}}
- [ ] Notify {{STAKEHOLDER_LIST}} of campaign timing
{{/if}}

### During Campaign

- [ ] Monitor engagement metrics daily
- [ ] Respond to comments within 2 hours
- [ ] Track click-through rates by variation
- [ ] Adjust budget allocation to winning variations (if using paid)
- [ ] Share user-generated content

### Post-Campaign

- [ ] Analyze A/B test results
- [ ] Document winning variations
- [ ] Calculate ROI and cost per acquisition
- [ ] Create follow-up campaign for non-converters
- [ ] Share learnings with team

---

## Approval Workflow

**Status:** {{STATUS}}
**Review Required:** {{REQUIRES_APPROVAL}}

{{#if REQUIRES_APPROVAL}}
### Approval Instructions

**To Approve:**
1. Update the YAML frontmatter:
   ```yaml
   status: approved
   approved_by: "Your Name <your.email@company.com>"
   approved_at: "{{CURRENT_TIMESTAMP}}"
   ```
2. (Optional) Add approval notes below
3. Save the file

**To Reject:**
1. Update the YAML frontmatter:
   ```yaml
   status: rejected
   rejected_by: "Your Name <your.email@company.com>"
   rejected_at: "{{CURRENT_TIMESTAMP}}"
   rejection_reason: "Your reason here"
   ```
2. Save the file

---

## Approval Notes

<!-- Approver: Add your notes here -->
{{/if}}

---

## Audit Trail

- **Draft ID:** {{DRAFT_ID}}
- **Created By:** {{AGENT_NAME}}
- **Created At:** {{CREATED_AT}}
- **Session ID:** {{SESSION_ID}}
- **Skill Version:** social_post_generator v{{SKILL_VERSION}}

{{#if AUDIT_LOG_ID}}
- **Audit Log ID:** {{AUDIT_LOG_ID}}
- **Audit Log Path:** {{AUDIT_LOG_PATH}}
{{/if}}

---

**Generated by Social Post Generator Skill v{{SKILL_VERSION}}**
