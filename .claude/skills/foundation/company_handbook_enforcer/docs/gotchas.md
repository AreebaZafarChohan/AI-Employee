# Company Handbook Enforcer - Common Gotchas & Troubleshooting

## Overview
This document catalogs common mistakes, edge cases, and troubleshooting guidance for company handbook enforcement operations.

---

## 1. Configuration Issues

### Gotcha: Incorrect Rule Path Configuration
**Problem:** The system fails to load policy rules because the HANDBOOK_RULES_PATH is incorrectly set.
**Symptoms:** Validation always passes or fails with "Rules file not found" errors.
**Solution:** 
1. Verify the path exists: `ls -la $HANDBOOK_RULES_PATH`
2. Check file permissions: `stat $HANDBOOK_RULES_PATH`
3. Ensure the file is valid JSON: `python -m json.tool $HANDBOOK_RULES_PATH`
4. Confirm the path is accessible to the running process

**Prevention:** Use absolute paths and verify them during deployment.

### Gotcha: Environment Variable Not Set
**Problem:** Environment variables like AUDIT_LOG_PATH are not set, causing the system to use defaults that may not exist.
**Symptoms:** Permission errors when writing logs, unexpected behavior.
**Solution:**
1. Check current environment: `env | grep HANDBOOK`
2. Set missing variables: `export AUDIT_LOG_PATH=/var/log/handbook-audit.log`
3. Verify directory exists: `mkdir -p $(dirname $AUDIT_LOG_PATH)`

**Prevention:** Create a configuration validation script that checks all required variables.

### Gotcha: Rule Cache TTL Too Short/Long
**Problem:** Cache TTL is set too short causing performance issues, or too long causing outdated rules to be used.
**Symptoms:** Performance degradation or outdated policy enforcement.
**Solution:** Adjust HANDBOOK_CACHE_TTL based on rule update frequency and performance requirements.
- For frequently updated rules: 300 seconds (5 minutes)
- For stable rules: 3600 seconds (1 hour)

---

## 2. Performance Issues

### Gotcha: Large File Processing
**Problem:** Attempting to validate very large files causes memory exhaustion or timeouts.
**Symptoms:** Process crashes, timeouts, or extremely slow validation.
**Solution:**
1. Set HANDBOOK_MAX_FILE_SIZE to limit file size: `export HANDBOOK_MAX_FILE_SIZE=10485760` (10MB)
2. Implement streaming validation for large files
3. Process large files in chunks if needed

**Prevention:** Implement file size checks before processing and set appropriate limits.

### Gotcha: Regex Performance with Complex Patterns
**Problem:** Complex regex patterns cause catastrophic backtracking, leading to extremely slow validation.
**Symptoms:** Validation takes much longer than expected, high CPU usage.
**Solution:**
1. Simplify complex patterns where possible
2. Use non-capturing groups: `(?:pattern)` instead of `(pattern)`
3. Limit quantifiers: Use `{1,10}` instead of `+` when possible
4. Test patterns with tools like regex101.com

**Prevention:** Test all regex patterns with worst-case inputs during rule development.

### Gotcha: Concurrent Validation Bottleneck
**Problem:** High concurrency causes system overload when validating many items simultaneously.
**Symptoms:** Slow response times, timeouts, resource exhaustion.
**Solution:**
1. Implement rate limiting
2. Use connection pooling
3. Add queuing mechanism for validation requests
4. Scale horizontally if needed

---

## 3. Policy Enforcement Issues

### Gotcha: False Positives in Credential Detection
**Problem:** The system flags legitimate content as containing credentials (e.g., "password" in "password_reset").
**Symptoms:** Legitimate content gets blocked incorrectly.
**Solution:**
1. Add context-aware rules that consider surrounding text
2. Implement fuzzy matching with confidence scores
3. Add whitelisting for known safe patterns
4. Use case-sensitive matching where appropriate

**Prevention:** Test rules extensively with diverse content samples before deployment.

### Gotcha: Inconsistent Severity Classification
**Problem:** Similar violations receive different severity ratings depending on context or rule ordering.
**Symptoms:** Inconsistent handling of similar violations, confusion about priority.
**Solution:**
1. Establish clear severity classification guidelines
2. Order rules deterministically
3. Use centralized severity mapping
4. Regularly audit and calibrate severity assignments

### Gotcha: Missing Context in Violation Reports
**Problem:** Violation reports lack sufficient context to understand or fix the issue.
**Symptoms:** Users can't understand why content was flagged or how to fix it.
**Solution:**
1. Include specific location information (line numbers, sections)
2. Provide clear, actionable descriptions
3. Suggest specific fixes when possible
4. Link to relevant policy documentation

---

## 4. Integration Problems

### Gotcha: Encoding Issues with Non-ASCII Characters
**Problem:** Documents with non-ASCII characters cause validation to fail or behave unexpectedly.
**Symptoms:** Unicode decode errors, incorrect pattern matching.
**Solution:**
1. Ensure consistent UTF-8 encoding: `with open(file, 'r', encoding='utf-8')`
2. Handle encoding detection for files: `chardet.detect(content)`
3. Normalize text before processing: `unicodedata.normalize('NFKC', text)`

**Prevention:** Implement encoding detection and normalization during content ingestion.

### Gotcha: API Rate Limiting
**Problem:** External API calls for validation trigger rate limits, causing intermittent failures.
**Symptoms:** Intermittent validation failures, especially during high-volume periods.
**Solution:**
1. Implement exponential backoff for retries
2. Add rate limiting to client requests
3. Cache results where appropriate
4. Use bulk validation APIs when available

### Gotcha: Authentication Token Expiry
**Problem:** Authentication tokens expire during long-running processes, causing validation failures.
**Symptoms:** Validation starts working then suddenly fails with authentication errors.
**Solution:**
1. Implement automatic token refresh
2. Check token validity before making requests
3. Handle authentication failures gracefully
4. Use short-lived tokens with refresh mechanisms

---

## 5. Exception Handling Issues

### Gotcha: Exception Approval Workflow Failures
**Problem:** Exception approval requests fail silently or don't reach the right people.
**Symptoms:** Users submit exception requests but get no response.
**Solution:**
1. Implement notification confirmations
2. Add escalation procedures for unresponded requests
3. Log all exception workflow steps
4. Provide status tracking for requestors

**Prevention:** Test exception workflows end-to-end before deployment.

### Gotcha: Temporary Exceptions Never Expire
**Problem:** Temporary exceptions remain active indefinitely after their intended expiration.
**Symptoms:** Policy violations continue to be allowed after exception period ends.
**Solution:**
1. Implement automatic expiration checks
2. Add cleanup jobs for expired exceptions
3. Log expiration events
4. Send notifications before expiration

### Gotcha: Overlapping Exception Rules
**Problem:** Multiple exception rules apply to the same situation, causing unpredictable behavior.
**Symptoms:** Inconsistent handling of similar situations.
**Solution:**
1. Establish rule precedence hierarchy
2. Validate for conflicts during rule updates
3. Document rule interaction patterns
4. Use rule grouping to manage dependencies

---

## 6. Audit and Logging Issues

### Gotcha: Sensitive Information in Logs
**Problem:** Audit logs contain sensitive information that shouldn't be stored.
**Symptoms:** Credentials, PII, or other sensitive data appears in logs.
**Solution:**
1. Implement log sanitization filters
2. Mask sensitive information before logging
3. Use structured logging with field filtering
4. Regularly audit log content for sensitive data

**Prevention:** Implement log sanitization as a core feature, not an afterthought.

### Gotcha: Log File Rotation Problems
**Problem:** Log files grow indefinitely or rotate at inappropriate times.
**Symptoms:** Disk space exhaustion, missing log data during critical periods.
**Solution:**
1. Implement proper log rotation with size/time limits
2. Use external log management systems
3. Monitor disk space usage
4. Set up alerts for log-related issues

### Gotcha: Incomplete Audit Trail
**Problem:** Important validation events are not logged, making compliance verification difficult.
**Symptoms:** Unable to prove compliance during audits, gaps in security monitoring.
**Solution:**
1. Define mandatory audit events
2. Implement comprehensive logging coverage
3. Regularly audit log completeness
4. Use log aggregation tools for analysis

---

## 7. Rule Management Issues

### Gotcha: Rule Syntax Errors
**Problem:** Invalid JSON syntax in rule files causes the entire system to fail.
**Symptoms:** System crashes or refuses to start, validation stops working.
**Solution:**
1. Validate rule syntax before applying: `python -m json.tool rules.json`
2. Implement rule validation during deployment
3. Maintain backup copies of working rules
4. Use version control for rule changes

**Prevention:** Implement automated syntax validation in CI/CD pipelines.

### Gotcha: Rule Ordering Dependencies
**Problem:** Rules have implicit dependencies on execution order, causing inconsistent results.
**Symptoms:** Validation results vary depending on internal implementation details.
**Solution:**
1. Make rule execution order explicit
2. Eliminate inter-rule dependencies where possible
3. Document any necessary ordering requirements
4. Test rule sets in different orders

### Gotcha: Performance Degradation with Many Rules
**Problem:** Adding many rules causes validation performance to degrade significantly.
**Symptoms:** Slower validation times, increased resource usage.
**Solution:**
1. Profile rule performance individually
2. Optimize expensive rules
3. Group related rules for efficiency
4. Consider rule hierarchies or categorization

---

## 8. Testing and Validation Issues

### Gotcha: Inadequate Test Coverage
**Problem:** Rules aren't tested with enough variety of content, leading to undetected issues.
**Symptoms:** Rules work in testing but fail in production with real content.
**Solution:**
1. Create comprehensive test suites with diverse content
2. Include edge cases and unusual patterns
3. Test with real-world examples
4. Regularly update test data

**Prevention:** Establish testing requirements for all new rules.

### Gotcha: Test Environment Differences
**Problem:** Test environment differs from production, causing issues that aren't caught.
**Symptoms:** Rules pass tests but fail in production.
**Solution:**
1. Mirror production environment as closely as possible
2. Use production-like data for testing
3. Implement canary deployments for new rules
4. Monitor for differences between environments