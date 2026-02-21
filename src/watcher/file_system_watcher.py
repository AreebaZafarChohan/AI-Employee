"""Bronze Tier filesystem watcher for the AI Employee Obsidian vault.

Monitors the Inbox/ folder for new files. When a file arrives it is:
1. Copied to Needs_Action/ (original stays in Inbox).
2. Accompanied by a metadata markdown sidecar with type, name, timestamp, status.
3. Logged to Logs/ inside the vault.

Duplicate processing is prevented by a persistent ledger file that survives restarts.
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, Set

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..utils.file_utils import FileUtils
from ..utils.logger import get_logger


# ---------------------------------------------------------------------------
# Processed-files ledger (persistent duplicate guard)
# ---------------------------------------------------------------------------

_LEDGER_NAME = ".processed_files.json"


def _load_ledger(path: Path) -> Set[str]:
    """Load the set of already-processed filenames from the ledger."""
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return set(data)
    except (json.JSONDecodeError, OSError):
        return set()


def _save_ledger(path: Path, entries: Set[str]) -> None:
    """Persist the processed-files set to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(entries), indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Metadata sidecar
# ---------------------------------------------------------------------------

def _build_metadata(original_name: str, created_at: str) -> str:
    """Return a YAML-frontmatter markdown string for the sidecar file."""
    return (
        "---\n"
        "type: file_drop\n"
        f"original_name: \"{original_name}\"\n"
        f"created_at: \"{created_at}\"\n"
        "status: pending\n"
        "---\n"
        "\n"
        f"# {original_name}\n"
        "\n"
        "Automatically created by the Bronze Tier filesystem watcher.\n"
    )


# ---------------------------------------------------------------------------
# Vault logger (writes markdown entries to Logs/)
# ---------------------------------------------------------------------------

def _log_to_vault(logs_dir: Path, message: str) -> None:
    """Append *message* to today's vault log file inside Logs/."""
    logs_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = logs_dir / f"watcher-{today}.md"

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"- `{timestamp}` — {message}\n"

    with open(log_file, "a", encoding="utf-8") as fh:
        if not log_file.exists() or log_file.stat().st_size == 0:
            fh.write(f"# Watcher Log — {today}\n\n")
        fh.write(entry)


# ---------------------------------------------------------------------------
# Watchdog event handler
# ---------------------------------------------------------------------------

class InboxHandler(FileSystemEventHandler):
    """Reacts to new files appearing in Inbox/."""

    def __init__(
        self,
        vault_path: Path,
        patterns: List[str],
        debounce_time: float = 1.0,
    ):
        super().__init__()
        self.vault_path = vault_path
        self.inbox_path = vault_path / "Inbox"
        self.needs_action_path = vault_path / "Needs_Action"
        self.logs_path = vault_path / "Logs"
        self.patterns = patterns
        self.debounce_time = debounce_time
        self.logger = get_logger("watcher")

        # Persistent ledger lives next to the vault
        self._ledger_path = vault_path / _LEDGER_NAME
        self._processed: Set[str] = _load_ledger(self._ledger_path)

        # In-flight debounce tracker: filepath -> first-seen epoch
        self._pending: dict[str, float] = {}

    # -- pattern matching ---------------------------------------------------

    def _matches(self, path: Path) -> bool:
        return any(path.match(p) for p in self.patterns)

    def _is_metadata_file(self, path: Path) -> bool:
        return path.stem.endswith(".meta")

    # -- watchdog callbacks -------------------------------------------------

    def on_created(self, event) -> None:  # noqa: ANN001
        if event.is_directory:
            return
        file_path = Path(event.src_path)
        if not self._matches(file_path):
            return
        if self._is_metadata_file(file_path):
            return
        self._pending.setdefault(str(file_path), time.time())
        self.logger.info(f"New file detected in Inbox: {file_path.name}")

    def on_modified(self, event) -> None:  # noqa: ANN001
        if event.is_directory:
            return
        file_path = Path(event.src_path)
        str_path = str(file_path)
        if str_path not in self._pending:
            return
        elapsed = time.time() - self._pending[str_path]
        if elapsed >= self.debounce_time:
            del self._pending[str_path]
            self._process_file(file_path)

    # -- core processing ----------------------------------------------------

    def _process_file(self, file_path: Path) -> None:
        """Copy *file_path* to Needs_Action/ and create a metadata sidecar."""
        name = file_path.name

        # Duplicate guard
        if name in self._processed:
            self.logger.info(f"Skipping already-processed file: {name}")
            return

        try:
            FileUtils.ensure_directory(self.needs_action_path)

            # Resolve destination (handle name collisions)
            dest_path = self.needs_action_path / name
            if dest_path.exists():
                ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                dest_path = self.needs_action_path / f"{file_path.stem}_{ts}{file_path.suffix}"

            # Copy file (original stays in Inbox)
            FileUtils.copy_file(file_path, dest_path)
            self.logger.info(f"Copied to Needs_Action: {dest_path.name}")

            # Create metadata sidecar
            created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            meta_content = _build_metadata(name, created_at)
            meta_path = self.needs_action_path / f"{dest_path.stem}.meta.md"
            FileUtils.write_file(meta_path, meta_content)
            self.logger.info(f"Metadata written: {meta_path.name}")

            # Record in ledger
            self._processed.add(name)
            _save_ledger(self._ledger_path, self._processed)

            # Vault log
            _log_to_vault(self.logs_path, f"Copied **{name}** → Needs_Action/")

        except Exception as exc:
            self.logger.error(f"Failed to process {name}: {exc}")
            _log_to_vault(self.logs_path, f"ERROR processing **{name}**: {exc}")


# ---------------------------------------------------------------------------
# Public watcher class
# ---------------------------------------------------------------------------

class FileSystemWatcher:
    """Bronze Tier filesystem watcher for the AI Employee vault.

    Usage::

        watcher = FileSystemWatcher(vault_path="/path/to/AI-Employee-Vault")
        watcher.start()          # blocking — Ctrl-C to stop
        # or
        watcher.start(blocking=False)
        ...
        watcher.stop()
    """

    DEFAULT_PATTERNS: List[str] = ["*.md", "*.txt"]
    DEFAULT_DEBOUNCE: float = 1.0
    DEFAULT_POLL: float = 1.0

    def __init__(
        self,
        vault_path: str | Path,
        patterns: Optional[List[str]] = None,
        debounce_time: float = DEFAULT_DEBOUNCE,
        polling_interval: float = DEFAULT_POLL,
    ):
        self.vault_path = Path(vault_path).resolve()
        self.inbox_path = self.vault_path / "Inbox"
        self.patterns = patterns or self.DEFAULT_PATTERNS
        self.debounce_time = debounce_time
        self.polling_interval = polling_interval
        self.logger = get_logger("watcher")
        self._observer: Optional[Observer] = None

    # -- lifecycle ----------------------------------------------------------

    def start(self, blocking: bool = True) -> None:
        """Start watching Inbox/ for new files.

        Args:
            blocking: If True, block the calling thread until interrupted.
        """
        if not self.inbox_path.exists():
            self.inbox_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created Inbox directory: {self.inbox_path}")

        handler = InboxHandler(
            vault_path=self.vault_path,
            patterns=self.patterns,
            debounce_time=self.debounce_time,
        )

        self._observer = Observer()
        self._observer.schedule(handler, str(self.inbox_path), recursive=False)
        self._observer.start()
        self.logger.info(f"Watcher started — monitoring {self.inbox_path}")

        if blocking:
            try:
                while self._observer.is_alive():
                    self._observer.join(self.polling_interval)
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received")
            finally:
                self.stop()

    def stop(self) -> None:
        """Stop the watcher gracefully."""
        if self._observer is not None:
            self.logger.info("Stopping watcher")
            self._observer.stop()
            self._observer.join()
            self._observer = None

    @property
    def is_running(self) -> bool:
        return self._observer is not None and self._observer.is_alive()

    # -- one-shot scan (useful for cron / manual triggers) ------------------

    def scan_once(self) -> dict:
        """Scan Inbox/ once, process any new files, and return a summary.

        Returns:
            dict with keys: found, processed, skipped, errors.
        """
        result = {"found": 0, "processed": 0, "skipped": 0, "errors": []}

        if not self.inbox_path.exists():
            return result

        files = FileUtils.list_files(self.inbox_path, self.patterns)
        result["found"] = len(files)

        ledger_path = self.vault_path / _LEDGER_NAME
        processed = _load_ledger(ledger_path)
        needs_action = self.vault_path / "Needs_Action"
        logs_dir = self.vault_path / "Logs"
        FileUtils.ensure_directory(needs_action)

        for file_path in files:
            name = file_path.name
            if name in processed:
                result["skipped"] += 1
                self.logger.info(f"Scan: skipping already-processed {name}")
                continue

            try:
                dest = needs_action / name
                if dest.exists():
                    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                    dest = needs_action / f"{file_path.stem}_{ts}{file_path.suffix}"

                FileUtils.copy_file(file_path, dest)

                created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                meta = _build_metadata(name, created_at)
                FileUtils.write_file(needs_action / f"{dest.stem}.meta.md", meta)

                processed.add(name)
                result["processed"] += 1
                self.logger.info(f"Scan: processed {name}")
                _log_to_vault(logs_dir, f"Copied **{name}** → Needs_Action/ (scan)")

            except Exception as exc:
                result["errors"].append(f"{name}: {exc}")
                self.logger.error(f"Scan: failed to process {name}: {exc}")
                _log_to_vault(logs_dir, f"ERROR processing **{name}** (scan): {exc}")

        _save_ledger(ledger_path, processed)
        return result
