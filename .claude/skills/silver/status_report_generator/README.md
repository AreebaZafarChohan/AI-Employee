# Status Report Generator Skill

**Domain:** `silver`
**Version:** 1.0.0
**Status:** Production Ready

## Quick Start

Generate automated, clear, and concise status reports in Markdown format for tasks, approvals, and project milestones.

### Prerequisites

```bash
# Set required environment variables
export STATUS_REPORT_TEMPLATE_PATH="./assets"
export STATUS_REPORT_OUTPUT_PATH="./reports"
export STATUS_REPORT_DATA_SOURCE="json"
```

### Basic Usage

**Python:**
```python
from report_generator import ReportGenerator
from pathlib import Path
import json
from datetime import datetime, timedelta

generator = ReportGenerator()

# Example data
dummy_data = {
    "REPORT_TITLE": "Weekly Project Omega Status",
    "PROJECT_NAME": "Project Omega",
    "EXECUTIVE_SUMMARY": "Project Omega is progressing well. Phase 1 completed.",
    "DATA_LAST_UPDATED": (datetime.utcnow() - timedelta(minutes=30)).isoformat() + "Z",
    "SCOPE_STATUS": "Stable", "SCOPE_RAG": "Green", "SCOPE_COMMENTS": "No changes.",
    "SCHEDULE_STATUS": "On Track", "SCHEDULE_RAG": "Green", "SCHEDULE_COMMENTS": "Ahead of schedule.",
    "HIGHLIGHT_1": "Completed critical module X.",
    "UPCOMING_DATE_1": "2026-02-15", "UPCOMING_DESCRIPTION_1": "Begin Phase 2 planning.",
    "HIGH_TASK_COUNT": "1", "HIGH_TASK_THIS_WEEK": "1", "HIGH_TASK_BLOCKED": "0", "HIGH_TASK_OWNERS": "Alice",
    "MILESTONE_NAME_1": "Phase 1 Completion", "MILESTONE_DATE_1": "2026-02-05", "MILESTONE_STATUS_1": "Completed", "MILESTONE_COMMENTS_1": "Ahead of schedule."
}

# Create dummy data file
output_dir = Path("./reports_output")
output_dir.mkdir(parents=True, exist_ok=True)
dummy_data_file = output_dir / 'example-data.json'
with open(dummy_data_file, 'w') as f:
    json.dump(dummy_data, f, indent=2)

# Generate report
os.environ['STATUS_REPORT_TEMPLATE_PATH'] = './assets' # Ensure template path is correct for execution
os.environ['STATUS_REPORT_OUTPUT_PATH'] = str(output_dir)
os.environ['STATUS_REPORT_FAIL_ON_MISSING_DATA'] = 'false'
output_file = generator.generate_report(dummy_data_file, "project-omega-weekly-status.md")
print(f"Generated report: {output_file}")
```

## Documentation Structure

-   **[SKILL.md](./SKILL.md)** - Complete specification (1,000+ lines)
-   **[docs/patterns.md](./docs/patterns.md)** - Status report generation strategies
-   **[docs/impact-checklist.md](./docs/impact-checklist.md)** - Quality assessment
-   **[docs/gotchas.md](./docs/gotchas.md)** - Common pitfalls

## Asset Templates

-   `assets/report-template.md` - Main Markdown template for reports
-   `assets/report_generator.py` - Python script for report generation
-   `assets/example-report-data.json` - Example JSON data for reports

## Key Features

✅ **Automated Generation**
-   Produces structured reports from data sources.
-   Reduces manual effort for recurring reports.

✅ **Comprehensive Reporting**
-   Summarizes tasks, approvals, and project milestones.
-   Highlights critical issues, risks, and dependencies.

✅ **Data Integrity & Timeliness**
-   Ensures accurate data aggregation.
-   Includes timestamps and warns on stale data.

✅ **Customizable**
-   Flexible templates for various reporting needs.
-   Supports multiple data sources (JSON, YAML).

## Anti-Patterns to Avoid

❌ Incomplete reports with missing crucial information.
❌ Hardcoding values instead of dynamically pulling data.
❌ Ignoring dependencies or critical blockers.
❌ Lack of timestamps or stale data warnings.

See [SKILL.md](./SKILL.md#anti-patterns) for detailed examples.

---

**Maintained by:** Silver Team
**Last Updated:** 2026-02-06
**License:** Internal Use Only
