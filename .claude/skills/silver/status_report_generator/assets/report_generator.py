# Status Report Generator Skill

## Overview

**Skill Name:** `status_report_generator`
**Domain:** `silver`
**Purpose:** Generate automated, clear, and concise status reports in Markdown format for tasks, approvals, and project milestones, ensuring timely communication and accurate progress tracking.

**Core Capabilities:**
- Generate structured Markdown status reports from various data sources.
- Summarize task progress, blockers, and upcoming activities.
- Report on the status of approval requests and their lifecycle.
- Track project milestones, their completion status, and any deviations.
- Highlight critical issues, risks, and dependencies.
- Ensure accurate aggregation of data and inclusion of relevant timestamps.
- Handle missing updates or incomplete data gracefully.
- Support customizable report layouts and content sections.

**When to Use:**
- Weekly, bi-weekly, or monthly project status updates.
- Executive reporting on project health and progress.
- Stakeholder communications regarding key milestones and approvals.
- Daily stand-up or team sync reports.
- Automated generation for recurring reporting cycles.
- Documenting project history and progress over time.

**When NOT to Use:**
- Real-time interactive dashboards (use dedicated BI tools).
- Ad-hoc data analysis requiring deep drill-down capabilities.
- Storing raw, sensitive data directly in Markdown reports (reports should be summaries).
- Extremely detailed technical documentation (use dedicated documentation tools).
- For highly dynamic data that changes minute-to-minute (reports are snapshots).

---

## Impact Analysis

### Communication Impact: **CRITICAL**
-   **Accuracy Risk:** Inaccurate or outdated information misleads stakeholders and causes incorrect decisions.
-   **Clarity:** Vague or poorly organized reports lead to misunderstanding and rework.
-   **Completeness:** Missing critical updates (tasks, approvals, milestones) can result in missed deadlines or ignored risks.
-   **Timeliness:** Delayed reports make information irrelevant and reduce proactive decision-making.

### Business Impact: **HIGH**
-   **Decision Making:** Accurate and timely reports enable informed business and strategic decisions.
-   **Transparency:** Clear reporting fosters trust and alignment among project teams and stakeholders.
-   **Efficiency:** Automated generation saves significant manual effort, allowing teams to focus on core tasks.
-   **Risk Management:** Early identification and reporting of issues and risks help in timely mitigation.
-   **Accountability:** Provides a clear record of progress and accountability for deliverables.

### System Impact: **MEDIUM**
-   **Data Source Integration:** Requires robust and reliable connections to various project management, approval, and metric systems.
-   **Performance:** Report generation must be efficient, especially for large projects or frequent reporting.
-   **Template Maintenance:** Templates need to be flexible, easy to update, and maintain consistency across reports.
-   **Security:** Data extracted for reports must adhere to access controls and privacy policies; reports themselves should not expose sensitive raw data.

---

## Environment Variables

### Required Variables

```bash
# Report generation configuration
STATUS_REPORT_TEMPLATE_PATH="./templates/reports" # Template directory
STATUS_REPORT_OUTPUT_PATH="./reports"             # Output directory
STATUS_REPORT_DATA_SOURCE="json"                  # Data source type (e.g., json, yaml, api)

# Content preferences
STATUS_REPORT_DATE_FORMAT="%Y-%m-%d %H:%M:%S"     # Date format for reports
STATUS_REPORT_TIMEZONE="UTC"                      # Timezone for date/time sensitive data
```

### Optional Variables

```bash
# Advanced options
STATUS_REPORT_INCLUDE_TOC="true"                  # Generate table of contents
STATUS_REPORT_TOC_DEPTH="3"                       # TOC depth (1-6)
STATUS_REPORT_INCLUDE_MERMAID="true"              # Include Mermaid diagrams (e.g., for project timelines)

# Data fetching
STATUS_REPORT_API_ENDPOINT=""                     # API endpoint for fetching data
STATUS_REPORT_API_TOKEN=""                        # API token for authentication
STATUS_REPORT_FALLBACK_DATA_PATH="./fallback_data.json" # Local fallback data if API fails

# Styling and branding
STATUS_REPORT_LOGO_URL=""                         # URL to company logo in report header
STATUS_REPORT_THEME="default"                     # 'default', 'light', 'dark' (influences Mermaid)

# Validation and quality
STATUS_REPORT_MIN_SECTIONS="4"                    # Minimum sections required for a report
STATUS_REPORT_REQUIRE_MILESTONES="true"           # Require at least one milestone section
STATUS_REPORT_FAIL_ON_MISSING_DATA="true"         # If true, fail if required data is missing
STATUS_REPORT_WARN_ON_STALE_DATA="true"           # If true, add warning if data is older than X hours
STATUS_REPORT_STALE_DATA_THRESHOLD_HOURS="24"     # Threshold for stale data warning
```

---

## Network and Authentication Implications

### Local Generation Mode

**Primary Mode:** File-based data and template processing.

**Requirements:**
- Read access to local data files (JSON, YAML).
- Read access to template directory.
- Write access to output directory.
- No network dependencies (fully offline capable).

### Integrated Mode (Optional)

**For external data source integration (e.g., Jira, GitHub, internal APIs):**

```bash
# API Authentication
STATUS_REPORT_API_AUTH_TYPE="bearer"             # e.g., bearer, basic, api_key
STATUS_REPORT_API_USERNAME=""                    # For basic auth
STATUS_REPORT_API_PASSWORD=""                    # For basic auth

# External data sources
STATUS_REPORT_TASKS_API="https://jira.example.com/api"
STATUS_REPORT_APPROVALS_API="https://approvals.example.com/api"
STATUS_REPORT_MILESTONES_API="https://roadmap.example.com/api"
```

**Authentication Patterns:**
- **Bearer Token:** For modern REST APIs (recommended).
- **Basic Auth:** For legacy systems or internal tools.
- **API Key:** For simple service-to-service communication.
- **OAuth 2.0:** For complex delegated access (if external API supports).

### Network Patterns

**Pattern 1: Standalone (No Network)**
```bash
# Generates reports solely from local data files.
# Ideal for disconnected environments or pre-processed data.
```

**Pattern 2: Hybrid (Optional Network)**
```bash
# Fetches data from APIs, but uses local fallback data if network issues occur.
# Provides resilience and partial reporting capabilities.
```

**Pattern 3: Fully Integrated (Network Required)**
```bash
# Reliant on network connectivity to fetch real-time or near real-time data from external systems.
# Essential for up-to-the-minute reporting.
```

---

## Blueprints & Templates

### Template 1: Standard Project Status Report

**File:** `assets/report-template.md`

```markdown
---
title: {{REPORT_TITLE}}
date: {{REPORT_DATE}}
author: {{AUTHOR}}
project: {{PROJECT_NAME}}
version: 1.0.0
status: generated
---

# {{REPORT_TITLE}}
### For Project: {{PROJECT_NAME}}

## Executive Summary

{{EXECUTIVE_SUMMARY}}

{{STALE_DATA_WARNING}}

---

## Table of Contents

<!-- AUTO-GENERATED TOC -->

---

## 1. Overall Project Status

| Item        | Status    | RAG (Red/Amber/Green) | Comments / Trend |
|-------------|-----------|-----------------------|------------------|
| Scope       | {{SCOPE_STATUS}}      | {{SCOPE_RAG}}         | {{SCOPE_COMMENTS}}       |
| Schedule    | {{SCHEDULE_STATUS}}   | {{SCHEDULE_RAG}}      | {{SCHEDULE_COMMENTS}}    |
| Budget      | {{BUDGET_STATUS}}     | {{BUDGET_RAG}}        | {{BUDGET_COMMENTS}}      |
| Resources   | {{RESOURCES_STATUS}}  | {{RESOURCES_RAG}}     | {{RESOURCES_COMMENTS}}   |
| Quality     | {{QUALITY_STATUS}}    | {{QUALITY_RAG}}       | {{QUALITY_COMMENTS}}     |

### Key Highlights
- {{HIGHLIGHT_1}}
- {{HIGHLIGHT_2}}

### Key Lowlights
- {{LOWLIGHT_1}}
- {{LOWLIGHT_2}}

---

## 2. Recent Progress & Activities (Last Reporting Period)

- **{{ACTIVITY_DATE_1}}**: {{ACTIVITY_DESCRIPTION_1}}
- **{{ACTIVITY_DATE_2}}**: {{ACTIVITY_DESCRIPTION_2}}
- **{{ACTIVITY_DATE_3}}**: {{ACTIVITY_DESCRIPTION_3}}
{{OTHER_RECENT_ACTIVITIES}}

---

## 3. Upcoming Activities (Next Reporting Period)

- **{{UPCOMING_DATE_1}}**: {{UPCOMING_DESCRIPTION_1}}
- **{{UPCOMING_DATE_2}}**: {{UPCOMING_DESCRIPTION_2}}
- **{{UPCOMING_DATE_3}}**: {{UPCOMING_DESCRIPTION_3}}
{{OTHER_UPCOMING_ACTIVITIES}}

---

## 4. Task Status Update

### Open Tasks by Priority

| Priority | Count | Due This Week | Blocked Tasks | Owners   |
|----------|-------|---------------|---------------|----------|
| High     | {{HIGH_TASK_COUNT}} | {{HIGH_TASK_THIS_WEEK}} | {{HIGH_TASK_BLOCKED}} | {{HIGH_TASK_OWNERS}} |
| Medium   | {{MEDIUM_TASK_COUNT}} | {{MEDIUM_TASK_THIS_WEEK}} | {{MEDIUM_TASK_BLOCKED}} | {{MEDIUM_TASK_OWNERS}} |
| Low      | {{LOW_TASK_COUNT}} | {{LOW_TASK_THIS_WEEK}} | {{LOW_TASK_BLOCKED}} | {{LOW_TASK_OWNERS}} |

### Critical Blockers & Dependencies
- **Task ID: {{BLOCKER_TASK_ID_1}}**: {{BLOCKER_DESCRIPTION_1}} (Dependency: {{BLOCKER_DEPENDENCY_1}})
- **Task ID: {{BLOCKER_TASK_ID_2}}**: {{BLOCKER_DESCRIPTION_2}} (Dependency: {{BLOCKER_DEPENDENCY_2}})
{{OTHER_BLOCKERS}}

---

## 5. Approvals Status

### Pending Critical Approvals

| Request ID | Type         | Initiator   | Current Approver | Status    | Due Date   |
|------------|--------------|-------------|------------------|-----------|------------|
| {{APPROVE_ID_1}} | {{APPROVE_TYPE_1}} | {{APPROVE_INIT_1}} | {{APPROVE_APPROVER_1}} | {{APPROVE_STATUS_1}} | {{APPROVE_DUEDATE_1}} |
| {{APPROVE_ID_2}} | {{APPROVE_TYPE_2}} | {{APPROVE_INIT_2}} | {{APPROVE_APPROVER_2}} | {{APPROVE_STATUS_2}} | {{APPROVE_DUEDATE_2}} |
{{OTHER_PENDING_APPROVALS}}

---

## 6. Project Milestones

### Upcoming Milestones

| Milestone Name | Target Date | Status      | Comments                                 |
|----------------|-------------|-------------|------------------------------------------|
| {{MILESTONE_NAME_1}} | {{MILESTONE_DATE_1}} | {{MILESTONE_STATUS_1}} | {{MILESTONE_COMMENTS_1}} |
| {{MILESTONE_NAME_2}} | {{MILESTONE_DATE_2}} | {{MILESTONE_STATUS_2}} | {{MILESTONE_COMMENTS_2}} |
{{OTHER_UPCOMING_MILESTONES}}

### Recently Achieved Milestones

- **{{ACHIEVED_MILESTONE_1}}** (Achieved: {{ACHIEVED_DATE_1}}) - {{ACHIEVED_COMMENTS_1}}
- **{{ACHIEVED_MILESTONE_2}}** (Achieved: {{ACHIEVED_DATE_2}}) - {{ACHIEVED_COMMENTS_2}}
{{OTHER_ACHIEVED_MILESTONES}}

```mermaid
gantt
    dateFormat  YYYY-MM-DD
    title Project Timeline Overview
    section Phase 1
    Task A           :a1, 2026-01-01, 7d
    Task B           :after a1, 5d
    section Phase 2
    Task C           :2026-01-15, 12d
    Task D           :crit, after c1, 8d
```

---

## 7. Risks & Issues

### Top Risks

| Risk ID | Description                                     | Impact   | Probability | Mitigation Plan                    | Status   |
|---------|-------------------------------------------------|----------|-------------|------------------------------------|----------|
| {{RISK_ID_1}} | {{RISK_DESCRIPTION_1}} | {{RISK_IMPACT_1}} | {{RISK_PROBABILITY_1}} | {{RISK_MITIGATION_1}} | {{RISK_STATUS_1}} |
| {{RISK_ID_2}} | {{RISK_DESCRIPTION_2}} | {{RISK_IMPACT_2}} | {{RISK_PROBABILITY_2}} | {{RISK_MITIGATION_2}} | {{RISK_STATUS_2}} |
{{OTHER_RISKS}}

### Open Issues

- **Issue {{ISSUE_ID_1}}**: {{ISSUE_DESCRIPTION_1}} (Owner: {{ISSUE_OWNER_1}}, Due: {{ISSUE_DUE_1}})
- **Issue {{ISSUE_ID_2}}**: {{ISSUE_DESCRIPTION_2}} (Owner: {{ISSUE_OWNER_2}}, Due: {{ISSUE_DUE_2}})
{{OTHER_ISSUES}}

---

## Action Items for Next Period

- **Action 1:** {{ACTION_ITEM_1}}
- **Action 2:** {{ACTION_ITEM_2}}
- **Action 3:** {{ACTION_ITEM_3}}
{{OTHER_ACTION_ITEMS}}

---

## Appendices

### Contact Information
- **Project Manager:** {{PM_NAME}} ({{PM_EMAIL}})
- **Technical Lead:** {{TL_NAME}} ({{TL_EMAIL}})
{{OTHER_CONTACTS}}

---

## Report Details

**Generated By:** Status Report Generator Skill
**Source Data Last Updated:** {{DATA_LAST_UPDATED}}
**Report Generation Time:** {{REPORT_GENERATION_TIME}}
```

### Template 2: Python Report Generator

**File:** `assets/report_generator.py`

```python
#!/usr/bin/env python3
"""
report_generator.py
Generates Markdown status reports from structured data.
"""

import os
import json
import yaml
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates Markdown status reports."""

    def __init__(self,
                 template_path: Optional[Path] = None,
                 output_path: Optional[Path] = None):

        self.template_path = template_path or Path(os.getenv('STATUS_REPORT_TEMPLATE_PATH', './templates/reports'))
        self.output_path = output_path or Path(os.getenv('STATUS_REPORT_OUTPUT_PATH', './reports'))
        self.data_source_type = os.getenv('STATUS_REPORT_DATA_SOURCE', 'json').lower()

        self.output_path.mkdir(parents=True, exist_ok=True)

        self.report_date_format = os.getenv('STATUS_REPORT_DATE_FORMAT', '%Y-%m-%d %H:%M:%S')
        self.timezone = os.getenv('STATUS_REPORT_TIMEZONE', 'UTC')
        self.include_toc = os.getenv('STATUS_REPORT_INCLUDE_TOC', 'true').lower() == 'true'
        self.toc_depth = int(os.getenv('STATUS_REPORT_TOC_DEPTH', '3'))
        self.include_mermaid = os.getenv('STATUS_REPORT_INCLUDE_MERMAID', 'true').lower() == 'true'
        self.fail_on_missing_data = os.getenv('STATUS_REPORT_FAIL_ON_MISSING_DATA', 'true').lower() == 'true'
        self.warn_on_stale_data = os.getenv('STATUS_REPORT_WARN_ON_STALE_DATA', 'true').lower() == 'true'
        self.stale_data_threshold_hours = int(os.getenv('STATUS_REPORT_STALE_DATA_THRESHOLD_HOURS', '24'))

        logger.info("ReportGenerator initialized.")

    def _load_template(self, template_name: str = "report-template.md") -> str:
        """Loads a Markdown template file."""
        template_file = self.template_path / template_name
        if not template_file.exists():
            logger.error(f"Template file not found: {template_file}, tried: {self.template_path.absolute()}")
            raise FileNotFoundError(f"Template file not found: {template_file}")
        with open(template_file, 'r') as f:
            return f.read()

    def _load_data(self, data_file: Path) -> Dict[str, Any]:
        """Loads data from a JSON or YAML file."""
        if not data_file.exists():
            logger.warning(f"Data file not found: {data_file}")
            if self.fail_on_missing_data:
                raise FileNotFoundError(f"Required data file not found: {data_file}")
            return {}

        try:
            if data_file.suffix == '.json':
                with open(data_file, 'r') as f:
                    return json.load(f)
            elif data_file.suffix in ('.yaml', '.yml'):
                with open(data_file, 'r') as f:
                    return yaml.safe_load(f)
            else:
                logger.error(f"Unsupported data file type: {data_file.suffix}")
                raise ValueError(f"Unsupported data file type: {data_file.suffix}")
        except Exception as e:
            logger.error(f"Error loading data from {data_file}: {e}")
            if self.fail_on_missing_data:
                raise
            return {}

    def _generate_stale_data_warning(self, data: Dict[str, Any]) -> str:
        """Generates a warning if source data is stale."""
        if not self.warn_on_stale_data:
            return ""

        data_last_updated_str = data.get('DATA_LAST_UPDATED')
        if not data_last_updated_str:
            return ""

        try:
            data_last_updated = datetime.fromisoformat(data_last_updated_str.replace('Z', '+00:00')) # Handle Z for UTC
            now = datetime.utcnow()
            
            if (now - data_last_updated) > timedelta(hours=self.stale_data_threshold_hours):
                return (
                    f"
**WARNING:** The data in this report was last updated on "
                    f"{data_last_updated_str} and is older than {self.stale_data_threshold_hours} hours. "
                    f"Information may be outdated.
"
                )
        except ValueError as e:
            logger.warning(f"Could not parse DATA_LAST_UPDATED '{data_last_updated_str}': {e}")
        return ""

    def _populate_template(self, template_content: str, data: Dict[str, Any]) -> str:
        """Populates the Markdown template with data."""
        # Common placeholders
        data['REPORT_DATE'] = datetime.now().strftime(self.report_date_format)
        data['AUTHOR'] = os.getenv('USER', 'Gemini CLI') # Default author
        data['REPORT_GENERATION_TIME'] = datetime.now().strftime(self.report_date_format)
        data['STALE_DATA_WARNING'] = self._generate_stale_data_warning(data)


        populated_content = template_content
        for key, value in data.items():
            placeholder = '{{' + key.upper() + '}}'
            if isinstance(value, (str, int, float, bool)):
                populated_content = populated_content.replace(placeholder, str(value))
            elif isinstance(value, list):
                # Basic handling for lists - join with newline or format as table rows
                if key.upper().endswith('_TABLE'): # Assuming tables are already formatted as rows
                    list_content = "
".join(value)
                else: # Generic list item rendering
                    list_content = "
".join([f"- {item}" for item in value]) # Or customize further
                populated_content = populated_content.replace(placeholder, list_content)
            elif isinstance(value, dict):
                # Simple dict to string conversion, might need more sophisticated handling
                populated_content = populated_content.replace(placeholder, json.dumps(value, indent=2))
            
        # Remove any remaining {{PLACEHOLDER}} that weren't populated
        # Replace with empty string or 'N/A' based on preference
        populated_content = re.sub(r'\{\{.*?\}\}', 'N/A', populated_content)

        return populated_content

    def generate_report(self, data_file: Path, output_filename: Optional[str] = None) -> Path:
        """Generates a status report Markdown file."""
        logger.info(f"Generating report for data file: {data_file}")

        try:
            template_content = self._load_template()
            data = self._load_data(data_file)
            
            self._validate_data(data)

            populated_markdown = self._populate_template(template_content, data)

            if self.include_toc:
                populated_markdown = self._add_table_of_contents(populated_markdown)
            if not self.include_mermaid:
                populated_markdown = re.sub(r'```mermaid.*?```', '', populated_markdown, flags=re.DOTALL)

            output_filename = output_filename or f"status-report-{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
            output_file = self.output_path / output_filename

            with open(output_file, 'w') as f:
                f.write(populated_markdown)

            logger.info(f"Status report successfully generated: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            raise

    def _add_table_of_contents(self, markdown_content: str) -> str:
        """Adds a simple Table of Contents to the Markdown content."""
        lines = markdown_content.split('
')
        toc_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
            
            if not in_code_block and (line.startswith('# ') or line.startswith('## ') or line.startswith('### ')):
                level = line.count('#')
                title = line.lstrip('# ').strip()
                slug = re.sub(r'[^\w\s-]', '', title.lower().replace(' ', '-'))
                
                if level <= self.toc_depth:
                    # Adjust indentation based on header level
                    indentation = '  ' * (level - 1) 
                    toc_lines.append(f"{indentation}- [{title}](#{slug})")

        toc_section_index = -1
        try:
            # Find the <!-- AUTO-GENERATED TOC --> placeholder
            for i, line in enumerate(lines):
                if "<!-- AUTO-GENERATED TOC -->" in line:
                    toc_section_index = i
                    break
        except ValueError:
            return markdown_content # No TOC placeholder found

        if toc_section_index != -1:
            # Insert TOC and ensure proper spacing
            new_lines = lines[:toc_section_index] + toc_lines + [''] + lines[toc_section_index+1:]
            return '
'.join(new_lines)
        return markdown_content


    def _validate_data(self, data: Dict[str, Any]):
        """Validates essential data for report generation."""
        if self.fail_on_missing_data:
            if not data.get('REPORT_TITLE'):
                raise ValueError("Missing required data: REPORT_TITLE")
            if not data.get('PROJECT_NAME'):
                raise ValueError("Missing required data: PROJECT_NAME")
            if not data.get('EXECUTIVE_SUMMARY'):
                raise ValueError("Missing required data: EXECUTIVE_SUMMARY")
            
            min_sections = int(os.getenv('STATUS_REPORT_MIN_SECTIONS', '4'))
            # This is a very rough check, ideally we'd check parsed markdown sections
            # For now, just ensure a reasonable number of top-level data elements are present
            if len(data.keys()) < min_sections:
                 logger.warning(f"Data object has fewer than {min_sections} top-level keys, consider adding more sections for a comprehensive report.")

            if os.getenv('STATUS_REPORT_REQUIRE_MILESTONES', 'true').lower() == 'true':
                if not (data.get('MILESTONE_NAME_1') or data.get('OTHER_UPCOMING_MILESTONES') or data.get('ACHIEVED_MILESTONE_1') or data.get('OTHER_ACHIEVED_MILESTONES')):
                    logger.warning("STATUS_REPORT_REQUIRE_MILESTONES is true, but no primary milestone data found.")
        
# Example usage
if __name__ == "__main__":
    # Setup environment variables for demonstration
    script_dir = Path(__file__).parent
    os.environ['STATUS_REPORT_TEMPLATE_PATH'] = str(script_dir) # points to current directory for template
    
    # Create a temporary output directory for the example
    example_output_dir = script_dir / "example_output"
    os.environ['STATUS_REPORT_OUTPUT_PATH'] = str(example_output_dir)
    os.makedirs(example_output_dir, exist_ok=True)

    os.environ['STATUS_REPORT_FAIL_ON_MISSING_DATA'] = 'false' # Allow generation even if data is incomplete
    os.environ['STATUS_REPORT_WARN_ON_STALE_DATA'] = 'true'
    os.environ['STATUS_REPORT_STALE_DATA_THRESHOLD_HOURS'] = '1' # Set to 1 hour for quick testing

    generator = ReportGenerator()

    # Create a dummy data file for demonstration in the example_output_dir
    dummy_data = {
        "REPORT_TITLE": "Weekly Project Alpha Status Report",
        "PROJECT_NAME": "Project Alpha",
        "EXECUTIVE_SUMMARY": "Project Alpha is progressing according to schedule. We have completed 80% of Phase 1 tasks. A critical blocker related to external API integration has been identified and is being actively addressed. Overall project health is Green, but schedule risk is Amber due to the blocker.",
        "DATA_LAST_UPDATED": (datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z", # Example stale data
        "SCOPE_STATUS": "Stable", "SCOPE_RAG": "Green", "SCOPE_COMMENTS": "No changes to scope.",
        "SCHEDULE_STATUS": "Minor Delay", "SCHEDULE_RAG": "Amber", "SCHEDULE_COMMENTS": "External API dependency causing 2-day delay.",
        "BUDGET_STATUS": "On Track", "BUDGET_RAG": "Green", "BUDGET_COMMENTS": "Within allocated budget.",
        "RESOURCES_STATUS": "Sufficient", "RESOURCES_RAG": "Green", "RESOURCES_COMMENTS": "Team fully staffed.",
        "QUALITY_STATUS": "High", "QUALITY_RAG": "Green", "QUALITY_COMMENTS": "No critical bugs found in QA.",
        "HIGHLIGHT_1": "Completed Module X development and testing.",
        "HIGHLIGHT_2": "Successfully integrated with Payment Gateway V2.",
        "LOWLIGHT_1": "Identified critical blocker with Partner API integration.",
        "LOWLIGHT_2": "Two team members on unplanned leave for 3 days.",
        "ACTIVITY_DATE_1": "2026-02-03", "ACTIVITY_DESCRIPTION_1": "Finalized Module X code review.",
        "ACTIVITY_DATE_2": "2026-02-04", "ACTIVITY_DESCRIPTION_2": "Began integration testing for Module Y.",
        "ACTIVITY_DATE_3": "2026-02-05", "ACTIVITY_DESCRIPTION_3": "Met with external vendor for API discussion.",
        "UPCOMING_DATE_1": "2026-02-10", "UPCOMING_DESCRIPTION_1": "Target completion for Module Y integration.",
        "UPCOMING_DATE_2": "2026-02-12", "UPCOMING_DESCRIPTION_2": "Kick-off meeting for Phase 2 planning.",
        "UPCOMING_DATE_3": "2026-02-15", "UPCOMING_DESCRIPTION_3": "Internal demo of new features.",
        "HIGH_TASK_COUNT": "3", "HIGH_TASK_THIS_WEEK": "2", "HIGH_TASK_BLOCKED": "1", "HIGH_TASK_OWNERS": "Alice, Bob",
        "MEDIUM_TASK_COUNT": "7", "MEDIUM_TASK_THIS_WEEK": "4", "MEDIUM_TASK_BLOCKED": "0", "MEDIUM_TASK_OWNERS": "Team Alpha",
        "LOW_TASK_COUNT": "5", "LOW_TASK_THIS_WEEK": "3", "LOW_TASK_BLOCKED": "0", "LOW_TASK_OWNERS": "Team Alpha",
        "BLOCKER_TASK_ID_1": "TASK-456", "BLOCKER_DESCRIPTION_1": "Awaiting API Keys from Partner", "BLOCKER_DEPENDENCY_1": "Partner Co. API",
        "APPROVE_ID_1": "APP-007", "APPROVE_TYPE_1": "Prod Deployment", "APPROVE_INIT_1": "DevOps", "APPROVE_APPROVER_1": "Security Lead", "APPROVE_STATUS_1": "Pending", "APPROVE_DUEDATE_1": "2026-02-08",
        "MILESTONE_NAME_1": "Phase 1 Completion", "MILESTONE_DATE_1": "2026-02-20", "MILESTONE_STATUS_1": "On Track", "MILESTONE_COMMENTS_1": "All tasks for Phase 1 are progressing.",
        "ACHIEVED_MILESTONE_1": "Feature X Go-Live", "ACHIEVED_DATE_1": "2026-01-30", "ACHIEVED_COMMENTS_1": "Successfully launched Feature X to production.",
        "RISK_ID_1": "RISK-001", "RISK_DESCRIPTION_1": "External API integration delays", "RISK_IMPACT_1": "High", "RISK_PROBABILITY_1": "Medium", "RISK_MITIGATION_1": "Escalate to partner management; explore alternatives.", "RISK_STATUS_1": "Active",
        "ISSUE_ID_1": "ISSUE-003", "ISSUE_DESCRIPTION_1": "Unexpected downtime in Staging environment", "ISSUE_OWNER_1": "SRE Team", "ISSUE_DUE_1": "2026-02-07",
        "ACTION_ITEM_1": "Follow up with Partner Co. on API key delivery.",
        "ACTION_ITEM_2": "Conduct root cause analysis for Staging downtime.",
        "PM_NAME": "Jane Doe", "PM_EMAIL": "jane.doe@example.com",
        "TL_NAME": "John Smith", "TL_EMAIL": "john.smith@example.com"
    }
    
    dummy_data_file = example_output_dir / 'example-report-data.json'
    with open(dummy_data_file, 'w') as f:
        json.dump(dummy_data, f, indent=2)

    # Generate report
    output_file = generator.generate_report(dummy_data_file, "project-alpha-weekly-status.md")
    print(f"
Generated report example: {output_file}")
    
    # Clean up dummy data and output directory
    os.remove(dummy_data_file)
    os.remove(output_file)
    os.rmdir(example_output_dir)
