# Integrated AI Insights Generator

## Overview
The Integrated AI Insights Generator is a Claude Code skill that generates actionable insights by analyzing project data, logs, or task metrics using AI. It provides a comprehensive solution for extracting valuable information from various data sources to drive informed decision-making and improve operational efficiency.

## Key Features
- **Multi-Source Data Analysis**: Processes data from various sources including project management tools, system logs, and task tracking systems
- **AI-Powered Insights**: Leverages AI to identify patterns, trends, and anomalies in data
- **Customizable Dashboards**: Generates visual representations of insights tailored to specific needs
- **Anomaly Detection**: Identifies unusual patterns that may indicate issues or opportunities
- **Actionable Recommendations**: Provides specific recommendations based on analysis results

## Quick Start

1. **Configure your data sources** in `data_sources_config.json`:
```json
{
  "version": "1.0",
  "data_sources": {
    "project_management": {
      "type": "jira",
      "url": "https://your-company.atlassian.net",
      "api_token": "${JIRA_API_TOKEN}",
      "projects": ["PROJ1", "PROJ2"]
    },
    "system_logs": {
      "type": "file",
      "path": "/var/log/application.log",
      "format": "json"
    },
    "task_metrics": {
      "type": "database",
      "connection_string": "${DATABASE_CONNECTION_STRING}",
      "table": "task_metrics"
    }
  },
  "ai_configuration": {
    "provider": "openai",
    "model": "gpt-4",
    "api_key": "${OPENAI_API_KEY}",
    "temperature": 0.3
  },
  "analysis_settings": {
    "anomaly_detection": {
      "enabled": true,
      "sensitivity": 0.7,
      "algorithm": "isolation_forest"
    },
    "trend_analysis": {
      "enabled": true,
      "time_periods": ["7d", "30d", "90d"]
    }
  }
}
```

2. **Set up environment variables**:
```bash
export OPENAI_API_KEY=your-openai-api-key
export JIRA_API_TOKEN=your-jira-api-token
export DATABASE_CONNECTION_STRING=postgresql://user:pass@localhost/db
```

3. **Start the insights generator**:
```bash
python ai_insights_generator.py
```

4. **Generate insights**:
```bash
curl -X POST http://localhost:8083/generate-insights \
  -H "Content-Type: application/json" \
  -d '{
    "data_source": "project_management",
    "analysis_types": ["trend", "anomaly", "benchmark"],
    "time_range": {
      "start": "2023-01-01T00:00:00Z",
      "end": "2023-12-31T23:59:59Z"
    },
    "output_format": "dashboard"
  }'
```

## Documentation
- `SKILL.md` - Full specification and implementation details
- `docs/patterns.md` - AI analysis and insights patterns
- `docs/impact-checklist.md` - Impact assessment for AI insights generation
- `docs/gotchas.md` - Common pitfalls and troubleshooting

## Assets
- `data_sources_config.json` - Configuration template for data sources
- `ai_insights_generator.py` - Core AI insights generation engine
- `example-insights-config.json` - Example configuration file
- `MANIFEST.md` - Skill manifest

## Anti-Patterns to Avoid
- Using misleading metrics that don't accurately represent the situation
- Over-relying on AI-generated insights without human validation
- Creating hardcoded dashboards that don't adapt to different needs
- Ignoring data quality before analysis
- Generating insights without sufficient context

For detailed information on configuration options, AI analysis patterns, and advanced features, refer to `SKILL.md`.