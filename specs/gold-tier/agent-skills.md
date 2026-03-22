# Gold Tier Agent Skills Specification

This document defines all Agent Skills required for Gold Tier operation. Skills are modular AI capabilities that can be invoked by the Ralph Wiggum reasoning loop.

## Skills Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Ralph Wiggum Loop                        │
│                                                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│  │  PERCEIVE   │──▶│   REASON    │──▶│   DECIDE    │       │
│  └─────────────┘   └─────────────┘   └─────────────┘       │
│                           │                    │            │
│                           │  Invoke Skills     │            │
│                           ▼                    ▼            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Agent Skills Library                    │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │   │
│  │  │ Reasoning│ │ Execution│ │ Analysis │ │ Report │ │   │
│  │  │ Skills   │ │ Skills   │ │ Skills   │ │ Skills │ │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Skills Organization

Skills are organized in the following structure:

```
.claude/skills/
├── foundation/           # Core skills (Silver Tier)
│   ├── company_handbook_enforcer/
│   ├── dashboard_writer/
│   ├── needs_action_triage/
│   ├── plan_md_generator/
│   ├── task_lifecycle_manager/
│   └── vault_state_manager/
│
├── silver/               # Silver Tier skills
│   ├── approval_workflow_enforcer/
│   ├── deadline_monitor/
│   ├── linkedin_post_generator/
│   ├── recurring_task_scheduler/
│   ├── silver_process_engine/
│   ├── silver_reasoning_engine/
│   ├── status_report_generator/
│   └── task_assigner/
│
└── gold/                 # Gold Tier skills (NEW)
    ├── cross_domain_automation/
    ├── odoo_accounting_integration/
    ├── social_media_automation/
    ├── weekly_business_audit/
    ├── monday_ceo_briefing/
    ├── error_handling_retry/
    ├── audit_logging/
    └── ralph_wiggum_reasoning/
```

---

## Gold Tier Skills Catalog

### Category 1: Cross-Domain Automation Skills

#### Skill: domain_classifier

**Path:** `.claude/skills/gold/cross_domain_automation/domain_classifier.py`

**Purpose:** Classifies incoming tasks into Personal or Business domain

**Input:**
```python
{
    "content": str,           # Task content
    "source": str,            # Source system (gmail, whatsapp, etc.)
    "metadata": dict          # Additional context
}
```

**Output:**
```python
{
    "domain": str,            # "personal" | "business"
    "subdomain": str,         # e.g., "finance", "operations", "health"
    "confidence": float,      # 0.0 - 1.0
    "reasoning": str          # Classification reasoning
}
```

**Usage Example:**
```python
from .claude.skills.gold.cross_domain_automation.domain_classifier import DomainClassifier

classifier = DomainClassifier()
result = await classifier.classify(
    content="Invoice #2026-001 payment reminder",
    source="gmail",
    metadata={"from": "client@example.com"}
)
# Result: {"domain": "business", "subdomain": "finance", "confidence": 0.95, ...}
```

---

#### Skill: task_prioritizer

**Path:** `.claude/skills/gold/cross_domain_automation/task_prioritizer.py`

**Purpose:** Prioritizes tasks across domains using Eisenhower Matrix

**Input:**
```python
{
    "tasks": list,            # List of task objects
    "context": dict           # Current context (time, energy, deadlines)
}
```

**Output:**
```python
{
    "prioritized_tasks": list,
    "matrix": {
        "urgent_important": list,
        "not_urgent_important": list,
        "urgent_not_important": list,
        "not_urgent_not_important": list
    }
}
```

**Priority Rules:**
| Quadrant | Description | Action |
|----------|-------------|--------|
| Q1: Urgent & Important | Crises, deadlines | Do immediately |
| Q2: Not Urgent & Important | Planning, relationships | Schedule |
| Q3: Urgent & Not Important | Interruptions, some calls | Delegate |
| Q4: Not Urgent & Not Important | Time wasters | Eliminate |

---

#### Skill: context_switcher

**Path:** `.claude/skills/gold/cross_domain_automation/context_switcher.py`

**Purpose:** Manages context switching between Personal and Business domains

**Input:**
```python
{
    "from_domain": str,
    "to_domain": str,
    "current_task": dict,
    "next_task": dict
}
```

**Output:**
```python
{
    "context_summary": str,
    "pending_actions": list,
    "handover_notes": str,
    "estimated_switch_cost": int  # seconds
}
```

---

### Category 2: Odoo Accounting Integration Skills

#### Skill: invoice_processor

**Path:** `.claude/skills/gold/odoo_accounting_integration/invoice_processor.py`

**Purpose:** Processes invoices from Odoo, creates payment tasks

**Input:**
```python
{
    "invoice_id": str,
    "action": str           # "process" | "review" | "pay"
}
```

**Output:**
```python
{
    "invoice_data": dict,
    "payment_due": bool,
    "suggested_action": str,
    "risk_assessment": dict,
    "markdown_file": str    # Created in Needs_Action
}
```

**Processing Flow:**
```
1. Fetch invoice from Odoo
2. Validate invoice data
3. Check against purchase orders
4. Assess payment priority
5. Create payment task or flag for review
6. Log to audit trail
```

---

#### Skill: payment_tracker

**Path:** `.claude/skills/gold/odoo_accounting_integration/payment_tracker.py`

**Purpose:** Tracks overdue payments and generates collection tasks

**Input:**
```python
{
    "partner_id": int,
    "days_overdue": int
}
```

**Output:**
```python
{
    "overdue_invoices": list,
    "total_amount": float,
    "collection_priority": str,  # "low" | "medium" | "high"
    "recommended_actions": list,
    "draft_communications": list
}
```

**Collection Escalation:**
| Days Overdue | Priority | Action |
|--------------|----------|--------|
| 1-7 | Low | Automated reminder |
| 8-15 | Medium | Personal email |
| 16-30 | High | Phone call |
| 31-60 | Critical | Collections agency |
| 60+ | Legal | Legal action |

---

#### Skill: financial_report_generator

**Path:** `.claude/skills/gold/odoo_accounting_integration/financial_report_generator.py`

**Purpose:** Generates financial reports from Odoo data

**Input:**
```python
{
    "report_type": str,     # "profit_loss" | "balance_sheet" | "cash_flow"
    "period": str,          # "monthly" | "quarterly" | "annual"
    "comparison": bool      # Include prior period comparison
}
```

**Output:**
```python
{
    "report_data": dict,
    "markdown_report": str,
    "key_metrics": dict,
    "anomalies": list,
    "recommendations": list
}
```

**Report Template:**
```markdown
# Financial Report: {report_type}

## Period: {period}

### Summary
| Metric | Current | Previous | Change |
|--------|---------|----------|--------|
| Revenue | $X | $Y | Z% |
| Expenses | $X | $Y | Z% |
| Net Income | $X | $Y | Z% |

### Key Insights
- {insight 1}
- {insight 2}

### Recommendations
- {recommendation 1}
- {recommendation 2}
```

---

#### Skill: budget_monitor

**Path:** `.claude/skills/gold/odoo_accounting_integration/budget_monitor.py`

**Purpose:** Monitors budget vs actual spending

**Input:**
```python
{
    "category": str,
    "period": str
}
```

**Output:**
```python
{
    "budgeted": float,
    "actual": float,
    "variance": float,
    "variance_percent": float,
    "status": str,        # "on_track" | "warning" | "over_budget"
    "alerts": list
}
```

---

### Category 3: Social Media Automation Skills

#### Skill: content_generator

**Path:** `.claude/skills/gold/social_media_automation/content_generator.py`

**Purpose:** Generates social media content for all platforms

**Input:**
```python
{
    "topic": str,
    "platform": str,      # "linkedin" | "facebook" | "instagram" | "twitter"
    "content_type": str,  # "post" | "story" | "reel" | "thread"
    "tone": str,          # "professional" | "casual" | "promotional"
    "hashtags": list
}
```

**Output:**
```python
{
    "content": str,
    "character_count": int,
    "hashtags": list,
    "media_suggestions": list,
    "optimal_posting_time": str,
    "estimated_reach": int
}
```

**Platform-Specific Rules:**
| Platform | Max Characters | Hashtag Strategy | Media |
|----------|---------------|------------------|-------|
| LinkedIn | 3,000 | 3-5 professional | Images, documents |
| Facebook | 63,206 | 1-3 casual | Images, videos |
| Instagram | 2,200 | 5-10 trending | Images, reels |
| Twitter | 280 | 1-2 trending | Images, GIFs |

---

#### Skill: engagement_responder

**Path:** `.claude/skills/gold/social_media_automation/engagement_responder.py`

**Purpose:** Generates responses to social media engagement

**Input:**
```python
{
    "platform": str,
    "engagement_type": str,  # "comment" | "message" | "mention"
    "content": str,
    "sentiment": str,        # "positive" | "neutral" | "negative"
    "author": dict
}
```

**Output:**
```python
{
    "suggested_response": str,
    "response_tone": str,
    "escalation_required": bool,
    "response_priority": str,
    "draft_approval_file": str
}
```

**Response Templates:**
```python
TEMPLATES = {
    "positive_comment": "Thank you for your kind words, {name}! We're thrilled that...",
    "neutral_inquiry": "Hi {name}, great question! Let me help you with that...",
    "negative_complaint": "Hi {name}, we're sorry to hear about your experience...",
    "sales_inquiry": "Hi {name}, thanks for your interest! Here's what you need to know...",
}
```

---

#### Skill: analytics_analyzer

**Path:** `.claude/skills/gold/social_media_automation/analytics_analyzer.py`

**Purpose:** Analyzes social media performance metrics

**Input:**
```python
{
    "platform": str,
    "period": str,
    "metrics": list
}
```

**Output:**
```python
{
    "metrics_summary": dict,
    "trends": list,
    "top_performing_posts": list,
    "recommendations": list,
    "next_period_goals": dict
}
```

**Key Metrics Tracked:**
- Impressions
- Engagement rate
- Click-through rate
- Follower growth
- Best posting times
- Top content types

---

#### Skill: posting_scheduler

**Path:** `.claude/skills/gold/social_media_automation/posting_scheduler.py`

**Purpose:** Schedules social media posts for optimal times

**Input:**
```python
{
    "posts": list,
    "platform": str,
    "schedule_type": str   # "optimal" | "custom" | "recurring"
}
```

**Output:**
```python
{
    "scheduled_posts": list,
    "schedule_calendar": dict,
    "conflicts": list,
    "approval_files": list
}
```

**Optimal Posting Times (by platform):**
| Platform | Best Days | Best Times |
|----------|-----------|------------|
| LinkedIn | Tue-Thu | 9-11 AM |
| Facebook | Wed, Fri | 1-3 PM |
| Instagram | Mon, Thu | 11 AM-1 PM |
| Twitter | Mon-Fri | 12-1 PM |

---

### Category 4: Weekly Business Audit Skills

#### Skill: weekly_audit_generator

**Path:** `.claude/skills/gold/weekly_business_audit/weekly_audit_generator.py`

**Purpose:** Generates comprehensive weekly business audit

**Input:**
```python
{
    "week_number": int,
    "year": int,
    "include_financials": bool
}
```

**Output:**
```python
{
    "audit_report": str,
    "metrics": dict,
    "achievements": list,
    "missed_targets": list,
    "recommendations": list,
    "markdown_file": str
}
```

**Audit Sections:**
```markdown
# Weekly Business Audit - Week {week}

## 1. Task Completion Summary
## 2. Financial Summary
## 3. Social Media Performance
## 4. Communication Summary
## 5. System Health
## 6. Recommendations for Next Week
```

---

#### Skill: metrics_aggregator

**Path:** `.claude/skills/gold/weekly_business_audit/metrics_aggregator.py`

**Purpose:** Aggregates metrics from all domains

**Input:**
```python
{
    "period": str,
    "domains": list
}
```

**Output:**
```python
{
    "aggregated_metrics": dict,
    "domain_breakdown": dict,
    "trends": dict,
    "anomalies": list
}
```

**Metrics Sources:**
- Gmail: Emails processed, response time
- WhatsApp: Messages handled
- Social: Posts published, engagement
- Odoo: Invoices, payments
- Tasks: Completed, pending, failed

---

#### Skill: kpi_tracker

**Path:** `.claude/skills/gold/weekly_business_audit/kpi_tracker.py`

**Purpose:** Tracks KPIs against targets

**Input:**
```python
{
    "kpi_definitions": dict,
    "actual_values": dict
}
```

**Output:**
```python
{
    "kpi_status": dict,
    "target_vs_actual": dict,
    "variance_analysis": dict,
    "alerts": list
}
```

**Default KPIs:**
| KPI | Target | Measurement |
|-----|--------|-------------|
| Email Response Time | < 2 hours | Average |
| Task Completion Rate | > 90% | Weekly |
| Invoice Payment Time | < 30 days | Average |
| Social Engagement Rate | > 3% | Per post |

---

### Category 5: Monday CEO Briefing Skills

#### Skill: briefing_generator

**Path:** `.claude/skills/gold/monday_ceo_briefing/briefing_generator.py`

**Purpose:** Generates Monday morning CEO briefing

**Input:**
```python
{
    "date": str,
    "include_week_ahead": bool
}
```

**Output:**
```python
{
    "briefing": str,
    "sections": dict,
    "action_items": list,
    "decisions_needed": list,
    "markdown_file": str
}
```

**Briefing Structure:**
```markdown
# CEO Briefing - {date}

## Executive Summary
## Last Week's Achievements
## This Week's Priorities
## Financial Snapshot
## Pending Decisions
## System Status
## Calendar Highlights
```

---

#### Skill: priority_extractor

**Path:** `.claude/skills/gold/monday_ceo_briefing/priority_extractor.py`

**Purpose:** Extracts and ranks weekly priorities

**Input:**
```python
{
    "tasks": list,
    "deadlines": list,
    "meetings": list
}
```

**Output:**
```python
{
    "top_priorities": list,
    "secondary_priorities": list,
    "deferred_items": list,
    "time_estimates": dict
}
```

---

#### Skill: decision_tracker

**Path:** `.claude/skills/gold/monday_ceo_briefing/decision_tracker.py`

**Purpose:** Tracks decisions requiring CEO attention

**Input:**
```python
{
    "pending_decisions": list
}
```

**Output:**
```python
{
    "decisions_summary": list,
    "urgency_ranking": list,
    "context_briefs": dict,
    "recommended_actions": dict
}
```

---

### Category 6: Error Handling & Retry Skills

#### Skill: error_classifier

**Path:** `.claude/skills/gold/error_handling_retry/error_classifier.py`

**Purpose:** Classifies errors and determines retry strategy

**Input:**
```python
{
    "error": dict,
    "context": dict
}
```

**Output:**
```python
{
    "error_type": str,
    "severity": str,
    "retryable": bool,
    "retry_strategy": dict,
    "escalation_required": bool
}
```

**Error Classification:**
| Error Type | Retry | Max Retries | Escalation |
|------------|-------|-------------|------------|
| NetworkTimeout | Yes | 3 | After 3 retries |
| RateLimit | Yes | 5 | After 5 retries |
| Authentication | No | 0 | Immediate |
| Validation | No | 0 | Log only |
| ServerError | Yes | 3 | After 3 retries |

---

#### Skill: retry_executor

**Path:** `.claude/skills/gold/error_handling_retry/retry_executor.py`

**Purpose:** Executes retry with exponential backoff

**Input:**
```python
{
    "operation": str,
    "params": dict,
    "retry_config": dict
}
```

**Output:**
```python
{
    "success": bool,
    "result": any,
    "attempts": int,
    "total_time": float,
    "error": str
}
```

**Retry Configuration:**
```python
RETRY_CONFIG = {
    "max_retries": 3,
    "base_delay": 2.0,
    "max_delay": 60.0,
    "exponential_base": 2,
    "jitter": 0.1,
}
```

---

#### Skill: dead_letter_handler

**Path:** `.claude/skills/gold/error_handling_retry/dead_letter_handler.py`

**Purpose:** Handles items that exceeded max retries

**Input:**
```python
{
    "failed_item": dict,
    "error_history": list
}
```

**Output:**
```python
{
    "quarantine_file": str,
    "human_review_required": bool,
    "suggested_resolution": str,
    "recovery_options": list
}
```

---

### Category 7: Audit Logging Skills

#### Skill: audit_logger

**Path:** `.claude/skills/gold/audit_logging/audit_logger.py`

**Purpose:** Logs all actions to immutable audit trail

**Input:**
```python
{
    "event_type": str,
    "details": dict,
    "context": dict
}
```

**Output:**
```python
{
    "audit_id": str,
    "log_file": str,
    "timestamp": str,
    "success": bool
}
```

**Audit Entry Schema:**
```json
{
  "audit_id": "uuid-v4",
  "timestamp": "ISO-8601",
  "event_type": "action_type",
  "source": "component_name",
  "actor": "ralph_wiggum_loop",
  "domain": "business|personal",
  "risk_level": "low|medium|high",
  "action_details": {},
  "result": {},
  "execution_time_ms": 123,
  "correlation_id": "uuid-v4"
}
```

---

#### Skill: audit_query

**Path:** `.claude/skills/gold/audit_logging/audit_query.py`

**Purpose:** Queries audit logs for analysis

**Input:**
```python
{
    "filters": dict,
    "date_range": dict,
    "aggregations": list
}
```

**Output:**
```python
{
    "results": list,
    "count": int,
    "aggregations": dict,
    "export_path": str
}
```

**Query Examples:**
```python
# Query by event type
audit_query(filters={"event_type": "email_sent"}, date_range={"from": "2026-03-01"})

# Query by approval ID
audit_query(filters={"approval_id": "uuid"}, date_range={})

# Export all audits for date
audit_query(filters={}, date_range={"from": "2026-03-06", "to": "2026-03-06"})
```

---

#### Skill: compliance_checker

**Path:** `.claude/skills/gold/audit_logging/compliance_checker.py`

**Purpose:** Checks actions against compliance rules

**Input:**
```python
{
    "action": dict,
    "rules": list
}
```

**Output:**
```python
{
    "compliant": bool,
    "violations": list,
    "warnings": list,
    "recommendations": list
}
```

---

### Category 8: Ralph Wiggum Reasoning Skills

#### Skill: situation_assessor

**Path:** `.claude/skills/gold/ralph_wiggum_reasoning/situation_assessor.py`

**Purpose:** Assesses current situation from inputs

**Input:**
```python
{
    "inputs": list,
    "context": dict
}
```

**Output:**
```python
{
    "situation_summary": str,
    "key_factors": list,
    "constraints": list,
    "opportunities": list,
    "risks": list
}
```

---

#### Skill: option_generator

**Path:** `.claude/skills/gold/ralph_wiggum_reasoning/option_generator.py`

**Purpose:** Generates possible action options

**Input:**
```python
{
    "situation": dict,
    "goals": list
}
```

**Output:**
```python
{
    "options": list,
    "option_details": dict,
    "tradeoffs": dict
}
```

---

#### Skill: decision_maker

**Path:** `.claude/skills/gold/ralph_wiggum_reasoning/decision_maker.py`

**Purpose:** Makes decisions based on analysis

**Input:**
```python
{
    "options": list,
    "criteria": dict,
    "constraints": list
}
```

**Output:**
```python
{
    "decision": dict,
    "reasoning": str,
    "confidence": float,
    "alternatives": list
}
```

---

#### Skill: action_planner

**Path:** `.claude/skills/gold/ralph_wiggum_reasoning/action_planner.py`

**Purpose:** Creates detailed action plans

**Input:**
```python
{
    "decision": dict,
    "resources": dict
}
```

**Output:**
```python
{
    "plan": dict,
    "steps": list,
    "timeline": dict,
    "dependencies": list,
    "approval_required": bool
}
```

---

#### Skill: outcome_evaluator

**Path:** `.claude/skills/gold/ralph_wiggum_reasoning/outcome_evaluator.py`

**Purpose:** Evaluates outcomes and updates models

**Input:**
```python
{
    "plan": dict,
    "actual_outcome": dict,
    "expected_outcome": dict
}
```

**Output:**
```python
{
    "success": bool,
    "variance": dict,
    "learnings": list,
    "model_updates": list
}
```

---

## Skill Invocation Pattern

All skills follow a consistent invocation pattern:

```python
from .claude.skills.gold.<category>.<skill_name> import SkillClass

async def invoke_skill(skill_name: str, input_data: dict) -> dict:
    """Invoke a skill with input data."""
    skill = SkillClass()
    
    try:
        # Validate input
        validated_input = skill.validate_input(input_data)
        
        # Execute skill
        result = await skill.execute(validated_input)
        
        # Log invocation
        await audit_logger.log({
            "event_type": "skill_invocation",
            "skill": skill_name,
            "input": validated_input,
            "output": result,
        })
        
        return result
        
    except Exception as e:
        # Handle error
        await error_handler.handle({
            "skill": skill_name,
            "error": str(e),
            "input": input_data,
        })
        raise
```

---

## Skill Testing

Each skill includes comprehensive tests:

```python
# tests/skills/gold/<category>/test_<skill>.py

import pytest
from .claude.skills.gold.<category>.<skill_name> import SkillClass

@pytest.mark.asyncio
async def test_skill_basic():
    skill = SkillClass()
    result = await skill.execute({"test": "input"})
    assert result["success"] == True

@pytest.mark.asyncio
async def test_skill_edge_case():
    skill = SkillClass()
    result = await skill.execute({"edge": "case"})
    assert result["handled"] == True
```

---

**Document End**
