# Plan MD Generator - Common Gotchas & Troubleshooting

## Overview
Common mistakes and troubleshooting guidance for plan generation.

---

## 1. Content Issues

### Gotcha: Vague Instructions Without Commands

**Symptom:**
Steps say "configure the system" without specifics.

**Problem:**
```markdown
### Step 1: Set up the environment
1. Install dependencies
2. Configure the application
3. Start the server
```

**Solution:**
```markdown
### Step 1.1: Set up Python Environment
**Actions:**
1. Install Python 3.9: `sudo apt install python3.9`
2. Create virtual environment: `python3.9 -m venv venv`
3. Activate environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy config template: `cp config.example.yaml config.yaml`
6. Edit config: Set `DATABASE_URL` in config.yaml
7. Start server: `python app.py`

**Verification:**
```bash
curl http://localhost:8000/health
# Expected: {"status": "ok"}
```
```

---

### Gotcha: Missing Acceptance Criteria

**Symptom:**
No way to verify step completion.

**Solution:**
Always include specific, testable criteria:
```markdown
**Acceptance Criteria:**
- [ ] Application starts without errors
- [ ] Health endpoint returns 200 OK
- [ ] Database connection successful
- [ ] Logs show "Server started on port 8000"
```

---

## 2. Dependency Problems

### Gotcha: Circular Dependencies

**Symptom:**
Step A depends on B, B depends on C, C depends on A.

**Detection:**
```python
def detect_cycles(steps):
    """Detect circular dependencies"""
    visited = set()
    path = set()

    def dfs(step_id):
        if step_id in path:
            return True  # Cycle detected
        if step_id in visited:
            return False

        visited.add(step_id)
        path.add(step_id)

        step = steps[step_id]
        for dep in step.dependencies:
            if dfs(dep):
                return True

        path.remove(step_id)
        return False

    return any(dfs(sid) for sid in steps.keys())
```

**Solution:**
Review dependency graph and break cycles by reordering or splitting steps.

---

### Gotcha: Wrong Dependency Order

**Symptom:**
Database migration runs before database is created.

**Solution:**
```markdown
Correct order:
Step 1.1: Create database
Step 1.2: Run migrations (depends on 1.1)
Step 1.3: Deploy app (depends on 1.2)
```

---

## 3. Link and Reference Issues

### Gotcha: Broken Relative Links

**Symptom:**
Links work in development but break when plan is moved.

**Problem:**
```markdown
[API Doc](../api/spec.md)
```

**Solution:**
Use repository-relative paths or absolute URLs:
```markdown
[API Doc](/docs/api/spec.md) - From repository root
[API Doc](https://docs.example.com/api) - Absolute URL
```

---

## 4. Format Issues

### Gotcha: Inconsistent Heading Levels

**Problem:**
```markdown
# Plan Title
### Step 1 (skipped ##)
## Step 2 (inconsistent)
```

**Solution:**
```markdown
# Plan Title
## Phase 1
### Step 1.1
### Step 1.2
## Phase 2
### Step 2.1
```

---

## 5. Technical Accuracy

### Gotcha: Untested Commands

**Symptom:**
Commands in plan don't actually work.

**Solution:**
Always test commands before including:
```bash
# Test in clean environment
docker run -it ubuntu:20.04 bash
# Run each command and verify output
```

---

## Quick Reference: Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Missing acceptance criteria" | Step has no criteria | Add testable criteria |
| "Circular dependency detected" | Step depends on itself | Break cycle |
| "Link validation failed" | Broken URL | Fix or remove link |
| "Invalid Markdown syntax" | Format error | Run linter |
| "Step too vague" | No specific actions | Add commands/examples |

---

**Last Updated:** 2026-02-06
