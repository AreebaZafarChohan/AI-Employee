"""Vault manager for Obsidian vault operations."""

import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from ..utils.file_utils import FileUtils
from ..utils.logger import get_logger


class VaultManager:
    """Manages Obsidian vault structure and operations."""

    REQUIRED_FOLDERS = ["Needs_Action", "Plans", "Done"]

    DASHBOARD_TEMPLATE = """# AI Employee Dashboard

## Quick Status

| Folder | Count |
|--------|-------|
| Needs Action | 0 |
| Plans | 0 |
| Done | 0 |

## Recent Activity

*No recent activity*

---

*Last updated: {timestamp}*
"""

    HANDBOOK_TEMPLATE = """# Company Handbook

## AI Employee Guidelines

This vault is managed by your Personal AI Employee. Below are the guidelines for how the system operates.

## Folder Structure

### /Needs_Action
Tasks that require processing by the AI Employee. Place new tasks here or use the file watcher.

### /Plans
Generated plans created by the AI Employee after processing tasks from /Needs_Action.

### /Done
Completed tasks and plans that have been finalized.

## Workflow

1. **Input**: Place task files in the watched directory or directly in /Needs_Action
2. **Processing**: AI Employee processes tasks and creates plans
3. **Review**: Review generated plans in /Plans
4. **Completion**: Mark plans as done to move them to /Done

## Data Retention

Completed tasks in /Done are retained for 30 days by default.

## Security

- No secrets should be stored in this vault
- All inputs are sanitized before processing
- Safe-by-default behavior is enforced

---

*Created: {timestamp}*
"""

    def __init__(self, vault_path: str | Path):
        """Initialize the vault manager.

        Args:
            vault_path: Path to the Obsidian vault.
        """
        self.vault_path = Path(vault_path)
        self.logger = get_logger("vault_manager")

    def create_vault(self) -> dict:
        """Create the initial vault structure.

        Returns:
            Dictionary with creation status and details.
        """
        result = {
            "success": True,
            "vault_path": str(self.vault_path),
            "created_folders": [],
            "created_files": [],
            "skipped_files": [],
            "errors": []
        }

        try:
            # Create vault directory
            FileUtils.ensure_directory(self.vault_path)
            self.logger.info(f"Vault directory ensured: {self.vault_path}")

            # Create required folders
            for folder in self.REQUIRED_FOLDERS:
                folder_path = self.vault_path / folder
                FileUtils.ensure_directory(folder_path)
                result["created_folders"].append(folder)
                self.logger.info(f"Created folder: {folder}")

            # Create Dashboard.md
            dashboard_path = self.vault_path / "Dashboard.md"
            if not dashboard_path.exists():
                content = self.DASHBOARD_TEMPLATE.format(
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                FileUtils.write_file(dashboard_path, content)
                result["created_files"].append("Dashboard.md")
                self.logger.info("Created Dashboard.md")
            else:
                result["skipped_files"].append("Dashboard.md (already exists)")
                self.logger.info("Skipped Dashboard.md (already exists)")

            # Create Company_Handbook.md
            handbook_path = self.vault_path / "Company_Handbook.md"
            if not handbook_path.exists():
                content = self.HANDBOOK_TEMPLATE.format(
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                FileUtils.write_file(handbook_path, content)
                result["created_files"].append("Company_Handbook.md")
                self.logger.info("Created Company_Handbook.md")
            else:
                result["skipped_files"].append("Company_Handbook.md (already exists)")
                self.logger.info("Skipped Company_Handbook.md (already exists)")

        except Exception as e:
            result["success"] = False
            result["errors"].append(str(e))
            self.logger.error(f"Vault creation failed: {e}")

        return result

    def validate_vault(self) -> tuple[bool, List[str]]:
        """Validate that the vault structure is correct.

        Returns:
            Tuple of (is_valid, list of error messages).
        """
        errors = []

        # Check vault exists
        if not self.vault_path.exists():
            errors.append(f"Vault path does not exist: {self.vault_path}")
            return False, errors

        # Check required folders
        for folder in self.REQUIRED_FOLDERS:
            folder_path = self.vault_path / folder
            if not folder_path.exists():
                errors.append(f"Required folder missing: {folder}")

        # Check required files
        for file_name in ["Dashboard.md", "Company_Handbook.md"]:
            file_path = self.vault_path / file_name
            if not file_path.exists():
                errors.append(f"Required file missing: {file_name}")

        return len(errors) == 0, errors

    def get_folder_path(self, folder_name: str) -> Path:
        """Get the path to a vault folder.

        Args:
            folder_name: Name of the folder (needs_action, plans, done).

        Returns:
            Path to the folder.

        Raises:
            ValueError: If folder name is invalid.
        """
        folder_map = {
            "needs_action": "Needs_Action",
            "plans": "Plans",
            "done": "Done"
        }

        folder = folder_map.get(folder_name.lower())
        if not folder:
            raise ValueError(f"Invalid folder name: {folder_name}")

        return self.vault_path / folder

    def list_files_in_folder(
        self,
        folder_name: str,
        patterns: Optional[List[str]] = None
    ) -> List[Path]:
        """List files in a vault folder.

        Args:
            folder_name: Name of the folder.
            patterns: Optional glob patterns to filter files.

        Returns:
            List of file paths.
        """
        folder_path = self.get_folder_path(folder_name)
        return FileUtils.list_files(folder_path, patterns or ["*.md"])

    def get_vault_stats(self) -> dict:
        """Get statistics about the vault.

        Returns:
            Dictionary with vault statistics.
        """
        stats = {
            "vault_path": str(self.vault_path),
            "folders": {}
        }

        for folder in self.REQUIRED_FOLDERS:
            folder_path = self.vault_path / folder
            if folder_path.exists():
                files = FileUtils.list_files(folder_path, ["*.md"])
                stats["folders"][folder] = {
                    "count": len(files),
                    "files": [f.name for f in files]
                }
            else:
                stats["folders"][folder] = {"count": 0, "files": []}

        return stats

    def update_dashboard(self) -> None:
        """Update the dashboard with current vault statistics."""
        stats = self.get_vault_stats()

        dashboard_content = f"""# AI Employee Dashboard

## Quick Status

| Folder | Count |
|--------|-------|
| Needs Action | {stats['folders'].get('Needs_Action', {}).get('count', 0)} |
| Plans | {stats['folders'].get('Plans', {}).get('count', 0)} |
| Done | {stats['folders'].get('Done', {}).get('count', 0)} |

## Recent Activity

"""
        # Add recent files from each folder
        for folder_name, folder_stats in stats["folders"].items():
            if folder_stats["files"]:
                dashboard_content += f"### {folder_name}\n"
                for file_name in folder_stats["files"][:5]:  # Show last 5
                    dashboard_content += f"- {file_name}\n"
                dashboard_content += "\n"

        dashboard_content += f"""---

*Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

        dashboard_path = self.vault_path / "Dashboard.md"
        FileUtils.write_file(dashboard_path, dashboard_content)
        self.logger.info("Dashboard updated")
