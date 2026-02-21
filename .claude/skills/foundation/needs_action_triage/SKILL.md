# Needs Action Triage Skill

## Overview

**Skill Name:** `needs_action_triage`
**Domain:** `foundation`
**Purpose:** Automatically classify, prioritize, and route items requiring action using intelligent scoring, duplicate detection, and dependency analysis to ensure critical items receive appropriate attention.

**Core Capabilities:**
- Automatic classification of action items by category and urgency
- Priority scoring based on multiple factors (severity, impact, deadline)
- Duplicate detection and deduplication
- Dependency analysis and prerequisite identification
- Smart routing to appropriate handlers/teams
- Escalation path determination
- Audit trail maintenance for accountability

**When to Use:**
- Incoming issue/ticket triage systems
- Email inbox processing and prioritization
- Pull request review assignment
- Customer support ticket routing
- Bug report classification
- Feature request prioritization
- Security vulnerability assessment
- Incident response coordination

**When NOT to Use:**
- Simple FIFO queue processing (no prioritization needed)
- Pre-classified items with manual assignment
- Single-handler systems with no routing logic
- Real-time chat/messaging (requires instant response)
- Stateless operations without persistence needs

---

## Impact Analysis

### Operational Impact: **CRITICAL**
- **Misclassification Risk:** Critical items marked as low priority can cause incidents
- **Routing Errors:** Wrong team assignment delays resolution
- **Duplicate Handling:** Duplicate items waste effort if not detected
- **Audit Requirements:** Compliance requires complete decision trail

### Business Impact: **HIGH**
- **SLA Compliance:** Incorrect prioritization can breach SLAs
- **Customer Satisfaction:** Slow response to urgent items harms reputation
- **Team Efficiency:** Poor routing causes context switching and delays
- **Resource Allocation:** Priority errors lead to misallocated effort

### System Impact: **MEDIUM**
- **Performance:** Classification must be fast (<1s per item)
- **Accuracy:** Requires high precision for critical items (>95%)
- **Scalability:** Must handle bursts of incoming items
- **Integration:** Needs to connect with multiple upstream/downstream systems

---

## Environment Variables

### Required Variables

```bash
# Triage configuration
TRIAGE_RULES_PATH="./config/triage-rules.json"     # Classification rules
TRIAGE_STORAGE_PATH="./triage"                     # Item storage
TRIAGE_AUDIT_LOG="./logs/triage-audit.log"         # Audit trail

# Scoring thresholds
TRIAGE_CRITICAL_THRESHOLD="90"       # Score ≥90 = critical
TRIAGE_HIGH_THRESHOLD="70"           # Score ≥70 = high priority
TRIAGE_MEDIUM_THRESHOLD="40"         # Score ≥40 = medium priority
# Below medium = low priority

# Processing limits
TRIAGE_MAX_BATCH_SIZE="100"          # Max items per batch
TRIAGE_DEDUP_WINDOW="7d"             # Look-back for duplicates
```

### Optional Variables

```bash
# Advanced configuration
TRIAGE_ENABLE_ML="false"             # Enable ML-based classification
TRIAGE_ML_MODEL_PATH=""              # Path to ML model
TRIAGE_SIMILARITY_THRESHOLD="0.85"   # Duplicate detection threshold

# Integration endpoints
TRIAGE_SLACK_WEBHOOK=""              # Slack notifications for critical items
TRIAGE_JIRA_URL=""                   # JIRA integration
TRIAGE_EMAIL_SMTP=""                 # Email notifications

# Performance tuning
TRIAGE_CACHE_ENABLED="true"          # Cache classification results
TRIAGE_CACHE_TTL="3600"              # Cache TTL in seconds
TRIAGE_PARALLEL_WORKERS="5"          # Parallel classification workers

# Debug and monitoring
TRIAGE_DEBUG_MODE="false"            # Verbose debug logging
TRIAGE_METRICS_PORT="9091"           # Prometheus metrics port
```

---

## Network and Authentication Implications

### Local Classification Mode

**Primary Mode:** File-based rules with local processing

**Requirements:**
- Read access to rules configuration
- Write access to storage and audit logs
- No network dependencies

### Integrated Mode (API-Based)

**For external service integration:**

```bash
# Authentication
TRIAGE_API_KEY="<api-key>"           # API authentication
TRIAGE_API_SECRET="<secret>"         # API secret

# Service endpoints
TRIAGE_NLP_SERVICE="http://nlp.internal:8080"
TRIAGE_TICKET_API="https://tickets.example.com/api"
TRIAGE_NOTIFICATION_API="https://notify.example.com/api"
```

**Authentication Patterns:**
- **API Key Auth:** For service-to-service communication
- **OAuth 2.0:** For user-delegated actions
- **Service Account:** For automated processing
- **Webhook Signatures:** For incoming item verification

### Network Patterns

**Pattern 1: Standalone (No Network)**
```bash
# Local rules, local storage
# No external dependencies
```

**Pattern 2: Hybrid (Optional Network)**
```bash
# Local classification with optional notifications
# Graceful degradation if services unavailable
```

**Pattern 3: Fully Integrated (Network Required)**
```bash
# NLP service for content analysis
# Ticket system for routing
# Notification service for alerts
```

---

## Blueprints & Templates

### Template 1: Classification Rules Configuration

**File:** `assets/triage-rules.json`

```json
{
  "version": "1.0",
  "categories": {
    "security": {
      "keywords": ["vulnerability", "exploit", "CVE", "security", "breach", "attack"],
      "severity_boost": 30,
      "auto_escalate": true,
      "default_owner": "security-team",
      "sla_hours": 4
    },
    "bug_critical": {
      "keywords": ["crash", "outage", "down", "broken", "critical bug", "production"],
      "severity_boost": 25,
      "auto_escalate": true,
      "default_owner": "sre-team",
      "sla_hours": 2
    },
    "bug_major": {
      "keywords": ["error", "broken", "not working", "failing", "bug"],
      "severity_boost": 15,
      "auto_escalate": false,
      "default_owner": "dev-team",
      "sla_hours": 24
    },
    "feature_request": {
      "keywords": ["feature", "enhancement", "improvement", "would be nice", "request"],
      "severity_boost": 0,
      "auto_escalate": false,
      "default_owner": "product-team",
      "sla_hours": 168
    },
    "question": {
      "keywords": ["how to", "question", "help", "documentation", "unclear"],
      "severity_boost": 5,
      "auto_escalate": false,
      "default_owner": "support-team",
      "sla_hours": 48
    }
  },
  "urgency_indicators": {
    "immediate": {
      "patterns": ["URGENT", "ASAP", "NOW", "IMMEDIATE", "EMERGENCY"],
      "score_boost": 20
    },
    "deadline_near": {
      "patterns": ["today", "by EOD", "this week", "deadline"],
      "score_boost": 15
    },
    "blocking": {
      "patterns": ["blocked", "blocking", "cannot proceed", "stuck"],
      "score_boost": 10
    }
  },
  "impact_indicators": {
    "high_impact": {
      "patterns": ["all users", "production", "customer-facing", "revenue"],
      "score_multiplier": 1.5
    },
    "medium_impact": {
      "patterns": ["some users", "staging", "internal"],
      "score_multiplier": 1.2
    },
    "low_impact": {
      "patterns": ["single user", "development", "cosmetic"],
      "score_multiplier": 1.0
    }
  },
  "routing_rules": {
    "escalation_chain": [
      {
        "condition": "score >= 90",
        "action": "escalate_to_oncall",
        "notify": ["slack", "pagerduty"]
      },
      {
        "condition": "category == 'security'",
        "action": "escalate_to_security",
        "notify": ["email", "slack"]
      },
      {
        "condition": "sla_breach_imminent",
        "action": "escalate_to_manager",
        "notify": ["email"]
      }
    ]
  }
}
```

### Template 2: Python Triage Engine

**File:** `assets/triage_engine.py`

```python
#!/usr/bin/env python3
"""
triage_engine.py
Intelligent action item triage with classification and prioritization
"""

import os
import json
import re
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TriageItem:
    """Item requiring triage"""
    item_id: str
    title: str
    description: str
    source: str  # e.g., "github", "email", "jira"
    created_at: str
    category: Optional[str] = None
    priority: Optional[str] = None
    score: Optional[int] = None
    owner: Optional[str] = None
    tags: List[str] = None
    sla_deadline: Optional[str] = None
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None
    dependencies: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.dependencies is None:
            self.dependencies = []


class TriageEngine:
    """Intelligent triage engine for action items"""

    def __init__(
        self,
        rules_path: str = None,
        storage_path: str = None,
        audit_log_path: str = None
    ):
        self.rules_path = Path(rules_path or os.getenv('TRIAGE_RULES_PATH', './config/triage-rules.json'))
        self.storage_path = Path(storage_path or os.getenv('TRIAGE_STORAGE_PATH', './triage'))
        self.audit_log_path = audit_log_path or os.getenv('TRIAGE_AUDIT_LOG', './logs/triage-audit.log')

        # Load rules
        self.rules = self._load_rules()

        # Thresholds
        self.critical_threshold = int(os.getenv('TRIAGE_CRITICAL_THRESHOLD', '90'))
        self.high_threshold = int(os.getenv('TRIAGE_HIGH_THRESHOLD', '70'))
        self.medium_threshold = int(os.getenv('TRIAGE_MEDIUM_THRESHOLD', '40'))

        # Deduplication
        self.dedup_window_days = int(os.getenv('TRIAGE_DEDUP_WINDOW', '7').rstrip('d'))
        self.similarity_threshold = float(os.getenv('TRIAGE_SIMILARITY_THRESHOLD', '0.85'))

        # Ensure directories exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        Path(self.audit_log_path).parent.mkdir(parents=True, exist_ok=True)

        logger.info("TriageEngine initialized")

    def _load_rules(self) -> Dict[str, Any]:
        """Load triage rules from configuration"""
        if not self.rules_path.exists():
            logger.warning(f"Rules file not found: {self.rules_path}, using defaults")
            return self._default_rules()

        try:
            with open(self.rules_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load rules: {e}")
            return self._default_rules()

    def _default_rules(self) -> Dict[str, Any]:
        """Default triage rules"""
        return {
            "categories": {
                "bug": {"severity_boost": 15, "default_owner": "dev-team"},
                "feature": {"severity_boost": 0, "default_owner": "product-team"},
                "question": {"severity_boost": 5, "default_owner": "support-team"}
            }
        }

    def _audit_log(self, action: str, item_id: str, details: Dict[str, Any]):
        """Write audit log entry"""
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'action': action,
            'item_id': item_id,
            'details': details
        }

        try:
            with open(self.audit_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.warning(f"Failed to write audit log: {e}")

    def classify_category(self, item: TriageItem) -> str:
        """Classify item into category"""
        text = f"{item.title} {item.description}".lower()

        # Check each category's keywords
        category_scores = {}
        for category_name, category_config in self.rules.get('categories', {}).items():
            keywords = category_config.get('keywords', [])
            match_count = sum(1 for keyword in keywords if keyword.lower() in text)

            if match_count > 0:
                category_scores[category_name] = match_count

        # Return category with highest match count
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])[0]
            logger.info(f"Classified {item.item_id} as '{best_category}' (matches: {category_scores[best_category]})")
            return best_category

        # Default category
        return "uncategorized"

    def calculate_score(self, item: TriageItem) -> int:
        """Calculate priority score (0-100)"""
        score = 50  # Base score

        text = f"{item.title} {item.description}".lower()

        # Category boost
        category_config = self.rules.get('categories', {}).get(item.category, {})
        score += category_config.get('severity_boost', 0)

        # Urgency indicators
        urgency_config = self.rules.get('urgency_indicators', {})
        for urgency_type, config in urgency_config.items():
            for pattern in config.get('patterns', []):
                if pattern.lower() in text:
                    score += config.get('score_boost', 0)
                    logger.debug(f"Urgency boost: {pattern} (+{config.get('score_boost', 0)})")
                    break  # Only count once per urgency type

        # Impact multiplier
        impact_config = self.rules.get('impact_indicators', {})
        for impact_type, config in impact_config.items():
            for pattern in config.get('patterns', []):
                if pattern.lower() in text:
                    multiplier = config.get('score_multiplier', 1.0)
                    score = int(score * multiplier)
                    logger.debug(f"Impact multiplier: {pattern} (x{multiplier})")
                    break  # Only apply first matching impact
            else:
                continue
            break  # Only apply one impact level

        # Clamp to 0-100
        return max(0, min(100, score))

    def determine_priority(self, score: int) -> str:
        """Convert score to priority label"""
        if score >= self.critical_threshold:
            return "critical"
        elif score >= self.high_threshold:
            return "high"
        elif score >= self.medium_threshold:
            return "medium"
        else:
            return "low"

    def calculate_sla_deadline(self, item: TriageItem) -> str:
        """Calculate SLA deadline based on category"""
        category_config = self.rules.get('categories', {}).get(item.category, {})
        sla_hours = category_config.get('sla_hours', 48)  # Default 48 hours

        deadline = datetime.utcnow() + timedelta(hours=sla_hours)
        return deadline.isoformat()

    def assign_owner(self, item: TriageItem) -> str:
        """Assign default owner based on category"""
        category_config = self.rules.get('categories', {}).get(item.category, {})
        return category_config.get('default_owner', 'unassigned')

    def _compute_fingerprint(self, item: TriageItem) -> str:
        """Compute fingerprint for duplicate detection"""
        # Normalize text
        text = f"{item.title} {item.description}".lower()
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation

        # Hash
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity (simple Jaccard)"""
        # Tokenize
        tokens1 = set(text1.lower().split())
        tokens2 = set(text2.lower().split())

        # Jaccard similarity
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def find_duplicates(self, item: TriageItem) -> Optional[str]:
        """Find duplicate items within window"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.dedup_window_days)
        fingerprint = self._compute_fingerprint(item)

        # Search existing items
        for existing_file in self.storage_path.glob("*.json"):
            try:
                with open(existing_file, 'r') as f:
                    existing_data = json.load(f)

                existing_created = datetime.fromisoformat(existing_data['created_at'])

                # Skip if outside window
                if existing_created < cutoff_date:
                    continue

                # Check fingerprint match
                existing_fingerprint = self._compute_fingerprint(
                    TriageItem(**existing_data)
                )

                if fingerprint == existing_fingerprint:
                    logger.info(f"Exact duplicate found: {item.item_id} -> {existing_data['item_id']}")
                    return existing_data['item_id']

                # Check similarity
                similarity = self._calculate_similarity(
                    f"{item.title} {item.description}",
                    f"{existing_data['title']} {existing_data['description']}"
                )

                if similarity >= self.similarity_threshold:
                    logger.info(f"Similar duplicate found: {item.item_id} -> {existing_data['item_id']} (similarity: {similarity:.2f})")
                    return existing_data['item_id']

            except Exception as e:
                logger.warning(f"Error checking duplicate against {existing_file}: {e}")
                continue

        return None

    def check_escalation(self, item: TriageItem) -> List[Dict[str, Any]]:
        """Check if item should be escalated"""
        escalations = []

        routing_rules = self.rules.get('routing_rules', {})
        escalation_chain = routing_rules.get('escalation_chain', [])

        for rule in escalation_chain:
            condition = rule.get('condition', '')

            # Evaluate condition (simple evaluation)
            should_escalate = False

            if 'score >=' in condition:
                threshold = int(condition.split('>=')[1].strip())
                should_escalate = item.score >= threshold

            elif 'category ==' in condition:
                category = condition.split('==')[1].strip().strip('"').strip("'")
                should_escalate = item.category == category

            elif condition == 'sla_breach_imminent':
                # Check if SLA deadline is within 25% of window
                if item.sla_deadline:
                    deadline = datetime.fromisoformat(item.sla_deadline)
                    now = datetime.utcnow()
                    created = datetime.fromisoformat(item.created_at)

                    total_window = (deadline - created).total_seconds()
                    elapsed = (now - created).total_seconds()

                    should_escalate = (elapsed / total_window) > 0.75

            if should_escalate:
                escalations.append({
                    'action': rule.get('action'),
                    'notify': rule.get('notify', []),
                    'reason': condition
                })

        return escalations

    def triage_item(self, item: TriageItem) -> TriageItem:
        """Perform complete triage on item"""
        logger.info(f"Triaging item: {item.item_id}")

        self._audit_log('TRIAGE_START', item.item_id, {'title': item.title})

        try:
            # 1. Check for duplicates
            duplicate_of = self.find_duplicates(item)
            if duplicate_of:
                item.is_duplicate = True
                item.duplicate_of = duplicate_of
                self._audit_log('DUPLICATE_FOUND', item.item_id, {'duplicate_of': duplicate_of})
                logger.info(f"Item {item.item_id} marked as duplicate of {duplicate_of}")
                return item

            # 2. Classify category
            item.category = self.classify_category(item)

            # 3. Calculate score
            item.score = self.calculate_score(item)

            # 4. Determine priority
            item.priority = self.determine_priority(item.score)

            # 5. Calculate SLA deadline
            item.sla_deadline = self.calculate_sla_deadline(item)

            # 6. Assign owner
            item.owner = self.assign_owner(item)

            # 7. Check escalation
            escalations = self.check_escalation(item)
            if escalations:
                item.tags.append('escalated')
                self._audit_log('ESCALATION', item.item_id, {'escalations': escalations})

            # Log result
            self._audit_log('TRIAGE_COMPLETE', item.item_id, {
                'category': item.category,
                'priority': item.priority,
                'score': item.score,
                'owner': item.owner,
                'escalations': len(escalations)
            })

            logger.info(f"Triage complete: {item.item_id} -> {item.category}/{item.priority} (score: {item.score})")

            return item

        except Exception as e:
            logger.error(f"Triage failed for {item.item_id}: {e}")
            self._audit_log('TRIAGE_ERROR', item.item_id, {'error': str(e)})
            raise

    def save_item(self, item: TriageItem) -> bool:
        """Save triaged item to storage"""
        item_file = self.storage_path / f"{item.item_id}.json"

        try:
            with open(item_file, 'w') as f:
                json.dump(asdict(item), f, indent=2)

            logger.info(f"Saved item: {item_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save item {item.item_id}: {e}")
            return False

    def get_item(self, item_id: str) -> Optional[TriageItem]:
        """Retrieve triaged item"""
        item_file = self.storage_path / f"{item_id}.json"

        if not item_file.exists():
            return None

        try:
            with open(item_file, 'r') as f:
                data = json.load(f)
                return TriageItem(**data)

        except Exception as e:
            logger.error(f"Failed to load item {item_id}: {e}")
            return None

    def list_items_by_priority(self, priority: str = None) -> List[TriageItem]:
        """List items, optionally filtered by priority"""
        items = []

        for item_file in self.storage_path.glob("*.json"):
            try:
                with open(item_file, 'r') as f:
                    data = json.load(f)
                    item = TriageItem(**data)

                    if priority is None or item.priority == priority:
                        items.append(item)

            except Exception as e:
                logger.warning(f"Error loading {item_file}: {e}")
                continue

        # Sort by score (descending)
        items.sort(key=lambda x: x.score or 0, reverse=True)

        return items


# Example usage
if __name__ == "__main__":
    engine = TriageEngine()

    # Create sample item
    item = TriageItem(
        item_id="ITEM-001",
        title="Production database crash - URGENT",
        description="The main database crashed and all users are affected. Need immediate attention.",
        source="github",
        created_at=datetime.utcnow().isoformat()
    )

    # Triage
    triaged_item = engine.triage_item(item)

    # Save
    engine.save_item(triaged_item)

    # Display results
    print(f"\nTriage Results:")
    print(f"  Category: {triaged_item.category}")
    print(f"  Priority: {triaged_item.priority}")
    print(f"  Score: {triaged_item.score}")
    print(f"  Owner: {triaged_item.owner}")
    print(f"  SLA Deadline: {triaged_item.sla_deadline}")
    print(f"  Is Duplicate: {triaged_item.is_duplicate}")
```

### Template 3: Batch Triage Script

**File:** `assets/batch-triage.sh`

```bash
#!/usr/bin/env bash
# batch-triage.sh
# Batch process items for triage

set -euo pipefail

INPUT_DIR="${1:?Usage: $0 <input-dir>}"
TRIAGE_ENGINE="${TRIAGE_ENGINE:-./assets/triage_engine.py}"
MAX_BATCH="${TRIAGE_MAX_BATCH_SIZE:-100}"

process_item() {
    local item_file="$1"
    
    echo "Processing: $item_file"
    
    # Extract item data
    local item_id=$(jq -r '.id' "$item_file")
    local title=$(jq -r '.title' "$item_file")
    local description=$(jq -r '.description // ""' "$item_file")
    local source=$(jq -r '.source // "unknown"' "$item_file")
    
    # Run triage
    python3 "$TRIAGE_ENGINE" triage \
        --id "$item_id" \
        --title "$title" \
        --description "$description" \
        --source "$source"
    
    echo "  ✓ Triaged: $item_id"
}

# Main processing
count=0
for item_file in "$INPUT_DIR"/*.json; do
    if [[ ! -f "$item_file" ]]; then
        continue
    fi
    
    process_item "$item_file"
    
    count=$((count + 1))
    if [[ $count -ge $MAX_BATCH ]]; then
        echo "Reached batch limit ($MAX_BATCH)"
        break
    fi
done

echo "Processed $count items"
```

---

## Validation Checklist

### Pre-Deployment Checklist

- [ ] **Classification Rules**
  - [ ] All categories defined with keywords
  - [ ] Severity boosts configured appropriately
  - [ ] Default owners assigned for each category
  - [ ] SLA hours realistic and approved

- [ ] **Scoring Configuration**
  - [ ] Thresholds calibrated (critical, high, medium)
  - [ ] Urgency indicators identified
  - [ ] Impact multipliers validated
  - [ ] Test cases verify expected scores

- [ ] **Duplicate Detection**
  - [ ] Deduplication window appropriate
  - [ ] Similarity threshold tuned (avoid false positives)
  - [ ] Fingerprinting algorithm tested
  - [ ] Edge cases handled (near-duplicates)

- [ ] **Routing and Escalation**
  - [ ] Escalation paths defined
  - [ ] Notification channels configured
  - [ ] Owner team mappings correct
  - [ ] Auto-escalation rules validated

- [ ] **Audit and Compliance**
  - [ ] Audit log path writable
  - [ ] All decisions logged
  - [ ] Log retention policy defined
  - [ ] Compliance requirements met

- [ ] **Integration Points**
  - [ ] Source systems configured
  - [ ] Notification webhooks tested
  - [ ] API credentials valid
  - [ ] Error handling for unavailable services

### Post-Deployment Validation

- [ ] **Accuracy Testing**
  - [ ] Critical items correctly identified (>95%)
  - [ ] Low false positive rate for duplicates (<5%)
  - [ ] Routing accuracy validated
  - [ ] No misclassified security issues

- [ ] **Performance Testing**
  - [ ] Triage latency <1s per item
  - [ ] Batch processing meets throughput
  - [ ] No memory leaks under load
  - [ ] Graceful degradation on errors

- [ ] **Monitoring**
  - [ ] Classification metrics collected
  - [ ] SLA breach alerts configured
  - [ ] Duplicate detection rate tracked
  - [ ] Owner workload balanced

---

## Anti-Patterns

### ❌ Anti-Pattern 1: Misclassifying Critical Items as Low Priority

**Bad Example:**
```python
# NEVER do this - ignores urgency signals
def calculate_score(item):
    score = 50  # Base score
    
    # Only check category
    if 'bug' in item.description.lower():
        score += 10
    
    return score  # ❌ Ignores "URGENT", "PRODUCTION", "CRASH"
```

**Why It's Bad:**
- Critical production issues marked as normal bugs
- SLA breaches due to delayed response
- Customer impact not considered
- Revenue loss from mishandled incidents

**Correct Approach:**
```python
def calculate_score(item):
    score = 50
    text = f"{item.title} {item.description}".lower()
    
    # Category boost
    if 'bug' in text:
        score += 10
    
    # CRITICAL: Check urgency signals
    urgency_keywords = ['urgent', 'critical', 'asap', 'emergency', 'now']
    for keyword in urgency_keywords:
        if keyword in text:
            score += 20
            break
    
    # CRITICAL: Check impact
    if any(x in text for x in ['production', 'all users', 'outage']):
        score = int(score * 1.5)  # High impact multiplier
    
    # CRITICAL: Check for crashes/data loss
    if any(x in text for x in ['crash', 'data loss', 'security breach']):
        score = max(score, 90)  # Force high priority
    
    return min(100, score)
```

---

### ❌ Anti-Pattern 2: Ignoring Task Dependencies

**Bad Example:**
```python
# NEVER do this - processes items independently
def triage_item(item):
    item.category = classify(item)
    item.priority = calculate_priority(item)
    # ❌ No dependency checking
    return item
```

**Why It's Bad:**
- Work started on blocked tasks
- Duplicate effort on related items
- Wrong execution order
- Wasted resources

**Correct Approach:**
```python
def triage_item(item):
    item.category = classify(item)
    item.priority = calculate_priority(item)
    
    # Check for dependencies
    dependencies = find_dependencies(item)
    item.dependencies = dependencies
    
    # Adjust priority if blocked
    if dependencies:
        unresolved = [d for d in dependencies if not is_resolved(d)]
        if unresolved:
            item.tags.append('blocked')
            item.priority = adjust_priority_for_blocked(item.priority)
            logger.info(f"{item.id} blocked by: {unresolved}")
    
    # Check for related items (potential duplicates)
    related = find_related_items(item)
    if related:
        item.tags.append('has_related')
        item.related_items = related
    
    return item
```

---

### ❌ Anti-Pattern 3: Poor Duplicate Detection

**Bad Example:**
```python
# NEVER do this - exact string matching only
def is_duplicate(item, existing_items):
    for existing in existing_items:
        if item.title == existing.title:  # ❌ Exact match only
            return True
    return False
```

**Why It's Bad:**
- Misses similar items with different wording
- Creates duplicate work
- Fragments discussions
- Wastes team effort

**Correct Approach:**
```python
import hashlib
from difflib import SequenceMatcher

def compute_fingerprint(text):
    """Normalize and hash for fuzzy matching"""
    # Normalize
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    
    # Extract key terms (remove stop words)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at'}
    words = [w for w in text.split() if w not in stop_words]
    
    # Hash
    return hashlib.sha256(' '.join(sorted(words)).encode()).hexdigest()[:16]

def calculate_similarity(text1, text2):
    """Calculate text similarity"""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def find_duplicates(item, existing_items, window_days=7):
    """Find duplicates using multiple strategies"""
    cutoff = datetime.utcnow() - timedelta(days=window_days)
    fingerprint = compute_fingerprint(f"{item.title} {item.description}")
    
    for existing in existing_items:
        # Skip old items
        if existing.created_at < cutoff:
            continue
        
        # Strategy 1: Fingerprint match (fast)
        existing_fp = compute_fingerprint(f"{existing.title} {existing.description}")
        if fingerprint == existing_fp:
            return existing.id
        
        # Strategy 2: High similarity (slower)
        similarity = calculate_similarity(
            f"{item.title} {item.description}",
            f"{existing.title} {existing.description}"
        )
        
        if similarity >= 0.85:  # 85% similar
            logger.info(f"Similar item found: {similarity:.2%}")
            return existing.id
    
    return None
```

---

### ❌ Anti-Pattern 4: No Audit Trail

**Bad Example:**
```python
# NEVER do this - no logging of decisions
def triage_item(item):
    item.category = 'bug'
    item.priority = 'high'
    item.owner = 'dev-team'
    # ❌ No record of why these decisions were made
    save(item)
```

**Why It's Bad:**
- Cannot debug misclassifications
- No accountability
- Cannot improve rules
- Compliance violations

**Correct Approach:**
```python
def triage_item(item):
    audit_trail = []
    
    # Classification with reasoning
    category, category_reason = classify_with_reason(item)
    item.category = category
    audit_trail.append({
        'decision': 'category',
        'value': category,
        'reason': category_reason,
        'timestamp': datetime.utcnow().isoformat()
    })
    
    # Scoring with factors
    score, score_factors = calculate_score_with_factors(item)
    item.score = score
    audit_trail.append({
        'decision': 'score',
        'value': score,
        'factors': score_factors,
        'timestamp': datetime.utcnow().isoformat()
    })
    
    # Priority determination
    priority = determine_priority(score)
    item.priority = priority
    audit_trail.append({
        'decision': 'priority',
        'value': priority,
        'score': score,
        'timestamp': datetime.utcnow().isoformat()
    })
    
    # Owner assignment
    owner, assignment_reason = assign_owner_with_reason(item)
    item.owner = owner
    audit_trail.append({
        'decision': 'owner',
        'value': owner,
        'reason': assignment_reason,
        'timestamp': datetime.utcnow().isoformat()
    })
    
    # Save audit trail
    item.audit_trail = audit_trail
    
    # Also log to central audit system
    log_audit('TRIAGE_COMPLETE', item.id, {
        'category': category,
        'priority': priority,
        'score': score,
        'owner': owner,
        'audit_trail': audit_trail
    })
    
    save(item)
```

---

### ❌ Anti-Pattern 5: Static Rules Without Feedback Loop

**Bad Example:**
```python
# NEVER do this - rules never improve
RULES = {
    'bug': {'keywords': ['bug', 'error'], 'score': 50},
    'feature': {'keywords': ['feature'], 'score': 30}
}

def classify(item):
    for category, config in RULES.items():
        if any(kw in item.title.lower() for kw in config['keywords']):
            return category
    # ❌ Rules never updated based on actual performance
```

**Why It's Bad:**
- Accuracy degrades over time
- New patterns not captured
- No learning from mistakes
- Manual tuning required

**Correct Approach:**
```python
class AdaptiveTriageEngine:
    """Triage engine with feedback loop"""
    
    def __init__(self):
        self.rules = load_rules()
        self.feedback_db = FeedbackDatabase()
    
    def classify(self, item):
        # Use current rules
        category = self._apply_rules(item)
        
        # Record prediction for feedback
        self._record_prediction(item.id, category)
        
        return category
    
    def record_feedback(self, item_id, correct_category, was_correct):
        """Record human feedback on classification"""
        self.feedback_db.add_feedback({
            'item_id': item_id,
            'predicted': self._get_prediction(item_id),
            'correct': correct_category,
            'was_correct': was_correct,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Trigger rule update if enough feedback
        if self.feedback_db.count_since_last_update() >= 100:
            self.update_rules()
    
    def update_rules(self):
        """Update rules based on feedback"""
        logger.info("Updating rules based on feedback")
        
        # Analyze feedback
        misclassifications = self.feedback_db.get_misclassifications()
        
        # Find patterns in errors
        for category, errors in misclassifications.items():
            # Extract keywords from misclassified items
            new_keywords = self._extract_keywords_from_errors(errors)
            
            # Update rules
            if new_keywords:
                self.rules[category]['keywords'].extend(new_keywords)
                logger.info(f"Added keywords to {category}: {new_keywords}")
        
        # Save updated rules
        self._save_rules()
        
        # Log performance metrics
        accuracy = self.feedback_db.calculate_accuracy()
        logger.info(f"Current accuracy: {accuracy:.2%}")
```

---

## Related Documentation

- [patterns.md](./docs/patterns.md) - Triage strategies and workflows
- [impact-checklist.md](./docs/impact-checklist.md) - Full system impact assessment
- [gotchas.md](./docs/gotchas.md) - Common pitfalls and troubleshooting

---

## Support and Troubleshooting

### Common Issues

1. **Low Classification Accuracy**
   - Review and update keyword lists
   - Tune scoring thresholds
   - Add more urgency/impact indicators
   - Collect feedback and iterate

2. **Too Many False Positive Duplicates**
   - Lower similarity threshold
   - Increase deduplication window
   - Improve fingerprinting algorithm
   - Review duplicate pairs manually

3. **Incorrect Routing**
   - Verify owner team mappings
   - Check category classification
   - Review escalation rules
   - Test with real examples

4. **SLA Breaches**
   - Review SLA hour configuration
   - Check escalation triggers
   - Ensure notifications working
   - Monitor queue depth

### Getting Help

- Review audit logs for decision reasoning
- Check classification accuracy metrics
- Consult patterns.md for workflows
- Complete impact-checklist.md for deployment

---

**Version:** 1.0.0
**Last Updated:** 2026-02-06
**Maintainer:** Foundation Team
