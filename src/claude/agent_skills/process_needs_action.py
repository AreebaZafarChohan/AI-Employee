"""Process Needs Action skill — Bronze Tier vault processor.

Reads every file in Needs_Action/, generates a Plan markdown in Plans/,
moves the original to Done/, and writes a structured JSON log entry in Logs/.

Constraints (Bronze Tier):
- No external API calls, network requests, or side-effects.
- All I/O is confined to the vault directory tree.
- Every action is logged to Logs/YYYY-MM-DD.json.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime, timezone

from .skill_base import SkillBase, SkillExecutionError
from ...utils.file_utils import FileUtils
from ...utils.logger import get_logger


class ProcessNeedsAction(SkillBase):
    """Skill that processes every file in Needs_Action/.

    For each file it:
    1. Reads and analyses the content.
    2. Creates a Plan file in Plans/.
    3. Moves the original to Done/.
    4. Appends a JSON log entry to Logs/YYYY-MM-DD.json.
    """

    def __init__(self, vault_path: str | Path):
        super().__init__(
            name="process_needs_action",
            description="Process Needs_Action items into Plans and archive to Done",
            version="1.0.0",
        )
        self.vault_path = Path(vault_path).resolve()
        self.needs_action = self.vault_path / "Needs_Action"
        self.plans = self.vault_path / "Plans"
        self.done = self.vault_path / "Done"
        self.logs = self.vault_path / "Logs"
        self.logger = get_logger("process_needs_action")

    # -- SkillBase interface ------------------------------------------------

    def validate_input(self, input_data: Dict[str, Any]) -> tuple[bool, str]:
        if not self.vault_path.exists():
            return False, f"Vault path does not exist: {self.vault_path}"
        if not self.needs_action.exists():
            return False, f"Needs_Action folder does not exist: {self.needs_action}"
        return True, ""

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        patterns = input_data.get("patterns", ["*.md", "*.txt"])
        files = FileUtils.list_files(self.needs_action, patterns)

        # Filter out metadata sidecars created by the watcher
        files = [f for f in files if not f.stem.endswith(".meta")]

        result: Dict[str, Any] = {
            "success": True,
            "found": len(files),
            "processed": 0,
            "skipped": 0,
            "errors": [],
            "plans_created": [],
        }

        for file_path in files:
            file_result = self._process_file(file_path)
            if file_result["success"]:
                result["processed"] += 1
                result["plans_created"].append(file_result["plan_path"])
            else:
                result["errors"].append(file_result["error"])

        if result["errors"]:
            result["success"] = len(result["errors"]) < result["found"]

        return result

    # -- internal -----------------------------------------------------------

    def _process_file(self, file_path: Path) -> Dict[str, Any]:
        """Process a single Needs_Action file end-to-end."""
        name = file_path.name
        self.logger.info(f"Processing: {name}")

        try:
            content = FileUtils.read_file(file_path)
            objective, steps = self._analyse_content(name, content)

            # Create plan
            FileUtils.ensure_directory(self.plans)
            plan_name = f"plan-{file_path.stem}.md"
            plan_path = self.plans / plan_name
            plan_content = self._build_plan(name, objective, steps)
            FileUtils.write_file(plan_path, plan_content)
            self.logger.info(f"Plan created: {plan_name}")

            # Move original + its sidecar to Done
            FileUtils.ensure_directory(self.done)
            dest = self.done / name
            if dest.exists():
                ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                dest = self.done / f"{file_path.stem}_{ts}{file_path.suffix}"
            FileUtils.move_file(file_path, dest)

            meta_sidecar = self.needs_action / f"{file_path.stem}.meta.md"
            if meta_sidecar.exists():
                FileUtils.move_file(meta_sidecar, self.done / meta_sidecar.name)

            self.logger.info(f"Moved to Done: {dest.name}")

            # Log
            self._write_log(name, str(plan_path), "processed")

            return {"success": True, "plan_path": str(plan_path)}

        except Exception as exc:
            error_msg = f"{name}: {exc}"
            self.logger.error(f"Failed: {error_msg}")
            self._write_log(name, "", "error", str(exc))
            return {"success": False, "error": error_msg}

    # -- content analysis (offline, no external calls) ----------------------

    @staticmethod
    def _analyse_content(filename: str, content: str) -> tuple[str, List[str]]:
        """Derive an objective and action steps from file content.

        This is a deterministic, offline analysis — no LLM call.
        It extracts headings, bullet points, and key sentences.
        """
        lines = [ln.strip() for ln in content.splitlines() if ln.strip()]

        # Objective: first heading or first non-empty line
        objective = filename
        for line in lines:
            if line.startswith("# "):
                objective = line.lstrip("# ").strip()
                break
            if not line.startswith("---"):
                objective = line[:120]
                break

        # Steps: collect bullet points and numbered items
        steps: List[str] = []
        for line in lines:
            stripped = line.lstrip("-*•0123456789.) ")
            if line != stripped and stripped:
                steps.append(stripped)

        # Fallback: if no structured steps found, create generic ones
        if not steps:
            steps = [
                f"Review content of {filename}",
                "Identify required actions",
                "Execute actions per Company Handbook",
                "Verify completion criteria",
            ]

        return objective, steps

    # -- plan builder -------------------------------------------------------

    @staticmethod
    def _build_plan(source_file: str, objective: str, steps: List[str]) -> str:
        """Build a Plans/ markdown file."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        step_lines = "\n".join(f"- [ ] {s}" for s in steps)

        return (
            "---\n"
            f"source: \"{source_file}\"\n"
            f"created_at: \"{timestamp}\"\n"
            "status: pending\n"
            "---\n"
            "\n"
            f"# Plan: {objective}\n"
            "\n"
            "## Objective\n"
            "\n"
            f"{objective}\n"
            "\n"
            "## Steps\n"
            "\n"
            f"{step_lines}\n"
            "\n"
            "## Status\n"
            "\n"
            "**pending** — awaiting human review or agent execution.\n"
        )

    # -- JSON log -----------------------------------------------------------

    def _write_log(
        self, filename: str, plan_path: str, status: str, error: str = ""
    ) -> None:
        """Append an entry to today's JSON log in Logs/."""
        FileUtils.ensure_directory(self.logs)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_file = self.logs / f"{today}.json"

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "skill": self.name,
            "file": filename,
            "plan_path": plan_path,
            "status": status,
        }
        if error:
            entry["error"] = error

        # Read existing entries or start fresh
        entries: List[Dict[str, Any]] = []
        if log_file.exists():
            try:
                entries = json.loads(log_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                entries = []

        entries.append(entry)
        log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")
