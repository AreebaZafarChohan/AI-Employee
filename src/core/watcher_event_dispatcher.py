"""
Watcher Event Dispatcher.
Routes events from watchers to specific AI agent handlers.
Automatically triggers reply drafting, task creation, or information gathering.
"""

import logging
from typing import Dict, Any
from pathlib import Path

from src.core.config import get_settings
from src.core.event_queue import event_queue
from src.core.command_router import command_router
from src.api.events import notify_new_task

settings = get_settings()
logger = logging.getLogger("watcher_dispatcher")

class WatcherEventDispatcher:
    def __init__(self):
        self.vault_path = Path(settings.VAULT_PATH)

    async def handle_gmail_event(self, event_data: Dict[str, Any]):
        """Analyze new emails and suggest replies."""
        filename = event_data.get("file")
        if not filename: return
        
        logger.info(f"Dispatching Gmail event: {filename}")
        
        # Construct a natural language command for the agent
        command = f"Draft a professional reply to this email: {filename}. If the email is a simple inquiry, low risk. If it involves payments or data, high risk."
        
        # Process via CommandRouter
        result = command_router.process_command(command)
        
        # Notify UI about the autonomous task
        await notify_new_task(result.get("plan_id"), f"Analyzing Email: {filename}")

    async def handle_whatsapp_event(self, event_data: Dict[str, Any]):
        """Analyze new WhatsApp messages."""
        filename = event_data.get("file")
        if not filename: return
        
        logger.info(f"Dispatching WhatsApp event: {filename}")
        
        command = f"Suggest a friendly WhatsApp reply for the message in: {filename}. Keep it short and use emojis if appropriate."
        result = command_router.process_command(command)
        
        await notify_new_task(result.get("plan_id"), f"Replying to WhatsApp: {filename}")

    async def handle_filesystem_event(self, event_data: Dict[str, Any]):
        """Analyze new file drops."""
        filename = event_data.get("file")
        if not filename: return
        
        logger.info(f"Dispatching Filesystem event: {filename}")
        
        command = f"Analyze the contents of this new file: {filename} and suggest appropriate actions or summary."
        result = command_router.process_command(command)
        
        await notify_new_task(result.get("plan_id"), f"Analyzing File: {filename}")

    async def handle_odoo_event(self, event_data: Dict[str, Any]):
        """Analyze Odoo events."""
        filename = event_data.get("file")
        if not filename: return
        
        logger.info(f"Dispatching Odoo event: {filename}")
        
        command = f"Process this Odoo system event: {filename}. If it's a new lead, suggest a follow-up. If it's an invoice, verify the details."
        result = command_router.process_command(command)
        
        await notify_new_task(result.get("plan_id"), f"Odoo Event: {filename}")

    async def handle_default(self, event_data: Dict[str, Any]):
        """Default handler for unknown sources."""
        source = event_data.get("source", "unknown")
        filename = event_data.get("file", "unknown")
        logger.info(f"Generic event handling for {source}: {filename}")
        
        # Generic "What should I do?" command
        command = f"New item from {source} detected in vault: {filename}. Decide the best course of action."
        command_router.process_command(command)

# Global instance
dispatcher = WatcherEventDispatcher()

async def setup_event_handlers():
    """Configure event_queue with dispatcher handlers."""
    event_queue.register_handler("gmail_watcher", dispatcher.handle_gmail_event)
    event_queue.register_handler("whatsapp_watcher", dispatcher.handle_whatsapp_event)
    event_queue.register_handler("filesystem_watcher", dispatcher.handle_filesystem_event)
    event_queue.register_handler("odoo_watcher", dispatcher.handle_odoo_event)
    event_queue.register_handler("social_watcher", dispatcher.handle_default)
    event_queue.register_handler("default", dispatcher.handle_default)
    
    # Start the worker task
    await event_queue.start_worker()
