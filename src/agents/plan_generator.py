"""
Plan Generator Agent.
Interprets natural language commands and generates structured execution plans.
"""

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from src.core.ai_router import generate
from src.core.config import get_settings
from src.core.exceptions import AIError

settings = get_settings()
logger = logging.getLogger("plan_generator")

class PlanGenerator:
    def __init__(self):
        self.vault_path = Path(settings.VAULT_PATH)
        self.plans_dir = self.vault_path / "Plans"
        self.plans_dir.mkdir(parents=True, exist_ok=True)

    def create_plan(self, command: str) -> Dict[str, Any]:
        """
        Analyzes the user command and generates a structured plan.
        Returns the plan metadata and saves the plan file to the Vault.
        """
        logger.info(f"Generating plan for command: {command}")
        
        # prompt for structured JSON output
        prompt = f"""
You are an expert AI Assistant Planner. Your goal is to break down a user request into a structured execution plan.

User Command: "{command}"

Analyze the request and output a JSON object with the following structure:
{{
  "title": "Short descriptive title",
  "intent": "social_post | email_reply | invoice_creation | whatsapp_message | other",
  "steps": [
    {{
      "step_id": 1,
      "action": "generate_content | draft_email | create_invoice | send_message",
      "description": "Detailed description of what to do",
      "params": {
        "platform": "twitter | linkedin | instagram | facebook | email | whatsapp | odoo",
        "topic": "The main topic or subject",
        "recipient": "Target audience or person (if applicable)",
        "tone": "professional | casual | witty | urgent"
      }

    }}
  ],
  "risk_level": "low | medium | high"
}}

Rules:
1. "social_post" intent usually involves "generate_content" steps for each platform.
2. "email_reply" intent involves a "draft_email" step.
3. "invoice_creation" involves "create_invoice".
4. "whatsapp_message" involves "send_message".
5. Risk Level:
   - low: informational social posts, internal logs.
   - medium: public social posts, drafting emails.
   - high: sending emails, sending messages, financial transactions (invoices).

Output ONLY the JSON object. No markdown formatting.
"""

        try:
            response_text = generate(prompt)
            # Clean up potential markdown code blocks
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            plan_data = json.loads(response_text)
            
            # Enrich with metadata
            plan_id = f"plan-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
            plan_data["plan_id"] = plan_id
            plan_data["status"] = "created"
            plan_data["created_at"] = datetime.now(timezone.utc).isoformat()
            plan_data["original_command"] = command
            
            self._save_plan_to_vault(plan_data)
            return plan_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            raise AIError(f"Plan generation failed: Invalid JSON response from AI. Response: {response_text}")
        except Exception as e:
            logger.error(f"Plan generation failed: {e}")
            raise AIError(f"Plan generation failed: {e}")

    def _save_plan_to_vault(self, plan_data: Dict[str, Any]):
        """Saves the plan as a markdown file in Vault/Plans."""
        filename = f"PLAN_{plan_data['plan_id']}.md"
        filepath = self.plans_dir / filename
        
        # Create YAML frontmatter
        frontmatter = {
            "type": "execution_plan",
            "plan_id": plan_data["plan_id"],
            "status": "created",
            "created_at": plan_data["created_at"],
            "risk_level": plan_data["risk_level"],
            "intent": plan_data["intent"]
        }
        
        yaml_content = "---\n" + "\n".join([f"{k}: {v}" for k, v in frontmatter.items()]) + "\n---\n"
        
        # Create plan body
        body = f"# Plan: {plan_data['title']}\n\n"
        body += f"**Command:** {plan_data['original_command']}\n\n"
        body += "## Execution Steps\n"
        
        for step in plan_data["steps"]:
            params_str = ", ".join([f"{k}={v}" for k, v in step.get("params", {}).items()])
            body += f"{step['step_id']}. **{step['action']}**: {step['description']}\n"
            body += f"   - Params: `{params_str}`\n"
            
        filepath.write_text(yaml_content + body, encoding="utf-8")
        logger.info(f"Plan saved to {filepath}")
