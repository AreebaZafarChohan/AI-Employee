# Status Report Generator Skill Manifest

This document outlines the components, structure, and usage of the `status_report_generator` skill.

## Skill Details

*   **Skill Name:** `status_report_generator`
*   **Domain:** `silver`
*   **Purpose:** Generate automated Markdown status reports for tasks, approvals, and project milestones.
*   **Version:** 1.0.0

## Directory Structure

```
.
├── README.md                 # Quick start guide and overview
├── SKILL.md                  # Comprehensive skill specification
├── assets/                   # Templates and core logic
│   ├── report-template.md    # Main Markdown report template
│   ├── report_generator.py   # Python script for report generation
│   ├── example-report-data.json # Example data for report generation
│   └── MANIFEST.md           # This manifest file
└── docs/                     # Supporting documentation
    ├── gotchas.md            # Common pitfalls and troubleshooting
    ├── impact-checklist.md   # Impact assessment guide
    └── patterns.md           # Status report generation patterns and best practices
```

## Core Components

### `report_generator.py`

*   **Description:** A Python script responsible for taking structured data (JSON/YAML) and populating a Markdown template (`report-template.md`) to produce the final status report.
*   **Functionality:**
    *   Loads templates and data files.
    *   Performs string replacement for placeholders.
    *   Includes data validation and handles missing data gracefully.
    *   Generates a warning for stale data based on a configurable threshold.
    *   Can optionally generate a Table of Contents.
    *   Can optionally remove Mermaid diagrams.
*   **Usage:** `python report_generator.py <data_file.json> [output_filename.md]`

### `report-template.md`

*   **Description:** The primary Markdown template that defines the structure and layout of the generated status reports. It contains placeholders (e.g., `{{REPORT_TITLE}}`) that are replaced by data from the `report_generator.py` script.
*   **Sections:** Includes sections for Executive Summary, Overall Project Status (RAG), Recent/Upcoming Activities, Task Status, Approvals, Project Milestones, Risks & Issues, and Action Items.
*   **Visualizations:** Integrates Mermaid syntax for basic diagrams (e.g., Gantt charts for timelines).

### `example-report-data.json`

*   **Description:** A sample JSON file demonstrating the expected data structure for generating a status report. It includes example values for all common placeholders used in `report-template.md`.
*   **Purpose:** Serves as a reference for users to understand how to structure their input data and for testing the `report_generator.py` script.

## Documentation

*   **`SKILL.md`:** Detailed specification covering overview, impact analysis, environment variables, network implications, blueprints, validation checklist, and anti-patterns.
*   **`README.md`:** A concise overview of the skill, quick start instructions, and key features.
*   **`docs/patterns.md`:** Explores different patterns and strategies for effective status report generation, including types of reports and best practices.
*   **`docs/impact-checklist.md`:** A checklist to assess the impact of status report generation on various aspects (e.g., communication, business, operational).
*   **`docs/gotchas.md`:** Highlights common issues, anti-patterns, and troubleshooting tips related to generating and using Markdown status reports.

## Environment Variables

Refer to `SKILL.md` for a comprehensive list of required and optional environment variables that configure the behavior of the `status_report_generator` skill, including template paths, output paths, data sources, and formatting preferences.

## Anti-Patterns

Refer to `SKILL.md` and `docs/gotchas.md` for detailed descriptions of anti-patterns to avoid when creating and using status reports, such as incomplete reports, hardcoding values, and ignoring dependencies.

## Validation

The skill includes internal validation checks within `report_generator.py` to ensure data completeness and structure. A comprehensive `Validation Checklist` is provided in `SKILL.md` to guide users in assessing the quality and accuracy of generated status reports.

---
**Last Updated:** 2026-02-06
**Maintained by:** Silver Team
