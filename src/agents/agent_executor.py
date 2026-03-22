"""
Agent Executor.
Executes individual steps from a plan and generates action files for approval.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from src.core.ai_router import generate
from src.core.config import get_settings

settings = get_settings()
logger = logging.getLogger("agent_executor")

import asyncio
from src.api.events import notify_new_draft, notify_approval_required

class AgentExecutor:
    def __init__(self):
        self.vault_path = Path(settings.VAULT_PATH)
        self.pending_dir = self.vault_path / "Pending_Approval"
        self.pending_dir.mkdir(parents=True, exist_ok=True)

    def execute_plan(self, plan_data: Dict[str, Any]):
        """
        Iterates through plan steps and executes them.
        """
        logger.info(f"Executing plan: {plan_data['plan_id']}")
        
        results = []
        for step in plan_data.get("steps", []):
            try:
                result = self._execute_step(step, plan_data)
                results.append(result)
            except Exception as e:
                logger.error(f"Step execution failed: {step['step_id']} - {e}")
                results.append({"step_id": step["step_id"], "status": "failed", "error": str(e)})
        
        return results

    def _execute_step(self, step: Dict[str, Any], plan_data: Dict[str, Any]):
        """Dispatches execution to specific handler based on action type."""
        action = step.get("action")
        logger.info(f"Executing step {step['step_id']}: {action}")
        
        if action == "generate_content":
            return self._generate_social_content(step, plan_data)
        elif action == "draft_email":
            return self._draft_email(step, plan_data)
        elif action == "send_message":
            return self._draft_message(step, plan_data)
        elif action == "create_invoice":
             # For invoice creation, we might need a structured data generation step first
             return self._draft_invoice(step, plan_data)
        else:
            logger.warning(f"Unknown action: {action}")
            return {"step_id": step["step_id"], "status": "skipped", "reason": "unknown_action"}

    def _generate_social_content(self, step: Dict[str, Any], plan_data: Dict[str, Any]):
        params = step.get("params", {})
        platform = params.get("platform", "twitter").lower()
        topic = params.get("topic", "general update")
        tone = params.get('tone', 'professional')
        
        platform_instructions = {
            "twitter": "Max 280 characters. Use 2-3 relevant hashtags. Witty or engaging hook.",
            "linkedin": "Professional long-form post. Break into paragraphs. Use emojis sparingly. End with a question for engagement.",
            "instagram": "Engaging caption. Visually descriptive language. Use a block of 5-10 relevant hashtags at the end.",
            "facebook": "Friendly and community-focused. Informative but conversational."
        }
        
        instruction = platform_instructions.get(platform, "Standard engaging post.")
        
        prompt = f"""
Generate a high-quality social media post for {platform.upper()}.
Topic: {topic}
Tone: {tone}
Platform Guidelines: {instruction}

Requirements:
- engaging and clear.
- No markdown code blocks in the output, just the raw post text.
"""
        content = generate(prompt)
        
        filename = f"POST_{platform.upper()}_{plan_data['plan_id']}_{step['step_id']}.md"
        meta = {
                "approval_id": f"apprv-{plan_data['plan_id']}-{step['step_id']}",
                "type": "social_post",
                "item_type": "social_post",
                "action_type": "publish_post",
                "platform": platform,
                "topic": topic,
                "plan_id": plan_data["plan_id"],
                "plan_file": f"Plans/PLAN_{plan_data['plan_id']}.md",
                "source_file": filename, # Using itself as source for now
                "step_id": step["step_id"],
                "risk_level": "medium",
                "requested_at": datetime.now(timezone.utc).isoformat(),
                "filename": filename
            }
        self._save_pending_action(filename, content, metadata=meta)
        
        # Async notification
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(notify_new_draft(filename, "social_post"))
                loop.create_task(notify_approval_required(filename))
        except:
            pass

        return {"step_id": step["step_id"], "status": "success", "file": filename}

    def _draft_email(self, step: Dict[str, Any], plan_data: Dict[str, Any]):
        params = step.get("params", {})
        recipient = params.get("recipient", "Unknown")
        topic = params.get("topic", "Inquiry")
        
        prompt = f"""
Draft a professional email.
Recipient: {recipient}
Topic: {topic}
Tone: {params.get('tone', 'professional')}

Format:
Subject: [Subject Line]

[Body]
"""
        content = generate(prompt)
        
        filename = f"EMAIL_{plan_data['plan_id']}_{step['step_id']}.md"
        meta = {
                "approval_id": f"apprv-{plan_data['plan_id']}-{step['step_id']}",
                "type": "email_draft",
                "item_type": "email",
                "action_type": "send_email",
                "recipient": recipient,
                "plan_id": plan_data["plan_id"],
                "plan_file": f"Plans/PLAN_{plan_data['plan_id']}.md",
                "source_file": filename,
                "step_id": step["step_id"],
                "risk_level": "high",
                "requested_at": datetime.now(timezone.utc).isoformat(),
                "filename": filename
            }
        self._save_pending_action(filename, content, metadata=meta)
        return {"step_id": step["step_id"], "status": "success", "file": filename}

    def _draft_message(self, step: Dict[str, Any], plan_data: Dict[str, Any]):
        params = step.get("params", {})
        platform = params.get("platform", "whatsapp")
        recipient = params.get("recipient", "Unknown")
        
        prompt = f"""
Draft a short message for {platform}.
Recipient: {recipient}
Topic: {params.get("topic", "update")}
Tone: {params.get('tone', 'casual')}
"""
        content = generate(prompt)
        
        filename = f"MSG_{platform.upper()}_{plan_data['plan_id']}_{step['step_id']}.md"
        meta = {
                "approval_id": f"apprv-{plan_data['plan_id']}-{step['step_id']}",
                "type": "message_draft",
                "item_type": "whatsapp",
                "action_type": "reply_whatsapp",
                "platform": platform,
                "recipient": recipient,
                "plan_id": plan_data["plan_id"],
                "plan_file": f"Plans/PLAN_{plan_data['plan_id']}.md",
                "source_file": filename,
                "step_id": step["step_id"],
                "risk_level": "high",
                "requested_at": datetime.now(timezone.utc).isoformat(),
                "filename": filename
            }
        self._save_pending_action(filename, content, metadata=meta)
        return {"step_id": step["step_id"], "status": "success", "file": filename}

    def _draft_invoice(self, step: Dict[str, Any], plan_data: Dict[str, Any]):
        # This is a placeholder. Real invoice generation would likely involve structured data.
        params = step.get("params", {})
        recipient = params.get("recipient", "Client")
        
        content = f"""
# Invoice Request
**Recipient:** {recipient}
**Details:** {params.get('topic', 'Services rendered')}

*This is a placeholder for Odoo invoice creation. Approving this will trigger the invoice creation via MCP.*
"""
        filename = f"INVOICE_{plan_data['plan_id']}_{step['step_id']}.md"
        self._save_pending_action(
            filename,
            content,
            metadata={
                "type": "invoice_draft",
                "recipient": recipient,
                "plan_id": plan_data["plan_id"],
                "step_id": step["step_id"],
                "risk_level": "high",
                "action_type": "create_odoo_invoice"
            }
        )
        return {"step_id": step["step_id"], "status": "success", "file": filename}


    def _save_pending_action(self, filename: str, content: str, metadata: Dict[str, Any]):
        filepath = self.pending_dir / filename
        
        meta_str = "\n".join([f"{k}: {v}" for k, v in metadata.items()])
        full_content = f"---\n{meta_str}\nstatus: pending_approval\ncreated_at: {datetime.now(timezone.utc).isoformat()}\n---\n\n{content}"
        
        filepath.write_text(full_content, encoding="utf-8")
        logger.info(f"Generated action file: {filepath}")
