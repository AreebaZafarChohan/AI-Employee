#!/usr/bin/env python3
"""
dashboard_generator.py
Generates Markdown dashboard summaries from data.
"""

import os
import json
import yaml
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DashboardGenerator:
    """Generates Markdown dashboard summaries."""

    def __init__(self,
                 template_path: Optional[Path] = None,
                 output_path: Optional[Path] = None,
                 data_source_type: str = "json"):

        self.template_path = template_path or Path(os.getenv('DASHBOARD_TEMPLATE_PATH', './templates/dashboards'))
        self.output_path = output_path or Path(os.getenv('DASHBOARD_OUTPUT_PATH', './dashboards'))
        self.data_source_type = data_source_type.lower()

        self.output_path.mkdir(parents=True, exist_ok=True)

        self.report_date_format = os.getenv('DASHBOARD_REPORT_DATE_FORMAT', '%Y-%m-%d')
        self.timezone = os.getenv('DASHBOARD_TIMEZONE', 'UTC') # Not fully implemented, for documentation
        self.include_toc = os.getenv('DASHBOARD_INCLUDE_TOC', 'true').lower() == 'true'
        self.include_mermaid = os.getenv('DASHBOARD_INCLUDE_MERMAID', 'true').lower() == 'true'

        logger.info("DashboardGenerator initialized.")

    def _load_template(self, template_name: str = "dashboard-template.md") -> str:
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
            if os.getenv('DASHBOARD_FAIL_ON_MISSING_DATA', 'true').lower() == 'true':
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
            if os.getenv('DASHBOARD_FAIL_ON_MISSING_DATA', 'true').lower() == 'true':
                raise
            return {}

    def _populate_template(self, template_content: str, data: Dict[str, Any]) -> str:
        """Populates the Markdown template with data."""
        # Common placeholders
        data['REPORT_DATE'] = datetime.now().strftime(self.report_date_format)
        data['AUTHOR'] = os.getenv('USER', 'Gemini CLI') # Default author

        populated_content = template_content
        for key, value in data.items():
            placeholder = '{{' + key.upper() + '}}'
            if isinstance(value, (str, int, float)):
                populated_content = populated_content.replace(placeholder, str(value))
            elif isinstance(value, list) and key.upper() == 'PERFORMANCE_METRICS_TABLE':
                # Custom handling for table generation
                table_rows = []
                for metric in value:
                    table_rows.append(f"| {metric.get('name', '')} | {metric.get('value', '')} | {metric.get('trend', '')} | {metric.get('status', '')} |")
                populated_content = populated_content.replace(placeholder, "
".join(table_rows))
            # For other lists/dicts, direct replacement might not be desired,
            # but for simple placeholders, we can convert to string.
            elif isinstance(value, (list, dict)):
                populated_content = populated_content.replace(placeholder, json.dumps(value, indent=2))
            
        # Remove any remaining {{PLACEHOLDER}} that weren't populated
        populated_content = re.sub(r'\{\{.*?\}\}', 'N/A', populated_content)

        return populated_content

    def generate_dashboard(self, data_file: Path, output_filename: Optional[str] = None) -> Path:
        """Generates a dashboard Markdown file."""
        logger.info(f"Generating dashboard for data file: {data_file}")

        try:
            template_content = self._load_template()
            data = self._load_data(data_file)
            
            # Validate essential data
            self._validate_data(data)

            populated_markdown = self._populate_template(template_content, data)

            # Post-processing for TOC and Mermaid if enabled (simple approach)
            if self.include_toc:
                populated_markdown = self._add_table_of_contents(populated_markdown)
            if not self.include_mermaid:
                # Remove mermaid blocks if not enabled
                populated_markdown = re.sub(r'```mermaid.*?```', '', populated_markdown, flags=re.DOTALL)

            output_filename = output_filename or f"dashboard-{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
            output_file = self.output_path / output_filename

            with open(output_file, 'w') as f:
                f.write(populated_markdown)

            logger.info(f"Dashboard successfully generated: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"Failed to generate dashboard: {e}")
            raise

    def _add_table_of_contents(self, markdown_content: str) -> str:
        """Adds a simple Table of Contents to the Markdown content."""
        lines = markdown_content.split('
')
        toc_lines = []
        in_code_block = False
        
        # Collect headers
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
            
            if not in_code_block and (line.startswith('## ') or line.startswith('### ')):
                level = line.count('#')
                title = line.lstrip('# ').strip()
                # Basic slugify: lowercase, replace spaces with hyphens, remove non-alphanumeric
                slug = re.sub(r'[^\w\s-]', '', title.lower().replace(' ', '-'))
                
                # Only include up to the level specified by DASHBOARD_TOC_DEPTH (default 2 for ##)
                toc_depth = int(os.getenv('DASHBOARD_TOC_DEPTH', '2'))
                if level <= toc_depth:
                    toc_lines.append(f"{'  ' * (level - 2)}- [{title}](#{slug})") # Adjust indentation for level 2 (##) and 3 (###)

        toc_section_index = -1
        try:
            toc_section_index = lines.index("<!-- AUTO-GENERATED TOC -->")
        except ValueError:
            return markdown_content # No TOC placeholder found

        # Insert TOC
        new_lines = lines[:toc_section_index] + toc_lines + [''] + lines[toc_section_index+1:]
        return '
'.join(new_lines)

    def _validate_data(self, data: Dict[str, Any]):
        """Validates essential data for dashboard generation."""
        if os.getenv('DASHBOARD_FAIL_ON_MISSING_DATA', 'true').lower() == 'true':
            if not data.get('DASHBOARD_TITLE'):
                raise ValueError("Missing required data: DASHBOARD_TITLE")
            if not data.get('EXECUTIVE_SUMMARY'):
                raise ValueError("Missing required data: EXECUTIVE_SUMMARY")
            if os.getenv('DASHBOARD_REQUIRE_METRICS', 'true').lower() == 'true':
                # Check for at least one of the main metric placeholders to be present
                if not (data.get('METRIC_1') or data.get('PERFORMANCE_METRICS_TABLE')):
                    logger.warning("DASHBOARD_REQUIRE_METRICS is true, but no primary metric data found.")
                    # Optionally raise error here if strict enforcement is needed for this warning.
                    # For now, just a warning as the template might handle it gracefully.

        min_sections = int(os.getenv('DASHBOARD_MIN_SECTIONS', '3'))
        # This is a very rough check, ideally we'd check parsed markdown sections
        # For now, just ensure top-level data elements are present
        if len(data.keys()) < min_sections:
             logger.warning(f"Data object has fewer than {min_sections} top-level keys, consider adding more sections.")

# Example usage
if __name__ == "__main__":
    # Setup environment variables for demonstration
    # Make sure these paths are correctly pointing to the skill's asset and output directories
    script_dir = Path(__file__).parent
    os.environ['DASHBOARD_TEMPLATE_PATH'] = str(script_dir) # points to current directory for template
    
    # Create a temporary output directory for the example
    example_output_dir = script_dir / "example_output"
    os.environ['DASHBOARD_OUTPUT_PATH'] = str(example_output_dir)
    os.makedirs(example_output_dir, exist_ok=True)


    os.environ['DASHBOARD_FAIL_ON_MISSING_DATA'] = 'false' # Allow generation even if data is incomplete

    generator = DashboardGenerator()

    # Create a dummy data file for demonstration in the example_output_dir
    dummy_data = {
        "DASHBOARD_TITLE": "Weekly Project Status",
        "EXECUTIVE_SUMMARY": "Project Alpha is progressing well. Key milestones achieved include module X completion. Minor delays in module Y due to external dependency. Overall health is good.",
        "METRIC_1": "Backend Latency", "VALUE_1": "150ms", "TREND_1": "Stable", "STATUS_1": "Green",
        "METRIC_2": "Error Rate", "VALUE_2": "0.01%", "TREND_2": "Decreasing", "STATUS_2": "Green",
        "METRIC_3": "Uptime", "VALUE_3": "99.98%", "TREND_3": "Stable", "STATUS_3": "Green",
        "PERFORMANCE_METRICS_TABLE": [
            {"name": "API Response Time (P95)", "value": "250ms", "trend": "Stable", "status": "Green"},
            {"name": "Database CPU Usage", "value": "45%", "trend": "Stable", "status": "Green"},
            {"name": "Queue Depth", "value": "100 messages", "trend": "Stable", "status": "Green"}
        ],
        "HIGH_TASK_COUNT": "2", "HIGH_TASK_ASSIGNEE": "Alice", "HIGH_TASK_DUEDATE": "2026-02-10",
        "MEDIUM_TASK_COUNT": "5", "MEDIUM_TASK_ASSIGNEE": "Bob", "MEDIUM_TASK_DUEDATE": "2026-02-15",
        "LOW_TASK_COUNT": "8", "LOW_TASK_ASSIGNEE": "Charlie", "LOW_TASK_DUEDATE": "2026-02-20",
        "TASK_ID_1": "TASK-001", "TASK_DESC_1": "Fix critical bug in payment module", "TASK_STATUS_1": "In Progress",
        "TASK_ID_2": "TASK-002", "TASK_DESC_2": "Implement new user authentication flow", "TASK_STATUS_2": "Review",
        "TASK_ID_3": "TASK-003", "TASK_DESC_3": "Update documentation for API v2", "TASK_STATUS_3": "Completed",
        "APPROVAL_ID_1": "APP-001", "APPROVAL_TYPE_1": "Feature Deployment", "APPROVAL_INIT_1": "Dev Team", "APPROVAL_STATUS_1": "Pending", "APPROVAL_DUEDATE_1": "2026-02-08",
        "APPROVAL_ID_2": "APP-002", "APPROVAL_TYPE_2": "Budget Request", "APPROVAL_INIT_2": "Finance", "APPROVAL_STATUS_2": "Pending", "APPROVAL_DUEDATE_2": "2026-02-12",
        "APPROVED_ID_1": "APP-003", "APPROVED_TYPE_1": "Marketing Campaign", "APPROVED_BY_1": "VP Marketing",
        "APPROVED_ID_2": "APP-004", "APPROVED_TYPE_2": "Hiring Request", "APPROVED_BY_2": "HR Lead",
        "ACTION_ITEM_1": "Follow up on Module Y dependency with external vendor.",
        "ACTION_ITEM_2": "Prioritize critical bug fixes for next sprint.",
        "RECOMMENDATION_1": "Allocate additional resources to Module Y to mitigate delays.",
        "DATA_LAST_UPDATED": "2026-02-06 17:30:00 UTC"
    }
    
    dummy_data_file = example_output_dir / 'example-dashboard-data.json'
    with open(dummy_data_file, 'w') as f:
        json.dump(dummy_data, f, indent=2)

    # Generate dashboard
    output_file = generator.generate_dashboard(dummy_data_file, "weekly-report.md")
    print(f"
Generated dashboard example: {output_file}")
    
    # Clean up dummy data and output directory
    os.remove(dummy_data_file)
    os.remove(output_file)
    os.rmdir(example_output_dir)
