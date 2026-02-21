# Multi-Service Orchestrator

## Overview
The Multi-Service Orchestrator is a Claude Code skill that coordinates multiple services (APIs, databases, queues) to complete complex workflows automatically. It provides a robust framework for orchestrating distributed systems by managing service dependencies, handling failures gracefully, and maintaining workflow state across multiple services.

## Key Features
- **Service Coordination**: Seamlessly connect and coordinate multiple services to achieve complex business objectives
- **Workflow Management**: Define and execute complex workflows with dependencies, branching, and error handling
- **Fault Tolerance**: Automatic retry mechanisms, circuit breakers, and graceful degradation when services fail
- **State Management**: Persistent storage of workflow state across service interactions
- **Monitoring & Observability**: Comprehensive logging and metrics for workflow execution

## Quick Start

1. **Configure your workflow definitions** in `workflow_definitions.json`:
```json
{
  "workflows": [
    {
      "id": "order_processing",
      "name": "Order Processing Workflow",
      "steps": [
        {
          "id": "validate_order",
          "service": "validation_service",
          "endpoint": "/validate",
          "method": "POST"
        },
        {
          "id": "process_payment",
          "service": "payment_service", 
          "endpoint": "/charge",
          "method": "POST",
          "depends_on": ["validate_order"]
        },
        {
          "id": "fulfill_order",
          "service": "fulfillment_service",
          "endpoint": "/ship",
          "method": "POST",
          "depends_on": ["process_payment"]
        }
      ]
    }
  ]
}
```

2. **Set up environment variables**:
```bash
export ORCHESTRATOR_WORKFLOW_DEFINITIONS_PATH=./workflow_definitions.json
export ORCHESTRATOR_STATE_BACKEND=redis
export ORCHESTRATOR_SERVICE_REGISTRY_URL=http://service-registry:8080
```

3. **Start the orchestrator**:
```bash
python orchestrator_engine.py
```

4. **Trigger a workflow**:
```bash
curl -X POST http://localhost:8080/workflows/order_processing/execute \
  -H "Content-Type: application/json" \
  -d '{"order_id": "12345", "amount": 99.99}'
```

## Documentation
- `SKILL.md` - Full specification and implementation details
- `docs/patterns.md` - Orchestration strategies and best practices
- `docs/impact-checklist.md` - Impact assessment for multi-service orchestration
- `docs/gotchas.md` - Common pitfalls and troubleshooting

## Assets
- `workflow_definitions.json` - Template for defining service workflows
- `orchestrator_engine.py` - Core orchestration engine implementation
- `example-workflow-config.json` - Example configuration file
- `MANIFEST.md` - Skill manifest

## Anti-Patterns to Avoid
- Hardcoding service endpoints in workflow definitions
- Ignoring failure handling and retry logic
- Skipping authorization checks for sensitive operations
- Creating tightly coupled service dependencies
- Performing synchronous long-running operations that block workflows

For detailed information on configuration options, orchestration patterns, and advanced features, refer to `SKILL.md`.