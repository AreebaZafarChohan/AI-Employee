"""Plan generator skill for creating structured plans."""

from typing import Any, Dict
from datetime import datetime

from .skill_base import SkillBase, SkillExecutionError
from ..claude_client import ClaudeClient


class PlanGenerator(SkillBase):
    """Skill for generating structured plans from task content."""

    PLAN_PROMPT = """Create a detailed plan for the following task:

Task ID: {task_id}
Task Content:
{content}

Generate a comprehensive plan with:
1. Clear objectives
2. Step-by-step approach
3. Timeline estimates
4. Risk considerations
5. Success criteria

Format the plan in Markdown with clear sections."""

    def __init__(self, claude_client: ClaudeClient):
        """Initialize the plan generator.

        Args:
            claude_client: Claude API client.
        """
        super().__init__(
            name="plan_generator",
            description="Generates structured plans from task descriptions",
            version="1.0.0"
        )
        self.client = claude_client

    def validate_input(self, input_data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate input data for plan generation.

        Args:
            input_data: Input data containing task content.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if "content" not in input_data:
            return False, "Missing required field: content"

        content = input_data["content"]
        if not content or not content.strip():
            return False, "Content cannot be empty"

        if len(content) > 50000:
            return False, "Content exceeds maximum length (50000 characters)"

        return True, ""

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plan generation.

        Args:
            input_data: Dictionary with task content.

        Returns:
            Dictionary with generated plan.
        """
        content = input_data["content"]
        task_id = input_data.get("task_id", "task")

        try:
            # Build prompt
            prompt = self.PLAN_PROMPT.format(task_id=task_id, content=content)

            # Send to Claude
            response = self.client.send_request(
                prompt=prompt,
                system_prompt="You are a planning assistant. Create detailed, actionable plans in Markdown format."
            )

            if not response.get("success"):
                raise SkillExecutionError("Gemini API request failed")

            plan_content = response.get("content", "")

            # Ensure plan has proper structure
            if not plan_content.startswith('#'):
                plan_content = f"# Plan: {task_id}\n\n{plan_content}"

            # Add metadata
            plan_content = self._add_plan_metadata(plan_content, task_id)

            return {
                "success": True,
                "task_id": task_id,
                "plan_content": plan_content,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            # Fallback to basic plan
            return self._create_fallback_plan(content, task_id, str(e))

    def _add_plan_metadata(self, content: str, task_id: str) -> str:
        """Add metadata section to plan content.

        Args:
            content: Plan content.
            task_id: Task identifier.

        Returns:
            Content with metadata added.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Check if status section exists
        if "## Status" not in content and "**Status**" not in content:
            # Add status section after title
            lines = content.split('\n')
            result = []
            title_found = False

            for i, line in enumerate(lines):
                result.append(line)
                if line.startswith('# ') and not title_found:
                    title_found = True
                    result.append("")
                    result.append("## Status")
                    result.append(f"- **Task ID**: {task_id}")
                    result.append(f"- **Created**: {timestamp}")
                    result.append("- **Status**: Draft")
                    result.append("")

            content = '\n'.join(result)

        return content

    def _create_fallback_plan(
        self,
        content: str,
        task_id: str,
        error: str
    ) -> Dict[str, Any]:
        """Create fallback plan when Claude is unavailable.

        Args:
            content: Task content.
            task_id: Task identifier.
            error: Error message.

        Returns:
            Basic plan dictionary.
        """
        # Extract title from content
        lines = content.split('\n')
        title = task_id
        for line in lines:
            if line.strip().startswith('#'):
                title = line.strip().lstrip('#').strip()
                break

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        plan_content = f"""# Plan: {title}

## Status
- **Task ID**: {task_id}
- **Created**: {timestamp}
- **Status**: Draft
- **Processing**: Manual review required

## Original Task

{content}

## Objectives

1. Review and understand the task requirements
2. Identify key deliverables and success criteria
3. Create actionable steps for completion
4. Validate and verify results

## Approach

### Phase 1: Analysis
- Review task description thoroughly
- Identify dependencies and prerequisites
- Assess resource requirements
- Define scope boundaries

### Phase 2: Planning
- Break down into smaller tasks
- Establish timeline and milestones
- Identify potential risks
- Prepare mitigation strategies

### Phase 3: Execution
- Implement required changes step by step
- Document progress and decisions
- Handle edge cases and exceptions
- Maintain communication with stakeholders

### Phase 4: Validation
- Verify all requirements are met
- Test functionality and quality
- Document results and learnings
- Prepare for handoff or closure

## Timeline

| Phase | Estimated Duration | Status |
|-------|-------------------|--------|
| Analysis | 1 day | Pending |
| Planning | 1 day | Pending |
| Execution | 2-3 days | Pending |
| Validation | 1 day | Pending |

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Unclear requirements | High | Seek clarification early |
| Scope creep | Medium | Maintain focus on core deliverables |
| Dependencies | Medium | Identify and track blockers |

## Success Criteria

- [ ] All requirements addressed
- [ ] Quality standards met
- [ ] Documentation complete
- [ ] Stakeholder approval obtained

## Notes

*This plan was generated automatically as Claude API was unavailable.*
*Error: {error}*
*Please review and update as needed.*

---

*Generated: {timestamp}*
"""

        return {
            "success": True,
            "task_id": task_id,
            "plan_content": plan_content,
            "fallback": True,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }

    def get_prompt_template(self) -> str:
        """Get the prompt template for this skill.

        Returns:
            Prompt template string.
        """
        return self.PLAN_PROMPT
