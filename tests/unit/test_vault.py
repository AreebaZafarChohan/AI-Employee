"""Unit tests for vault management."""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.vault.vault_manager import VaultManager
from src.vault.validators import InputValidator, RetryHandler


class TestVaultManager:
    """Tests for VaultManager class."""

    @pytest.fixture
    def temp_vault(self):
        """Create a temporary directory for vault testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_create_vault_success(self, temp_vault):
        """Test successful vault creation."""
        vault_manager = VaultManager(temp_vault)
        result = vault_manager.create_vault()

        assert result["success"] is True
        assert "Needs_Action" in result["created_folders"]
        assert "Plans" in result["created_folders"]
        assert "Done" in result["created_folders"]

    def test_create_vault_creates_dashboard(self, temp_vault):
        """Test that vault creation creates Dashboard.md."""
        vault_manager = VaultManager(temp_vault)
        vault_manager.create_vault()

        dashboard_path = Path(temp_vault) / "Dashboard.md"
        assert dashboard_path.exists()
        content = dashboard_path.read_text()
        assert "AI Employee Dashboard" in content

    def test_create_vault_creates_handbook(self, temp_vault):
        """Test that vault creation creates Company_Handbook.md."""
        vault_manager = VaultManager(temp_vault)
        vault_manager.create_vault()

        handbook_path = Path(temp_vault) / "Company_Handbook.md"
        assert handbook_path.exists()
        content = handbook_path.read_text()
        assert "Company Handbook" in content

    def test_create_vault_does_not_overwrite(self, temp_vault):
        """Test that existing files are not overwritten."""
        vault_manager = VaultManager(temp_vault)

        # Create existing file
        dashboard_path = Path(temp_vault) / "Dashboard.md"
        dashboard_path.write_text("Custom content")

        result = vault_manager.create_vault()

        assert "Dashboard.md (already exists)" in result["skipped_files"]
        assert dashboard_path.read_text() == "Custom content"

    def test_validate_vault_success(self, temp_vault):
        """Test vault validation with valid structure."""
        vault_manager = VaultManager(temp_vault)
        vault_manager.create_vault()

        is_valid, errors = vault_manager.validate_vault()

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_vault_missing_folders(self, temp_vault):
        """Test vault validation with missing folders."""
        vault_manager = VaultManager(temp_vault)
        # Create partial structure
        Path(temp_vault).mkdir(exist_ok=True)

        is_valid, errors = vault_manager.validate_vault()

        assert is_valid is False
        assert any("Needs_Action" in e for e in errors)

    def test_get_folder_path(self, temp_vault):
        """Test getting folder paths."""
        vault_manager = VaultManager(temp_vault)

        needs_action = vault_manager.get_folder_path("needs_action")
        assert needs_action.name == "Needs_Action"

        plans = vault_manager.get_folder_path("plans")
        assert plans.name == "Plans"

        done = vault_manager.get_folder_path("done")
        assert done.name == "Done"

    def test_get_folder_path_invalid(self, temp_vault):
        """Test getting invalid folder path."""
        vault_manager = VaultManager(temp_vault)

        with pytest.raises(ValueError):
            vault_manager.get_folder_path("invalid_folder")

    def test_get_vault_stats(self, temp_vault):
        """Test getting vault statistics."""
        vault_manager = VaultManager(temp_vault)
        vault_manager.create_vault()

        # Add a test file
        needs_action = Path(temp_vault) / "Needs_Action"
        (needs_action / "test_task.md").write_text("# Test Task")

        stats = vault_manager.get_vault_stats()

        assert stats["folders"]["Needs_Action"]["count"] == 1
        assert "test_task.md" in stats["folders"]["Needs_Action"]["files"]


class TestInputValidator:
    """Tests for InputValidator class."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return InputValidator()

    def test_validate_content_success(self, validator):
        """Test validation of safe content."""
        content = "# Test Task\nThis is a safe task description."
        is_valid, error = validator.validate_content(content)

        assert is_valid is True
        assert error == ""

    def test_validate_content_empty(self, validator):
        """Test validation of empty content."""
        is_valid, error = validator.validate_content("")

        assert is_valid is False
        assert "empty" in error.lower()

    def test_validate_content_script_tag(self, validator):
        """Test detection of script tags."""
        content = "# Task\n<script>alert('xss')</script>"
        is_valid, error = validator.validate_content(content)

        assert is_valid is False
        assert "unsafe" in error.lower()

    def test_validate_content_javascript_url(self, validator):
        """Test detection of javascript URLs."""
        content = "# Task\n[Click](javascript:alert('xss'))"
        is_valid, error = validator.validate_content(content)

        assert is_valid is False

    def test_validate_content_event_handler(self, validator):
        """Test detection of event handlers."""
        content = '# Task\n<div onclick="evil()">Click me</div>'
        is_valid, error = validator.validate_content(content)

        assert is_valid is False

    def test_sanitize_content(self, validator):
        """Test content sanitization."""
        content = "# Task\n<script>evil()</script>\nSafe content"
        sanitized = validator.sanitize_content(content)

        assert "<script>" not in sanitized
        assert "Safe content" in sanitized

    def test_sanitize_content_preserves_markdown(self, validator):
        """Test that sanitization preserves markdown."""
        content = "# Heading\n\n## Subheading\n\n- Item 1\n- Item 2\n\n**Bold** and *italic*"
        sanitized = validator.sanitize_content(content)

        assert "# Heading" in sanitized
        assert "## Subheading" in sanitized
        assert "- Item 1" in sanitized
        assert "**Bold**" in sanitized

    def test_validate_file_path_traversal(self, validator):
        """Test detection of path traversal."""
        is_valid, error = validator.validate_file_path("../../../etc/passwd")

        assert is_valid is False
        assert "traversal" in error.lower()

    def test_validate_file_path_blocked_extension(self, validator):
        """Test blocking of dangerous file extensions."""
        is_valid, error = validator.validate_file_path("malware.exe")

        assert is_valid is False
        assert "not allowed" in error.lower()

    def test_sanitize_filename(self, validator):
        """Test filename sanitization."""
        filename = "test<>:\"/\\|?*.md"
        sanitized = validator.sanitize_filename(filename)

        assert "<" not in sanitized
        assert ">" not in sanitized
        assert ":" not in sanitized

    def test_sanitize_filename_empty(self, validator):
        """Test sanitization of empty filename."""
        sanitized = validator.sanitize_filename("")
        assert sanitized == "unnamed"


class TestRetryHandler:
    """Tests for RetryHandler class."""

    @pytest.fixture
    def handler(self):
        """Create retry handler instance."""
        return RetryHandler(max_retries=3, base_delay=0.01)

    def test_calculate_delay_exponential(self, handler):
        """Test exponential backoff calculation."""
        delay0 = handler.calculate_delay(0)
        delay1 = handler.calculate_delay(1)
        delay2 = handler.calculate_delay(2)

        assert delay1 > delay0
        assert delay2 > delay1

    def test_calculate_delay_max_limit(self, handler):
        """Test that delay doesn't exceed maximum."""
        handler.max_delay = 1.0
        delay = handler.calculate_delay(100)

        assert delay <= 1.0

    def test_should_retry_connection_error(self, handler):
        """Test that ConnectionError is retryable."""
        assert handler.should_retry(ConnectionError("Connection refused")) is True

    def test_should_retry_timeout_error(self, handler):
        """Test that TimeoutError is retryable."""
        assert handler.should_retry(TimeoutError("Timed out")) is True

    def test_should_retry_value_error(self, handler):
        """Test that ValueError is not retryable."""
        assert handler.should_retry(ValueError("Bad value")) is False

    def test_execute_with_retry_success(self, handler):
        """Test successful execution on first attempt."""
        def success_func():
            return "success"

        result = handler.execute_with_retry(success_func)
        assert result == "success"

    def test_execute_with_retry_eventual_success(self, handler):
        """Test successful execution after retries."""
        call_count = 0

        def eventual_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Transient failure")
            return "success"

        result = handler.execute_with_retry(eventual_success)
        assert result == "success"
        assert call_count == 3

    def test_execute_with_retry_all_failures(self, handler):
        """Test failure after all retries exhausted."""
        def always_fail():
            raise ConnectionError("Persistent failure")

        with pytest.raises(ConnectionError):
            handler.execute_with_retry(always_fail)
