"""Agent Service for processing natural language commands and managing autonomous tasks."""

import os
import re
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Tuple, Optional
from src.core.config import get_settings

settings = get_settings()

PLATFORM_KEYWORDS = {
    "twitter": ["twitter", "tweet", "x.com"],
    "linkedin": ["linkedin"],
    "facebook": ["facebook", "fb"],
    "instagram": ["instagram", "insta", "ig"],
    "whatsapp": ["whatsapp", "wa"],
    "email": ["email", "mail", "gmail"],
    "odoo": ["odoo", "erp"],
}

class AgentService:
    def __init__(self):
        self.vault_path = Path(settings.VAULT_PATH)
        self.needs_action_dir = self.vault_path / "Needs_Action"
        self.pending_dir = self.vault_path / "Pending_Approval"
        self.done_dir = self.vault_path / "Done"
        self.logs_dir = self.vault_path / "Logs"
        
        # Ensure directories exist
        for d in [self.needs_action_dir, self.pending_dir, self.done_dir, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def process_command(self, command: str) -> dict:
        """Process a natural language command from the frontend."""
        # 1. Parse intent (detect platforms)
        platforms = self._detect_platforms(command)
        topic = self._extract_topic(command)
        
        # 2. Create a task file in Needs_Action
        # This will be picked up by ralph_loop.py or a similar orchestrator
        task_id = f"task-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        filename = f"{task_id}.md"
        
        # Determine risk level based on platforms (social media is medium, email is high)
        risk_level = "medium"
        if "email" in platforms:
            risk_level = "high"
            
        platforms_str = ", ".join(platforms) if platforms else "all relevant"
        
        content = f"""---
type: autonomous_task
task_id: {task_id}
command: "{command.replace('"', '\\"')}"
platforms: {json.dumps(platforms)}
topic: "{topic.replace('"', '\\"')}"
risk_level: {risk_level}
status: needs_action
created_at: "{datetime.now(timezone.utc).isoformat()}"
---

# Task: {command}

**Intent:** Generate social media posts for: {platforms_str}
**Topic:** {topic}

## Instructions for Agent:
1. Generate high-quality content for each requested platform: {platforms_str}.
2. Use the standard social media generation guidelines.
3. Save each result as a separate file in `Pending_Approval/`.
4. Use the naming convention: `social-post-<platform>-<topic-slug>-<timestamp>.md`.
5. Once all posts are generated, move THIS task file to `Done/`.

<promise>TASK_START</promise>
"""
        
        task_path = self.needs_action_dir / filename
        task_path.write_text(content, encoding="utf-8")
        
        self._log_action("COMMAND_RECEIVED", f"command={command} task_id={task_id}")
        
        return {
            "task_id": task_id,
            "filename": filename,
            "status": "needs_action",
            "platforms": platforms,
            "topic": topic,
            "message": "Task created in Needs_Action. Agent loop will process it shortly."
        }

    def _detect_platforms(self, text: str) -> List[str]:
        """Detect mentioned platforms in text."""
        lower = text.lower()
        detected = []
        for platform, keywords in PLATFORM_KEYWORDS.items():
            for kw in keywords:
                if re.search(rf'\b{re.escape(kw)}\b', lower):
                    detected.append(platform)
                    break
        return detected

    def _extract_topic(self, text: str) -> str:
        """Extract topic from command by removing platform keywords and fillers."""
        topic = text
        filler = [
            "pr", "pe", "par", "per", "ke", "ka", "ki", "mein", "about",
            "post", "karo", "kro", "likho", "likh", "write", "create",
            "bhi", "same", "topic", "ek", "acha", "baare", "generate"
        ]
        # Remove platform keywords
        for keywords in PLATFORM_KEYWORDS.values():
            for kw in keywords:
                topic = re.sub(rf'\b{re.escape(kw)}\b', '', topic, flags=re.IGNORECASE)
        # Remove filler words
        for f in filler:
            topic = re.sub(rf'\b{re.escape(f)}\b', '', topic, flags=re.IGNORECASE)
        
        topic = re.sub(r'\s+', ' ', topic).strip()
        
        if not topic or len(topic) < 3:
            topic = "General AI and automation updates"
            
        return topic

    def _log_action(self, action: str, details: str = ""):
        """Log agent actions."""
        log_file = self.logs_dir / f"agent-{datetime.now(timezone.utc).strftime('%Y%m%d')}.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {action} {details}\n")
