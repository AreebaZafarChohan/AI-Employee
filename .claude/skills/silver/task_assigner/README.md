# Task Assigner Skill

**Domain:** `silver`
**Version:** 1.0.0
**Status:** Production Ready

## Quick Start

This skill provides intelligent task assignment capabilities that automatically distribute work among team members based on their workload, skillset, and task priority. It optimizes team efficiency while ensuring fair distribution of work.

### Prerequisites
- Python 3.8+ (for Python components)
- Bash shell environment (for shell components)
- Access to team and task management APIs
- Appropriate authentication tokens for API access

### Installation
1. Clone or copy the skill assets to your system
2. Ensure required environment variables are configured
3. Make scripts executable: `chmod +x *.sh`
4. Install Python dependencies if using the Python module

### Configuration
Set the required environment variables:
```bash
export TASK_ASSIGNER_STRATEGY=balanced  # Options: balanced, skill_priority, workload_priority
export TEAM_MEMBERS_API_URL=https://api.company.com/team
export TASKS_API_URL=https://api.company.com/tasks
export ASSIGNMENT_LOG_PATH=/var/log/task_assignment.log
```

## Core Components

### 1. Task Assignment Script
The `task-assigner.sh` script provides command-line task assignment functionality. It evaluates team members based on skills, workload, and task requirements to make optimal assignments.

Usage:
```bash
./task-assigner.sh
```

### 2. Task Assignment Engine
The `task_assigner.py` Python module offers programmatic access to advanced assignment capabilities. It includes multiple assignment strategies and sophisticated evaluation algorithms.

Usage:
```python
from task_assigner import TaskAssigner, AssignmentStrategy

assigner = TaskAssigner(strategy=AssignmentStrategy.BALANCED)
results = assigner.run_assignment_process()
```

### 3. Assignment Rules Configuration
The `assignment-rules.json` file defines the rules and constraints for task assignment, including weights, thresholds, and specializations.

## Environment Variables

### Required Variables
- `TASK_ASSIGNER_STRATEGY`: Assignment strategy to use (balanced, skill_priority, workload_priority)
- `TEAM_MEMBERS_API_URL`: URL for team member data API
- `TASKS_API_URL`: URL for task management API
- `ASSIGNMENT_LOG_PATH`: Path for assignment logs

### Optional Variables
- `TASK_ASSIGNER_DEBUG_MODE`: Enable debug output (default: false)
- `TASK_ASSIGNER_WORKLOAD_THRESHOLD`: Workload percentage threshold (default: 0.8)
- `TASK_ASSIGNER_SKILL_WEIGHT`: Weight for skill matching (0.0-1.0, default: 0.6)
- `TASK_ASSIGNER_WORKLOAD_WEIGHT`: Weight for workload balance (0.0-1.0, default: 0.3)
- `TASK_ASSIGNER_PRIORITY_WEIGHT`: Weight for priority consideration (0.0-1.0, default: 0.1)
- `TASK_ASSIGNER_CACHE_TTL`: Cache TTL in seconds (default: 300)
- `TASK_ASSIGNER_EXCLUSION_DAYS`: Days to avoid assigning tasks (default: Sat,Sun)

## Assignment Strategies

### Balanced Strategy
Considers skill matching, workload balance, and task priority with configurable weights. This is the default strategy that aims for optimal overall assignment.

### Skill Priority Strategy
Prioritizes assignment to team members with the best skill match for the task, regardless of their current workload.

### Workload Priority Strategy
Focuses on distributing tasks to team members with the lowest current workload, potentially at the expense of skill matching.

## Integration Examples

### CI/CD Pipeline Integration
Add to your deployment pipeline to automatically assign review tasks:
```bash
# After code is pushed, assign reviewers
./task-assigner.sh --task-type code-review --repository $REPO --branch $BRANCH
```

### Project Management Integration
Integrate with project management tools to automatically assign newly created tasks:
```python
def on_task_created(task_data):
    assigner = TaskAssigner()
    result = assigner.assign_single_task(task_data)
    update_task_assignee(task_data['id'], result.assigned_to)
```

## Best Practices

1. **Regular Calibration**: Periodically review and adjust assignment weights based on outcomes
2. **Monitor Fairness**: Track assignment distribution to ensure equitable workload
3. **Validate Data Quality**: Ensure team member skills and workload data are accurate
4. **Plan for Failures**: Implement fallback procedures for when the assignment system is unavailable
5. **Consider Time Zones**: Account for team members in different geographic locations
6. **Respect Boundaries**: Honor team members' availability and working hour preferences

## Troubleshooting

Refer to the `docs/gotchas.md` file for common issues and solutions.

For additional support, consult the integration patterns in `docs/patterns.md` and the impact checklist in `docs/impact-checklist.md`.