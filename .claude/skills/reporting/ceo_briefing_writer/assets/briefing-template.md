# CEO Briefing - Week of {{WEEK_START_DATE}}

**Generated:** {{GENERATION_TIMESTAMP}}
**Period:** {{PERIOD_START}} to {{PERIOD_END}}
**Overall Status:** {{STATUS_EMOJI}} {{STATUS_TEXT}}

---

## Executive Summary

{{#each executive_highlights}}
- {{emoji}} **{{title}}**: {{description}}
{{/each}}

---

## Business Health Score: {{OVERALL_HEALTH_SCORE}}/100

| Dimension | Score | Status | Trend |
|-----------|-------|--------|-------|
| Financial Health | {{financial_health_score}}/100 | {{financial_status_emoji}} {{financial_status}} | {{financial_trend_emoji}} {{financial_trend}} |
| Operational Health | {{operational_health_score}}/100 | {{operational_status_emoji}} {{operational_status}} | {{operational_trend_emoji}} {{operational_trend}} |
| Team Health | {{team_health_score}}/100 | {{team_status_emoji}} {{team_status}} | {{team_trend_emoji}} {{team_trend}} |

**Overall Assessment:** {{overall_health_assessment}}

---

## Goals & Progress

### Strategic Objectives ({{goals_on_track_count}}/{{total_goals_count}} on track)

{{#each goals}}
#### {{goal_number}}. {{goal_title}}

- **Target:** {{target_value}}
- **Current:** {{current_value}} ({{progress_percentage}}%)
- **Status:** {{status_emoji}} {{status_text}}
- **Owner:** {{owner_name}}
- **Deadline:** {{deadline_date}}

{{#if is_at_risk}}
⚠️ **Risk:** {{risk_description}}
**Action Needed:** {{required_action}}
{{/if}}

{{#if is_blocked}}
🔴 **Blocked:** {{blocker_description}}
**Blocked Since:** {{blocked_since_date}}
{{/if}}

---
{{/each}}

### At-Risk Goals ({{at_risk_goals_count}})

{{#if has_at_risk_goals}}
{{#each at_risk_goals}}
- 🔴 **{{title}}**: {{progress_percentage}}% complete, {{days_remaining}} days remaining
  - **Gap:** {{gap_description}}
  - **Action:** {{recommended_action}}
  - **Owner:** {{owner_name}}
{{/each}}
{{else}}
✅ All goals are on track or ahead of schedule.
{{/if}}

---

## Financial Performance

### Revenue

- **MRR:** {{mrr_currency}}{{mrr_value}} ({{mrr_trend_emoji}} {{mrr_change_percentage}}% vs {{comparison_period}})
- **ARR:** {{arr_currency}}{{arr_value}}
- **Growth Rate:** {{growth_rate_percentage}}% MoM
- **Target:** {{revenue_target_currency}}{{revenue_target}} ({{percent_to_target}}% achieved)

{{#if revenue_milestone}}
🎯 **Milestone:** {{revenue_milestone_description}}
{{/if}}

### Expenses & Runway

- **Monthly Burn:** {{burn_currency}}{{burn_rate}}
- **Runway:** {{runway_months}} months ({{runway_end_date}})
- **Cash Balance:** {{cash_currency}}{{cash_balance}}

{{#if runway_warning}}
⚠️ **Warning:** Runway below {{runway_warning_threshold}} months. {{runway_warning_message}}
{{/if}}

### Unit Economics

- **CAC:** {{cac_currency}}{{cac_value}}
- **LTV:** {{ltv_currency}}{{ltv_value}}
- **LTV:CAC Ratio:** {{ltv_cac_ratio}}:1 (target: >3:1) {{ltv_cac_status_emoji}}
- **Magic Number:** {{magic_number}} (target: >0.75) {{magic_number_status_emoji}}
- **Payback Period:** {{payback_months}} months

{{#if unit_economics_note}}
📊 **Note:** {{unit_economics_note}}
{{/if}}

---

## Operational Highlights

### Completed This Week ({{tasks_completed_count}})

{{#each top_accomplishments}}
{{accomplishment_number}}. ✅ **{{title}}**
   - **Impact:** {{impact_description}}
   - **Owner:** {{owner_name}}
   {{#if metrics}}
   - **Metrics:** {{metrics_description}}
   {{/if}}
{{/each}}

{{#if has_more_tasks}}
[See all {{total_tasks_completed}} completed tasks →]({{all_tasks_link}})
{{/if}}

### Key Operational Metrics

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Deployments | {{deployments_count}} | {{deployments_target}} | {{deployments_status_emoji}} |
| Deployment Success Rate | {{deployment_success_rate}}% | {{deployment_success_target}}% | {{deployment_success_status_emoji}} |
| Features Shipped | {{features_shipped_count}} | {{features_target}} | {{features_status_emoji}} |
| Bugs Fixed | {{bugs_fixed_count}} | - | {{bugs_fixed_status_emoji}} |
| Customer Issues Resolved | {{issues_resolved_count}} | {{issues_target}} | {{issues_status_emoji}} |
| Avg Response Time | {{avg_response_time}} hours | {{response_time_target}} hours | {{response_time_status_emoji}} |

---

## Bottlenecks & Risks

{{#if has_bottlenecks}}

### Critical Issues ({{critical_bottlenecks_count}})

{{#each critical_bottlenecks}}
#### {{severity_emoji}} {{title}}

- **Type:** {{bottleneck_type}}
- **Impact:** {{impact_description}}
- **Duration:** {{duration_description}}
- **Affected:** {{affected_areas}}
- **Owner:** {{owner_name}}
- **Recommendation:** {{recommendation}}

---
{{/each}}

### High Priority ({{high_priority_bottlenecks_count}})

{{#each high_priority_bottlenecks}}
- ⚠️ **{{title}}**: {{impact_description}}
  - **Action:** {{recommended_action}}
  - **Owner:** {{owner_name}}
{{/each}}

### Medium Priority ({{medium_priority_bottlenecks_count}})

{{#each medium_priority_bottlenecks}}
- 🟡 **{{title}}**: {{brief_description}}
{{/each}}

{{else}}

✅ **No critical bottlenecks identified this week.**

All systems operating normally. Continue monitoring key metrics.

{{/if}}

---

## Strategic Recommendations

{{#if has_recommendations}}

{{#each recommendations}}
### {{priority_emoji}} {{recommendation_title}}

**Category:** {{category}}
**Priority:** {{priority_level}}
**Confidence:** {{confidence_level}}

**Rationale:** {{rationale_description}}

**Recommended Action:** {{action_description}}

**Expected Outcome:** {{expected_outcome}}

**Timeline:** {{recommended_timeline}}

{{#if requires_resources}}
**Resources Required:** {{resources_description}}
{{/if}}

{{#if risks}}
**Risks:** {{risks_description}}
{{/if}}

---
{{/each}}

{{else}}

✅ **No new strategic recommendations this week.**

Current strategy is on track. Continue execution as planned.

{{/if}}

---

## Week Ahead

### Upcoming Milestones

{{#each upcoming_milestones}}
- **{{milestone_date}}**: {{milestone_title}}
  - Status: {{status_emoji}} {{status_text}}
  - Owner: {{owner_name}}
  {{#if at_risk}}
  - ⚠️ Risk: {{risk_description}}
  {{/if}}
{{/each}}

### Decisions Needed

{{#if has_decisions_needed}}
{{#each decisions_needed}}
- [ ] **{{decision_title}}**
  - **Context:** {{decision_context}}
  - **Owner:** {{decision_owner}}
  - **Deadline:** {{decision_deadline}}
  - **Options:** {{decision_options}}
{{/each}}
{{else}}
✅ No critical decisions pending.
{{/if}}

### Focus Areas

{{#each focus_areas}}
- 🎯 **{{area_title}}**: {{area_description}}
  - **Owner:** {{area_owner}}
  - **Success Criteria:** {{success_criteria}}
{{/each}}

---

## Appendix

### Data Sources
- **Goals:** {{goals_data_source}}
- **Tasks:** {{tasks_data_source}}
- **Financials:** {{financials_data_source}}
- **Last Updated:** {{data_last_updated}}

### Methodology
- **Health Score Calculation:** {{health_score_methodology}}
- **Trend Analysis Period:** {{trend_analysis_period}}
- **Bottleneck Detection:** {{bottleneck_detection_method}}

### Archive
- **Previous Briefing:** [Week of {{previous_week_date}}]({{previous_briefing_link}})
- **All Briefings:** [Archive]({{archive_link}})

---

**Next Briefing:** {{next_briefing_date}}

---

*Generated by CEO Briefing Writer v{{version}} | [Documentation]({{documentation_link}})*
