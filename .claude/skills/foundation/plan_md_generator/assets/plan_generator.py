#!/usr/bin/env python3
"""
plan_generator.py
Generate structured Markdown implementation plans with validation
"""

import os
import sys
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class Step:
    """Represents a single implementation step"""
    number: int
    title: str
    objective: str
    actions: List[str]
    validation: List[str]
    owner: str = "TBD"
    duration: str = "TBD"
    dependencies: List[int] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    rollback: List[str] = field(default_factory=list)
    status: str = "pending"
    
    def to_markdown(self) -> str:
        """Convert step to Markdown format"""
        deps = ", ".join([f"Step {d}" for d in self.dependencies]) if self.dependencies else "None"
        
        md = f"""### Step {self.number}: {self.title}

**Status:** {self.status}
**Owner:** {self.owner}
**Duration:** {self.duration}
**Dependencies:** {deps}

#### Objective
{self.objective}

"""
        
        if self.prerequisites:
            md += "#### Prerequisites\n"
            for prereq in self.prerequisites:
                md += f"- {prereq}\n"
            md += "\n"
        
        md += "#### Actions\n"
        for action in self.actions:
            md += f"- [ ] {action}\n"
        md += "\n"
        
        md += "#### Validation\n"
        for validation in self.validation:
            md += f"- [ ] {validation}\n"
        md += "\n"
        
        if self.rollback:
            md += "#### Rollback\n"
            for rb in self.rollback:
                md += f"- {rb}\n"
            md += "\n"
        
        md += "---\n\n"
        return md


@dataclass
class Milestone:
    """Represents a project milestone"""
    number: int
    title: str
    target_date: str
    deliverables: List[str]
    exit_criteria: List[str]
    stakeholders: List[str] = field(default_factory=list)
    status: str = "not started"
    completion: int = 0
    
    def to_markdown(self) -> str:
        """Convert milestone to Markdown format"""
        md = f"""## Milestone {self.number}: {self.title}

**Target Date:** {self.target_date}
**Status:** {self.status}
**Completion:** {self.completion}%

### Deliverables
"""
        for deliverable in self.deliverables:
            md += f"- {deliverable}\n"
        
        md += "\n### Exit Criteria\n"
        for criterion in self.exit_criteria:
            md += f"- [ ] {criterion}\n"
        
        if self.stakeholders:
            md += "\n### Stakeholders\n"
            for stakeholder in self.stakeholders:
                md += f"- {stakeholder}\n"
        
        md += "\n---\n\n"
        return md


@dataclass
class Plan:
    """Represents a complete implementation plan"""
    project_name: str
    executive_summary: str
    goals: List[str]
    success_criteria: List[str]
    steps: List[Step] = field(default_factory=list)
    milestones: List[Milestone] = field(default_factory=list)
    version: str = "1.0.0"
    owner: str = "TBD"
    status: str = "draft"
    target_date: str = "TBD"
    dependencies: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    testing_strategy: str = ""
    rollout_plan: str = ""
    rollback_strategy: str = ""
    references: List[str] = field(default_factory=list)
    
    def validate(self) -> List[str]:
        """Validate plan completeness and correctness"""
        errors = []
        
        # Check required fields
        if not self.project_name:
            errors.append("Project name is required")
        if not self.executive_summary:
            errors.append("Executive summary is required")
        if not self.goals:
            errors.append("At least one goal is required")
        if not self.success_criteria:
            errors.append("At least one success criterion is required")
        if not self.steps:
            errors.append("At least one implementation step is required")
        
        # Validate step dependencies
        step_numbers = {step.number for step in self.steps}
        for step in self.steps:
            for dep in step.dependencies:
                if dep not in step_numbers:
                    errors.append(f"Step {step.number} references non-existent dependency: Step {dep}")
                if dep >= step.number:
                    errors.append(f"Step {step.number} depends on later step {dep} (circular/forward dependency)")
        
        # Check for gaps in step numbering
        expected_numbers = set(range(1, len(self.steps) + 1))
        if step_numbers != expected_numbers:
            errors.append(f"Step numbering has gaps or duplicates: {sorted(step_numbers)}")
        
        # Validate each step
        for step in self.steps:
            if not step.title:
                errors.append(f"Step {step.number} missing title")
            if not step.objective:
                errors.append(f"Step {step.number} missing objective")
            if not step.actions:
                errors.append(f"Step {step.number} has no actions defined")
            if not step.validation:
                errors.append(f"Step {step.number} has no validation criteria")
        
        # Validate milestones
        for milestone in self.milestones:
            if not milestone.deliverables:
                errors.append(f"Milestone {milestone.number} has no deliverables")
            if not milestone.exit_criteria:
                errors.append(f"Milestone {milestone.number} has no exit criteria")
        
        return errors
    
    def to_markdown(self) -> str:
        """Generate complete Markdown plan"""
        date = datetime.now().strftime("%Y-%m-%d")
        
        md = f"""# {self.project_name} - Implementation Plan

**Generated:** {date}
**Version:** {self.version}
**Status:** {self.status}
**Owner:** {self.owner}
**Target Completion:** {self.target_date}

---

## Executive Summary

{self.executive_summary}

**Goals:**
"""
        for goal in self.goals:
            md += f"- {goal}\n"
        
        md += "\n**Success Criteria:**\n"
        for criterion in self.success_criteria:
            md += f"- {criterion}\n"
        
        md += "\n---\n\n## Prerequisites\n\n"
        
        if self.dependencies:
            md += "### Dependencies\n"
            for dep in self.dependencies:
                md += f"- {dep}\n"
            md += "\n"
        
        if self.resources:
            md += "### Resources Required\n"
            for resource in self.resources:
                md += f"- {resource}\n"
            md += "\n"
        
        if self.risks:
            md += "### Risks\n"
            for risk in self.risks:
                md += f"- {risk}\n"
            md += "\n"
        
        md += "---\n\n## Implementation Steps\n\n"
        for step in sorted(self.steps, key=lambda s: s.number):
            md += step.to_markdown()
        
        if self.milestones:
            md += "---\n\n## Milestones\n\n"
            for milestone in sorted(self.milestones, key=lambda m: m.number):
                md += milestone.to_markdown()
        
        if self.testing_strategy:
            md += f"---\n\n## Testing Strategy\n\n{self.testing_strategy}\n\n"
        
        if self.rollout_plan:
            md += f"---\n\n## Rollout Plan\n\n{self.rollout_plan}\n\n"
        
        if self.rollback_strategy:
            md += f"---\n\n## Rollback Strategy\n\n{self.rollback_strategy}\n\n"
        
        if self.references:
            md += "---\n\n## References\n\n"
            for ref in self.references:
                md += f"- {ref}\n"
            md += "\n"
        
        md += f"""---

## Change Log

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| {date} | {self.version} | {self.owner} | Initial plan |

"""
        return md


def load_plan_from_json(filepath: str) -> Plan:
    """Load plan from JSON file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    steps = [Step(**step_data) for step_data in data.get('steps', [])]
    milestones = [Milestone(**ms_data) for ms_data in data.get('milestones', [])]
    
    plan = Plan(
        project_name=data['project_name'],
        executive_summary=data['executive_summary'],
        goals=data['goals'],
        success_criteria=data['success_criteria'],
        steps=steps,
        milestones=milestones,
        version=data.get('version', '1.0.0'),
        owner=data.get('owner', 'TBD'),
        status=data.get('status', 'draft'),
        target_date=data.get('target_date', 'TBD'),
        dependencies=data.get('dependencies', []),
        resources=data.get('resources', []),
        risks=data.get('risks', []),
        testing_strategy=data.get('testing_strategy', ''),
        rollout_plan=data.get('rollout_plan', ''),
        rollback_strategy=data.get('rollback_strategy', ''),
        references=data.get('references', [])
    )
    
    return plan


def main():
    """CLI entry point"""
    if len(sys.argv) < 3:
        print("Usage: plan_generator.py <input.json> <output.md>")
        print("       plan_generator.py --validate <input.json>")
        sys.exit(1)
    
    if sys.argv[1] == '--validate':
        plan = load_plan_from_json(sys.argv[2])
        errors = plan.validate()
        
        if errors:
            print(f"❌ Plan validation failed with {len(errors)} error(s):")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
        else:
            print("✅ Plan validation passed!")
            sys.exit(0)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Load and validate plan
    plan = load_plan_from_json(input_file)
    errors = plan.validate()
    
    if errors:
        print(f"❌ Plan validation failed with {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    
    # Generate Markdown
    markdown = plan.to_markdown()
    
    # Write output
    with open(output_file, 'w') as f:
        f.write(markdown)
    
    print(f"✅ Plan generated successfully: {output_file}")
    print(f"   - {len(plan.steps)} steps")
    print(f"   - {len(plan.milestones)} milestones")


if __name__ == '__main__':
    main()
