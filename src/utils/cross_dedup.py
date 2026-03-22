"""Cross-Source Duplicate Detection — Silver Tier.

Prevents the same content from creating multiple Needs_Action files when
it arrives via more than one channel (e.g. Gmail + WhatsApp).

Uses SHA-256 content hashing with a shared JSON store.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Optional

_MAX_ENTRIES = 5000

ROOT = Path(__file__).resolve().parent.parent.parent
VAULT = Path(os.getenv("VAULT_PATH", ROOT / "AI-Employee-Vault")).resolve()


class CrossSourceDedup:
    """SHA-256 content-hash dedup across all watcher sources."""

    def __init__(self, store_path: Optional[Path] = None):
        self._store_path = store_path or (VAULT / ".cross_source_dedup.json")
        self._hashes: dict[str, str] = self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> dict[str, str]:
        if self._store_path.exists():
            try:
                data = json.loads(self._store_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def _save(self) -> None:
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        # Cap entries to prevent unbounded growth
        if len(self._hashes) > _MAX_ENTRIES:
            keys = list(self._hashes.keys())
            for k in keys[: len(keys) - _MAX_ENTRIES]:
                del self._hashes[k]
        self._store_path.write_text(
            json.dumps(self._hashes, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def content_hash(content: str) -> str:
        """Return hex SHA-256 of *content*."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def is_duplicate(self, content: str, source: str) -> bool:
        """Return True if *content* was already seen from any source."""
        h = self.content_hash(content)
        if h in self._hashes:
            return True
        self._hashes[h] = source
        self._save()
        return False
