"""Unit tests for Claude integration."""

import pytest
from unittest.mock import MagicMock, patch

from src.claude.claude_client import ClaudeClient, ClaudeAPIError
from src.claude.response_processor import ResponseProcessor
from src.claude.agent_skills.skill_base import SkillBase, SkillExecutionError, SkillValidationError
from src.claude.agent_skills.task_analyzer import TaskAnalyzer
from src.claude.agent_skills.plan_generator import PlanGenerator


class TestClaudeClient:
    """Tests for ClaudeClient class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = MagicMock()
        config.gemini_api_key = "test-api-key-12345"
        return config

    def test_init_with_api_key(self, mock_config):
        """Test initialization with API key."""
        client = ClaudeClient(mock_config)
        assert client.api_key == "test-api-key-12345"

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        config = MagicMock()
        config.gemini_api_key = ""
        client = ClaudeClient(config)
        assert client.api_key == ""

    def test_send_request_success(self, mock_config):
        """Test successful API request."""
        client = ClaudeClient(mock_config)
        response = client.send_request("Test prompt")

        assert response["success"] is True
        assert "content" in response
        assert response["model"] == "gemini-2.5-flash"

    def test_send_request_no_api_key(self):
        """Test request without API key raises error."""
        config = MagicMock()
        config.gemini_api_key = ""
        client = ClaudeClient(config)

        with pytest.raises(ClaudeAPIError):
            client.send_request("Test prompt")

    def test_validate_connection_success(self, mock_config):
        """Test successful connection validation."""
        client = ClaudeClient(mock_config)
        is_valid, message = client.validate_connection()

        assert is_valid is True

    def test_validate_connection_no_key(self):
        """Test connection validation without API key."""
        config = MagicMock()
        config.gemini_api_key = ""
        client = ClaudeClient(config)

        is_valid, message = client.validate_connection()

        assert is_valid is False
        assert "not configured" in message

    def test_get_stats(self, mock_config):
        """Test getting client statistics."""
        client = ClaudeClient(mock_config)
        client.send_request("Test")

        stats = client.get_stats()

        assert stats["request_count"] == 1
        assert stats["api_configured"] is True


class TestResponseProcessor:
    """Tests for ResponseProcessor class."""

    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return ResponseProcessor()

    def test_process_response_success(self, processor):
        """Test processing successful response."""
        response = {
            "success": True,
            "content": "# Plan\n\nThis is a test plan.",
            "model": "gemini-2.5-flash",
            "tokens_used": 10
        }

        result = processor.process_response(response)

        assert result["success"] is True
        assert "Plan" in result["content"]

    def test_process_response_failure(self, processor):
        """Test processing failed response."""
        response = {"success": False}

        result = processor.process_response(response)

        assert result["success"] is False
        assert len(result["errors"]) > 0

    def test_validate_response_empty(self, processor):
        """Test validation of empty response."""
        is_valid, error = processor.validate_response("")

        assert is_valid is False
        assert "empty" in error.lower()

    def test_validate_response_with_script(self, processor):
        """Test validation detects script tags."""
        content = "# Plan\n<script>evil()</script>"

        is_valid, error = processor.validate_response(content)

        assert is_valid is False
        assert "unsafe" in error.lower()

    def test_sanitize_response(self, processor):
        """Test response sanitization."""
        content = "# Plan\n<script>evil()</script>\nGood content"

        sanitized = processor.sanitize_response(content)

        assert "<script>" not in sanitized
        assert "Good content" in sanitized

    def test_extract_plan_sections(self, processor):
        """Test extracting plan sections."""
        content = """# Plan

## Overview
This is the overview.

## Approach
This is the approach.

## Timeline
This is the timeline.
"""
        sections = processor.extract_plan_sections(content)

        assert "overview" in sections
        assert "approach" in sections
        assert "timeline" in sections

    def test_extract_action_items(self, processor):
        """Test extracting action items."""
        content = """# Plan

## Action Items
- [ ] First task
- [x] Completed task
- [ ] Third task
"""
        items = processor.extract_action_items(content)

        assert "First task" in items
        assert "Completed task" in items
        assert "Third task" in items


class TestTaskAnalyzer:
    """Tests for TaskAnalyzer skill."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Claude client."""
        client = MagicMock(spec=ClaudeClient)
        client.send_request.return_value = {
            "success": True,
            "content": """
Summary: Test task summary

Requirements:
- Requirement 1
- Requirement 2

Complexity: Medium

Dependencies:
- Dependency 1

Priority: P2
"""
        }
        return client

    def test_validate_input_success(self, mock_client):
        """Test input validation with valid input."""
        analyzer = TaskAnalyzer(mock_client)
        is_valid, error = analyzer.validate_input({"content": "# Test Task"})

        assert is_valid is True

    def test_validate_input_missing_content(self, mock_client):
        """Test input validation with missing content."""
        analyzer = TaskAnalyzer(mock_client)
        is_valid, error = analyzer.validate_input({})

        assert is_valid is False
        assert "content" in error.lower()

    def test_validate_input_empty_content(self, mock_client):
        """Test input validation with empty content."""
        analyzer = TaskAnalyzer(mock_client)
        is_valid, error = analyzer.validate_input({"content": ""})

        assert is_valid is False

    def test_execute_success(self, mock_client):
        """Test successful task analysis."""
        analyzer = TaskAnalyzer(mock_client)
        result = analyzer.execute({
            "content": "# Test Task\nThis is a test.",
            "task_id": "test-1"
        })

        assert result["success"] is True
        assert "analysis" in result

    def test_execute_fallback(self, mock_client):
        """Test fallback when Claude fails."""
        mock_client.send_request.side_effect = Exception("API Error")

        analyzer = TaskAnalyzer(mock_client)
        result = analyzer.execute({
            "content": "# Test Task",
            "task_id": "test-1"
        })

        assert result["success"] is True
        assert result.get("fallback") is True


class TestPlanGenerator:
    """Tests for PlanGenerator skill."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Claude client."""
        client = MagicMock(spec=ClaudeClient)
        client.send_request.return_value = {
            "success": True,
            "content": """# Plan: Test Task

## Overview
This is a test plan.

## Approach
Step by step approach.
"""
        }
        return client

    def test_validate_input_success(self, mock_client):
        """Test input validation with valid input."""
        generator = PlanGenerator(mock_client)
        is_valid, error = generator.validate_input({"content": "# Test Task"})

        assert is_valid is True

    def test_validate_input_missing_content(self, mock_client):
        """Test input validation with missing content."""
        generator = PlanGenerator(mock_client)
        is_valid, error = generator.validate_input({})

        assert is_valid is False

    def test_execute_success(self, mock_client):
        """Test successful plan generation."""
        generator = PlanGenerator(mock_client)
        result = generator.execute({
            "content": "# Test Task\nThis is a test.",
            "task_id": "test-1"
        })

        assert result["success"] is True
        assert "plan_content" in result
        assert "# Plan" in result["plan_content"]

    def test_execute_adds_metadata(self, mock_client):
        """Test that plan includes metadata."""
        generator = PlanGenerator(mock_client)
        result = generator.execute({
            "content": "# Test Task",
            "task_id": "test-1"
        })

        plan = result["plan_content"]
        assert "Status" in plan

    def test_execute_fallback(self, mock_client):
        """Test fallback when Claude fails."""
        mock_client.send_request.side_effect = Exception("API Error")

        generator = PlanGenerator(mock_client)
        result = generator.execute({
            "content": "# Test Task",
            "task_id": "test-1"
        })

        assert result["success"] is True
        assert result.get("fallback") is True
        assert "plan_content" in result
