# Task Assigner - Common Assignment Patterns

## Overview
This document describes common patterns for implementing task assignment strategies based on workload, skillset, and priority.

---

## Pattern 1: Round-Robin with Skill Filtering

### Use Case
Distribute tasks evenly among qualified team members while ensuring basic skill requirements are met.

### Implementation
```python
def round_robin_assignment(tasks, team_members):
    """
    Assign tasks using round-robin selection among qualified members.
    """
    # Filter members by required skills for each task
    assignments = []
    
    for task in tasks:
        qualified_members = [
            member for member in team_members
            if has_required_skills(member, task) and member.availability
        ]
        
        if not qualified_members:
            assignments.append((task.id, None, "No qualified members"))
            continue
        
        # Sort by last assignment time to ensure even distribution
        qualified_members.sort(key=lambda m: getattr(m, 'last_assignment_time', datetime.min))
        
        # Select the member with oldest assignment
        selected_member = qualified_members[0]
        
        assignments.append((task.id, selected_member.id, "Round-robin selection"))
        
        # Update last assignment time
        selected_member.last_assignment_time = datetime.now()
    
    return assignments
```

### Benefits
- Ensures even distribution among qualified members
- Simple to implement and understand
- Prevents any single member from being overwhelmed

---

## Pattern 2: Skill-Based Weighted Assignment

### Use Case
Prioritize assignment to team members with the highest proficiency in required skills.

### Implementation
```python
def skill_weighted_assignment(tasks, team_members):
    """
    Assign tasks based on weighted skill matching scores.
    """
    assignments = []
    
    for task in tasks:
        candidate_scores = []
        
        for member in team_members:
            if not (member.availability and has_required_skills(member, task)):
                continue
            
            # Calculate skill proficiency score
            skill_score = calculate_skill_proficiency(member, task)
            
            # Factor in current workload
            workload_factor = 1 - member.current_workload
            
            # Combined score
            total_score = skill_score * 0.7 + workload_factor * 0.3
            
            candidate_scores.append((member, total_score))
        
        if not candidate_scores:
            assignments.append((task.id, None, "No available qualified members"))
            continue
        
        # Select member with highest score
        best_candidate = max(candidate_scores, key=lambda x: x[1])
        assignments.append((task.id, best_candidate[0].id, f"Skill-weighted: {best_candidate[1]:.2f}"))
    
    return assignments
```

### Benefits
- Optimizes for task completion quality
- Considers both skill and availability
- Adaptable weighting for different project needs

---

## Pattern 3: Priority-Aware Load Balancer

### Use Case
Balance workload while ensuring high-priority tasks are assigned to capable members.

### Implementation
```python
def priority_load_balanced_assignment(tasks, team_members):
    """
    Balance workload while prioritizing critical tasks.
    """
    # Separate tasks by priority
    critical_tasks = [t for t in tasks if t.priority == "critical"]
    high_tasks = [t for t in tasks if t.priority == "high"]
    medium_tasks = [t for t in tasks if t.priority == "medium"]
    low_tasks = [t for t in tasks if t.priority == "low"]
    
    assignments = []
    updated_members = [m for m in team_members]  # Copy to track changes
    
    # Process in priority order
    for task_list, priority in [(critical_tasks, "critical"), 
                                (high_tasks, "high"), 
                                (medium_tasks, "medium"), 
                                (low_tasks, "low")]:
        
        for task in task_list:
            qualified_members = [
                member for member in updated_members
                if has_required_skills(member, task) and member.availability
            ]
            
            if not qualified_members:
                assignments.append((task.id, None, f"No qualified members for {priority} task"))
                continue
            
            # For high-priority tasks, prefer members with lower workload
            if priority in ["critical", "high"]:
                best_member = min(qualified_members, key=lambda m: m.current_workload)
            else:
                # For lower priority, consider skill match more heavily
                best_member = max(qualified_members, 
                                key=lambda m: calculate_skill_match(m, task) * 0.6 + 
                                             (1 - m.current_workload) * 0.4)
            
            assignments.append((task.id, best_member.id, f"{priority.capitalize()} priority assignment"))
            
            # Update member's workload for subsequent assignments
            best_member.current_workload = min(1.0, best_member.current_workload + 
                                             task.estimated_hours / best_member.max_daily_hours)
    
    return assignments
```

### Benefits
- Ensures critical tasks get appropriate attention
- Maintains workload balance across the team
- Prevents overloading of members with critical tasks

---

## Pattern 4: Dynamic Pool Assignment

### Use Case
Dynamically form specialized pools of team members based on current needs and skills.

### Implementation
```python
def dynamic_pool_assignment(tasks, team_members):
    """
    Form dynamic pools based on task requirements and assign accordingly.
    """
    # Group members by primary skill areas
    skill_pools = {}
    for member in team_members:
        for skill in member.skills:
            if skill not in skill_pools:
                skill_pools[skill] = []
            skill_pools[skill].append(member)
    
    assignments = []
    
    for task in tasks:
        # Find the best skill pool for this task
        best_pool = None
        best_pool_score = -1
        
        for skill in task.required_skills:
            if skill in skill_pools:
                # Calculate pool readiness score
                available_members = [m for m in skill_pools[skill] if m.availability]
                avg_workload = sum(m.current_workload for m in available_members) / len(available_members) if available_members else 1.0
                readiness_score = len(available_members) * (1 - avg_workload)
                
                if readiness_score > best_pool_score:
                    best_pool = skill_pools[skill]
                    best_pool_score = readiness_score
        
        if not best_pool:
            assignments.append((task.id, None, "No suitable skill pool found"))
            continue
        
        # Within the best pool, select the most appropriate member
        qualified_in_pool = [
            member for member in best_pool
            if has_required_skills(member, task) and member.availability
        ]
        
        if not qualified_in_pool:
            assignments.append((task.id, None, "No available qualified members in skill pool"))
            continue
        
        # Select based on workload and skill match
        best_member = max(qualified_in_pool, 
                         key=lambda m: calculate_skill_match(m, task) * 0.5 + 
                                      (1 - m.current_workload) * 0.5)
        
        assignments.append((task.id, best_member.id, "Dynamic pool assignment"))
    
    return assignments
```

### Benefits
- Efficiently utilizes specialized skills
- Forms flexible teams based on current needs
- Improves overall team utilization

---

## Pattern 5: Deadline-Driven Assignment

### Use Case
Prioritize task assignment based on approaching deadlines and required effort.

### Implementation
```python
def deadline_driven_assignment(tasks, team_members):
    """
    Assign tasks based on urgency (deadline proximity) and required effort.
    """
    # Sort tasks by urgency (time until deadline / estimated hours)
    urgent_tasks = []
    for task in tasks:
        if task.deadline:
            time_to_deadline = (task.deadline - datetime.now()).total_seconds() / 3600  # in hours
            urgency_ratio = time_to_deadline / task.estimated_hours if task.estimated_hours > 0 else float('inf')
            urgent_tasks.append((task, urgency_ratio))
    
    # Sort by urgency ratio (lower is more urgent)
    urgent_tasks.sort(key=lambda x: x[1])
    
    assignments = []
    member_workloads = {m.id: m.current_workload for m in team_members}
    
    for task, urgency_ratio in urgent_tasks:
        qualified_members = [
            member for member in team_members
            if (has_required_skills(member, task) and 
                member.availability and 
                member_workloads[member.id] < 0.9)  # Leave some buffer
        ]
        
        if not qualified_members:
            assignments.append((task.id, None, "No available qualified members"))
            continue
        
        # For urgent tasks, select member with lowest current workload
        best_member = min(qualified_members, key=lambda m: member_workloads[m.id])
        
        assignments.append((task.id, best_member.id, f"Deadline-driven (urgency: {urgency_ratio:.2f})"))
        
        # Update projected workload
        hours_per_day = best_member.max_daily_hours
        projected_increase = task.estimated_hours / hours_per_day
        member_workloads[best_member.id] = min(1.0, member_workloads[best_member.id] + projected_increase)
    
    return assignments
```

### Benefits
- Addresses time-sensitive tasks promptly
- Considers effort required vs. time available
- Helps meet critical deadlines

---

## Pattern 6: Learning Opportunity Assignment

### Use Case
Intentionally assign tasks to develop team members' skills while maintaining productivity.

### Implementation
```python
def learning_opportunity_assignment(tasks, team_members):
    """
    Assign tasks to promote skill development while maintaining productivity.
    """
    assignments = []
    
    for task in tasks:
        # Find members who have some related skills but could grow
        growth_candidates = []
        qualified_members = []
        
        for member in team_members:
            if not member.availability:
                continue
                
            skill_overlap = len(set(member.skills) & set(task.required_skills))
            if skill_overlap > 0 and skill_overlap < len(task.required_skills):
                # Has some skills but not all - good for learning
                growth_candidates.append(member)
            elif has_required_skills(member, task):
                # Fully qualified
                qualified_members.append(member)
        
        # Decide based on task priority
        if task.priority in ["low", "medium"]:
            # For lower priority tasks, favor growth candidates
            if growth_candidates:
                # Among growth candidates, pick one with lowest workload
                best_member = min(growth_candidates, key=lambda m: m.current_workload)
                assignments.append((task.id, best_member.id, "Learning opportunity assignment"))
            elif qualified_members:
                best_member = min(qualified_members, key=lambda m: m.current_workload)
                assignments.append((task.id, best_member.id, "Standard assignment"))
            else:
                assignments.append((task.id, None, "No suitable members"))
        else:
            # For high priority tasks, prioritize qualified members
            if qualified_members:
                best_member = min(qualified_members, key=lambda m: m.current_workload)
                assignments.append((task.id, best_member.id, "Priority assignment"))
            elif growth_candidates:
                # If no fully qualified, pick best available
                best_member = min(growth_candidates, key=lambda m: m.current_workload)
                assignments.append((task.id, best_member.id, "Priority assignment to developing member"))
            else:
                assignments.append((task.id, None, "No suitable members"))
    
    return assignments
```

### Benefits
- Promotes continuous learning and development
- Balances skill building with productivity
- Increases team versatility over time

---

## Pattern 7: Collaborative Assignment

### Use Case
Assign complex tasks requiring multiple skills to a team of specialists.

### Implementation
```python
def collaborative_assignment(tasks, team_members):
    """
    Assign complex tasks to a team of specialists with complementary skills.
    """
    assignments = []
    
    for task in tasks:
        # Identify required skill sets
        required_skills = set(task.required_skills)
        
        # Find potential collaborators
        skill_to_members = {}
        for skill in required_skills:
            skill_to_members[skill] = [
                m for m in team_members 
                if skill in m.skills and m.availability
            ]
        
        # Check if we have members for all required skills
        if any(len(members) == 0 for members in skill_to_members.values()):
            assignments.append((task.id, None, "Missing required skills in team"))
            continue
        
        # Form a team with minimum overlap and maximum coverage
        selected_team = set()
        for skill, members in skill_to_members.items():
            # Pick the member with the lowest workload who isn't already selected
            available_members = [m for m in members if m.id not in selected_team]
            if available_members:
                best_member = min(available_members, key=lambda m: m.current_workload)
                selected_team.add(best_member.id)
        
        if len(selected_team) < 2:
            # If only one member selected, treat as regular assignment
            solo_member = next(m for m in team_members if m.id in selected_team)
            assignments.append((task.id, solo_member.id, "Solo assignment"))
        else:
            # Create a collaborative assignment
            team_list = list(selected_team)
            assignments.append((task.id, team_list, f"Collaborative team of {len(team_list)} members"))
    
    return assignments
```

### Benefits
- Leverages collective expertise for complex tasks
- Distributes workload for large tasks
- Facilitates knowledge sharing between specialists