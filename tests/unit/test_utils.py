"""Unit tests for utility modules."""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils.config import Config
from src.utils.file_utils import FileUtils
from src.utils.logger import setup_logger, get_logger, ProcessingLogger


class TestConfig:
    """Tests for Config class."""

    @pytest.fixture
    def temp_env_file(self):
        """Create a temporary .env file."""
        temp_dir = tempfile.mkdtemp()
        env_path = Path(temp_dir) / ".env"
        env_path.write_text("""
GEMINI_API_KEY=test-key-123
VAULT_PATH=/test/vault
WATCH_PATH=/test/watch
WATCH_RECURSIVE=true
WATCH_PATTERNS=*.md,*.txt,*.json
MAX_PROCESSING_TIME=60
RETRY_ATTEMPTS=5
RETENTION_DAYS=14
LOG_LEVEL=DEBUG
""")
        yield str(env_path)
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_load_from_env_file(self, temp_env_file):
        """Test loading configuration from .env file."""
        config = Config(temp_env_file)

        assert config.gemini_api_key == "test-key-123"
        assert config.vault_path == "/test/vault"
        assert config.watch_path == "/test/watch"

    def test_load_custom_values(self, temp_env_file):
        """Test loading custom values."""
        config = Config(temp_env_file)

        assert config.watch_recursive is True
        assert config.watch_patterns == ["*.md", "*.txt", "*.json"]
        assert config.max_processing_time == 60
        assert config.retry_attempts == 5
        assert config.retention_days == 14

    def test_default_values(self):
        """Test default values when no .env file."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()

            assert config.max_processing_time == 30
            assert config.retry_attempts == 3
            assert config.retention_days == 30
            assert config.log_level == "INFO"

    def test_validate_missing_api_key(self, tmp_path):
        """Test validation with missing API key."""
        # Create empty env file to override any existing .env
        empty_env = tmp_path / ".env"
        empty_env.write_text("VAULT_PATH=/test\n")
        with patch.dict(os.environ, {"VAULT_PATH": "/test", "GEMINI_API_KEY": ""}, clear=True):
            config = Config(str(empty_env))
            config.gemini_api_key = ""  # Force empty
            is_valid, errors = config.validate()

            assert is_valid is False
            assert any("GEMINI_API_KEY" in e for e in errors)

    def test_validate_missing_vault_path(self, tmp_path):
        """Test validation with missing vault path."""
        empty_env = tmp_path / ".env"
        empty_env.write_text("GEMINI_API_KEY=test\n")
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test", "VAULT_PATH": ""}, clear=True):
            config = Config(str(empty_env))
            config.vault_path = ""  # Force empty
            is_valid, errors = config.validate()

            assert is_valid is False
            assert any("VAULT_PATH" in e for e in errors)

    def test_to_dict_masks_api_key(self, temp_env_file):
        """Test that API key is masked in dictionary output."""
        config = Config(temp_env_file)
        config_dict = config.to_dict()

        assert config_dict["gemini_api_key"] == "***"

    def test_get_vault_folders(self, temp_env_file):
        """Test getting vault folder paths."""
        config = Config(temp_env_file)
        folders = config.get_vault_folders()

        assert "needs_action" in folders
        assert "plans" in folders
        assert "done" in folders


class TestFileUtils:
    """Tests for FileUtils class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_ensure_directory_creates(self, temp_dir):
        """Test creating a new directory."""
        new_dir = Path(temp_dir) / "new_folder"
        result = FileUtils.ensure_directory(new_dir)

        assert result.exists()
        assert result.is_dir()

    def test_ensure_directory_existing(self, temp_dir):
        """Test with existing directory."""
        result = FileUtils.ensure_directory(temp_dir)

        assert result.exists()

    def test_read_file_success(self, temp_dir):
        """Test reading a file."""
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Hello, World!")

        content = FileUtils.read_file(test_file)

        assert content == "Hello, World!"

    def test_read_file_not_found(self, temp_dir):
        """Test reading non-existent file."""
        with pytest.raises(FileNotFoundError):
            FileUtils.read_file(Path(temp_dir) / "nonexistent.txt")

    def test_write_file_success(self, temp_dir):
        """Test writing a file."""
        test_file = Path(temp_dir) / "output.txt"
        result = FileUtils.write_file(test_file, "Test content")

        assert result.exists()
        assert result.read_text() == "Test content"

    def test_write_file_creates_parent(self, temp_dir):
        """Test that write creates parent directories."""
        test_file = Path(temp_dir) / "nested" / "dir" / "file.txt"
        result = FileUtils.write_file(test_file, "Content")

        assert result.exists()

    def test_move_file_success(self, temp_dir):
        """Test moving a file."""
        source = Path(temp_dir) / "source.txt"
        source.write_text("Content")
        dest = Path(temp_dir) / "dest.txt"

        result = FileUtils.move_file(source, dest)

        assert result.exists()
        assert not source.exists()
        assert dest.read_text() == "Content"

    def test_move_file_not_found(self, temp_dir):
        """Test moving non-existent file."""
        with pytest.raises(FileNotFoundError):
            FileUtils.move_file(
                Path(temp_dir) / "nonexistent.txt",
                Path(temp_dir) / "dest.txt"
            )

    def test_copy_file_success(self, temp_dir):
        """Test copying a file."""
        source = Path(temp_dir) / "source.txt"
        source.write_text("Content")
        dest = Path(temp_dir) / "dest.txt"

        result = FileUtils.copy_file(source, dest)

        assert result.exists()
        assert source.exists()  # Original still exists

    def test_delete_file_success(self, temp_dir):
        """Test deleting a file."""
        test_file = Path(temp_dir) / "delete_me.txt"
        test_file.write_text("Delete me")

        result = FileUtils.delete_file(test_file)

        assert result is True
        assert not test_file.exists()

    def test_delete_file_not_exists(self, temp_dir):
        """Test deleting non-existent file."""
        result = FileUtils.delete_file(Path(temp_dir) / "nonexistent.txt")

        assert result is False

    def test_list_files_all(self, temp_dir):
        """Test listing all files."""
        (Path(temp_dir) / "file1.txt").write_text("1")
        (Path(temp_dir) / "file2.md").write_text("2")

        files = FileUtils.list_files(temp_dir)

        assert len(files) == 2

    def test_list_files_pattern(self, temp_dir):
        """Test listing files with pattern."""
        (Path(temp_dir) / "file1.txt").write_text("1")
        (Path(temp_dir) / "file2.md").write_text("2")

        files = FileUtils.list_files(temp_dir, ["*.md"])

        assert len(files) == 1
        assert files[0].suffix == ".md"

    def test_list_files_recursive(self, temp_dir):
        """Test recursive file listing."""
        (Path(temp_dir) / "file1.txt").write_text("1")
        subdir = Path(temp_dir) / "subdir"
        subdir.mkdir()
        (subdir / "file2.txt").write_text("2")

        files = FileUtils.list_files(temp_dir, ["*.txt"], recursive=True)

        assert len(files) == 2

    def test_get_file_hash(self, temp_dir):
        """Test getting file hash."""
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Test content")

        hash1 = FileUtils.get_file_hash(test_file)

        # Same content should produce same hash
        test_file2 = Path(temp_dir) / "test2.txt"
        test_file2.write_text("Test content")
        hash2 = FileUtils.get_file_hash(test_file2)

        assert hash1 == hash2

    def test_generate_unique_filename(self, temp_dir):
        """Test generating unique filename."""
        import time
        path1 = FileUtils.generate_unique_filename(temp_dir, "task")
        time.sleep(1.1)  # Wait for timestamp to change
        path2 = FileUtils.generate_unique_filename(temp_dir, "task")

        # Should be different due to timestamp
        assert path1.stem != path2.stem or path1 != path2


class TestLogger:
    """Tests for logger module."""

    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary log directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_setup_logger_creates_files(self, temp_log_dir):
        """Test that setup_logger creates log files."""
        logger = setup_logger("test_logger", temp_log_dir)

        # Log something to trigger file creation
        logger.info("Test message")

        app_log = Path(temp_log_dir) / "application.log"
        assert app_log.exists()

    def test_get_logger_returns_same_instance(self, temp_log_dir):
        """Test that get_logger returns the same instance."""
        logger1 = setup_logger("same_logger", temp_log_dir)
        logger2 = get_logger("same_logger")

        assert logger1 is logger2

    def test_processing_logger_timing(self, temp_log_dir):
        """Test ProcessingLogger timing."""
        base_logger = setup_logger("timing_test", temp_log_dir)
        proc_logger = ProcessingLogger(base_logger)

        proc_logger.start_operation("op1", "Test operation")
        import time
        time.sleep(0.1)
        duration = proc_logger.end_operation("op1", "Completed", success=True)

        assert duration >= 0.1

    def test_processing_logger_error(self, temp_log_dir):
        """Test ProcessingLogger error logging."""
        base_logger = setup_logger("error_test", temp_log_dir)
        proc_logger = ProcessingLogger(base_logger)

        # Should not raise
        proc_logger.log_error("op1", ValueError("Test error"))

        error_log = Path(temp_log_dir) / "errors.log"
        content = error_log.read_text()
        assert "ValueError" in content
