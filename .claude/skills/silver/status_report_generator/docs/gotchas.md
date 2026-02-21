# Status Report Generator - Common Gotchas & Troubleshooting

## Overview
This document outlines common pitfalls, anti-patterns, and troubleshooting tips encountered when generating Markdown status reports using the `status_report_generator` skill.

---

## 1. Data-Related Issues

### Gotcha: Stale Data Not Detected or Warning Not Displayed

**Symptom:**
Reports are generated with old data, but no warning is present, or the warning is displayed incorrectly.

**Problem:**
-   `DATA_LAST_UPDATED` field is missing or malformed in the input data.
-   `STATUS_REPORT_WARN_ON_STALE_DATA` is `false`.
-   `STATUS_REPORT_STALE_DATA_THRESHOLD_HOURS` is set too high or too low.
-   Timestamp format in `DATA_LAST_UPDATED` doesn't match `datetime.fromisoformat` expectations (e.g., missing timezone info for `Z` suffix).

**Solution:**
-   **Standardize `DATA_LAST_UPDATED`:** Ensure all data sources provide `DATA_LAST_UPDATED` in ISO 8601 format (e.g., `YYYY-MM-DDTHH:MM:SSZ` or with offset).
-   **Check Environment Variables:** Verify `STATUS_REPORT_WARN_ON_STALE_DATA` is `true` and adjust `STATUS_REPORT_STALE_DATA_THRESHOLD_HOURS` to an appropriate value (e.g., `24` for daily reports, `168` for weekly).
-   **Review `report_generator.py`:** Inspect the `_generate_stale_data_warning` method for correct parsing and comparison logic.

### Gotcha: Missing or Incomplete Data for Sections

**Symptom:**
Sections appear as "N/A" or contain empty tables/lists, even for seemingly important data.

**Problem:**
-   The input data (JSON/YAML) does not contain the expected keys for specific sections (e.g., `HIGH_TASK_COUNT`, `MILESTONE_NAME_1`).
-   Data fetching from external APIs failed or returned partial results.
-   `STATUS_REPORT_FAIL_ON_MISSING_DATA` is `false`, silently allowing generation.

**Solution:**
-   **Ensure Data Completeness:** Thoroughly check the input data against the `report-template.md` to ensure all expected placeholders have corresponding data.
-   **Robust Data Fetching:** Implement error handling and retry mechanisms for API calls. Log missing data points during data preparation.
-   **Set `STATUS_REPORT_FAIL_ON_MISSING_DATA=true`:** For critical reports, force failure if essential data is absent.
-   **Provide Defaults:** In your data preparation script, provide sensible default values (e.g., "0", "N/A", empty lists) for optional data.

### Gotcha: Incorrect Data Aggregation

**Symptom:**
Task counts are wrong, RAG statuses are miscalculated, or milestone dates are off.

**Problem:**
The data source provides raw data, and the aggregation logic (which should be external to `report_generator.py`) is flawed.

**Solution:**
-   **Verify Pre-processing:** The `report_generator.py` expects pre-aggregated data. Ensure your external scripts or services that prepare the data perform correct calculations and summaries.
-   **Unit Tests for Aggregation:** Write unit tests for your data aggregation logic to confirm accuracy.
-   **Manual Spot Checks:** Regularly compare reported aggregate numbers with raw data to catch discrepancies.

---

## 2. Template and Formatting Issues

### Gotcha: Placeholder Names Don't Match Data Keys

**Symptom:**
Literal placeholders like `{{PROJECT_NAME}}` appear in the final report.

**Problem:**
The name of the placeholder in `report-template.md` does not exactly match the key in the input JSON/YAML data. Case sensitivity and exact spelling are crucial.

**Solution:**
-   **Strict Naming Convention:** Use a consistent naming convention (e.g., `UPPER_SNAKE_CASE`) for all placeholders and data keys.
-   **Cross-Reference:** Always cross-reference template placeholders with your data preparation script's output keys.
-   **Use a Template Engine:** If simple string replacement becomes too cumbersome, consider using a more robust templating engine (like Jinja2) in `report_generator.py`, which often provides better error reporting for missing variables.

### Gotcha: Markdown Formatting Errors

**Symptom:**
Tables are broken, lists are unformatted, or code blocks are rendered incorrectly.

**Problem:**
-   Errors in the Markdown syntax within `report-template.md`.
-   Incorrectly formatted data being injected into tables or lists (e.g., `value` for a table row not starting with `|`).
-   `report_generator.py`'s list/table handling logic is insufficient for complex data.

**Solution:**
-   **Validate Template Markdown:** Use a Markdown linter (e.g., `markdownlint`) on `report-template.md` during development.
-   **Review `report_generator.py` Logic:** Ensure the `_populate_template` method correctly formats lists and table rows, especially for dynamic content.
-   **Test with Edge Cases:** Test generation with empty lists, long strings, and special characters to ensure robust formatting.

### Gotcha: Mermaid Diagrams Not Rendering

**Symptom:**
Raw Mermaid code blocks appear instead of rendered charts (e.g., `gantt dateFormat YYYY-MM-DD...`).

**Problem:**
-   The Markdown viewer/renderer does not support Mermaid syntax.
-   `STATUS_REPORT_INCLUDE_MERMAID` is set to `false`.
-   Mermaid syntax itself has errors.

**Solution:**
-   **Enable Mermaid:** Ensure `STATUS_REPORT_INCLUDE_MERMAID=true` is set in environment variables.
-   **Viewer Support:** Use a Markdown viewer that natively supports Mermaid (e.g., VS Code with extensions, GitHub, GitLab, modern web-based renderers).
-   **Validate Mermaid Syntax:** Copy the Mermaid code block content into an online Mermaid editor (e.g., Mermaid Live Editor) to check for syntax errors.

---

## 3. Configuration & Execution Issues

### Gotcha: Incorrect File Paths or Permissions

**Symptom:**
`FileNotFoundError` when loading templates or data, or the generated report is not found in the expected location. `PermissionDenied` errors.

**Problem:**
-   `STATUS_REPORT_TEMPLATE_PATH` or `STATUS_REPORT_OUTPUT_PATH` environment variables are incorrect or refer to non-existent directories.
-   The user/process running `report_generator.py` lacks read permissions for input files/templates or write permissions for the output directory.

**Solution:**
-   **Verify Paths:** Double-check environment variable values. Use absolute paths if relative paths are causing ambiguity.
-   **Check Permissions:** Ensure the execution context has `r` access for input and `rw` access for output directories.
-   **Ensure Directories Exist:** The `report_generator.py` should create the output directory, but ensure parent directories exist or handle their creation.

### Gotcha: Excessive Log Output / Debug Mode Left On

**Symptom:**
Terminal output is flooded with verbose logging during report generation.

**Problem:**
`logging.basicConfig(level=logging.INFO)` or `DEBUG` environment variables are enabled, causing too much detail.

**Solution:**
-   **Adjust Logging Level:** Set `logging.basicConfig(level=logging.WARNING)` or configure a logger with a file handler for debug output, keeping console output clean for normal operation.
-   **Use Specific Flags:** If custom debug flags exist (e.g., `REPORT_DEBUG_MODE`), ensure they are `false` in production.

---

## Quick Reference: Error Messages

| Error Message                               | Common Cause                                                              | Solution                                                                |
|---------------------------------------------|---------------------------------------------------------------------------|-------------------------------------------------------------------------|
| `FileNotFoundError`                         | Missing template/data file, incorrect path, or insufficient permissions.  | Verify `STATUS_REPORT_TEMPLATE_PATH`, `STATUS_REPORT_OUTPUT_PATH`, data file paths. Check `r/w` permissions. |
| `ValueError: Missing required data: ...`    | Input data missing critical keys for report generation.                   | Ensure all required keys are present in the input data or provide defaults. Check `STATUS_REPORT_FAIL_ON_MISSING_DATA`. |
| `ValueError: Unsupported data file type`    | Attempting to load unsupported file type (e.g., `.txt`) for data.         | Use `.json`, `.yaml`, or `.yml` for input data files.                   |
| HTTP 4xx/5xx (during data fetch)            | API authentication failure, network error, or API service issues.         | Check `STATUS_REPORT_API_TOKEN`, network connectivity, and API status. Implement retries. |
| Literal `{{PLACEHOLDER}}` in output         | Placeholder in template doesn't exactly match data key.                   | Double-check spelling and case sensitivity between template and data.   |
| Raw Mermaid block in output                 | Markdown viewer lacks Mermaid support, or `STATUS_REPORT_INCLUDE_MERMAID` is `false`. | Use a Mermaid-compatible viewer. Ensure `STATUS_REPORT_INCLUDE_MERMAID` is `true`. |
| `KeyError` (during _populate_template)      | Python code attempts to access a dictionary key that doesn't exist.        | Provide default values for optional keys in data preparation. Ensure `_populate_template` handles missing data gracefully. |
| Report too long/unreadable                  | Overly verbose input data or insufficient summarization.                  | Pre-process data to be concise. Tailor report to audience.             |

---

**Last Updated:** 2026-02-06
