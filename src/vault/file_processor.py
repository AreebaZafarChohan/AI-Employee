"""File processor for vault workflow operations."""

import time
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta

from ..utils.file_utils import FileUtils
from ..utils.logger import get_logger, ProcessingLogger
from ..utils.config import Config
from ..vault.vault_manager import VaultManager
from ..vault.validators import InputValidator


class FileProcessor:
    """Processes files through the vault workflow."""

    def __init__(self, config: Config):
        """Initialize the file processor.

        Args:
            config: Configuration object.
        """
        self.config = config
        self.vault_manager = VaultManager(config.vault_path)
        self.validator = InputValidator()
        self.logger = get_logger("processor")
        self.processing_logger = ProcessingLogger()

    def process_needs_action_files(self) -> dict:
        """Process all files in the Needs_Action folder.

        Returns:
            Dictionary with processing results.
        """
        result = {
            "success": True,
            "found_count": 0,
            "processed_count": 0,
            "plan_count": 0,
            "duration": 0.0,
            "errors": []
        }

        start_time = time.time()

        try:
            # Get files from Needs_Action
            needs_action_path = self.vault_manager.get_folder_path("needs_action")
            files = FileUtils.list_files(needs_action_path, ["*.md", "*.txt"])
            result["found_count"] = len(files)

            self.logger.info(f"Found {len(files)} files in Needs_Action")

            # Process each file
            for file_path in files:
                try:
                    file_result = self._process_single_file(file_path)
                    if file_result["success"]:
                        result["processed_count"] += 1
                        if file_result.get("plan_created"):
                            result["plan_count"] += 1
                    else:
                        result["errors"].append(f"{file_path.name}: {file_result.get('error', 'Unknown error')}")

                except Exception as e:
                    result["errors"].append(f"{file_path.name}: {str(e)}")
                    self.logger.error(f"Failed to process {file_path}: {e}")

        except Exception as e:
            result["success"] = False
            result["errors"].append(str(e))
            self.logger.error(f"Processing failed: {e}")

        result["duration"] = time.time() - start_time

        # Update dashboard
        try:
            self.vault_manager.update_dashboard()
        except Exception as e:
            self.logger.warning(f"Failed to update dashboard: {e}")

        return result

    def _process_single_file(self, file_path: Path) -> dict:
        """Process a single task file.

        Args:
            file_path: Path to the file to process.

        Returns:
            Dictionary with processing result.
        """
        result = {
            "success": False,
            "plan_created": False,
            "error": None
        }

        operation_id = f"process_{file_path.stem}"
        self.processing_logger.start_operation(operation_id, f"Processing {file_path.name}")

        try:
            # Read file content
            content = FileUtils.read_file(file_path)

            # Validate input
            is_valid, error_message = self.validator.validate_content(content)
            if not is_valid:
                result["error"] = f"Validation failed: {error_message}"
                return result

            # Sanitize content
            sanitized_content = self.validator.sanitize_content(content)

            # Process with Claude
            plan_content = self._generate_plan_with_claude(file_path.stem, sanitized_content)

            if plan_content:
                # Create plan file
                plan_path = self._create_plan_file(file_path.stem, plan_content)
                result["plan_created"] = True
                result["plan_path"] = str(plan_path)

                # Move original file to indicate processing complete
                # (or delete it, depending on requirements)
                self.logger.info(f"Plan created: {plan_path}")

            result["success"] = True

        except Exception as e:
            result["error"] = str(e)
            self.processing_logger.log_error(operation_id, e)

        finally:
            duration = self.processing_logger.end_operation(
                operation_id,
                f"Completed {file_path.name}",
                result["success"]
            )

            # Check processing time limit
            if duration > self.config.max_processing_time:
                self.logger.warning(
                    f"Processing time exceeded limit: {duration:.2f}s > {self.config.max_processing_time}s"
                )

        return result

    def _generate_plan_with_claude(self, task_id: str, content: str) -> Optional[str]:
        """Generate a plan using Claude.

        Args:
            task_id: Unique identifier for the task.
            content: Task content.

        Returns:
            Generated plan content or None if failed.
        """
        try:
            # Import here to avoid circular imports
            from ..claude.claude_client import ClaudeClient
            from ..claude.agent_skills.plan_generator import PlanGenerator

            client = ClaudeClient(self.config)
            plan_generator = PlanGenerator(client)

            result = plan_generator.run({
                "task_id": task_id,
                "content": content
            })

            return result.get("plan_content")

        except Exception as e:
            self.logger.error(f"Gemini processing failed: {e}")
            # Fallback: create a simple plan structure
            return self._create_fallback_plan(task_id, content)

    def _create_fallback_plan(self, task_id: str, content: str) -> str:
        """Create a fallback plan when Claude is unavailable.

        Args:
            task_id: Task identifier.
            content: Original task content.

        Returns:
            Simple plan content.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""# Plan: {task_id}

## Status
- **Created**: {timestamp}
- **Status**: Draft
- **Processing**: Manual review required

## Original Task

{content}

## Proposed Approach

1. Review the task requirements
2. Identify key deliverables
3. Create action items
4. Execute and validate

## Notes

*This plan was generated automatically. Please review and update as needed.*

---

*Generated: {timestamp}*
"""

    def _create_plan_file(self, task_id: str, content: str) -> Path:
        """Create a plan file in the Plans folder.

        Args:
            task_id: Task identifier.
            content: Plan content.

        Returns:
            Path to the created plan file.
        """
        plans_path = self.vault_manager.get_folder_path("plans")
        FileUtils.ensure_directory(plans_path)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Plan_{task_id}_{timestamp}.md"
        file_path = plans_path / filename

        FileUtils.write_file(file_path, content)
        return file_path

    def move_completed_task(self, plan_id: str) -> dict:
        """Move a completed plan to the Done folder.

        Args:
            plan_id: Identifier of the plan to complete.

        Returns:
            Dictionary with completion result.
        """
        result = {
            "success": False,
            "error": None
        }

        try:
            # Find the plan file
            plans_path = self.vault_manager.get_folder_path("plans")
            plan_files = FileUtils.list_files(plans_path, [f"*{plan_id}*.md"])

            if not plan_files:
                result["error"] = f"Plan with ID '{plan_id}' not found in /Plans"
                return result

            plan_file = plan_files[0]

            # Update plan status
            content = FileUtils.read_file(plan_file)
            updated_content = self._update_plan_status(content, "Completed")

            # Move to Done folder
            done_path = self.vault_manager.get_folder_path("done")
            FileUtils.ensure_directory(done_path)

            dest_path = done_path / plan_file.name
            FileUtils.write_file(dest_path, updated_content)
            FileUtils.delete_file(plan_file)

            result["success"] = True
            self.logger.info(f"Plan completed and moved to Done: {plan_file.name}")

            # Apply retention policy
            self._apply_retention_policy()

            # Update dashboard
            self.vault_manager.update_dashboard()

        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"Failed to complete task: {e}")

        return result

    def _update_plan_status(self, content: str, new_status: str) -> str:
        """Update the status in a plan file.

        Args:
            content: Plan content.
            new_status: New status value.

        Returns:
            Updated content.
        """
        lines = content.split("\n")
        updated_lines = []

        for line in lines:
            if line.startswith("- **Status**:"):
                line = f"- **Status**: {new_status}"
            updated_lines.append(line)

        # Add completion timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updated_lines.append(f"\n---\n*Completed: {timestamp}*")

        return "\n".join(updated_lines)

    def _apply_retention_policy(self) -> None:
        """Apply data retention policy to Done folder."""
        done_path = self.vault_manager.get_folder_path("done")
        retention_days = self.config.retention_days
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        files = FileUtils.list_files(done_path, ["*.md"])
        for file_path in files:
            try:
                modified_time = FileUtils.get_file_modified_time(file_path)
                if modified_time < cutoff_date:
                    FileUtils.delete_file(file_path)
                    self.logger.info(f"Deleted expired file: {file_path.name}")
            except Exception as e:
                self.logger.warning(f"Failed to check retention for {file_path}: {e}")
