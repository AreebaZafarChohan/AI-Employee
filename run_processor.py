#!/usr/bin/env python3
"""Process all files in Needs_Action → Plans + Done + Logs."""

import sys
import shutil
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.utils.logger import log_action, set_default_logs_dir

vault = Path(__file__).resolve().parent / "AI-Employee-Vault"
na = vault / "Needs_Action"
plans = vault / "Plans"
done = vault / "Done"
logs = vault / "Logs"

set_default_logs_dir(logs)
plans.mkdir(exist_ok=True)
done.mkdir(exist_ok=True)

count = 0
for f in sorted(na.glob("*.md")):
    if f.name.startswith(".") or f.stem.endswith(".meta"):
        continue

    content = f.read_text(encoding="utf-8")
    lines = [l.strip() for l in content.splitlines() if l.strip()]

    obj = f.stem
    steps = []
    for l in lines:
        if l.startswith("# "):
            obj = l.lstrip("# ")
        s = l.lstrip("-*0123456789.) ")
        if l != s and s:
            steps.append(s)
    if not steps:
        steps = ["Review content", "Identify actions", "Execute", "Verify"]

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    step_lines = "\n".join(f"- [ ] {s}" for s in steps)
    plan_content = (
        f'---\nsource: "{f.name}"\ncreated_at: "{ts}"\nstatus: pending\n---\n\n'
        f"# Plan: {obj}\n\n## Steps\n\n{step_lines}\n\n"
        f"## Status\n\n**pending**\n"
    )

    (plans / f"plan-{f.stem}.md").write_text(plan_content, encoding="utf-8")
    log_action("plan_created", f"plan-{f.stem}.md", "success")

    shutil.move(str(f), str(done / f.name))
    log_action("file_moved", f.name, "success")

    meta = na / f"{f.stem}.meta.md"
    if meta.exists():
        shutil.move(str(meta), str(done / meta.name))

    count += 1
    print(f"  Done: {f.name} -> plan + archived")

if count == 0:
    print("Needs_Action is empty — nothing to process.")
else:
    print(f"\nProcessed {count} file(s).")
