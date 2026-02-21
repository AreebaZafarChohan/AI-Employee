# Task Priority Optimizer

The Task Priority Optimizer is a sophisticated system that dynamically adjusts task priorities based on multiple factors including deadlines, dependencies, workload, resource availability, and business impact. This system enables intelligent task prioritization that adapts to changing conditions in real-time, ensuring that the most critical work gets completed efficiently.

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Algorithms](#algorithms)
- [Integration](#integration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Overview

Traditional task management systems often rely on static priority assignments that become outdated as conditions change. The Task Priority Optimizer solves this by continuously recalculating priorities based on:

- Approaching deadlines
- Task dependencies and critical path analysis
- Current workload distribution
- Available resources
- Business impact scores
- Historical completion patterns

## Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/task-priority-optimizer.git
   cd task-priority-optimizer
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up configuration:
   ```bash
   cp config.example.yaml config.yaml
   # Edit config.yaml with your specific settings
   ```

## Configuration

### Environment Variables
The Task Priority Optimizer uses several environment variables for configuration:

```bash
# Required variables
export PRIORITY_UPDATE_INTERVAL=300  # Update every 5 minutes
export DEFAULT_URGENCY_WEIGHT=0.35
export DEFAULT_IMPORTANCE_WEIGHT=0.25
export DEFAULT_DEPENDENCY_WEIGHT=0.20
export DEFAULT_COMPLEXITY_WEIGHT=0.10
export DEFAULT_WORKLOAD_WEIGHT=0.10
export CRITICAL_TASK_THRESHOLD=0.9

# Optional variables
export MAX_PRIORITY_BUMP=0.1
export MIN_PRIORITY_DROP=-0.05
export WORKLOAD_BALANCE_ENABLED=true
export DEPENDENCY_ANALYSIS_ENABLED=true
export BUSINESS_IMPACT_ENABLED=true
export HISTORICAL_ANALYSIS_ENABLED=true
export PRIORITY_LOG_PATH=./logs/priority.log
export WEIGHT_ADJUSTMENT_ENABLED=false
```

### Configuration File
You can also configure the system using a YAML configuration file:

```yaml
# config.yaml
priority_optimizer:
  update_interval: 300  # seconds
  weights:
    urgency: 0.35
    importance: 0.25
    dependency: 0.20
    complexity: 0.10
    workload: 0.10
  thresholds:
    critical_task: 0.9
    max_priority_bump: 0.1
    min_priority_drop: -0.05
  features:
    workload_balance_enabled: true
    dependency_analysis_enabled: true
    business_impact_enabled: true
    historical_analysis_enabled: true
    weight_adjustment_enabled: false
  logging:
    log_path: "./logs/priority.log"
    level: "INFO"
  integrations:
    jira:
      enabled: true
      url: "https://your-company.atlassian.net"
      token: "${JIRA_TOKEN}"
    asana:
      enabled: false
    trello:
      enabled: false
```

## Usage

### Command Line Interface
The Task Priority Optimizer provides a command-line interface for common operations:

```bash
# Calculate priorities for all tasks
python -m priority_optimizer calculate-all

# Calculate priority for a specific task
python -m priority_optimizer calculate --task-id TASK-123

# Run the priority optimization service
python -m priority_optimizer service --config config.yaml

# Run a simulation with custom parameters
python -m priority_optimizer simulate --config simulation.yaml --output results.json
```

### Python API
You can also use the Task Priority Optimizer as a Python library:

```python
from priority_optimizer import PriorityOptimizer
from priority_optimizer.models import Task

# Initialize the optimizer
optimizer = PriorityOptimizer.from_config('config.yaml')

# Create a task
task = Task(
    id='TASK-123',
    title='Implement user authentication',
    deadline='2026-02-15T10:00:00Z',
    importance=0.8,
    complexity=0.6,
    assignees=['user@example.com'],
    dependencies=['TASK-100', 'TASK-101']
)

# Calculate priority
priority_result = optimizer.calculate_priority(task)
print(f"Priority score: {priority_result.score}")
print(f"Factors: {priority_result.factors}")
```

### Web Interface
The optimizer also includes a web interface for monitoring and configuration:

```bash
# Start the web interface
python -m priority_optimizer web --host 0.0.0.0 --port 8000
```

Access the interface at `http://localhost:8000` to:
- View current task priorities
- Adjust configuration parameters
- Monitor system performance
- Generate reports

## Algorithms

### Priority Calculation Formula
The priority score P(t) for task t is calculated as:

```
P(t) = w_u * U(t) + w_i * I(t) + w_d * D(t) + w_c * C(t) + w_w * W(t)
```

Where:
- U(t) = Urgency score (deadline proximity)
- I(t) = Importance score (business impact)
- D(t) = Dependency score (critical path relevance)
- C(t) = Complexity score (effort estimation)
- W(t) = Workload score (resource availability)
- w_* = respective weights (summing to 1.0)

### Urgency Calculation
Urgency is calculated using a sigmoid function based on time to deadline:

```
U(t) = 1 / (1 + e^(-k(t_d - t_c)))
```

Where:
- t_d = deadline timestamp
- t_c = current timestamp
- k = urgency curve steepness factor

## Integration

### Jira Integration
To integrate with Jira:

1. Obtain an API token from your Atlassian account
2. Add Jira configuration to your config.yaml:
   ```yaml
   integrations:
     jira:
       enabled: true
       url: "https://your-company.atlassian.net"
       username: "your-email@example.com"
       token: "your-api-token"
   ```
3. Run the sync command:
   ```bash
   python -m priority_optimizer sync jira
   ```

### Asana Integration
To integrate with Asana:

1. Obtain a personal access token from Asana
2. Add Asana configuration to your config.yaml:
   ```yaml
   integrations:
     asana:
       enabled: true
       token: "your-asana-token"
       workspace_id: "your-workspace-id"
   ```
3. Run the sync command:
   ```bash
   python -m priority_optimizer sync asana
   ```

### Custom Integrations
You can create custom integrations by implementing the `TaskSource` interface:

```python
from priority_optimizer.integrations import TaskSource

class CustomTaskSource(TaskSource):
    def get_tasks(self):
        # Implement logic to fetch tasks from your system
        pass
    
    def update_task_priority(self, task_id, priority):
        # Implement logic to update task priority in your system
        pass
```

Register your custom integration:

```python
from priority_optimizer import PriorityOptimizer

optimizer = PriorityOptimizer.from_config('config.yaml')
optimizer.register_integration('custom', CustomTaskSource())
```

## Troubleshooting

### Common Issues

#### Priority Calculation is Slow
- Check that you don't have too many tasks loaded at once
- Verify that database queries are properly indexed
- Consider increasing the update interval if real-time updates aren't needed

#### Unexpected Priority Changes
- Review your configuration weights
- Check for circular dependencies
- Verify that deadline calculations are correct
- Look for data quality issues in your task management system

#### Integration Failures
- Verify API credentials and permissions
- Check network connectivity to external systems
- Review API rate limits and adjust sync frequency accordingly
- Examine logs for specific error messages

### Logging
Enable detailed logging to troubleshoot issues:

```bash
# Set log level to DEBUG for more details
export LOG_LEVEL=DEBUG
python -m priority_optimizer calculate-all
```

### Health Checks
Run health checks to diagnose system issues:

```bash
python -m priority_optimizer health-check
```

## Contributing

We welcome contributions to the Task Priority Optimizer! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

Please make sure to update tests as appropriate and follow the existing code style.

For major changes, please open an issue first to discuss what you would like to change.