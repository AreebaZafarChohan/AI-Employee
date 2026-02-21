# CEO Briefing Writer - Examples

This document provides concrete, real-world examples of using the CEO Briefing Writer skill.

---

## Example 1: Early-Stage Startup (Pre-Seed)

### Context
- Company: TechStart Inc.
- Stage: Pre-seed, 3 months old
- Team: 4 people (2 engineers, 1 designer, 1 founder)
- Runway: 8 months
- Revenue: $0 (pre-revenue)

### Data Sources

**goals/q1-2025.goals.md:**
```yaml
---
id: G1
title: Launch MVP
target: 100
current: 65
status: on_track
owner: Sarah Chen
deadline: 2025-03-15
---

---
id: G2
title: Get 100 beta users
target: 100
current: 23
status: at_risk
owner: Mike Johnson
deadline: 2025-03-31
---

---
id: G3
title: Raise pre-seed round
target: 500000
current: 150000
status: in_progress
owner: Sarah Chen
deadline: 2025-04-30
---
```

**financials/2025-02.json:**
```json
{
  "period": "2025-02",
  "mrr": 0,
  "arr": 0,
  "burn_rate": 25000,
  "cash_balance": 200000,
  "runway_months": 8,
  "expenses": {
    "salaries": 20000,
    "infrastructure": 2000,
    "tools": 3000
  }
}
```

**done/week-2025-02-01.md:**
```markdown
# Completed Tasks - Week of Feb 1, 2025

## TASK-001: User authentication system
- Completed: 2025-02-01
- Impact: High
- Outcome: OAuth integration working, 95% test coverage

## TASK-002: Landing page redesign
- Completed: 2025-02-03
- Impact: Medium
- Outcome: Conversion rate improved from 2% to 5%

## TASK-003: Beta signup flow
- Completed: 2025-02-04
- Impact: High
- Outcome: 15 new beta signups in first 24 hours
```

### Generated Briefing

```markdown
# CEO Briefing - Week of February 1, 2025

**Generated:** 2025-02-05 16:00:00 UTC
**Period:** February 1-7, 2025
**Overall Status:** 🟡 Fair

---

## Executive Summary

- 🚀 **MVP Progress Strong**: 65% complete, on track for March 15 launch
- ⚠️ **Beta User Acquisition Behind**: Only 23/100 users, need acceleration
- 💰 **Fundraising Progressing**: $150K committed of $500K target
- ⏱️ **Runway Adequate**: 8 months remaining, but pre-revenue requires urgency
- ✅ **Key Technical Milestones**: Auth system and landing page completed

---

## Business Health Score: 58/100

| Dimension | Score | Status | Trend |
|-----------|-------|--------|-------|
| Financial Health | 45/100 | 🟡 Fair | ➡️ Stable |
| Operational Health | 72/100 | 🟢 Good | 📈 +8% |
| Team Health | 58/100 | 🟡 Fair | ➡️ Stable |

**Overall Assessment:** Operational execution is strong with MVP on track, but financial pressure from pre-revenue status and runway concerns. Beta user acquisition needs immediate attention.

---

## Goals & Progress

### Strategic Objectives (1/3 on track)

#### 1. Launch MVP
- **Target:** 100%
- **Current:** 65%
- **Status:** 🟢 On track
- **Owner:** Sarah Chen
- **Deadline:** March 15, 2025

#### 2. Get 100 beta users
- **Target:** 100 users
- **Current:** 23 users (23%)
- **Status:** 🔴 At risk
- **Owner:** Mike Johnson
- **Deadline:** March 31, 2025

⚠️ **Risk:** Current pace (23 users in 3 months) projects to only 30 users by deadline
**Action Needed:** Increase marketing efforts, consider paid acquisition

#### 3. Raise pre-seed round
- **Target:** $500,000
- **Current:** $150,000 (30%)
- **Status:** 🟡 In progress
- **Owner:** Sarah Chen
- **Deadline:** April 30, 2025

---

## Financial Performance

### Revenue
- **MRR:** $0 (pre-revenue)
- **ARR:** $0
- **Target:** Launch revenue model post-MVP

### Expenses & Runway
- **Monthly Burn:** $25,000
- **Runway:** 8 months (until October 2025)
- **Cash Balance:** $200,000

⚠️ **Warning:** Pre-revenue with 8 months runway. Fundraising timeline is critical.

### Burn Breakdown
- **Salaries:** $20,000 (80%)
- **Infrastructure:** $2,000 (8%)
- **Tools & Software:** $3,000 (12%)

---

## Operational Highlights

### Completed This Week (3)

1. ✅ **User authentication system**
   - **Impact:** High - Core functionality for MVP
   - **Owner:** Engineering team
   - **Metrics:** OAuth integration, 95% test coverage

2. ✅ **Landing page redesign**
   - **Impact:** Medium - Improved conversion
   - **Owner:** Design team
   - **Metrics:** Conversion rate 2% → 5% (+150%)

3. ✅ **Beta signup flow**
   - **Impact:** High - User acquisition
   - **Owner:** Engineering team
   - **Metrics:** 15 new signups in 24 hours

### Key Operational Metrics

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| MVP Completion | 65% | 100% by Mar 15 | 🟢 |
| Beta Users | 23 | 100 by Mar 31 | 🔴 |
| Weekly Signups | 5 | 10 | 🟡 |

---

## Bottlenecks & Risks

### Critical Issues (2)

#### 🔴 Beta user acquisition significantly behind target

- **Type:** Growth
- **Impact:** Risk of launching MVP without sufficient user feedback
- **Duration:** 3 months (since project start)
- **Affected:** Product development, fundraising narrative
- **Owner:** Mike Johnson
- **Recommendation:** Allocate 50% of founder time to user acquisition; consider paid ads budget of $2K/month

---

#### 🔴 Pre-revenue with limited runway

- **Type:** Financial
- **Impact:** Business continuity at risk if fundraising delayed
- **Duration:** Ongoing
- **Affected:** All operations
- **Owner:** Sarah Chen
- **Recommendation:** Accelerate fundraising timeline; have contingency plan for bridge financing

---

## Strategic Recommendations

### 🔴 Accelerate beta user acquisition immediately

**Category:** Growth
**Priority:** Critical
**Confidence:** High

**Rationale:** Current pace (7-8 users/month) will result in only ~30 users by deadline, far short of 100 target. This impacts product feedback loop and fundraising story.

**Recommended Action:**
1. Allocate 50% of founder time to direct outreach
2. Launch paid acquisition campaign ($2K/month budget)
3. Implement referral program (invite 3 friends → priority access)
4. Partner with 2-3 relevant communities for distribution

**Expected Outcome:** Increase signup rate to 15-20/week, reaching 80-100 users by deadline

**Timeline:** Start immediately, measure weekly

---

### 🟡 Prepare fundraising contingency plan

**Category:** Financial
**Priority:** High
**Confidence:** High

**Rationale:** 8 months runway with pre-revenue status creates urgency. If fundraising takes longer than expected, need backup options.

**Recommended Action:**
1. Identify 2-3 potential bridge financing sources
2. Explore revenue acceleration options (early access pricing)
3. Model reduced burn scenarios (defer hires, reduce infrastructure)
4. Set fundraising milestone checkpoints (March 15, April 1)

**Expected Outcome:** Reduce fundraising risk, extend effective runway to 10-12 months

**Timeline:** Complete contingency plan by February 15

---

### 🟢 Maintain MVP development momentum

**Category:** Operational
**Priority:** Medium
**Confidence:** High

**Rationale:** MVP is 65% complete and on track. Current pace is excellent and should be maintained.

**Recommended Action:**
1. Continue current sprint cadence
2. Protect engineering time from distractions
3. Ensure design assets ready 1 week ahead of development
4. Plan launch activities for March 15 target

**Expected Outcome:** MVP launch on schedule with high quality

**Timeline:** Ongoing through March 15

---

## Week Ahead

### Upcoming Milestones

- **February 10**: Investor pitch to Acme Ventures
  - Status: 🟢 Prepared
  - Owner: Sarah Chen

- **February 12**: Beta user feedback session #1
  - Status: 🟡 Need 10+ users confirmed
  - Owner: Mike Johnson

- **February 15**: MVP feature freeze
  - Status: 🟢 On track
  - Owner: Engineering team

### Decisions Needed

- [ ] **Paid acquisition budget approval**
  - **Context:** Need $2K/month for user acquisition ads
  - **Owner:** Sarah Chen
  - **Deadline:** February 8
  - **Options:** Approve $2K, approve $1K trial, defer

- [ ] **Referral program incentives**
  - **Context:** What to offer users who refer friends
  - **Owner:** Mike Johnson
  - **Deadline:** February 10
  - **Options:** Priority access, swag, future credits

### Focus Areas

- 🎯 **User Acquisition**: Launch paid campaigns and referral program
  - **Owner:** Mike Johnson
  - **Success Criteria:** 15+ new signups this week

- 🎯 **Fundraising**: Close 2 additional commitments
  - **Owner:** Sarah Chen
  - **Success Criteria:** $250K total committed

- 🎯 **MVP Development**: Complete payment integration
  - **Owner:** Engineering team
  - **Success Criteria:** Payment flow tested and working

---

**Next Briefing:** February 12, 2025
```

---

## Example 2: Growth-Stage Startup (Series A)

### Context
- Company: DataFlow Analytics
- Stage: Series A, 2 years old
- Team: 35 people
- Runway: 18 months
- Revenue: $150K MRR, growing 15% MoM

### Configuration

```bash
# Adjusted thresholds for growth stage
export CEO_BRIEFING_RUNWAY_WARNING="12"  # Warn at 12 months
export CEO_BRIEFING_REVENUE_TARGET_MONTHLY="200000"  # $200K target
export CEO_BRIEFING_GOAL_AT_RISK_THRESHOLD="0.75"  # More aggressive
```

### Key Differences from Example 1

**Health Score:**
- Financial Health: 82/100 (strong runway, revenue growth)
- Operational Health: 78/100 (scaling challenges)
- Team Health: 71/100 (hiring needs)

**Bottlenecks:**
- Engineering hiring behind (5/10 hires completed)
- Customer support response time degraded (8h avg vs 4h target)
- Infrastructure scaling issues (2 outages this month)

**Recommendations:**
- Engage recruiting agency for engineering hires
- Hire dedicated customer success manager
- Invest in infrastructure automation (estimated $50K)
- Consider raising Series B in 6 months (from position of strength)

---

## Example 3: Enterprise SaaS Company

### Context
- Company: EnterpriseSoft Inc.
- Stage: Series C, 5 years old
- Team: 200 people
- Runway: 24+ months
- Revenue: $2M MRR, growing 8% MoM

### Briefing Highlights

**Executive Summary:**
- 📈 **Revenue Growth Steady**: $2M MRR (+8% MoM), on track for $30M ARR
- 🎯 **Enterprise Deals Pipeline**: $5M in Q1 pipeline, 3 deals in final stages
- 🏆 **Product Milestones**: Enterprise tier launched, 5 customers migrated
- ⚠️ **Churn Uptick**: 3.2% monthly churn (up from 2.5%), needs investigation
- 💼 **Team Expansion**: 15 new hires this month, 8 open positions

**Strategic Recommendations:**
1. **Investigate churn increase**: Conduct customer interviews, analyze usage data
2. **Accelerate enterprise sales**: Hire 2 additional enterprise AEs
3. **Expand to EMEA**: Open London office in Q2 (market research complete)
4. **Consider Series D**: Strong metrics support raising $50M for international expansion

---

## Example 4: Bootstrapped Company

### Context
- Company: BootstrapCo
- Stage: Bootstrapped, 3 years old
- Team: 8 people
- Runway: N/A (profitable)
- Revenue: $80K MRR, growing 5% MoM

### Configuration

```bash
# Bootstrapped company configuration
export CEO_BRIEFING_RUNWAY_WARNING="0"  # Not applicable
export CEO_BRIEFING_ENABLE_RECOMMENDATIONS="true"
export CEO_BRIEFING_RECOMMENDATION_CONFIDENCE="medium"  # More conservative
```

### Briefing Highlights

**Financial Performance:**
- **MRR:** $80,000 (+5% MoM)
- **Expenses:** $45,000/month
- **Profit:** $35,000/month
- **Cash Balance:** $420,000
- **Runway:** Infinite (profitable)

**Strategic Recommendations:**
1. **Invest in growth**: Allocate $10K/month to marketing (still profitable)
2. **Hire strategically**: Add 1 senior engineer to accelerate product development
3. **Build cash reserves**: Target 12 months operating expenses ($540K)
4. **Consider fundraising**: Strong unit economics support raising capital for faster growth

---

## Example 5: Crisis Mode

### Context
- Company: TurnaroundTech
- Stage: Series A, facing challenges
- Runway: 4 months
- Revenue: Declining
- Recent: Lost major customer, missed revenue targets

### Briefing Highlights

**Overall Status:** 🔴 Critical

**Executive Summary:**
- 🚨 **Runway Critical**: 4 months remaining, immediate action required
- 📉 **Revenue Declined**: $120K MRR (-15% MoM), lost major customer ($30K MRR)
- 🔴 **Burn Rate High**: $180K/month, unsustainable
- ⚠️ **Team Morale**: 3 key employees at risk of leaving
- 🎯 **Turnaround Plan**: Cost reduction + revenue recovery initiatives launched

**Critical Bottlenecks:**
1. **Runway below 6 months**: Business continuity at immediate risk
2. **Revenue declining**: Lost major customer, pipeline weak
3. **Burn rate unsustainable**: Expenses exceed revenue by 50%
4. **Key person risk**: Critical employees considering leaving

**Strategic Recommendations (Crisis Mode):**
1. **Immediate cost reduction**: Cut burn to $100K/month within 2 weeks
   - Defer 3 planned hires
   - Reduce infrastructure costs by 30%
   - Negotiate vendor payment terms

2. **Emergency fundraising**: Raise bridge round ($500K) within 30 days
   - Approach existing investors first
   - Prepare for down round if necessary
   - Have contingency plan for acquisition discussions

3. **Revenue recovery**: Focus on customer retention and quick wins
   - Assign CEO to top 10 customers (prevent further churn)
   - Launch win-back campaign for churned customers
   - Accelerate 3 deals in late-stage pipeline

4. **Team stabilization**: Retain critical employees
   - Have 1-on-1s with key team members
   - Communicate turnaround plan transparently
   - Consider retention bonuses for critical roles

---

## Example 6: Automated Distribution

### Scenario: Automatically send briefing to leadership team

**Script: `generate_and_distribute_briefing.sh`**

```bash
#!/bin/bash

# Generate CEO briefing
echo "Generating CEO briefing..."
/ceo_briefing_writer

# Check if generation successful
if [ $? -ne 0 ]; then
  echo "Error: Briefing generation failed"
  exit 1
fi

# Extract executive summary for Slack
SUMMARY=$(head -n 20 CEO_Briefing.md | tail -n 10)

# Post to Slack
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d "{
    \"channel\": \"#leadership\",
    \"text\": \"📊 Weekly CEO Briefing Generated\",
    \"attachments\": [{
      \"text\": \"$SUMMARY\",
      \"color\": \"good\"
    }]
  }"

# Email full briefing to leadership team
/email_drafter \
  --template executive_update \
  --recipients "ceo@company.com,cfo@company.com,cto@company.com" \
  --subject "CEO Briefing - Week of $(date +%Y-%m-%d)" \
  --attach CEO_Briefing.md

echo "Briefing distributed successfully"
```

**Cron job:**
```bash
# Every Friday at 4 PM
0 16 * * 5 /path/to/generate_and_distribute_briefing.sh
```

---

## Example 7: Custom Recommendation Rules

### Scenario: Add company-specific recommendation logic

**Configuration:**

```javascript
// custom_recommendations.js
module.exports = {
  rules: [
    {
      name: "accelerate_hiring",
      condition: (data) => {
        return data.open_positions > 5 &&
               data.time_to_hire_avg > 60 &&
               data.runway_months > 12;
      },
      recommendation: {
        title: "Engage recruiting agency to accelerate hiring",
        category: "operational",
        priority: "high",
        rationale: "5+ open positions with 60+ day time-to-hire is slowing growth",
        action: "Engage specialized recruiting agency, budget $20K/month",
        expected_outcome: "Reduce time-to-hire to 30 days, fill positions 2x faster"
      }
    },
    {
      name: "expand_internationally",
      condition: (data) => {
        return data.arr > 10000000 &&
               data.international_revenue_percent < 20 &&
               data.runway_months > 18;
      },
      recommendation: {
        title: "Consider international expansion",
        category: "strategic",
        priority: "medium",
        rationale: "$10M+ ARR with <20% international revenue indicates opportunity",
        action: "Conduct market research for EMEA/APAC, hire international sales lead",
        expected_outcome: "Increase TAM by 3x, diversify revenue sources"
      }
    }
  ]
};
```

---

## Example 8: Multi-Period Comparison

### Scenario: Compare current week to multiple previous periods

**Command:**
```bash
/ceo_briefing_writer \
  --compare-to "last_week,last_month,last_quarter" \
  --include-trend-charts
```

**Output includes:**

```markdown
## Revenue Trends

| Period | MRR | Change | Trend |
|--------|-----|--------|-------|
| This Week | $150K | - | - |
| Last Week | $145K | +3.4% | 📈 |
| Last Month | $130K | +15.4% | 📈 |
| Last Quarter | $100K | +50.0% | 📈 |

**Analysis:** Strong consistent growth across all time periods. MRR increased 50% over last quarter, indicating healthy business momentum.
```

---

## Tips for Effective Briefings

### 1. Keep Data Sources Updated
```bash
# Daily: Update completed tasks
cp tasks/completed/* done/

# Weekly: Update goals progress
./scripts/update_goals_progress.sh

# Monthly: Update financials
./scripts/export_financials.sh > financials/$(date +%Y-%m).json
```

### 2. Calibrate Thresholds
Start conservative, adjust based on feedback:
```bash
# Week 1: Default thresholds
# Week 2-4: Observe false positives/negatives
# Week 5: Adjust thresholds
# Week 6+: Fine-tune based on executive feedback
```

### 3. Review Recommendations
Have human review high-impact recommendations before acting:
```bash
# Flag recommendations requiring approval
export CEO_BRIEFING_RECOMMENDATION_REVIEW_REQUIRED="financial,strategic"
```

### 4. Archive Management
Keep historical briefings organized:
```bash
# Archive structure
archive/briefings/
  2025/
    Q1/
      CEO_Briefing-2025-01-06.md
      CEO_Briefing-2025-01-13.md
      ...
```

---

## Common Patterns

### Pattern: Pre-Meeting Briefing
Generate briefing before weekly leadership meeting:
```bash
# Monday morning, before 9 AM meeting
0 8 * * 1 /path/to/generate_briefing.sh
```

### Pattern: Investor Update
Generate monthly briefing for investors:
```bash
# First day of each month
export CEO_BRIEFING_PERIOD="monthly"
export CEO_BRIEFING_ENABLE_RECOMMENDATIONS="false"  # Internal only
/ceo_briefing_writer --format investor_update
```

### Pattern: Board Meeting Prep
Generate comprehensive quarterly briefing:
```bash
# Week before board meeting
export CEO_BRIEFING_PERIOD="quarterly"
export CEO_BRIEFING_INCLUDE_DETAILED_FINANCIALS="true"
/ceo_briefing_writer --format board_presentation
```

---

These examples demonstrate the flexibility and power of the CEO Briefing Writer skill across different company stages, situations, and use cases.
