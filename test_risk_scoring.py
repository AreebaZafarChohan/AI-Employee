#!/usr/bin/env python3
"""Test the enhanced risk scoring system."""

import re
from pathlib import Path

# Copy the functions from silver_process_engine.py for testing
RISK_KEYWORDS = {
    "urgent", "legal", "lawsuit", "court",
    "payment", "invoice", "overdue",
    "password", "credentials", "breach",
    "terminate", "fired", "layoff",
    "critical", "emergency", "asap",
}

FINANCIAL_HIGH_THRESHOLD = 100.0


def _extract_amount(content: str, meta: dict) -> float:
    amount_str = meta.get("amount", "")
    if amount_str:
        try:
            return float(re.sub(r"[^\d.]", "", str(amount_str)))
        except (ValueError, TypeError):
            pass
    
    patterns = [
        r'\$[\d,]+\.?\d*',
        r'USD\s*[\d,]+\.?\d*',
        r'[\d,]+\.?\d*\s*dollars?',
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            try:
                return float(re.sub(r'[^\d.]', '', match.group().replace('$', '').replace('USD', '').replace('dollars', '')))
            except (ValueError, TypeError):
                pass
    
    return 0.0


def _is_unknown_sender(meta: dict) -> bool:
    from_field = meta.get("from", "").lower()
    internal_domains = ["company.com", "internal", "localhost"]
    
    if not from_field:
        return True
    
    for domain in internal_domains:
        if domain in from_field:
            return False
    
    return True


def _has_urgent_keywords(content: str) -> bool:
    content_lower = content.lower()
    urgent_keywords = {"urgent", "asap", "immediately", "rush", "deadline", "today only"}
    return any(kw in content_lower for kw in urgent_keywords)


def classify_risk(item_type: str, meta: dict, content: str):
    risk_factors = {
        "base_score": 0,
        "financial_score": 0,
        "sender_score": 0,
        "keyword_score": 0,
        "urgency_score": 0,
        "factors": [],
    }
    
    if item_type == "email":
        risk_factors["base_score"] = 20
        risk_factors["factors"].append("email type (+20)")
    elif item_type == "file_drop":
        risk_factors["base_score"] = 30
        risk_factors["factors"].append("file_drop type (+30)")
    elif item_type == "whatsapp":
        risk_factors["base_score"] = 25
        risk_factors["factors"].append("whatsapp type (+25)")
    
    priority = meta.get("priority", "").lower()
    if priority == "high":
        risk_factors["base_score"] += 30
        risk_factors["factors"].append("high priority (+30)")
    elif priority == "medium":
        risk_factors["base_score"] += 20
        risk_factors["factors"].append("medium priority (+20)")
    elif priority == "low":
        risk_factors["base_score"] += 10
        risk_factors["factors"].append("low priority (+10)")
    
    amount = _extract_amount(content, meta)
    if amount > FINANCIAL_HIGH_THRESHOLD:
        risk_factors["financial_score"] = 50
        risk_factors["factors"].append(f"amount ${amount:.2f} > ${FINANCIAL_HIGH_THRESHOLD} (+50)")
    elif amount > 0:
        risk_factors["financial_score"] = 20
        risk_factors["factors"].append(f"amount ${amount:.2f} (+20)")
    
    if _is_unknown_sender(meta):
        risk_factors["sender_score"] = 25
        risk_factors["factors"].append("unknown sender (+25)")
    else:
        risk_factors["sender_score"] = 5
        risk_factors["factors"].append("known sender (+5)")
    
    if _has_urgent_keywords(content):
        risk_factors["urgency_score"] = 25
        risk_factors["factors"].append("urgent keywords (+25)")
    
    content_lower = content.lower()
    if any(kw in content_lower for kw in RISK_KEYWORDS):
        risk_factors["keyword_score"] = 30
        risk_factors["factors"].append("risk keywords present (+30)")
    
    if item_type == "file_drop" and not _is_unknown_sender(meta):
        risk_factors["base_score"] = max(0, risk_factors["base_score"] - 20)
        risk_factors["factors"].append("internal file_drop (-20)")
    
    total_score = sum([
        risk_factors["base_score"],
        risk_factors["financial_score"],
        risk_factors["sender_score"],
        risk_factors["keyword_score"],
        risk_factors["urgency_score"],
    ])
    
    total_score = min(100, total_score)
    
    if total_score >= 70:
        risk_level = "high"
    elif total_score >= 40:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    confidence_factors = 0
    if meta.get("from"):
        confidence_factors += 1
    if meta.get("priority"):
        confidence_factors += 1
    if amount > 0:
        confidence_factors += 1
    if content:
        confidence_factors += 1
    
    confidence_score = min(100, 60 + (confidence_factors * 10))
    
    risk_factors["total_score"] = total_score
    risk_factors["confidence_score"] = confidence_score
    
    return risk_level, confidence_score, risk_factors


if __name__ == "__main__":
    print("=" * 70)
    print("Risk Scoring System Tests")
    print("=" * 70)
    print()
    
    # Test 1: High risk - external sender, high priority, payment > $100
    print("Test 1: HIGH RISK Email")
    print("-" * 50)
    meta1 = {'from': 'external@gmail.com', 'priority': 'high', 'amount': '500'}
    content1 = 'Urgent! Payment of $500 needed immediately'
    risk1, conf1, factors1 = classify_risk('email', meta1, content1)
    print(f"  Risk Level: {risk1.upper()}")
    print(f"  Confidence: {conf1}%")
    print(f"  Score: {factors1['total_score']}/100")
    print(f"  Factors:")
    for f in factors1['factors']:
        print(f"    - {f}")
    print()
    
    # Test 2: Low risk - internal file drop
    print("Test 2: LOW RISK Internal File")
    print("-" * 50)
    meta2 = {'from': 'john@company.com'}
    content2 = 'Monthly report attached'
    risk2, conf2, factors2 = classify_risk('file_drop', meta2, content2)
    print(f"  Risk Level: {risk2.upper()}")
    print(f"  Confidence: {conf2}%")
    print(f"  Score: {factors2['total_score']}/100")
    print(f"  Factors:")
    for f in factors2['factors']:
        print(f"    - {f}")
    print()
    
    # Test 3: Medium risk - external sender, medium priority
    print("Test 3: MEDIUM RISK Email")
    print("-" * 50)
    meta3 = {'from': 'client@external.com', 'priority': 'medium'}
    content3 = 'Question about the project'
    risk3, conf3, factors3 = classify_risk('email', meta3, content3)
    print(f"  Risk Level: {risk3.upper()}")
    print(f"  Confidence: {conf3}%")
    print(f"  Score: {factors3['total_score']}/100")
    print(f"  Factors:")
    for f in factors3['factors']:
        print(f"    - {f}")
    print()
    
    # Test 4: Amount in content
    print("Test 4: Amount Detection from Content")
    print("-" * 50)
    meta4 = {'from': 'vendor@external.com'}
    content4 = 'Please pay $150 for the invoice'
    risk4, conf4, factors4 = classify_risk('email', meta4, content4)
    print(f"  Risk Level: {risk4.upper()}")
    print(f"  Confidence: {conf4}%")
    print(f"  Score: {factors4['total_score']}/100")
    print(f"  Factors:")
    for f in factors4['factors']:
        print(f"    - {f}")
    print()
    
    print("=" * 70)
    print("All tests completed!")
    print("=" * 70)
