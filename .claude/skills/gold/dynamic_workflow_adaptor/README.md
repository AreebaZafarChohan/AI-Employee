# Dynamic Workflow Adaptor

## Overview
The Dynamic Workflow Adaptor is a Claude Code skill that modifies existing workflows dynamically based on real-time events, priority changes, or resource availability. It provides a flexible framework for adapting workflows at runtime to respond to changing conditions, ensuring optimal execution paths and resource utilization.

## Key Features
- **Event-Driven Adaptation**: Automatically modifies workflows based on real-time events
- **Dynamic Priority Management**: Adjusts task priorities in response to changing business needs
- **Resource-Aware Execution**: Reallocates resources based on availability and demand
- **Conditional Path Switching**: Changes workflow execution paths based on runtime conditions
- **State Validation**: Ensures workflow integrity during dynamic modifications

## Quick Start

1. **Configure your adaptation rules** in `adaptation_rules.json`:
```json
{
  "version": "1.0",
  "adaptation_rules": [
    {
      "id": "high_priority_boost",
      "name": "High Priority Boost",
      "description": "Boost priority of tasks when critical events occur",
      "trigger": {
        "event_type": "critical_alert",
        "condition": "event.severity === 'high'"
      },
      "actions": [
        {
          "type": "adjust_priority",
          "target": "current_task",
          "priority_level": 10
        }
      ]
    },
    {
      "id": "resource_fallback",
      "name": "Resource Fallback",
      "description": "Switch to alternative resource when primary is unavailable",
      "trigger": {
        "event_type": "resource_unavailable",
        "condition": "event.resource_type === 'primary_processor'"
      },
      "actions": [
        {
          "type": "reroute_task",
          "original_resource": "primary_processor",
          "alternative_resource": "secondary_processor"
        }
      ]
    }
  ]
}
```

2. **Set up environment variables**:
```bash
export DYNAMIC_WORKFLOW_DEFINITIONS_PATH=./base_workflows.json
export DYNAMIC_WORKFLOW_ADAPTATION_RULES_PATH=./adaptation_rules.json
export DYNAMIC_WORKFLOW_EVENT_SOURCE_URL=http://event-source:8080
```

3. **Start the adaptor**:
```bash
python workflow_adaptor.py
```

4. **Monitor dynamic adaptations**:
```bash
curl -X GET http://localhost:8081/adaptations/current
```

## Documentation
- `SKILL.md` - Full specification and implementation details
- `docs/patterns.md` - Dynamic workflow patterns and best practices
- `docs/impact-checklist.md` - Impact assessment for dynamic workflow adaptation
- `docs/gotchas.md` - Common pitfalls and troubleshooting

## Assets
- `adaptation_rules.json` - Template for defining workflow adaptation rules
- `workflow_adaptor.py` - Core dynamic workflow adaptation engine implementation
- `example-adaptation-config.json` - Example configuration file
- `MANIFEST.md` - Skill manifest

## Anti-Patterns to Avoid
- Creating static workflows without adaptation points
- Missing critical event handling that requires workflow changes
- Hardcoding execution paths without runtime flexibility
- Applying too many small adaptations without meaningful benefit
- Not validating workflow state consistency during modifications

For detailed information on configuration options, dynamic patterns, and advanced features, refer to `SKILL.md`.