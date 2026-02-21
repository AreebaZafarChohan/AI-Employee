# Dashboard Writer Skill

**Domain:** `foundation`
**Version:** 1.0.0
**Status:** Production Ready

## Quick Start

Generate clear, concise, and structured Markdown-based dashboard summaries for tasks, approvals, and metrics.

### Prerequisites

```bash
# Set required environment variables
export DASHBOARD_TEMPLATE_PATH="./assets"
export DASHBOARD_OUTPUT_PATH="./dashboards"
export DASHBOARD_DATA_SOURCE="json"
```

### Basic Usage

**Python:**
```python
from dashboard_generator import DashboardGenerator
from pathlib import Path
import json

generator = DashboardGenerator()

# Example data
dummy_data = {
    "DASHBOARD_TITLE": "Weekly Project Status",
    "EXECUTIVE_SUMMARY": "Project is on track.",
    "METRIC_1": "Uptime", "VALUE_1": "99.9%", "TREND_1": "Stable", "STATUS_1": "Green",
    "HIGH_TASK_COUNT": "2", "HIGH_TASK_ASSIGNEE": "Alice", "HIGH_TASK_DUEDATE": "2026-02-10",
    "DATA_LAST_UPDATED": "2026-02-06 17:30:00 UTC"
}

# Create dummy data file
dummy_data_file = Path('./output/example-data.json')
dummy_data_file.parent.mkdir(parents=True, exist_ok=True)
with open(dummy_data_file, 'w') as f:
    json.dump(dummy_data, f, indent=2)

# Generate dashboard
output_file = generator.generate_dashboard(dummy_data_file, "weekly-report.md")
print(f"Generated dashboard: {output_file}")
```

## Documentation Structure

- **[SKILL.md](./SKILL.md)** - Complete specification (1,000+ lines)
- **[docs/patterns.md](./docs/patterns.md)** - Dashboard generation strategies
- **[docs/impact-checklist.md](./docs/impact-checklist.md)** - Quality assessment
- **[docs/gotchas.md](./docs/gotchas.md)** - Common pitfalls

## Asset Templates

- `assets/dashboard-template.md` - Markdown dashboard template
- `assets/dashboard_generator.py` - Python dashboard generation engine
- `assets/example-dashboard-data.json` - Example JSON data for dashboards

## Key Features

✅ **Structured Format**
- YAML front matter metadata
- Hierarchical sections for tasks, metrics, approvals
- Mermaid diagrams for visualizations
- Automatic table of contents

✅ **Data Consistency**
- Ensures data integrity across various sections
- Handles missing data gracefully with fallbacks
- Customizable validation rules

✅ **Comprehensive Summaries**
- Clear executive summaries
- Detailed task overviews (priority, assignee, due date)
- Approval request tracking
- Actionable recommendations

✅ **Customizable**
- Flexible templates for different reporting needs
- Support for multiple data sources (JSON, YAML)
- Configurable environment variables for behavior

## Anti-Patterns to Avoid

❌ Hardcoding data within templates
❌ Skipping audit information for generated reports
❌ Ignoring errors or missing data points
❌ Generating ambiguous or unclear dashboards

See [SKILL.md](./SKILL.md#anti-patterns) for detailed examples.

---

**Maintained by:** Foundation Team
**Last Updated:** 2026-02-06
**License:** Internal Use Only
