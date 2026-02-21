# Task Assigner Skill

## Overview

**Skill Name:** `task_assigner`
**Domain:** `silver`
**Purpose:** Automatically assign tasks to team members based on workload, skillset, and priority to optimize team efficiency and ensure fair distribution of work.

**Core Capabilities:**
- Intelligent task assignment considering multiple factors (workload, skills, priority)
- Dynamic workload balancing across team members
- Skill-based matching for optimal task allocation
- Priority-aware assignment to ensure critical tasks are handled promptly
- Fair distribution algorithms to prevent overloading individuals

**When to Use:**
- Managing distributed teams with varying skill sets
- Balancing workload during high-volume periods
- Ensuring critical tasks are assigned to most qualified individuals
- Reducing manual assignment overhead in project management
- Maintaining equitable task distribution across team members

**When NOT to Use:**
- Small teams where manual assignment is more efficient
- Projects with highly specialized or unique tasks requiring human judgment
- Situations where team members have strong preferences for specific tasks
- Emergency situations requiring immediate human decision-making
- Cases where individual accountability is more important than optimization

## Impact Analysis

### Security Impact: LOW
- Assignment algorithms don't typically handle sensitive data
- May access user profiles and skill information (requires appropriate permissions)
- Assignment logs could contain team member information
- Need to ensure privacy of workload and performance data

### System Impact: MEDIUM
- Integration with task management systems required
- Real-time workload tracking may impact system performance
- Need for reliable data sources for skills and workload
- Potential for cascading effects if assignment logic fails

### Operational Impact: HIGH
- Incorrect assignments can reduce team productivity
- Algorithm bias could lead to unfair workload distribution
- Requires ongoing calibration and monitoring
- Team adoption depends on trust in assignment fairness

### Business Impact: HIGH
- Improved task completion rates and efficiency
- Better utilization of team skills and capacity
- Reduced manager overhead in task assignment
- Potential for improved team satisfaction through fair distribution

## Environment Variables

### Required Variables
```
TASK_ASSIGNER_STRATEGY=balanced  # Options: balanced, skill_priority, workload_priority
TEAM_MEMBERS_API_URL=https://api.company.com/team
TASKS_API_URL=https://api.company.com/tasks
ASSIGNMENT_LOG_PATH=/var/log/task_assignment.log
```

### Optional Variables
```
TASK_ASSIGNER_DEBUG_MODE=false
TASK_ASSIGNER_WORKLOAD_THRESHOLD=0.8  # 80% threshold for considering someone overloaded
TASK_ASSIGNER_SKILL_WEIGHT=0.6        # Weight for skill matching (0.0-1.0)
TASK_ASSIGNER_WORKLOAD_WEIGHT=0.3     # Weight for workload balance (0.0-1.0)
TASK_ASSIGNER_PRIORITY_WEIGHT=0.1     # Weight for priority consideration (0.0-1.0)
TASK_ASSIGNER_CACHE_TTL=300           # Cache team data for 5 minutes
TASK_ASSIGNER_EXCLUSION_DAYS=Sat,Sun  # Days to avoid assigning tasks
```

## Network and Authentication Implications

### Authentication Requirements
- OAuth 2.0 tokens for accessing team and task APIs
- Service account credentials for automated assignment
- JWT tokens for secure communication with task management systems
- Multi-factor authentication for administrative access

### Network Considerations
- Reliable connectivity to team and task management systems
- Latency considerations for real-time assignment decisions
- Bandwidth for frequent API calls to update workload data
- Fallback mechanisms when external systems are unavailable

### Integration Points
- Task management platforms (Jira, Asana, Trello)
- Team directory services (LDAP, Active Directory)
- Project management tools (Monday.com, ClickUp)
- Communication platforms (Slack, Teams) for assignment notifications

## Blueprints

### Blueprint 1: Task Assignment Script (Bash)
```bash
#!/usr/bin/env bash
# task-assigner.sh
# Automatically assigns tasks to team members based on workload and skills

set -euo pipefail

# Configuration
STRATEGY="${TASK_ASSIGNER_STRATEGY:-balanced}"
TEAM_API="${TEAM_MEMBERS_API_URL:-https://api.company.com/team}"
TASKS_API="${TASKS_API_URL:-https://api.company.com/tasks}"
LOG_PATH="${ASSIGNMENT_LOG_PATH:-/tmp/task_assignment.log}"
DEBUG="${TASK_ASSIGNER_DEBUG_MODE:-false}"
WORKLOAD_THRESHOLD="${TASK_ASSIGNER_WORKLOAD_THRESHOLD:-0.8}"
CACHE_TTL="${TASK_ASSIGNER_CACHE_TTL:-300}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log_assignment() {
    local level="$1"
    local message="$2"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local user=$(whoami)
    
    echo "{\"timestamp\":\"${timestamp}\",\"level\":\"${level}\",\"user\":\"${user}\",\"message\":\"${message}\"}" >> "${LOG_PATH}"
}

# Fetch team member data
fetch_team_data() {
    if [[ "$DEBUG" == "true" ]]; then
        echo "Debug: Fetching team data from $TEAM_API"
    fi
    
    # In a real implementation, this would call the API
    # curl -H "Authorization: Bearer $TOKEN" "$TEAM_API"
    
    # Mock data for demonstration
    cat << 'EOF'
[
  {
    "id": "user1",
    "name": "Alice Johnson",
    "skills": ["javascript", "react", "nodejs"],
    "current_workload": 0.6,
    "availability": true,
    "preferred_hours": {"start": 9, "end": 17}
  },
  {
    "id": "user2", 
    "name": "Bob Smith",
    "skills": ["python", "django", "sql"],
    "current_workload": 0.4,
    "availability": true,
    "preferred_hours": {"start": 10, "end": 18}
  },
  {
    "id": "user3",
    "name": "Carol Davis",
    "skills": ["design", "ui", "ux"],
    "current_workload": 0.9,
    "availability": true,
    "preferred_hours": {"start": 8, "end": 16}
  }
]
EOF
}

# Fetch pending tasks
fetch_pending_tasks() {
    if [[ "$DEBUG" == "true" ]]; then
        echo "Debug: Fetching pending tasks from $TASKS_API"
    fi
    
    # In a real implementation, this would call the API
    # curl -H "Authorization: Bearer $TOKEN" "$TASKS_API?status=pending"
    
    # Mock data for demonstration
    cat << 'EOF'
[
  {
    "id": "task1",
    "title": "Fix login bug",
    "description": "Resolve authentication issue in login flow",
    "priority": "high",
    "required_skills": ["javascript", "react"],
    "estimated_hours": 2
  },
  {
    "id": "task2",
    "title": "Database optimization",
    "description": "Optimize slow queries in user table",
    "priority": "medium", 
    "required_skills": ["sql", "python"],
    "estimated_hours": 4
  }
]
EOF
}

# Calculate assignment score based on strategy
calculate_score() {
    local user_json="$1"
    local task_json="$2"
    local strategy="$3"
    
    # Extract data from JSON
    local user_workload=$(echo "$user_json" | jq -r '.current_workload')
    local user_skills=$(echo "$user_json" | jq -r '.skills | join(",")')
    local task_skills=$(echo "$task_json" | jq -r '.required_skills | join(",")')
    local task_priority=$(echo "$task_json" | jq -r '.priority')
    
    # Calculate skill match (simple percentage for demo)
    local skill_match=0
    IFS=',' read -ra REQ_SKILLS <<< "$task_skills"
    for skill in "${REQ_SKILLS[@]}"; do
        if [[ "$user_skills" == *"$skill"* ]]; then
            ((skill_match++))
        fi
    done
    local total_req_skills=${#REQ_SKILLS[@]}
    if [[ $total_req_skills -gt 0 ]]; then
        skill_match=$(echo "$skill_match $total_req_skills" | awk '{printf "%.2f", $1/$2}')
    else
        skill_match=0
    fi
    
    # Calculate workload factor (lower workload = higher score)
    local workload_factor=$(echo "1 - $user_workload" | bc -l)
    
    # Calculate priority factor
    local priority_factor=0.5  # Default
    if [[ "$task_priority" == "high" ]]; then
        priority_factor=1.0
    elif [[ "$task_priority" == "medium" ]]; then
        priority_factor=0.7
    fi
    
    # Calculate final score based on strategy
    case "$strategy" in
        "skill_priority")
            echo "$(echo "$skill_match" | bc -l)"
            ;;
        "workload_priority")
            echo "$(echo "$workload_factor" | bc -l)"
            ;;
        *)
            # Balanced strategy
            local skill_weight="${TASK_ASSIGNER_SKILL_WEIGHT:-0.6}"
            local workload_weight="${TASK_ASSIGNER_WORKLOAD_WEIGHT:-0.3}"
            local priority_weight="${TASK_ASSIGNER_PRIORITY_WEIGHT:-0.1}"
            
            local score=$(echo "$skill_match * $skill_weight + $workload_factor * $workload_weight + $priority_factor * $priority_weight" | bc -l)
            echo "$score"
            ;;
    esac
}

# Assign tasks to team members
assign_tasks() {
    local team_data="$1"
    local tasks_data="$2"
    
    # Parse tasks
    local num_tasks=$(echo "$tasks_data" | jq 'length')
    
    for ((i=0; i<num_tasks; i++)); do
        local task=$(echo "$tasks_data" | jq ".[$i]")
        local task_id=$(echo "$task" | jq -r '.id')
        local task_title=$(echo "$task" | jq -r '.title')
        
        if [[ "$DEBUG" == "true" ]]; then
            echo "Debug: Processing task $task_id: $task_title"
        fi
        
        # Find best candidate for this task
        local best_user=""
        local best_score=-1
        
        local num_users=$(echo "$team_data" | jq 'length')
        for ((j=0; j<num_users; j++)); do
            local user=$(echo "$team_data" | jq ".[$j]")
            local user_id=$(echo "$user" | jq -r '.id')
            local user_available=$(echo "$user" | jq -r '.availability')
            local user_workload=$(echo "$user" | jq -r '.current_workload')
            
            # Skip unavailable users or those exceeding workload threshold
            if [[ "$user_available" != "true" ]] || (( $(echo "$user_workload > $WORKLOAD_THRESHOLD" | bc -l) )); then
                continue
            fi
            
            local score=$(calculate_score "$user" "$task" "$STRATEGY")
            
            if (( $(echo "$score > $best_score" | bc -l) )); then
                best_score=$score
                best_user=$user_id
            fi
        done
        
        if [[ -n "$best_user" ]]; then
            # In a real implementation, this would assign the task via API
            # curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
            #   "$TASKS_API/$task_id/assign" -d "{\"assignee\": \"$best_user\"}"
            
            echo "✅ Assigned task '$task_title' (ID: $task_id) to user $best_user (Score: $best_score)"
            log_assignment "INFO" "Assigned task $task_id to user $best_user with score $best_score"
        else
            echo "⚠️  Could not find suitable assignee for task '$task_title' (ID: $task_id)"
            log_assignment "WARN" "Could not assign task $task_id - no suitable candidates found"
        fi
    done
}

# Main execution
main() {
    echo "🚀 Starting task assignment process..."
    echo "Strategy: $STRATEGY"
    
    # Fetch team and task data
    local team_data
    team_data=$(fetch_team_data)
    
    local tasks_data
    tasks_data=$(fetch_pending_tasks)
    
    # Perform assignments
    assign_tasks "$team_data" "$tasks_data"
    
    echo "✅ Task assignment process completed!"
}

main "$@"
```

### Blueprint 2: Task Assignment Engine (Python)
```python
#!/usr/bin/env python3
"""
task_assigner.py
Automatically assign tasks to team members based on workload, skills, and priority
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging


class AssignmentStrategy(Enum):
    BALANCED = "balanced"
    SKILL_PRIORITY = "skill_priority"
    WORKLOAD_PRIORITY = "workload_priority"


@dataclass
class TeamMember:
    """Represents a team member with their attributes."""
    id: str
    name: str
    skills: List[str]
    current_workload: float  # 0.0 to 1.0
    availability: bool
    preferred_hours: Dict[str, int]  # start and end hours
    max_daily_hours: Optional[float] = 8.0


@dataclass
class Task:
    """Represents a task to be assigned."""
    id: str
    title: str
    description: str
    priority: str  # 'low', 'medium', 'high', 'critical'
    required_skills: List[str]
    estimated_hours: float
    deadline: Optional[datetime] = None
    project: Optional[str] = None


@dataclass
class AssignmentResult:
    """Result of a task assignment."""
    task_id: str
    assigned_to: Optional[str]
    score: float
    reason: str
    timestamp: datetime


class TaskAssigner:
    """
    Automatically assigns tasks to team members based on workload, skills, and priority.
    
    This class implements various assignment strategies to optimize team efficiency
    and ensure fair distribution of work.
    """
    
    def __init__(self, strategy: AssignmentStrategy = AssignmentStrategy.BALANCED):
        """
        Initialize the task assigner with a specific strategy.
        
        Args:
            strategy: The assignment strategy to use
        """
        self.strategy = strategy
        self.skill_weight = float(os.getenv('TASK_ASSIGNER_SKILL_WEIGHT', '0.6'))
        self.workload_weight = float(os.getenv('TASK_ASSIGNER_WORKLOAD_WEIGHT', '0.3'))
        self.priority_weight = float(os.getenv('TASK_ASSIGNER_PRIORITY_WEIGHT', '0.1'))
        self.workload_threshold = float(os.getenv('TASK_ASSIGNER_WORKLOAD_THRESHOLD', '0.8'))
        
        # Configure logging
        self.logger = self._setup_logger()
        
        # Cache for team data
        self.team_cache = None
        self.cache_expiry = None
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logger for assignment tracking."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        # Create file handler for assignment log
        log_path = os.getenv('ASSIGNMENT_LOG_PATH', '/tmp/task_assignment.log')
        handler = logging.FileHandler(log_path)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def fetch_team_members(self) -> List[TeamMember]:
        """
        Fetch team member data from the configured API.
        
        Returns:
            List of TeamMember objects
        """
        # Check if we have cached data that's still valid
        if self.team_cache and self.cache_expiry and datetime.now() < self.cache_expiry:
            self.logger.debug("Using cached team data")
            return self.team_cache
        
        # In a real implementation, this would fetch from an API
        # api_url = os.getenv('TEAM_MEMBERS_API_URL', 'https://api.company.com/team')
        # headers = {'Authorization': f'Bearer {get_token()}'}
        # response = requests.get(api_url, headers=headers)
        # team_data = response.json()
        
        # For this example, we'll return mock data
        team_data = [
            {
                "id": "user1",
                "name": "Alice Johnson",
                "skills": ["javascript", "react", "nodejs"],
                "current_workload": 0.6,
                "availability": True,
                "preferred_hours": {"start": 9, "end": 17},
                "max_daily_hours": 8.0
            },
            {
                "id": "user2",
                "name": "Bob Smith",
                "skills": ["python", "django", "sql"],
                "current_workload": 0.4,
                "availability": True,
                "preferred_hours": {"start": 10, "end": 18},
                "max_daily_hours": 8.0
            },
            {
                "id": "user3",
                "name": "Carol Davis",
                "skills": ["design", "ui", "ux"],
                "current_workload": 0.9,
                "availability": True,
                "preferred_hours": {"start": 8, "end": 16},
                "max_daily_hours": 6.0  # Part-time
            }
        ]
        
        team_members = []
        for member_data in team_data:
            member = TeamMember(
                id=member_data["id"],
                name=member_data["name"],
                skills=[skill.lower() for skill in member_data["skills"]],
                current_workload=member_data["current_workload"],
                availability=member_data["availability"],
                preferred_hours=member_data["preferred_hours"],
                max_daily_hours=member_data.get("max_daily_hours", 8.0)
            )
            team_members.append(member)
        
        # Cache the data
        cache_ttl = int(os.getenv('TASK_ASSIGNER_CACHE_TTL', '300'))  # 5 minutes default
        self.team_cache = team_members
        self.cache_expiry = datetime.now() + timedelta(seconds=cache_ttl)
        
        return team_members
    
    def fetch_pending_tasks(self) -> List[Task]:
        """
        Fetch pending tasks that need assignment.
        
        Returns:
            List of Task objects
        """
        # In a real implementation, this would fetch from an API
        # api_url = os.getenv('TASKS_API_URL', 'https://api.company.com/tasks')
        # headers = {'Authorization': f'Bearer {get_token()}'}
        # params = {'status': 'pending'}
        # response = requests.get(api_url, headers=headers, params=params)
        # tasks_data = response.json()
        
        # For this example, we'll return mock data
        tasks_data = [
            {
                "id": "task1",
                "title": "Fix login bug",
                "description": "Resolve authentication issue in login flow",
                "priority": "high",
                "required_skills": ["javascript", "react"],
                "estimated_hours": 2.0
            },
            {
                "id": "task2",
                "title": "Database optimization",
                "description": "Optimize slow queries in user table",
                "priority": "medium",
                "required_skills": ["sql", "python"],
                "estimated_hours": 4.0
            },
            {
                "id": "task3",
                "title": "UI redesign",
                "description": "Redesign the dashboard interface",
                "priority": "high",
                "required_skills": ["design", "ui", "ux"],
                "estimated_hours": 8.0
            }
        ]
        
        tasks = []
        for task_data in tasks_data:
            task = Task(
                id=task_data["id"],
                title=task_data["title"],
                description=task_data["description"],
                priority=task_data["priority"],
                required_skills=[skill.lower() for skill in task_data["required_skills"]],
                estimated_hours=task_data["estimated_hours"]
            )
            tasks.append(task)
        
        return tasks
    
    def calculate_skill_match_score(self, member: TeamMember, task: Task) -> float:
        """
        Calculate how well a team member's skills match the task requirements.
        
        Args:
            member: The team member
            task: The task to evaluate
            
        Returns:
            Score between 0.0 and 1.0 representing skill match
        """
        if not task.required_skills:
            return 1.0  # If no skills required, perfect match
        
        matching_skills = [skill for skill in task.required_skills if skill in member.skills]
        return len(matching_skills) / len(task.required_skills)
    
    def calculate_workload_score(self, member: TeamMember) -> float:
        """
        Calculate a score based on the member's current workload.
        Lower workload gets a higher score.
        
        Args:
            member: The team member
            
        Returns:
            Score between 0.0 and 1.0 representing availability
        """
        # Invert the workload so lower workload gets higher score
        return 1.0 - member.current_workload
    
    def calculate_priority_score(self, task: Task) -> float:
        """
        Calculate a score based on the task priority.
        
        Args:
            task: The task to evaluate
            
        Returns:
            Score between 0.0 and 1.0 representing priority weight
        """
        priority_mapping = {
            'critical': 1.0,
            'high': 0.8,
            'medium': 0.5,
            'low': 0.2
        }
        return priority_mapping.get(task.priority, 0.5)
    
    def calculate_assignment_score(self, member: TeamMember, task: Task) -> float:
        """
        Calculate the overall assignment score for a member-task pair.
        
        Args:
            member: The team member
            task: The task to assign
            
        Returns:
            Overall score between 0.0 and 1.0
        """
        skill_score = self.calculate_skill_match_score(member, task)
        workload_score = self.calculate_workload_score(member)
        priority_score = self.calculate_priority_score(task)
        
        if self.strategy == AssignmentStrategy.SKILL_PRIORITY:
            return skill_score
        elif self.strategy == AssignmentStrategy.WORKLOAD_PRIORITY:
            return workload_score
        else:  # BALANCED
            # Weighted combination of all factors
            total_weight = self.skill_weight + self.workload_weight + self.priority_weight
            if total_weight == 0:
                return 0.5  # Default if all weights are zero
            
            # Normalize weights if they don't sum to 1
            norm_skill_weight = self.skill_weight / total_weight
            norm_workload_weight = self.workload_weight / total_weight
            norm_priority_weight = self.priority_weight / total_weight
            
            return (
                skill_score * norm_skill_weight +
                workload_score * norm_workload_weight +
                priority_score * norm_priority_weight
            )
    
    def find_best_assignee(self, task: Task, team_members: List[TeamMember]) -> Tuple[Optional[TeamMember], float, str]:
        """
        Find the best team member to assign a task to.
        
        Args:
            task: The task to assign
            team_members: List of available team members
            
        Returns:
            Tuple of (best_member, score, reason)
        """
        eligible_members = [
            member for member in team_members
            if member.availability and member.current_workload < self.workload_threshold
        ]
        
        if not eligible_members:
            return None, 0.0, "No available team members"
        
        best_member = None
        best_score = -1.0
        best_reason = ""
        
        for member in eligible_members:
            score = self.calculate_assignment_score(member, task)
            
            if score > best_score:
                best_score = score
                best_member = member
                
                # Generate reason for assignment
                skill_match = self.calculate_skill_match_score(member, task)
                workload_score = self.calculate_workload_score(member)
                
                if skill_match >= 0.8:
                    best_reason = f"Best fit based on skills ({skill_match:.2f}) and availability"
                elif workload_score > 0.7:
                    best_reason = f"Most available with lowest workload ({member.current_workload})"
                else:
                    best_reason = f"Balanced choice based on skills and availability"
        
        return best_member, best_score, best_reason
    
    def assign_tasks(self, tasks: List[Task], team_members: List[TeamMember]) -> List[AssignmentResult]:
        """
        Assign a list of tasks to team members.
        
        Args:
            tasks: List of tasks to assign
            team_members: List of available team members
            
        Returns:
            List of AssignmentResult objects
        """
        results = []
        
        for task in tasks:
            assignee, score, reason = self.find_best_assignee(task, team_members)
            
            if assignee:
                # In a real implementation, this would update the task via API
                # api_url = f"{os.getenv('TASKS_API_URL', 'https://api.company.com/tasks')}/{task.id}/assign"
                # headers = {'Authorization': f'Bearer {get_token()}', 'Content-Type': 'application/json'}
                # payload = {"assignee": assignee.id}
                # response = requests.post(api_url, headers=headers, json=payload)
                
                result = AssignmentResult(
                    task_id=task.id,
                    assigned_to=assignee.id,
                    score=score,
                    reason=reason,
                    timestamp=datetime.now()
                )
                
                self.logger.info(f"Assigned task {task.id} to {assignee.name} (ID: {assignee.id}), Score: {score:.2f}")
            else:
                result = AssignmentResult(
                    task_id=task.id,
                    assigned_to=None,
                    score=0.0,
                    reason=reason,
                    timestamp=datetime.now()
                )
                
                self.logger.warning(f"Could not assign task {task.id} - {reason}")
            
            results.append(result)
        
        return results
    
    def run_assignment_process(self) -> List[AssignmentResult]:
        """
        Run the complete task assignment process.
        
        Returns:
            List of AssignmentResult objects
        """
        self.logger.info("Starting task assignment process")
        
        # Fetch team members and tasks
        team_members = self.fetch_team_members()
        tasks = self.fetch_pending_tasks()
        
        if not tasks:
            self.logger.info("No pending tasks to assign")
            return []
        
        if not team_members:
            self.logger.error("No team members available for assignment")
            return []
        
        # Perform assignments
        results = self.assign_tasks(tasks, team_members)
        
        # Log summary
        assigned_count = sum(1 for r in results if r.assigned_to is not None)
        self.logger.info(f"Assignment process completed: {assigned_count}/{len(results)} tasks assigned")
        
        return results


def main():
    """Example usage of the TaskAssigner."""
    import sys
    
    # Get strategy from command line or environment
    strategy_str = os.getenv('TASK_ASSIGNER_STRATEGY', 'balanced')
    try:
        strategy = AssignmentStrategy(strategy_str)
    except ValueError:
        print(f"Invalid strategy: {strategy_str}. Using 'balanced' as default.")
        strategy = AssignmentStrategy.BALANCED
    
    # Initialize assigner
    assigner = TaskAssigner(strategy=strategy)
    
    # Run assignment process
    results = assigner.run_assignment_process()
    
    # Print results
    print("\n📊 Assignment Results:")
    for result in results:
        if result.assigned_to:
            print(f"✅ Task {result.task_id} assigned (Score: {result.score:.2f})")
        else:
            print(f"❌ Task {result.task_id} not assigned - {result.reason}")
    
    assigned_count = sum(1 for r in results if r.assigned_to is not None)
    print(f"\n📈 Summary: {assigned_count}/{len(results)} tasks assigned")


if __name__ == "__main__":
    main()
```

### Blueprint 3: Assignment Rules Configuration (JSON)
```json
{
  "version": "1.0.0",
  "last_updated": "2026-02-06T00:00:00Z",
  "assignment_rules": {
    "default_strategy": "balanced",
    "weights": {
      "skill_matching": 0.5,
      "workload_balance": 0.3,
      "priority_consideration": 0.2
    },
    "constraints": {
      "max_workload_percentage": 0.85,
      "min_skill_match_percentage": 0.5,
      "max_tasks_per_day": 5,
      "avoid_weekends": true
    },
    "priorities": {
      "critical": {
        "multiplier": 1.5,
        "max_response_hours": 2
      },
      "high": {
        "multiplier": 1.2,
        "max_response_hours": 4
      },
      "medium": {
        "multiplier": 1.0,
        "max_response_hours": 24
      },
      "low": {
        "multiplier": 0.8,
        "max_response_hours": 168
      }
    },
    "specializations": [
      {
        "skill_group": "frontend",
        "members": ["user1", "user4", "user7"],
        "bonus_multiplier": 1.1
      },
      {
        "skill_group": "backend", 
        "members": ["user2", "user5", "user8"],
        "bonus_multiplier": 1.1
      },
      {
        "skill_group": "database",
        "members": ["user3", "user6"],
        "bonus_multiplier": 1.2
      }
    ],
    "exclusions": [
      {
        "user_id": "user9",
        "reason": "On vacation",
        "start_date": "2026-02-01",
        "end_date": "2026-02-15"
      }
    ]
  },
  "metadata": {
    "created_by": "Team Management System",
    "reviewed_by": "Operations Team",
    "next_review_date": "2026-05-06T00:00:00Z"
  }
}
```

## Pre-Deployment Validation Checklist

### Configuration Validation
- [ ] Verify TASK_ASSIGNER_STRATEGY is set to a valid option
- [ ] Confirm TEAM_MEMBERS_API_URL and TASKS_API_URL are accessible
- [ ] Check ASSIGNMENT_LOG_PATH directory is writable
- [ ] Validate all required environment variables are set
- [ ] Test API connectivity to team and task management systems

### Security Validation
- [ ] Ensure API tokens have appropriate scopes
- [ ] Verify authentication mechanisms for API calls
- [ ] Confirm sensitive data is not logged inappropriately
- [ ] Test access controls for assignment data
- [ ] Validate encryption of communication channels

### Functional Validation
- [ ] Test assignment algorithm with sample team and task data
- [ ] Verify all assignment strategies work correctly
- [ ] Confirm constraint enforcement (workload limits, etc.)
- [ ] Test edge cases (no available members, no tasks, etc.)
- [ ] Validate priority handling works as expected

### Performance Validation
- [ ] Measure assignment algorithm performance with realistic data
- [ ] Test caching mechanisms work correctly
- [ ] Verify API call rate limits are respected
- [ ] Confirm system handles peak loads appropriately
- [ ] Test failover mechanisms if applicable

### Operational Validation
- [ ] Verify monitoring and alerting for assignment failures
- [ ] Test backup and recovery procedures
- [ ] Confirm logging provides sufficient information for debugging
- [ ] Validate that assignment notifications work correctly
- [ ] Test rollback procedures for assignment changes

## Anti-Patterns

### Anti-Pattern 1: Hardcoded User Assignments
**Problem:** Embedding specific user IDs directly in assignment logic rather than using dynamic evaluation.
**Risk:** Makes the system inflexible and prone to errors when team members change.
**Solution:** Use dynamic evaluation based on skills, workload, and availability.

**Wrong:**
```python
# Bad: Hardcoded assignment
if task.title.contains("database"):
    assign_to_user("user3")  # Fixed assignment to user3
```

**Correct:**
```python
# Good: Dynamic assignment based on skills
def assign_database_task(task, team_members):
    db_specialists = [m for m in team_members if "database" in m.skills]
    available_specialists = [m for m in db_specialists if m.availability]
    
    if available_specialists:
        # Choose based on workload and other factors
        return select_optimal_member(available_specialists, task)
    else:
        # Fall back to general assignment logic
        return find_best_general_fit(task, team_members)
```

### Anti-Pattern 2: Ignoring Workload Limits
**Problem:** Assigning tasks without considering current workload, leading to overloading.
**Risk:** Decreased productivity, burnout, missed deadlines.
**Solution:** Implement workload checks and balancing mechanisms.

**Wrong:**
```python
# Bad: No workload consideration
def assign_task(task, team):
    # Just assign to anyone with the right skills
    for member in team:
        if has_required_skills(member, task):
            return member.id
    return None
```

**Correct:**
```python
# Good: Consider workload in assignment
def assign_task(task, team):
    eligible_members = [
        member for member in team
        if (has_required_skills(member, task) and 
            member.availability and 
            member.current_workload < MAX_WORKLOAD_THRESHOLD)
    ]
    
    if not eligible_members:
        return None
    
    # Among eligible members, pick the one with lowest workload
    return min(eligible_members, key=lambda m: m.current_workload).id
```

### Anti-Pattern 3: Static Priority Handling
**Problem:** Treating all tasks with the same priority level equally without considering urgency.
**Risk:** Critical tasks may not get the attention they need.
**Solution:** Implement dynamic priority adjustment based on deadlines and business impact.

**Wrong:**
```python
# Bad: Static priority handling
def get_priority_score(task):
    priority_map = {"low": 1, "medium": 2, "high": 3}
    return priority_map.get(task.priority, 2)
```

**Correct:**
```python
# Good: Dynamic priority considering deadlines
def get_priority_score(task):
    base_score = {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(task.priority, 2)
    
    # Boost score if task is urgent
    if task.deadline:
        hours_until_deadline = (task.deadline - datetime.now()).total_seconds() / 3600
        if hours_until_deadline <= 4:  # Due in next 4 hours
            base_score *= 1.5
        elif hours_until_deadline <= 24:  # Due in next day
            base_score *= 1.2
    
    return base_score
```

### Anti-Pattern 4: No Fallback Mechanisms
**Problem:** Failing completely when ideal assignees are unavailable.
**Risk:** Tasks remain unassigned during critical situations.
**Solution:** Implement progressive fallback strategies.

**Wrong:**
```python
# Bad: No fallback
def assign_task(task, team):
    perfect_matches = [m for m in team if is_perfect_match(m, task)]
    if perfect_matches:
        return perfect_matches[0].id
    else:
        return None  # Task stays unassigned
```

**Correct:**
```python
# Good: Progressive fallback
def assign_task(task, team):
    # Level 1: Perfect match with availability
    perfect_matches = [
        m for m in team 
        if is_perfect_match(m, task) and m.availability and m.workload < 0.8
    ]
    if perfect_matches:
        return select_least_loaded(perfect_matches).id
    
    # Level 2: Close match with availability
    close_matches = [
        m for m in team 
        if is_close_match(m, task) and m.availability and m.workload < 0.8
    ]
    if close_matches:
        return select_least_loaded(close_matches).id
    
    # Level 3: Any available member with minimal skills
    any_matches = [
        m for m in team 
        if has_minimal_skills(m, task) and m.availability and m.workload < 0.9
    ]
    if any_matches:
        return select_least_loaded(any_matches).id
    
    # Level 4: Override constraints for critical tasks
    if task.priority == "critical":
        all_with_skills = [m for m in team if has_any_relevant_skill(m, task)]
        if all_with_skills:
            return select_most_available(all_with_skills).id
    
    return None  # Only return None as last resort
```

### Anti-Pattern 5: Inconsistent Assignment Logic
**Problem:** Different parts of the system using different assignment criteria.
**Risk:** Inconsistent behavior and confusion among team members.
**Solution:** Centralize assignment logic with configurable strategies.

**Wrong:**
```python
# Bad: Inconsistent logic in different places
def assign_frontend_task(task, team):
    # Uses one logic here
    return sorted(team, key=lambda m: m.css_experience, reverse=True)[0].id

def assign_backend_task(task, team):
    # Uses different logic here
    return sorted(team, key=lambda m: m.python_experience + m.java_experience, reverse=True)[0].id
```

**Correct:**
```python
# Good: Centralized, configurable logic
class AssignmentEngine:
    def __init__(self, config):
        self.config = config
    
    def assign_task(self, task, team):
        # Apply consistent scoring across all task types
        scored_candidates = []
        for member in team:
            score = self.calculate_composite_score(member, task)
            scored_candidates.append((member, score))
        
        # Sort and return best candidate
        best_candidate = max(scored_candidates, key=lambda x: x[1])
        return best_candidate[0].id
    
    def calculate_composite_score(self, member, task):
        # Consistent formula applied everywhere
        skill_score = self.calculate_skill_score(member, task)
        workload_score = self.calculate_workload_score(member)
        priority_score = self.calculate_priority_score(task)
        
        return (
            skill_score * self.config.skill_weight +
            workload_score * self.config.workload_weight +
            priority_score * self.config.priority_weight
        )
```