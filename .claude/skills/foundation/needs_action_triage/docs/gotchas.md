# Needs Action Triage - Common Gotchas & Troubleshooting

## Overview
This document catalogs common mistakes, edge cases, and troubleshooting guidance for triage systems.

---

## 1. Classification Issues

### Gotcha: Keyword Collisions Between Categories

**Symptom:**
Items with ambiguous keywords get misclassified.

**Problem:**
```python
# WRONG - "error" matches both bug and question
categories = {
    'bug': {
        'keywords': ['error', 'bug', 'broken']
    },
    'question': {
        'keywords': ['error message', 'how to', 'question']
    }
}

# "Getting error message about permissions" 
# Matches both bug ('error') and question ('error message')
```

**Solution:**
```python
# CORRECT - Use phrase matching and priority order
def classify_with_priority(text):
    text_lower = text.lower()
    
    # Check multi-word phrases first (more specific)
    for category, config in categories.items():
        for phrase in config.get('phrases', []):
            if phrase.lower() in text_lower:
                return category
    
    # Then check single keywords
    keyword_scores = {}
    for category, config in categories.items():
        score = sum(1 for kw in config['keywords'] if kw in text_lower)
        if score > 0:
            keyword_scores[category] = score
    
    # Return category with highest match count
    if keyword_scores:
        return max(keyword_scores.items(), key=lambda x: x[1])[0]
    
    return 'uncategorized'
```

**Prevention:**
- Use multi-word phrases for specific patterns
- Order checks from most to least specific
- Count keyword frequency, not just presence
- Test with real examples from each category

---

### Gotcha: Over-Scoring Minor Items

**Symptom:**
Low-impact items get critical priority due to urgency words.

**Problem:**
```python
# WRONG - Any urgency word gives max boost
if 'urgent' in text.lower():
    score += 30  # ❌ Same boost regardless of impact
```

**Solution:**
```python
# CORRECT - Factor in both urgency and impact
def calculate_score_balanced(item):
    score = 50
    text = f"{item.title} {item.description}".lower()
    
    # Detect urgency
    urgency_level = 0
    if any(w in text for w in ['critical', 'urgent', 'asap']):
        urgency_level = 2
    elif any(w in text for w in ['soon', 'today']):
        urgency_level = 1
    
    # Detect impact
    impact_level = 0
    if any(w in text for w in ['production', 'all users', 'revenue']):
        impact_level = 2
    elif any(w in text for w in ['some users', 'staging']):
        impact_level = 1
    
    # Combined scoring (urgency * impact)
    if urgency_level == 2 and impact_level == 2:
        score += 40  # Both high
    elif urgency_level == 2 and impact_level == 1:
        score += 25  # High urgency, medium impact
    elif urgency_level == 2 and impact_level == 0:
        score += 15  # High urgency, low impact ✓ Reduced
    # ... other combinations
    
    return score
```

**Prevention:**
- Combine multiple factors (urgency × impact)
- Require evidence of actual impact
- Cap scores for low-impact urgent items
- Review false positives regularly

---

## 2. Duplicate Detection Issues

### Gotcha: False Positives from Common Phrases

**Symptom:**
Unrelated items flagged as duplicates due to boilerplate text.

**Problem:**
```python
# WRONG - Includes boilerplate in comparison
def are_duplicates(item1, item2):
    text1 = f"{item1.title} {item1.description}"
    text2 = f"{item2.title} {item2.description}"
    
    similarity = calculate_similarity(text1, text2)
    return similarity > 0.85
    # ❌ Boilerplate like "Steps to reproduce:" inflates similarity
```

**Solution:**
```python
# CORRECT - Remove boilerplate before comparison
def extract_meaningful_content(text):
    """Remove boilerplate sections"""
    # Remove common headers
    boilerplate_patterns = [
        r'Steps to reproduce:.*?(?=\n\n|\Z)',
        r'Expected behavior:.*?(?=\n\n|\Z)',
        r'Actual behavior:.*?(?=\n\n|\Z)',
        r'Environment:.*?(?=\n\n|\Z)',
    ]
    
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)
    
    return text.strip()

def are_duplicates_improved(item1, item2):
    # Extract meaningful content only
    content1 = extract_meaningful_content(f"{item1.title} {item1.description}")
    content2 = extract_meaningful_content(f"{item2.title} {item2.description}")
    
    # Also check title similarity separately (higher weight)
    title_sim = calculate_similarity(item1.title, item2.title)
    content_sim = calculate_similarity(content1, content2)
    
    # Weighted average
    combined_sim = (title_sim * 0.6) + (content_sim * 0.4)
    
    return combined_sim > 0.85
```

**Prevention:**
- Filter boilerplate before comparison
- Weight title more heavily than description
- Require minimum content length for comparison
- Manually review high-similarity pairs

---

### Gotcha: Missing Duplicates Due to Reformulation

**Symptom:**
Same issue reported differently not detected as duplicate.

**Problem:**
```
Item 1: "Login button doesn't work"
Item 2: "Cannot authenticate - sign in fails"
# Not flagged as duplicate due to different wording
```

**Solution:**
```python
# Use semantic similarity, not just keyword matching
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class SemanticDuplicateDetector:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),  # Include bigrams
            stop_words='english',
            min_df=1
        )
        self.item_vectors = {}
    
    def add_item(self, item_id, text):
        """Add item to index"""
        # Vectorize
        vector = self.vectorizer.fit_transform([text])
        self.item_vectors[item_id] = vector
    
    def find_similar(self, text, threshold=0.7):
        """Find similar items using semantic similarity"""
        if not self.item_vectors:
            return []
        
        # Vectorize query
        query_vector = self.vectorizer.transform([text])
        
        # Compute similarity with all items
        similar = []
        for item_id, item_vector in self.item_vectors.items():
            similarity = cosine_similarity(query_vector, item_vector)[0][0]
            if similarity >= threshold:
                similar.append((item_id, similarity))
        
        # Sort by similarity
        similar.sort(key=lambda x: x[1], reverse=True)
        return similar
```

**Prevention:**
- Use TF-IDF or embeddings for semantic matching
- Include synonyms in comparison
- Lower threshold for potential duplicates
- Human review of "similar but not duplicate" pairs

---

## 3. Routing and Assignment Issues

### Gotcha: Owner Overload from Imbalanced Assignment

**Symptom:**
Some team members get flooded while others idle.

**Problem:**
```python
# WRONG - Always assigns to default owner
def assign_owner(item):
    category_config = rules['categories'][item.category]
    item.owner = category_config['default_owner']
    # ❌ No load balancing
```

**Solution:**
```python
# CORRECT - Balance load across team members
class LoadBalancedAssigner:
    def __init__(self):
        self.owner_load = defaultdict(int)
        self.team_members = self.load_team_structure()
    
    def assign_owner(self, item):
        # Get eligible team members for category
        category_team = self.team_members[item.category]
        
        # Filter by availability
        available = [m for m in category_team if self.is_available(m)]
        
        if not available:
            # Fallback to default
            return rules['categories'][item.category]['default_owner']
        
        # Assign to least loaded available member
        least_loaded = min(available, key=lambda m: self.owner_load[m])
        self.owner_load[least_loaded] += 1
        
        logger.info(f"Assigned to {least_loaded} (load: {self.owner_load[least_loaded]})")
        return least_loaded
    
    def is_available(self, member):
        """Check if member is available (not on PTO, etc.)"""
        # Check calendar, PTO system, etc.
        return True  # Simplified
```

**Prevention:**
- Track current workload per owner
- Consider availability (PTO, meetings, etc.)
- Rotate assignments for fairness
- Allow manual override for special cases

---

## 4. SLA and Escalation Issues

### Gotcha: SLA Calculated from Wrong Timestamp

**Symptom:**
SLA deadlines too short or too long.

**Problem:**
```python
# WRONG - Uses current time instead of item creation time
def calculate_sla_deadline(item):
    sla_hours = get_sla_hours(item.category)
    # ❌ Should use item.created_at, not now
    deadline = datetime.utcnow() + timedelta(hours=sla_hours)
    return deadline
```

**Solution:**
```python
# CORRECT - Calculate from item creation time
def calculate_sla_deadline(item):
    sla_hours = get_sla_hours(item.category)
    
    # Use item creation time
    created = datetime.fromisoformat(item.created_at)
    deadline = created + timedelta(hours=sla_hours)
    
    # Adjust for business hours if needed
    if should_use_business_hours(item.category):
        deadline = adjust_for_business_hours(created, sla_hours)
    
    return deadline.isoformat()

def adjust_for_business_hours(start_time, hours):
    """Calculate deadline considering only business hours"""
    # Business hours: 9am-5pm, Mon-Fri
    # Implementation depends on business requirements
    # ... (complex logic to skip weekends/holidays)
    pass
```

**Prevention:**
- Always use item creation timestamp
- Document whether SLA is calendar or business hours
- Account for holidays and weekends
- Test edge cases (created on Friday evening)

---

## 5. Performance Issues

### Gotcha: Slow Duplicate Detection at Scale

**Symptom:**
Triage becomes slow as item count grows.

**Problem:**
```python
# WRONG - O(n) comparison with all existing items
def find_duplicates(new_item, all_items):
    for existing in all_items:  # ❌ Checks every item
        if is_similar(new_item, existing):
            return existing.id
    return None
```

**Solution:**
```python
# CORRECT - Use indexing for fast lookup
class IndexedDuplicateDetector:
    def __init__(self):
        # Index by fingerprint for O(1) lookup
        self.fingerprint_index = defaultdict(list)
        # Index by category for faster subset search
        self.category_index = defaultdict(list)
    
    def add_item(self, item):
        """Add item to indices"""
        fp = self.compute_fingerprint(item)
        self.fingerprint_index[fp].append(item.id)
        self.category_index[item.category].append(item.id)
    
    def find_duplicates(self, new_item):
        """Fast duplicate lookup"""
        fp = self.compute_fingerprint(new_item)
        
        # Fast exact match via fingerprint
        if fp in self.fingerprint_index:
            return self.fingerprint_index[fp][0]
        
        # Fuzzy match only within same category
        candidates = self.category_index[new_item.category]
        for candidate_id in candidates[-100:]:  # Only recent items
            candidate = self.get_item(candidate_id)
            if self.is_similar(new_item, candidate):
                return candidate_id
        
        return None
```

**Prevention:**
- Use fingerprint-based indexing
- Limit similarity search to recent items
- Consider same-category items only
- Cache expensive computations

---

## Quick Reference: Common Error Messages

| Error Message | Likely Cause | Solution |
|---------------|--------------|----------|
| "Classification accuracy below threshold" | Rules out of date | Review and update keyword lists |
| "Too many critical items" | Threshold too low | Raise critical threshold |
| "SLA breach rate spike" | Workload imbalance | Redistribute assignments |
| "Duplicate detection slow" | No indexing | Implement fingerprint index |
| "Owner not found" | Team configuration stale | Update team mappings |
| "Escalation loop detected" | Circular escalation path | Fix escalation chain |

---

**Last Updated:** 2026-02-06
**Contribute:** Found a new gotcha? Document it here!
