"""
Integration test for the AI Agent execution logic.
Verifies: Command -> Plan -> Draft Files.
"""

import pytest
import os
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from src.core.command_router import CommandRouter
from src.core.config import get_settings

@pytest.fixture
def mock_vault(tmp_path):
    """Sets up a temporary vault structure."""
    vault_dir = tmp_path / "AI-Employee-Vault"
    (vault_dir / "Plans").mkdir(parents=True)
    (vault_dir / "Pending_Approval").mkdir(parents=True)
    (vault_dir / "Done").mkdir(parents=True)
    (vault_dir / "Logs").mkdir(parents=True)
    return vault_dir

@pytest.fixture
def agent_system(mock_vault):
    """Initializes the command router with a mock vault."""
    settings = get_settings()
    with patch.object(settings, "VAULT_PATH", str(mock_vault)):
        router = CommandRouter()
        return router

def test_command_to_plan_execution(agent_system, mock_vault):
    """Tests the full flow from natural language command to vault files."""
    command = "Generate a LinkedIn post about AI employees"
    
    # 1. Mock AI response for PlanGenerator
    mock_plan = {
        "title": "LinkedIn Social Post",
        "intent": "social_post",
        "steps": [
            {
                "step_id": 1,
                "action": "generate_content",
                "description": "Generate LinkedIn post",
                "params": {
                    "platform": "linkedin",
                    "topic": "AI Employees",
                    "tone": "professional"
                }
            }
        ],
        "risk_level": "medium"
    }
    
    # 2. Mock AI response for AgentExecutor
    mock_content = "This is a LinkedIn post about AI. #AI #Future"
    
    # Patch the ai_router.generate function
    with patch("src.agents.plan_generator.generate", return_value=json.dumps(mock_plan)), \
         patch("src.agents.agent_executor.generate", return_value=mock_content):
        
        # Execute
        result = agent_system.process_command(command)
        
        # 3. Assertions
        assert result["status"] == "success"
        assert "plan_id" in result
        
        # Verify Plan File
        plan_files = list((mock_vault / "Plans").glob("PLAN_*.md"))
        assert len(plan_files) == 1
        assert "execution_plan" in plan_files[0].read_text()
        
        # Verify Pending Action File
        pending_files = list((mock_vault / "Pending_Approval").glob("POST_LINKEDIN_*.md"))
        assert len(pending_files) == 1
        content = pending_files[0].read_text()
        assert mock_content in content
        assert "action_type: publish_post" in content
        assert "status: pending_approval" in content

if __name__ == "__main__":
    # If run directly, try to execute with pytest
    import sys
    pytest.main([__file__])
