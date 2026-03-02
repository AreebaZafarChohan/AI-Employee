"""Tests for Approval Orchestrator.

Tests cover:
- Frontmatter parsing
- Validation (required fields, expiry, risk levels)
- File operations (move to done/quarantine/rejected)
- Retry wrapper
- MCP tool integration
- Audit logging
- Concurrent processing
"""

import json
import os
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from approval_orchestrator import (
    parse_frontmatter,
    load_markdown_file,
    validate_approval,
    validate_plan,
    get_timestamp,
    write_audit_log,
    log_action,
    move_to_done,
    move_to_quarantine,
    move_to_rejected,
    retry_with_backoff,
    call_mcp_tool,
    execute_action,
    process_approval_file,
    APPROVAL_EXPIRY_HOURS,
    MAX_RETRIES,
    DRY_RUN,
    VAULT,
    APPROVED_DIR,
    DONE_DIR,
    QUARANTINE_DIR,
    AUDIT_DIR,
    LOGS_DIR,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_vault():
    """Create a temporary vault directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Path(tmpdir)
        approved = vault / "Approved"
        done = vault / "Done"
        quarantine = vault / "Quarantine"
        rejected = vault / "Rejected"
        logs = vault / "Logs"
        audit = vault / "Audit"
        
        for d in [approved, done, quarantine, rejected, logs, audit]:
            d.mkdir(parents=True, exist_ok=True)
        
        yield {
            "vault": vault,
            "approved": approved,
            "done": done,
            "quarantine": quarantine,
            "rejected": rejected,
            "logs": logs,
            "audit": audit,
        }


@pytest.fixture
def sample_approval_file(temp_vault):
    """Create a sample approval file."""
    # Use a recent timestamp to avoid expiry issues
    # Quote it to ensure YAML parses it as a string
    recent_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    approval_content = f"""---
approval_id: test-001
plan_file: Plans/test-plan.md
source_file: Done/email-001.md
risk_level: low
requested_at: "{recent_time}"
status: approved
action_type: send_email
---

# Approval Request

This is a test approval request.
"""
    approval_path = temp_vault["approved"] / "test-approval.md"
    approval_path.write_text(approval_content, encoding="utf-8")
    return approval_path


@pytest.fixture
def sample_plan_file(temp_vault):
    """Create a sample plan file."""
    plan_content = """---
plan_id: plan-001
item_type: email
risk_level: low
requires_approval: true
source_file: Done/email-001.md
---

# Plan

This is a test plan.
"""
    plan_path = temp_vault["vault"] / "Plans" / "test-plan.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(plan_content, encoding="utf-8")
    return plan_path


# ---------------------------------------------------------------------------
# Frontmatter Parsing Tests
# ---------------------------------------------------------------------------


class TestFrontmatterParsing:
    """Test frontmatter parsing functions."""
    
    def test_parse_frontmatter_valid(self):
        """Test parsing valid YAML frontmatter."""
        content = """---
title: Test
status: approved
---
Body content here.
"""
        metadata, body = parse_frontmatter(content)
        
        assert metadata == {"title": "Test", "status": "approved"}
        assert "Body content here." in body
    
    def test_parse_frontmatter_no_frontmatter(self):
        """Test parsing content without frontmatter."""
        content = "Just body content without frontmatter."
        
        metadata, body = parse_frontmatter(content)
        
        assert metadata == {}
        assert body == content
    
    def test_parse_frontmatter_invalid_yaml(self):
        """Test parsing invalid YAML."""
        content = """---
title: Test
  invalid_indent: value
---
Body content.
"""
        metadata, body = parse_frontmatter(content)
        
        # Should return empty dict on parse error
        assert metadata == {}
        assert "Body content" in body
    
    def test_load_markdown_file(self, temp_vault):
        """Test loading markdown file with frontmatter."""
        test_file = temp_vault["approved"] / "test.md"
        test_file.write_text("""---
key: value
number: 42
---
Body text.
""", encoding="utf-8")
        
        metadata, body = load_markdown_file(test_file)
        
        assert metadata["key"] == "value"
        assert metadata["number"] == 42
        assert "Body text" in body
    
    def test_load_markdown_file_not_found(self, temp_vault):
        """Test loading non-existent file."""
        non_existent = temp_vault["approved"] / "does_not_exist.md"
        
        with pytest.raises(FileNotFoundError):
            load_markdown_file(non_existent)


# ---------------------------------------------------------------------------
# Validation Tests
# ---------------------------------------------------------------------------


class TestValidation:
    """Test validation functions."""
    
    def test_validate_approval_valid(self):
        """Test validating a valid approval."""
        metadata = {
            "approval_id": "test-001",
            "plan_file": "Plans/test.md",
            "source_file": "Done/email.md",
            "risk_level": "low",
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "status": "approved",
            "action_type": "send_email",
        }
        
        errors = validate_approval(metadata, Path("test.md"))
        
        assert len(errors) == 0
    
    def test_validate_approval_missing_field(self):
        """Test validation with missing required field."""
        metadata = {
            "approval_id": "test-001",
            # Missing plan_file
            "source_file": "Done/email.md",
            "risk_level": "low",
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "status": "approved",
            "action_type": "send_email",
        }
        
        errors = validate_approval(metadata, Path("test.md"))
        
        assert any("plan_file" in err for err in errors)
    
    def test_validate_approval_invalid_risk_level(self):
        """Test validation with invalid risk level."""
        metadata = {
            "approval_id": "test-001",
            "plan_file": "Plans/test.md",
            "source_file": "Done/email.md",
            "risk_level": "extreme",  # Invalid
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "status": "approved",
            "action_type": "send_email",
        }
        
        errors = validate_approval(metadata, Path("test.md"))
        
        assert any("Invalid risk_level" in err for err in errors)
    
    def test_validate_approval_invalid_action_type(self):
        """Test validation with invalid action type."""
        metadata = {
            "approval_id": "test-001",
            "plan_file": "Plans/test.md",
            "source_file": "Done/email.md",
            "risk_level": "low",
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "status": "approved",
            "action_type": "send_telegram",  # Invalid
        }
        
        errors = validate_approval(metadata, Path("test.md"))
        
        assert any("Invalid action_type" in err for err in errors)
    
    def test_validate_approval_expired(self):
        """Test validation with expired approval."""
        old_time = datetime.now(timezone.utc) - timedelta(hours=APPROVAL_EXPIRY_HOURS + 1)
        metadata = {
            "approval_id": "test-001",
            "plan_file": "Plans/test.md",
            "source_file": "Done/email.md",
            "risk_level": "low",
            "requested_at": old_time.isoformat(),
            "status": "approved",
            "action_type": "send_email",
        }
        
        errors = validate_approval(metadata, Path("test.md"))
        
        assert any("Approval expired" in err for err in errors)
    
    def test_validate_plan_valid(self):
        """Test validating a valid plan."""
        metadata = {
            "plan_id": "plan-001",
            "item_type": "email",
            "risk_level": "medium",
            "requires_approval": True,
        }
        
        errors = validate_plan(metadata)
        
        assert len(errors) == 0
    
    def test_validate_plan_invalid_item_type(self):
        """Test validation with invalid item type."""
        metadata = {
            "plan_id": "plan-001",
            "item_type": "telegram",  # Invalid
            "risk_level": "low",
            "requires_approval": True,
        }
        
        errors = validate_plan(metadata)
        
        assert any("Invalid item_type" in err for err in errors)
    
    def test_validate_plan_missing_field(self):
        """Test validation with missing required field."""
        metadata = {
            "plan_id": "plan-001",
            # Missing item_type
            "risk_level": "low",
            "requires_approval": True,
        }
        
        errors = validate_plan(metadata)
        
        assert any("item_type" in err for err in errors)


# ---------------------------------------------------------------------------
# Retry Wrapper Tests
# ---------------------------------------------------------------------------


class TestRetryWrapper:
    """Test retry with backoff decorator."""
    
    def test_retry_success_first_attempt(self):
        """Test function that succeeds on first attempt."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = success_func()
        
        assert result == "success"
        assert call_count == 1
    
    def test_retry_succeeds_after_failures(self):
        """Test function that succeeds after some failures."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def eventual_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"
        
        result = eventual_success()
        
        assert result == "success"
        assert call_count == 3
    
    def test_retry_exhausts_all_attempts(self):
        """Test function that always fails."""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent failure")
        
        with pytest.raises(ValueError):
            always_fails()
        
        assert call_count == 3  # Initial + 2 retries


# ---------------------------------------------------------------------------
# File Operations Tests
# ---------------------------------------------------------------------------


class TestFileOperations:
    """Test file operation functions."""
    
    def test_move_to_done(self, temp_vault, sample_approval_file):
        """Test moving file to Done directory."""
        # Mock DRY_RUN to False and patch the DONE_DIR
        with patch("approval_orchestrator.DRY_RUN", False):
            with patch("approval_orchestrator.DONE_DIR", temp_vault["done"]):
                done_path = move_to_done(
                    sample_approval_file,
                    "test-001",
                    {"status": "success"},
                )
        
        assert done_path.exists()
        assert not sample_approval_file.exists()
        assert done_path.parent == temp_vault["done"]
        
        # Verify metadata was added
        metadata, _ = load_markdown_file(done_path)
        assert metadata["execution_status"] == "completed"
        assert metadata["moved_to_done_from"] == "Approved"
    
    def test_move_to_quarantine(self, temp_vault, sample_approval_file):
        """Test moving file to Quarantine directory."""
        with patch("approval_orchestrator.DRY_RUN", False):
            with patch("approval_orchestrator.QUARANTINE_DIR", temp_vault["quarantine"]):
                quarantine_path = move_to_quarantine(
                    sample_approval_file,
                    "Test quarantine reason",
                    {"error": "Test error"}
                )
        
        assert quarantine_path.exists()
        assert not sample_approval_file.exists()
        assert quarantine_path.parent == temp_vault["quarantine"]
        
        # Verify metadata was added
        metadata, _ = load_markdown_file(quarantine_path)
        assert metadata["quarantine_reason"] == "Test quarantine reason"
        assert metadata["status"] == "quarantined"
    
    def test_move_to_rejected(self, temp_vault, sample_approval_file):
        """Test moving file to Rejected directory."""
        with patch("approval_orchestrator.DRY_RUN", False):
            with patch("approval_orchestrator.VAULT", temp_vault["vault"]):
                rejected_path = move_to_rejected(
                    sample_approval_file,
                    "Test rejection reason"
                )
        
        assert rejected_path.exists()
        assert not sample_approval_file.exists()
        assert rejected_path.parent == temp_vault["rejected"]
        
        # Verify metadata was added
        metadata, _ = load_markdown_file(rejected_path)
        assert metadata["rejection_reason"] == "Test rejection reason"
        assert metadata["status"] == "rejected"


# ---------------------------------------------------------------------------
# Audit Logging Tests
# ---------------------------------------------------------------------------


class TestAuditLogging:
    """Test audit logging functions."""
    
    def test_write_audit_log(self, temp_vault):
        """Test writing audit log entry."""
        audit_entry = {
            "approval_id": "test-001",
            "stage": "test_stage",
            "test_data": "value",
        }
        
        with patch("approval_orchestrator.AUDIT_DIR", temp_vault["audit"]):
            log_path = write_audit_log(audit_entry, temp_vault["audit"])
        
        assert log_path.exists()
        
        # Verify content
        with open(log_path, "r", encoding="utf-8") as f:
            entries = json.load(f)
        
        assert len(entries) == 1
        assert entries[0]["approval_id"] == "test-001"
        assert entries[0]["stage"] == "test_stage"
    
    def test_log_action(self, temp_vault):
        """Test logging action to daily log file."""
        with patch("approval_orchestrator.LOGS_DIR", temp_vault["logs"]):
            log_path = log_action(
                "test-001",
                "test_action",
                "completed",
                {"detail": "value"},
                temp_vault["logs"],
            )
        
        assert log_path.exists()
        
        # Verify content
        with open(log_path, "r", encoding="utf-8") as f:
            line = f.readline()
            entry = json.loads(line)
        
        assert entry["approval_id"] == "test-001"
        assert entry["action"] == "test_action"
        assert entry["status"] == "completed"


# ---------------------------------------------------------------------------
# MCP Integration Tests
# ---------------------------------------------------------------------------


class TestMCPIntegration:
    """Test MCP tool integration."""
    
    def test_call_mcp_tool_dry_run(self):
        """Test MCP tool call in dry run mode."""
        with patch("approval_orchestrator.DRY_RUN", True):
            result = call_mcp_tool("test_tool", {"param": "value"})
        
        assert result["status"] == "simulated"
        assert result["tool"] == "test_tool"
        assert "DRY_RUN" in result["message"]
    
    @patch("approval_orchestrator.httpx.Client")
    def test_call_mcp_tool_success(self, mock_client_class):
        """Test successful MCP tool call."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success", "result": "data"}
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response
        mock_client.__enter__.return_value = mock_client
        
        mock_client_class.return_value = mock_client
        
        with patch("approval_orchestrator.DRY_RUN", False):
            result = call_mcp_tool("test_tool", {"param": "value"})
        
        assert result["status"] == "success"
        mock_client.post.assert_called_once()
    
    @patch("approval_orchestrator.httpx.Client")
    def test_call_mcp_tool_http_error(self, mock_client_class):
        """Test MCP tool call with HTTP error."""
        mock_client = MagicMock()
        mock_client.post.side_effect = Exception("Connection refused")
        mock_client.__enter__.return_value = mock_client
        
        mock_client_class.return_value = mock_client
        
        with patch("approval_orchestrator.DRY_RUN", False):
            with pytest.raises(RuntimeError):
                call_mcp_tool("test_tool", {"param": "value"})


# ---------------------------------------------------------------------------
# Action Execution Tests
# ---------------------------------------------------------------------------


class TestActionExecution:
    """Test action execution routing."""
    
    def test_execute_action_email(self):
        """Test routing to email executor."""
        plan_metadata = {"plan_id": "plan-001", "item_type": "email"}
        approval_metadata = {"action_type": "send_email"}
        
        with patch("approval_orchestrator.execute_email_action") as mock_email:
            mock_email.return_value = {"status": "success", "action_type": "email_draft"}
            result = execute_action(plan_metadata, approval_metadata)
        
        mock_email.assert_called_once_with(plan_metadata, approval_metadata)
    
    def test_execute_action_publish_post(self):
        """Test routing to publish post executor."""
        plan_metadata = {"plan_id": "plan-001", "item_type": "linkedin_post"}
        approval_metadata = {"action_type": "publish_post"}
        
        with patch("approval_orchestrator.execute_publish_post_action") as mock_publish:
            mock_publish.return_value = {"status": "success", "action_type": "publish_post"}
            result = execute_action(plan_metadata, approval_metadata)
        
        mock_publish.assert_called_once_with(plan_metadata, approval_metadata)
    
    def test_execute_action_whatsapp(self):
        """Test routing to WhatsApp executor."""
        plan_metadata = {"plan_id": "plan-001", "item_type": "whatsapp"}
        approval_metadata = {"action_type": "reply_whatsapp"}
        
        with patch("approval_orchestrator.execute_whatsapp_action") as mock_whatsapp:
            mock_whatsapp.return_value = {"status": "success", "action_type": "reply_whatsapp"}
            result = execute_action(plan_metadata, approval_metadata)
        
        mock_whatsapp.assert_called_once_with(plan_metadata, approval_metadata)
    
    def test_execute_action_unknown(self):
        """Test routing with unknown action type."""
        plan_metadata = {"plan_id": "plan-001"}
        approval_metadata = {"action_type": "unknown_action"}
        
        with pytest.raises(ValueError, match="Unknown action_type"):
            execute_action(plan_metadata, approval_metadata)


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------


class TestIntegration:
    """Integration tests for full approval processing flow."""
    
    def test_process_approval_success(
        self, temp_vault, sample_approval_file, sample_plan_file
    ):
        """Test successful approval processing."""
        # Mock external dependencies
        with patch("approval_orchestrator.DRY_RUN", False):
            with patch("approval_orchestrator.execute_action") as mock_execute:
                mock_execute.return_value = {
                    "status": "success",
                    "action_type": "email_draft",
                    "tool": "draft_email",
                }
                
                # Temporarily redirect paths
                with patch("approval_orchestrator.VAULT", temp_vault["vault"]):
                    with patch("approval_orchestrator.APPROVED_DIR", temp_vault["approved"]):
                        with patch("approval_orchestrator.DONE_DIR", temp_vault["done"]):
                            with patch("approval_orchestrator.QUARANTINE_DIR", temp_vault["quarantine"]):
                                with patch("approval_orchestrator.AUDIT_DIR", temp_vault["audit"]):
                                    with patch("approval_orchestrator.LOGS_DIR", temp_vault["logs"]):
                                        result = process_approval_file(sample_approval_file)
        
        assert result is True
        # File should be moved to Done
        assert not sample_approval_file.exists()
        assert (temp_vault["done"] / "test-approval.md").exists()
    
    def test_process_approval_validation_failure(
        self, temp_vault, sample_approval_file
    ):
        """Test approval processing with validation failure."""
        # Create invalid approval (missing fields)
        invalid_content = """---
approval_id: test-001
---
Invalid approval.
"""
        sample_approval_file.write_text(invalid_content, encoding="utf-8")
        
        with patch("approval_orchestrator.DRY_RUN", False):
            with patch("approval_orchestrator.VAULT", temp_vault["vault"]):
                with patch("approval_orchestrator.APPROVED_DIR", temp_vault["approved"]):
                    with patch("approval_orchestrator.QUARANTINE_DIR", temp_vault["quarantine"]):
                        with patch("approval_orchestrator.AUDIT_DIR", temp_vault["audit"]):
                            result = process_approval_file(sample_approval_file)
        
        assert result is False
        # File should be rejected
        assert not sample_approval_file.exists()
        assert (temp_vault["rejected"] / "test-approval.md").exists()
    
    def test_process_approval_plan_not_found(
        self, temp_vault, sample_approval_file
    ):
        """Test approval processing when plan file is missing."""
        with patch("approval_orchestrator.DRY_RUN", False):
            with patch("approval_orchestrator.VAULT", temp_vault["vault"]):
                with patch("approval_orchestrator.APPROVED_DIR", temp_vault["approved"]):
                    with patch("approval_orchestrator.QUARANTINE_DIR", temp_vault["quarantine"]):
                        with patch("approval_orchestrator.AUDIT_DIR", temp_vault["audit"]):
                            result = process_approval_file(sample_approval_file)
        
        assert result is False
        # File should be rejected
        assert not sample_approval_file.exists()
        assert (temp_vault["rejected"] / "test-approval.md").exists()


# ---------------------------------------------------------------------------
# Timestamp Tests
# ---------------------------------------------------------------------------


class TestTimestamp:
    """Test timestamp generation."""
    
    def test_get_timestamp_format(self):
        """Test timestamp format is ISO 8601."""
        timestamp = get_timestamp()
        
        # Should be ISO format with Z suffix
        assert timestamp.endswith("Z")
        # Should be parseable
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert parsed.tzinfo is not None


# ---------------------------------------------------------------------------
# Run Tests
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
