#!/usr/bin/env python3
"""
Database migration script for Gold Tier Backend.
Wraps Alembic operations for easy CLI usage.

Usage:
    python src/models/migrate.py upgrade    # Upgrade to latest
    python src/models/migrate.py downgrade  # Downgrade one version
    python src/models/migrate.py current    # Show current version
    python src/models/migrate.py history    # Show migration history
    python src/models/migrate.py revision "description"  # Create new revision
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory


def get_alembic_config():
    """Get Alembic config with project paths."""
    alembic_cfg = Config(str(project_root / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(project_root / "alembic"))
    alembic_cfg.set_main_option("prepend_sys_path", str(project_root))
    return alembic_cfg


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    alembic_cfg = get_alembic_config()

    if cmd == "upgrade":
        command.upgrade(alembic_cfg, "head")
        print("✓ Database upgraded to latest version")

    elif cmd == "downgrade":
        command.downgrade(alembic_cfg, "-1")
        print("✓ Database downgraded by one version")

    elif cmd == "current":
        command.current(alembic_cfg)

    elif cmd == "history":
        command.history(alembic_cfg)

    elif cmd == "revision":
        if len(sys.argv) < 3:
            print("Usage: python src/models/migrate.py revision <description>")
            sys.exit(1)
        description = sys.argv[2]
        command.revision(alembic_cfg, autogenerate=True, message=description)
        print(f"✓ Migration created: {description}")

    elif cmd == "stamp":
        # Stamp database with a specific version
        version = sys.argv[2] if len(sys.argv) > 2 else "head"
        command.stamp(alembic_cfg, version)
        print(f"✓ Database stamped to {version}")

    elif cmd == "heads":
        command.heads(alembic_cfg, verbose=True)

    elif cmd == "branches":
        command.branches(alembic_cfg, verbose=True)

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
