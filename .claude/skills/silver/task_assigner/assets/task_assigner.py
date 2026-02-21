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