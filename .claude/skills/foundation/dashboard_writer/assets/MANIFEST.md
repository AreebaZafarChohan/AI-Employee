# Dashboard Writer Skill Manifest

This document outlines the components, structure, and usage of the `dashboard_writer` skill.

## Skill Details

*   **Skill Name:** `dashboard_writer`
*   **Domain:** `foundation`
*   **Purpose:** Generate Markdown-based dashboard summaries for various reporting needs.
*   **Version:** 1.0.0

## Directory Structure

```
.
├── README.md                 # Quick start guide and overview
├── SKILL.md                  # Comprehensive skill specification
├── assets/                   # Templates and core logic
│   ├── dashboard-template.md # Main Markdown dashboard template
│   ├── dashboard_generator.py # Python script for dashboard generation
│   ├── example-dashboard-data.json # Example data for dashboard generation
│   └── MANIFEST.md           # This manifest file
└── docs/                     # Supporting documentation
    ├── gotchas.md            # Common pitfalls and troubleshooting
    ├── impact-checklist.md   # Impact assessment guide
    └── patterns.md           # Dashboard generation patterns and best practices
```

## Core Components

### `dashboard_generator.py`

*   **Description:** A Python script responsible for taking structured data (JSON/YAML) and populating a Markdown template (`dashboard-template.md`) to produce the final dashboard summary.
*   **Functionality:**
    *   Loads templates and data files.
    *   Performs simple string replacement for placeholders.
    *   Includes basic data validation.
    *   Can optionally generate a Table of Contents.
    *   Can optionally remove Mermaid blocks if `DASHBOARD_INCLUDE_MERMAID` is `false`.
*   **Usage:** `python dashboard_generator.py <data_file.json> [output_filename.md]`

### `dashboard-template.md`

*   **Description:** The primary Markdown template that defines the structure and layout of the generated dashboards. It contains placeholders (e.g., `{{DASHBOARD_TITLE}}`) that are replaced by data from the `dashboard_generator.py` script.
*   **Sections:** Includes sections for Executive Summary, Key Metrics, Task Overview, Approval Requests, Action Items, and Recommendations.
*   **Visualizations:** Integrates Mermaid syntax for basic diagrams (e.g., pie charts, flowcharts).

### `example-dashboard-data.json`

*   **Description:** A sample JSON file demonstrating the expected data structure for generating a dashboard. It includes example values for all common placeholders used in `dashboard-template.md`.
*   **Purpose:** Serves as a reference for users to understand how to structure their input data and for testing the `dashboard_generator.py` script.

## Documentation

*   **`SKILL.md`:** Detailed specification covering overview, impact analysis, environment variables, network implications, blueprints, validation checklist, and anti-patterns.
*   **`README.md`:** A concise overview of the skill, quick start instructions, and key features.
*   **`docs/patterns.md`:** Explores different patterns and strategies for effective dashboard generation, including data aggregation, visualization choices, and reporting cycles.
*   **`docs/impact-checklist.md`:** A checklist to assess the impact of dashboard reporting on various aspects (e.g., business, operational, technical).
*   **`docs/gotchas.md`:** Highlights common issues, anti-patterns, and troubleshooting tips related to generating and using Markdown dashboards.

## Environment Variables

Refer to `SKILL.md` for a comprehensive list of required and optional environment variables that configure the behavior of the `dashboard_writer` skill, including template paths, output paths, data sources, and formatting preferences.

## Anti-Patterns

Refer to `SKILL.md` and `docs/gotchas.md` for detailed descriptions of anti-patterns to avoid when creating and using dashboards, such as hardcoding data, ignoring errors, and unclear reporting.

## Validation

The skill includes internal validation checks within `dashboard_generator.py` to ensure data completeness and structure. A comprehensive `Validation Checklist` is provided in `SKILL.md` to guide users in assessing the quality and accuracy of generated dashboards.

---
**Last Updated:** 2026-02-06
**Maintained by:** Foundation Team
