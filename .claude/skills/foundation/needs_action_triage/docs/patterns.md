# Needs Action Triage - Common Patterns

## Overview
This document describes common triage strategies, workflows, and integration patterns for intelligent action item classification.

---

## Pattern 1: Multi-Stage Triage Pipeline

### Use Case
Process items through multiple triage stages with increasing specificity.

### Implementation

```python
class MultiStageTriagePipeline:
    """Process items through triage stages"""

    def __init__(self, engine: TriageEngine):
        self.engine = engine

    def triage_with_stages(self, item: TriageItem) -> TriageItem:
        """Multi-stage triage process"""

        # Stage 1: Initial classification
        item = self.stage_1_classify(item)

        # Stage 2: Priority scoring
        item = self.stage_2_score(item)

        # Stage 3: Duplicate detection
        item = self.stage_3_dedup(item)

        # Stage 4: Dependency analysis
        item = self.stage_4_dependencies(item)

        # Stage 5: Routing and assignment
        item = self.stage_5_route(item)

        # Stage 6: Escalation check
        item = self.stage_6_escalate(item)

        return item

    def stage_1_classify(self, item):
        """Stage 1: Category classification"""
        item.category = self.engine.classify_category(item)
        item.tags.append(f"classified:{item.category}")
        return item

    def stage_2_score(self, item):
        """Stage 2: Priority scoring"""
        item.score = self.engine.calculate_score(item)
        item.priority = self.engine.determine_priority(item.score)
        return item

    def stage_3_dedup(self, item):
        """Stage 3: Duplicate detection"""
        duplicate_of = self.engine.find_duplicates(item)
        if duplicate_of:
            item.is_duplicate = True
            item.duplicate_of = duplicate_of
            item.tags.append("duplicate")
            # Stop further processing
            return item
        return item

    def stage_4_dependencies(self, item):
        """Stage 4: Dependency analysis"""
        # Check for blocking items
        dependencies = self.find_dependencies(item)
        if dependencies:
            item.dependencies = dependencies
            item.tags.append("has_dependencies")
        return item

    def stage_5_route(self, item):
        """Stage 5: Owner assignment"""
        item.owner = self.engine.assign_owner(item)
        item.sla_deadline = self.engine.calculate_sla_deadline(item)
        return item

    def stage_6_escalate(self, item):
        """Stage 6: Escalation check"""
        escalations = self.engine.check_escalation(item)
        if escalations:
            item.tags.append("escalated")
            self.notify_escalations(item, escalations)
        return item
```

---

## Pattern 2: Adaptive Threshold Tuning

### Use Case
Automatically adjust classification thresholds based on workload and accuracy.

### Implementation

```python
class AdaptiveThresholdTuner:
    """Automatically tune classification thresholds"""

    def __init__(self, engine: TriageEngine):
        self.engine = engine
        self.metrics = MetricsCollector()

    def tune_thresholds(self):
        """Adjust thresholds based on metrics"""

        # Get recent metrics
        accuracy = self.metrics.get_classification_accuracy()
        false_positive_rate = self.metrics.get_false_positive_rate()
        queue_depth_critical = self.metrics.get_queue_depth('critical')
        queue_depth_high = self.metrics.get_queue_depth('high')

        # Adjust critical threshold
        if queue_depth_critical > 50:  # Too many critical items
            # Raise threshold to be more selective
            self.engine.critical_threshold += 2
            logger.info(f"Raised critical threshold to {self.engine.critical_threshold}")

        elif queue_depth_critical < 5 and accuracy > 0.95:
            # Lower threshold to catch more
            self.engine.critical_threshold -= 1
            logger.info(f"Lowered critical threshold to {self.engine.critical_threshold}")

        # Adjust high threshold based on false positives
        if false_positive_rate > 0.10:  # Too many false positives
            self.engine.high_threshold += 3
            logger.info(f"Raised high threshold to {self.engine.high_threshold}")

        # Clamp thresholds
        self.engine.critical_threshold = max(80, min(95, self.engine.critical_threshold))
        self.engine.high_threshold = max(60, min(85, self.engine.high_threshold))
```

---

## Pattern 3: Context-Aware Classification

### Use Case
Use additional context (user history, time of day, recent activity) to improve classification.

### Implementation

```python
class ContextAwareClassifier:
    """Classify items using contextual information"""

    def __init__(self, engine: TriageEngine):
        self.engine = engine
        self.history = ItemHistory()

    def classify_with_context(self, item: TriageItem) -> str:
        """Classify using context"""

        # Base classification
        base_category = self.engine.classify_category(item)

        # Get context
        context = self.get_context(item)

        # Adjust based on context
        if context['user_has_recent_critical']:
            # User recently had critical issues, be more sensitive
            if base_category == 'bug_major':
                base_category = 'bug_critical'
                logger.info(f"Upgraded to critical due to user history")

        if context['is_business_hours']:
            # During business hours, questions get higher priority
            if base_category == 'question':
                item.score += 10
                logger.info("Boosted score due to business hours")

        if context['recent_similar_items'] > 3:
            # Multiple similar items - potential systemic issue
            item.tags.append('potential_pattern')
            item.score += 15
            logger.info("Boosted score due to similar recent items")

        return base_category

    def get_context(self, item: TriageItem) -> dict:
        """Gather contextual information"""
        return {
            'user_has_recent_critical': self.history.has_recent_critical(item.source),
            'is_business_hours': self.is_business_hours(),
            'recent_similar_items': self.history.count_similar_recent(item),
            'user_tier': self.get_user_tier(item.source),
            'time_since_last_item': self.history.time_since_last(item.source)
        }
```

---

## Pattern 4: Smart Batch Processing

### Use Case
Efficiently process large batches of items with dependency optimization.

### Implementation

```python
class SmartBatchProcessor:
    """Process items in batches with optimization"""

    def __init__(self, engine: TriageEngine):
        self.engine = engine

    def process_batch(self, items: List[TriageItem]) -> List[TriageItem]:
        """Process batch with optimization"""

        # Step 1: Quick pre-filter for obvious duplicates
        unique_items = self.filter_obvious_duplicates(items)
        logger.info(f"Filtered {len(items) - len(unique_items)} obvious duplicates")

        # Step 2: Parallel classification
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=5) as executor:
            classified = list(executor.map(
                self.engine.classify_category,
                unique_items
            ))

        # Step 3: Batch dependency analysis
        dependency_graph = self.build_dependency_graph(unique_items)

        # Step 4: Priority-based ordering
        sorted_items = self.sort_by_priority_and_deps(unique_items, dependency_graph)

        # Step 5: Assign to owners with load balancing
        assigned_items = self.assign_with_load_balancing(sorted_items)

        return assigned_items

    def filter_obvious_duplicates(self, items):
        """Fast duplicate filtering"""
        seen_fingerprints = set()
        unique = []

        for item in items:
            fp = self._quick_fingerprint(item)
            if fp not in seen_fingerprints:
                seen_fingerprints.add(fp)
                unique.append(item)

        return unique

    def assign_with_load_balancing(self, items):
        """Distribute items evenly across owners"""
        owner_load = defaultdict(int)

        for item in items:
            # Get possible owners for category
            possible_owners = self.get_possible_owners(item.category)

            # Assign to least loaded
            least_loaded = min(possible_owners, key=lambda o: owner_load[o])
            item.owner = least_loaded
            owner_load[least_loaded] += 1

        return items
```

---

## Pattern 5: Escalation Chain with Timeouts

### Use Case
Automatically escalate items if not handled within time limits.

### Implementation

```python
class EscalationManager:
    """Manage escalation chains and timeouts"""

    def __init__(self, engine: TriageEngine):
        self.engine = engine

    def check_escalations(self):
        """Check all items for escalation"""

        for item_file in self.engine.storage_path.glob("*.json"):
            item = self.engine.get_item(item_file.stem)

            if not item or item.is_duplicate:
                continue

            # Check various escalation conditions
            should_escalate, reason = self.should_escalate(item)

            if should_escalate:
                self.escalate_item(item, reason)

    def should_escalate(self, item: TriageItem) -> Tuple[bool, str]:
        """Determine if item should be escalated"""

        # Condition 1: SLA breach imminent
        if item.sla_deadline:
            deadline = datetime.fromisoformat(item.sla_deadline)
            time_remaining = (deadline - datetime.utcnow()).total_seconds()

            if time_remaining < 3600:  # Less than 1 hour
                return True, "SLA deadline approaching"

        # Condition 2: High priority not assigned
        if item.priority in ['critical', 'high'] and not item.owner:
            created = datetime.fromisoformat(item.created_at)
            age_hours = (datetime.utcnow() - created).total_seconds() / 3600

            if age_hours > 1:
                return True, "High priority unassigned for >1 hour"

        # Condition 3: Multiple reassignments
        if hasattr(item, 'assignment_history'):
            if len(item.assignment_history) > 3:
                return True, "Multiple reassignments"

        return False, ""

    def escalate_item(self, item: TriageItem, reason: str):
        """Escalate item to next level"""

        # Determine escalation target
        escalation_target = self.get_escalation_target(item)

        # Notify
        self.send_escalation_notification(item, escalation_target, reason)

        # Update item
        item.tags.append('escalated')
        if not hasattr(item, 'escalation_history'):
            item.escalation_history = []

        item.escalation_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'reason': reason,
            'target': escalation_target
        })

        self.engine.save_item(item)

        logger.warning(f"Escalated {item.item_id} to {escalation_target}: {reason}")
```

---

## Pattern 6: Machine Learning Enhancement

### Use Case
Use ML model to enhance rule-based classification.

### Implementation

```python
class MLEnhancedClassifier:
    """Combine rules and ML for classification"""

    def __init__(self, engine: TriageEngine, model_path: str = None):
        self.engine = engine
        self.model = self.load_model(model_path) if model_path else None

    def classify_hybrid(self, item: TriageItem) -> str:
        """Use both rules and ML"""

        # Get rule-based classification
        rule_category = self.engine.classify_category(item)
        rule_confidence = self.calculate_rule_confidence(item, rule_category)

        # If no ML model, use rules only
        if not self.model:
            return rule_category

        # Get ML prediction
        ml_category, ml_confidence = self.ml_predict(item)

        # Combine predictions
        if rule_confidence > 0.8:
            # High confidence in rules, use rules
            logger.info(f"Using rule-based: {rule_category} (conf: {rule_confidence})")
            return rule_category

        elif ml_confidence > 0.9:
            # High confidence in ML, use ML
            logger.info(f"Using ML: {ml_category} (conf: {ml_confidence})")
            return ml_category

        elif rule_category == ml_category:
            # Agreement, use either
            logger.info(f"Agreement: {rule_category}")
            return rule_category

        else:
            # Disagreement, use weighted average or conservative choice
            if rule_confidence > ml_confidence:
                logger.info(f"Disagreement, using rules: {rule_category}")
                return rule_category
            else:
                logger.info(f"Disagreement, using ML: {ml_category}")
                return ml_category

    def ml_predict(self, item: TriageItem) -> Tuple[str, float]:
        """Get ML model prediction"""
        # Vectorize text
        features = self.vectorize(f"{item.title} {item.description}")

        # Predict
        probabilities = self.model.predict_proba([features])[0]
        category_idx = probabilities.argmax()
        confidence = probabilities[category_idx]

        category = self.model.classes_[category_idx]

        return category, confidence
```

---

## Pattern 7: Feedback Loop Integration

### Use Case
Continuously improve classification by learning from human corrections.

### Implementation

```python
class FeedbackIntegration:
    """Integrate human feedback into triage system"""

    def __init__(self, engine: TriageEngine):
        self.engine = engine
        self.feedback_store = FeedbackStore()

    def record_feedback(
        self,
        item_id: str,
        predicted_category: str,
        actual_category: str,
        predicted_priority: str,
        actual_priority: str
    ):
        """Record human correction"""

        feedback = {
            'item_id': item_id,
            'predicted_category': predicted_category,
            'actual_category': actual_category,
            'category_correct': predicted_category == actual_category,
            'predicted_priority': predicted_priority,
            'actual_priority': actual_priority,
            'priority_correct': predicted_priority == actual_priority,
            'timestamp': datetime.utcnow().isoformat()
        }

        self.feedback_store.add(feedback)

        # Trigger analysis if enough feedback collected
        if self.feedback_store.count_since_last_analysis() >= 50:
            self.analyze_feedback()

    def analyze_feedback(self):
        """Analyze feedback and update rules"""

        feedback_items = self.feedback_store.get_recent(limit=100)

        # Calculate accuracy metrics
        category_accuracy = sum(1 for f in feedback_items if f['category_correct']) / len(feedback_items)
        priority_accuracy = sum(1 for f in feedback_items if f['priority_correct']) / len(feedback_items)

        logger.info(f"Accuracy - Category: {category_accuracy:.2%}, Priority: {priority_accuracy:.2%}")

        # Find common misclassifications
        misclassified = [f for f in feedback_items if not f['category_correct']]

        # Group by error type
        error_patterns = defaultdict(list)
        for error in misclassified:
            key = f"{error['predicted_category']}->{error['actual_category']}"
            error_patterns[key].append(error)

        # Report patterns
        for pattern, errors in error_patterns.items():
            if len(errors) >= 5:  # At least 5 instances
                logger.warning(f"Common misclassification: {pattern} ({len(errors)} instances)")
                self.suggest_rule_update(pattern, errors)

    def suggest_rule_update(self, pattern: str, errors: List[dict]):
        """Suggest rule updates based on errors"""

        # Extract keywords from misclassified items
        all_text = []
        for error in errors:
            item = self.engine.get_item(error['item_id'])
            if item:
                all_text.append(f"{item.title} {item.description}")

        # Find common words
        from collections import Counter
        all_words = ' '.join(all_text).lower().split()
        common_words = Counter(all_words).most_common(10)

        logger.info(f"Common words in {pattern} errors: {common_words}")

        # Generate suggested keywords
        suggested_keywords = [word for word, count in common_words if count >= len(errors) * 0.5]

        if suggested_keywords:
            logger.info(f"Suggested keywords for {pattern}: {suggested_keywords}")
```

---

## Best Practices Summary

1. **Multi-Stage Processing** - Break triage into discrete stages
2. **Adaptive Thresholds** - Automatically tune based on metrics
3. **Context Awareness** - Use historical and temporal context
4. **Batch Optimization** - Process efficiently in batches
5. **Escalation Management** - Automate escalation chains
6. **ML Enhancement** - Combine rules and machine learning
7. **Feedback Integration** - Continuously improve from corrections
8. **Audit Everything** - Log all decisions with reasoning
9. **Monitor Accuracy** - Track and report classification metrics
10. **Load Balancing** - Distribute work evenly across teams

---

**Last Updated:** 2026-02-06
