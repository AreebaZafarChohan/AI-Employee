"""Task analyzer skill for analyzing task content."""

from typing import Any, Dict
from datetime import datetime

from .skill_base import SkillBase, SkillExecutionError
from ..claude_client import ClaudeClient


class TaskAnalyzer(SkillBase):
    """Skill for analyzing task content and extracting key information."""

    ANALYSIS_PROMPT = """Analyze the following task and extract key information:

Task Content:
{content}

Please provide:
1. Task summary (1-2 sentences)
2. Key requirements (bullet points)
3. Estimated complexity (Low/Medium/High)
4. Dependencies or prerequisites
5. Suggested priority (P1-P4)

Format your response as a structured analysis."""

    def __init__(self, claude_client: ClaudeClient):
        """Initialize the task analyzer.

        Args:
            claude_client: Claude API client.
        """
        super().__init__(
            name="task_analyzer",
            description="Analyzes task content to extract requirements and metadata",
            version="1.0.0"
        )
        self.client = claude_client

    def validate_input(self, input_data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate input data for task analysis.

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
        """Execute task analysis.

        Args:
            input_data: Dictionary with task content.

        Returns:
            Dictionary with analysis results.
        """
        content = input_data["content"]
        task_id = input_data.get("task_id", "unknown")

        try:
            # Build prompt
            prompt = self.ANALYSIS_PROMPT.format(content=content)

            # Send to Claude
            response = self.client.send_request(
                prompt=prompt,
                system_prompt="You are a task analysis assistant. Analyze tasks and extract key information in a structured format."
            )

            if not response.get("success"):
                raise SkillExecutionError("Gemini API request failed")

            # Process response
            analysis = self._parse_analysis(response.get("content", ""))

            return {
                "success": True,
                "task_id": task_id,
                "analysis": analysis,
                "raw_response": response.get("content"),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            # Fallback to basic analysis
            return self._create_fallback_analysis(content, task_id, str(e))

    def _parse_analysis(self, response_content: str) -> Dict[str, Any]:
        """Parse analysis from Claude response.

        Args:
            response_content: Raw response content.

        Returns:
            Parsed analysis dictionary.
        """
        analysis = {
            "summary": "",
            "requirements": [],
            "complexity": "Medium",
            "dependencies": [],
            "priority": "P2"
        }

        lines = response_content.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()

            if 'summary' in line.lower() and ':' in line:
                current_section = 'summary'
                # Extract inline summary if present
                parts = line.split(':', 1)
                if len(parts) > 1 and parts[1].strip():
                    analysis['summary'] = parts[1].strip()
            elif 'requirement' in line.lower():
                current_section = 'requirements'
            elif 'complexity' in line.lower():
                current_section = 'complexity'
                for level in ['Low', 'Medium', 'High']:
                    if level.lower() in line.lower():
                        analysis['complexity'] = level
                        break
            elif 'dependenc' in line.lower() or 'prerequisite' in line.lower():
                current_section = 'dependencies'
            elif 'priority' in line.lower():
                current_section = 'priority'
                for p in ['P1', 'P2', 'P3', 'P4']:
                    if p in line:
                        analysis['priority'] = p
                        break
            elif line.startswith('-') or line.startswith('•'):
                item = line.lstrip('-•').strip()
                if current_section == 'requirements':
                    analysis['requirements'].append(item)
                elif current_section == 'dependencies':
                    analysis['dependencies'].append(item)
            elif current_section == 'summary' and line and not analysis['summary']:
                analysis['summary'] = line

        return analysis

    def _create_fallback_analysis(
        self,
        content: str,
        task_id: str,
        error: str
    ) -> Dict[str, Any]:
        """Create fallback analysis when Claude is unavailable.

        Args:
            content: Task content.
            task_id: Task identifier.
            error: Error message.

        Returns:
            Basic analysis dictionary.
        """
        # Extract title from content
        lines = content.split('\n')
        title = "Untitled Task"
        for line in lines:
            if line.strip().startswith('#'):
                title = line.strip().lstrip('#').strip()
                break

        # Estimate complexity based on content length
        complexity = "Low" if len(content) < 500 else "Medium" if len(content) < 2000 else "High"

        return {
            "success": True,
            "task_id": task_id,
            "analysis": {
                "summary": title,
                "requirements": ["Review task content", "Identify action items"],
                "complexity": complexity,
                "dependencies": [],
                "priority": "P2"
            },
            "fallback": True,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }

    def get_prompt_template(self) -> str:
        """Get the prompt template for this skill.

        Returns:
            Prompt template string.
        """
        return self.ANALYSIS_PROMPT
