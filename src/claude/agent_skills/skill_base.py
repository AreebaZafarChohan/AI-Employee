"""Base class for Claude Agent Skills."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime


class SkillBase(ABC):
    """Base class for all Claude agent skills.

    All AI behavior should be implemented via skills that extend this base class.
    No inline logic - all processing should be modular and extensible.
    """

    def __init__(self, name: str, description: str, version: str = "1.0.0"):
        """Initialize the skill.

        Args:
            name: Unique identifier for the skill.
            description: Human-readable description of what the skill does.
            version: Skill version.
        """
        self.name = name
        self.description = description
        self.version = version
        self.active = True
        self._last_execution: Optional[datetime] = None
        self._execution_count = 0

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the skill with the given input data.

        Args:
            input_data: Dictionary containing skill-specific input parameters.

        Returns:
            Dictionary containing skill execution results.

        Raises:
            SkillExecutionError: If skill execution fails.
        """
        pass

    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate the input data for this skill.

        Args:
            input_data: Dictionary containing skill-specific input parameters.

        Returns:
            Tuple of (is_valid, error_message).
        """
        pass

    def get_prompt_template(self) -> str:
        """Get the prompt template for this skill.

        Returns:
            String template for Claude prompts.
        """
        return ""

    def pre_execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Hook called before execute. Can be overridden for preprocessing.

        Args:
            input_data: Input data for the skill.

        Returns:
            Preprocessed input data.
        """
        return input_data

    def post_execute(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Hook called after execute. Can be overridden for postprocessing.

        Args:
            result: Result from skill execution.

        Returns:
            Postprocessed result.
        """
        self._last_execution = datetime.now()
        self._execution_count += 1
        return result

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the skill with full lifecycle management.

        Args:
            input_data: Input data for the skill.

        Returns:
            Skill execution results.

        Raises:
            SkillValidationError: If input validation fails.
            SkillExecutionError: If skill execution fails.
        """
        if not self.active:
            raise SkillExecutionError(f"Skill '{self.name}' is not active")

        # Validate input
        is_valid, error_message = self.validate_input(input_data)
        if not is_valid:
            raise SkillValidationError(f"Input validation failed: {error_message}")

        # Pre-execute hook
        processed_input = self.pre_execute(input_data)

        # Execute skill
        result = self.execute(processed_input)

        # Post-execute hook
        final_result = self.post_execute(result)

        return final_result

    def get_metadata(self) -> Dict[str, Any]:
        """Get skill metadata.

        Returns:
            Dictionary containing skill metadata.
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "active": self.active,
            "last_execution": self._last_execution.isoformat() if self._last_execution else None,
            "execution_count": self._execution_count
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', version='{self.version}')"


class SkillExecutionError(Exception):
    """Exception raised when skill execution fails."""
    pass


class SkillValidationError(Exception):
    """Exception raised when skill input validation fails."""
    pass
