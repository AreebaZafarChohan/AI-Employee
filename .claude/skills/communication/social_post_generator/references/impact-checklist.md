# Social Post Generator - Impact Checklist

Pre-deployment checklist for assessing the impact of the social_post_generator skill.

---

## Pre-Deployment Checklist

### Environment Setup

- [ ] **Vault Path Configured**
  ```bash
  echo $VAULT_PATH
  # Expected: /absolute/path/to/vault
  ```

- [ ] **Social_Posts Directory Created**
  ```bash
  test -d "$VAULT_PATH/Social_Posts" && echo "✅ Exists" || mkdir -p "$VAULT_PATH/Social_Posts"
  ```

- [ ] **Brand Configuration Set**
  ```bash
  echo $SOCIAL_BRAND_NAME
  echo $SOCIAL_BRAND_VOICE
  echo $SOCIAL_TARGET_AUDIENCE
  ```

---

### Functional Testing

- [ ] **Test LinkedIn Post Generation**
  ```javascript
  await generateSocialPost({
    campaign_type: "product_launch",
    platforms: ["linkedin"],
    content: { product_name: "Test Product" },
    tone: "professional"
  });
  ```

- [ ] **Test Twitter Post Generation (280 char limit)**
  ```javascript
  await generateSocialPost({
    campaign_type: "product_launch",
    platforms: ["twitter"],
    content: { product_name: "Test" }
  });
  // Verify output <= 280 chars
  ```

- [ ] **Test Facebook Post Generation**
  ```javascript
  await generateSocialPost({
    campaign_type: "company_news",
    platforms: ["facebook"],
    tone: "conversational"
  });
  ```

- [ ] **Test Multi-Platform Campaign**
  ```javascript
  await generateSocialPost({
    platforms: ["linkedin", "twitter", "facebook"]
  });
  // Verify 3 platform-specific versions generated
  ```

- [ ] **Test A/B Variation Generation**
  ```javascript
  await generateSocialPost({
    ab_testing: { enabled: true, variations_count: 3 }
  });
  // Verify 3 variations per platform
  ```

---

### Output Validation

- [ ] **YAML Frontmatter Present**
  ```bash
  head -n 20 "$VAULT_PATH/Social_Posts/"*.md | grep "draft_id:"
  ```

- [ ] **Platform-Specific Character Limits Enforced**
  - LinkedIn: Max 3,000 chars
  - Twitter: Max 280 chars
  - Facebook: Optimal 400-800 chars

- [ ] **Hashtags Within Limits**
  - LinkedIn: 3-5 hashtags
  - Twitter: 1-3 hashtags
  - Facebook: 1-3 hashtags

- [ ] **CTA Present and Trackable**
  ```bash
  grep -r "utm_source" "$VAULT_PATH/Social_Posts/"
  # Should find UTM parameters in URLs
  ```

- [ ] **A/B Variations Are Different**
  - Verify variations test different approaches
  - Check variations are meaningfully different (>30% word change)

---

### Security & Compliance

- [ ] **No Sensitive Data in Posts**
  ```bash
  grep -ri "password\|api_key\|secret" "$VAULT_PATH/Social_Posts/"
  # Expected: No matches
  ```

- [ ] **Competitor Mention Detection Working**
  ```bash
  export SOCIAL_FLAG_COMPETITOR_MENTIONS="true"
  export SOCIAL_COMPETITORS="CompetitorA,CompetitorB"
  # Test generating post mentioning competitor
  # Should be flagged for review
  ```

- [ ] **URL Validation Working**
  ```javascript
  // Test with invalid URL
  try {
    await generateSocialPost({
      cta: { url: "not-a-url" }
    });
  } catch (error) {
    console.log("✅ Validation working:", error.message);
  }
  ```

---

### Performance Testing

- [ ] **Single Post Generation Time**
  ```javascript
  const start = Date.now();
  await generateSocialPost({ /* config */ });
  const elapsed = Date.now() - start;
  console.log(`✅ Generated in ${elapsed}ms`);
  // Expected: < 3000ms (3 seconds)
  ```

- [ ] **Batch Generation (5 campaigns)**
  ```javascript
  const start = Date.now();
  await Promise.all([...Array(5)].map(() => generateSocialPost({ /* */ })));
  const elapsed = Date.now() - start;
  console.log(`✅ 5 campaigns in ${elapsed}ms`);
  // Expected: < 10000ms (10 seconds)
  ```

---

## Deployment Impact Assessment

### Storage Impact

- [ ] **Estimate Storage Requirements**
  ```bash
  du -sh "$VAULT_PATH/Social_Posts"/*.md | awk '{sum+=$1} END {print sum/NR " KB per post"}'
  ```

- [ ] **Calculate Monthly Storage**
  ```
  Expected posts per month: _______
  Average post size: _______ KB
  Monthly storage: _______ MB
  ```

### Platform-Specific Limits

- [ ] **LinkedIn API Rate Limits** (if posting via API)
  - Individual: 50 posts per day
  - Company page: 100 posts per day

- [ ] **Twitter API Rate Limits** (if posting via API)
  - Standard: 300 posts per 3 hours
  - Elevated: 500 posts per 3 hours

- [ ] **Facebook API Rate Limits** (if posting via API)
  - Page posts: 600 posts per 600 seconds

---

## Operational Readiness

### Monitoring

- [ ] **Post Creation Metrics**
  ```bash
  find "$VAULT_PATH/Social_Posts" -name '*.md' -mtime -1 | wc -l
  # Posts created today
  ```

- [ ] **Campaign Type Distribution**
  ```bash
  grep -r "campaign_type:" "$VAULT_PATH/Social_Posts" | cut -d':' -f3 | sort | uniq -c
  ```

### Success Criteria

Post deployment is successful if:

- [ ] All functional tests pass
- [ ] Character limits enforced correctly
- [ ] A/B variations are meaningfully different
- [ ] Hashtags within platform limits
- [ ] CTAs include tracking parameters
- [ ] No security vulnerabilities detected
- [ ] Generation time < 3 seconds
- [ ] Compliance checks working

---

## Rollback Plan

If issues arise:

### Step 1: Stop Post Generation
```bash
mv .claude/skills/communication/social_post_generator .claude/skills/communication/social_post_generator.disabled
```

### Step 2: Preserve Existing Posts
```bash
cp -r "$VAULT_PATH/Social_Posts" "$VAULT_PATH/Social_Posts.backup.$(date +%Y%m%d)"
```

### Step 3: Document Issues
```bash
echo "Issue: [description]" >> rollback.log
echo "Date: $(date)" >> rollback.log
```

---

## Post-Deployment Monitoring

### Day 1: Initial Validation
- [ ] Review first 5 posts manually
- [ ] Verify platform-specific formatting
- [ ] Check A/B variations quality
- [ ] Confirm hashtag strategy working

### Week 1: Performance Review
- [ ] Analyze engagement rates by platform
- [ ] Review A/B test results
- [ ] Check character limit enforcement
- [ ] Gather user feedback

### Month 1: Optimization
- [ ] Review which variations perform best
- [ ] Optimize hashtag strategy
- [ ] Refine CTA effectiveness
- [ ] Update tone guidelines if needed

---

**Status:** Ready for deployment when all checkboxes are complete! ✅
