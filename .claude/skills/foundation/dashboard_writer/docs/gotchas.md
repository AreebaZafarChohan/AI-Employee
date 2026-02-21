# Dashboard Writer - Common Gotchas & Troubleshooting

## Overview
This document outlines common pitfalls, anti-patterns, and troubleshooting tips encountered when generating Markdown dashboards using the `dashboard_writer` skill.

---

## 1. Data-Related Issues

### Gotcha: Missing or Incomplete Data

**Symptom:**
Placeholders remain unpopulated (e.g., `{{METRIC_1}}`), or entire sections are empty.

**Problem:**
The input data (JSON/YAML) does not contain the expected keys, or the data source API returned incomplete information.

**Solution:**
-   **Validate Input Data:** Before generation, ensure your input data schema matches the template's expected placeholders.
-   **Default Values:** In your data preparation logic, provide default or "N/A" values for optional metrics.
-   **`DASHBOARD_FAIL_ON_MISSING_DATA`:** Set `DASHBOARD_FAIL_ON_MISSING_DATA=true` (if not already) to immediately detect missing critical data rather than generating an incomplete report.
-   **Conditional Rendering:** Implement logic in your data processing to conditionally include/exclude sections based on data availability.

### Gotcha: Inconsistent Data Types

**Symptom:**
Dashboard output shows `[object Object]` or `[1, 2, 3]` instead of formatted values.

**Problem:**
The data provided for a placeholder is an object or array, but the template expects a simple string or a specific table format.

**Solution:**
-   **Flatten Data:** Ensure all data passed to simple string placeholders are primitive types (strings, numbers, booleans).
-   **Custom Rendering Logic:** For complex data structures (like lists of tasks or metrics tables), the `dashboard_generator.py` needs specific logic to format them into Markdown tables or lists.

---

## 2. Template-Related Issues

### Gotcha: Mismatched Placeholders

**Symptom:**
`{{DASHBOARD_TITLE}}` appears as literal text in the generated Markdown.

**Problem:**
The placeholder in the template doesn't exactly match the key in the input data, or there's a typo.

**Solution:**
-   **Case Sensitivity:** Double-check that placeholder names in `dashboard-template.md` (e.g., `{{DASHBOARD_TITLE}}`) match the keys in your input data (e.g., `"DASHBOARD_TITLE": "..."`) exactly, including case.
-   **Syntax:** Ensure the `{{PLACEHOLDER}}` syntax is correct.

### Gotcha: Invalid Markdown in Templates

**Symptom:**
Generated Markdown is malformed, or elements don't render correctly (e.g., broken tables, code blocks).

**Problem:**
Syntax errors in `dashboard-template.md` (e.g., missing pipe `|` in tables, incorrect fence ```` for code blocks).

**Solution:**
-   **Markdown Linter:** Use a Markdown linter (e.g., `markdownlint`) on `dashboard-template.md` to catch syntax errors.
-   **Review against Standards:** Refer to Markdown specifications for correct syntax.

---

## 3. Configuration & Environment Issues

### Gotcha: Incorrect File Paths

**Symptom:**
`FileNotFoundError` when loading templates or data, or output files not found in expected location.

**Problem:**
`DASHBOARD_TEMPLATE_PATH` or `DASHBOARD_OUTPUT_PATH` environment variables are set incorrectly or point to non-existent directories.

**Solution:**
-   **Verify Paths:** Double-check `export` statements for environment variables. Ensure paths are absolute or correctly relative to the execution directory.
-   **Permissions:** Confirm that the script has read/write permissions for the specified directories.

### Gotcha: API Authentication Failures

**Symptom:**
Dashboard generation fails with HTTP 401/403 errors when fetching data from external APIs.

**Problem:**
Missing or incorrect `DASHBOARD_API_TOKEN`, `DASHBOARD_API_USERNAME`, or `DASHBOARD_API_PASSWORD`.

**Solution:**
-   **Verify Credentials:** Ensure API keys/tokens are valid and have necessary permissions.
-   **Network Connectivity:** Confirm the host running the generator has network access to the API endpoint.
-   **Rate Limits:** Check if API rate limits are being hit. Implement retries with exponential backoff if necessary.

---

## 4. Output-Related Issues

### Gotcha: Overly Verbose or Unreadable Dashboards

**Symptom:**
Dashboards are too long, contain too much detail, or are difficult to scan for key information.

**Problem:**
Lack of focus on the audience's needs, inclusion of raw data instead of summaries, or poor content organization.

**Solution:**
-   **Conciseness:** Summarize, don't dump. Use the "Pattern: Metrics-Driven Dashboard" and "Pattern: Task & Project Status Dashboard" in `patterns.md` for guidance.
-   **Audience First:** Tailor content to the decision-making needs of the target audience.
-   **Filter and Aggregate:** Only include the most relevant data. Pre-process data to provide high-level summaries.

### Gotcha: Mermaid Diagrams Not Rendering

**Symptom:**
Raw Mermaid code blocks appear instead of rendered diagrams (e.g., `graph TD A --> B`).

**Problem:**
The Markdown viewer/renderer does not support Mermaid, or `DASHBOARD_INCLUDE_MERMAID` is set to `false`.

**Solution:**
-   **Enable Mermaid:** Ensure `DASHBOARD_INCLUDE_MERMAID=true` is set.
-   **Viewer Support:** Use a Markdown viewer that natively supports Mermaid (e.g., VS Code with extensions, GitHub, GitLab, many modern web-based renderers).
-   **Syntax Check:** Validate Mermaid syntax using an online editor.

---

## Quick Reference: Error Messages

| Error Message                 | Common Cause                                      | Solution                                                       |
|-------------------------------|---------------------------------------------------|----------------------------------------------------------------|
| `FileNotFoundError`           | Missing template/data file, incorrect path        | Verify `DASHBOARD_TEMPLATE_PATH`, `DASHBOARD_OUTPUT_PATH`, data file paths. Check permissions. |
| `ValueError: Missing required data` | Input data missing critical keys                  | Ensure all required keys are present in the input data or handle with defaults. |
| `ValueError: Unsupported data file type` | Attempting to load unsupported file type (e.g., `.txt`) | Use `.json`, `.yaml`, or `.yml` for input data.               |
| HTTP 4xx/5xx (API call)       | API authentication failure, network error, API issue | Check `DASHBOARD_API_TOKEN`, network connectivity, API status. |
| `KeyError` (during data processing) | Placeholder in template has no corresponding data key | Align template placeholders with data keys. Implement default handling. |
| Raw Mermaid block             | Markdown viewer lacks Mermaid support             | Use a Mermaid-compatible viewer or ensure `DASHBOARD_INCLUDE_MERMAID` is true. |

---

**Last Updated:** 2026-02-06
