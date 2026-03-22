"""
Integration test for the AI Employee FastAPI.
Verifies: REST Endpoints and Vault Interaction.
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import json
from unittest.mock import patch

from src.api.main import app
from src.core.config import get_settings

client = TestClient(app)

@pytest.fixture
def mock_vault(tmp_path):
    """Sets up a temporary vault structure."""
    vault_dir = tmp_path / "AI-Employee-Vault"
    (vault_dir / "Plans").mkdir(parents=True)
    (vault_dir / "Pending_Approval").mkdir(parents=True)
    (vault_dir / "Needs_Action").mkdir(parents=True)
    (vault_dir / "Done").mkdir(parents=True)
    (vault_dir / "Logs").mkdir(parents=True)
    return vault_dir

def test_api_health(mock_vault):
    """Verifies that the API root is accessible."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_agent_command_endpoint(mock_vault):
    """Tests the /agent/command endpoint flow."""
    settings = get_settings()
    
    with patch.object(settings, "VAULT_PATH", str(mock_vault)):
        # Mock the underlying router to avoid real AI calls
        with patch("src.core.command_router.command_router.process_command") as mock_proc:
            mock_proc.return_value = {
                "status": "success",
                "plan_id": "test-plan-123",
                "message": "Plan created and actions generated."
            }
            
            response = client.post("/api/v1/agent/command", json={
                "command": "Post something interesting"
            })
            
            assert response.status_code == 200
            assert response.json()["data"]["plan_id"] == "test-plan-123"
            mock_proc.assert_called_once()

def test_vault_pending_list(mock_vault):
    """Tests fetching pending approvals from vault."""
    settings = get_settings()
    
    # Create a fake pending file
    pending_file = mock_vault / "Pending_Approval" / "POST_TWITTER_1.md"
    pending_file.write_text("---\ntype: social_post\nplatform: twitter\n---\nPost content")
    
    with patch.object(settings, "VAULT_PATH", str(mock_vault)):
        response = client.get("/api/v1/tasks/pending")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["filename"] == "POST_TWITTER_1.md"

def test_approve_action(mock_vault):
    """Tests the approval endpoint (mocked logic)."""
    # Note: Real approval logic moves files. 
    # Current src/api/routes/vault.py:approve just returns success status.
    response = client.post("/api/v1/vault/approve", json={
        "filename": "some_file.md"
    })
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "approved"

if __name__ == "__main__":
    import sys
    pytest.main([__file__])
