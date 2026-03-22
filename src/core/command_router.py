"""
Command Router.
Main entry point for natural language commands.
Orchestrates the flow: Command -> Plan -> Action Generation.
"""

import logging
from typing import Dict, Any

from src.agents.plan_generator import PlanGenerator
from src.agents.agent_executor import AgentExecutor

logger = logging.getLogger("command_router")

class CommandRouter:
    def __init__(self):
        self.plan_generator = PlanGenerator()
        self.agent_executor = AgentExecutor()

    def process_command(self, command: str) -> Dict[str, Any]:
        """
        Processes a natural language command.
        1. Generates a structured plan.
        2. Executes the plan to generate action files.
        3. Returns the plan details to the frontend.
        """
        logger.info(f"Processing command: {command}")
        
        # Step 1: Create Plan
        plan_data = self.plan_generator.create_plan(command)
        
        # Step 2: Execute Plan (Generate Drafts)
        execution_results = self.agent_executor.execute_plan(plan_data)
        
        return {
            "status": "success",
            "message": "Plan created and actions generated.",
            "plan_id": plan_data["plan_id"],
            "plan": plan_data,
            "execution_results": execution_results
        }

# Global instance
command_router = CommandRouter()
