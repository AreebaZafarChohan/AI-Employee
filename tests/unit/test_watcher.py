"""Unit tests for file system watcher."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.watcher.watcher_config import WatcherConfig
from src.watcher.file_system_watcher import FileSystemWatcher, NewFileHandler
from src.utils.config import Config


class TestWatcherConfig:
    """Tests for WatcherConfig class."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        watch_dir = tempfile.mkdtemp()
        vault_dir = tempfile.mkdtemp()
        yield watch_dir, vault_dir
        shutil.rmtree(watch_dir, ignore_errors=True)
        shutil.rmtree(vault_dir, ignore_errors=True)

    def test_init_default_values(self, temp_dirs):
        """Test initialization with default values."""
        watch_dir, vault_dir = temp_dirs
        config = WatcherConfig(watch_path=watch_dir, vault_path=vault_dir)

        assert config.recursive is False
        assert config.file_patterns == ["*.md", "*.txt"]
        assert config.polling_interval == 1.0

    def test_init_custom_values(self, temp_dirs):
        """Test initialization with custom values."""
        watch_dir, vault_dir = temp_dirs
        config = WatcherConfig(
            watch_path=watch_dir,
            vault_path=vault_dir,
            recursive=True,
            file_patterns=["*.json"],
            polling_interval=2.0
        )

        assert config.recursive is True
        assert config.file_patterns == ["*.json"]
        assert config.polling_interval == 2.0

    def test_validate_success(self, temp_dirs):
        """Test validation with valid paths."""
        watch_dir, vault_dir = temp_dirs
        config = WatcherConfig(watch_path=watch_dir, vault_path=vault_dir)

        is_valid, errors = config.validate()

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_missing_watch_path(self, temp_dirs):
        """Test validation with missing watch path."""
        _, vault_dir = temp_dirs
        config = WatcherConfig(watch_path="/nonexistent/path", vault_path=vault_dir)

        is_valid, errors = config.validate()

        assert is_valid is False
        assert any("Watch path" in e for e in errors)

    def test_validate_missing_vault_path(self, temp_dirs):
        """Test validation with missing vault path."""
        watch_dir, _ = temp_dirs
        config = WatcherConfig(watch_path=watch_dir, vault_path="/nonexistent/path")

        is_valid, errors = config.validate()

        assert is_valid is False
        assert any("Vault path" in e for e in errors)

    def test_validate_empty_patterns(self, temp_dirs):
        """Test validation with empty file patterns."""
        watch_dir, vault_dir = temp_dirs
        config = WatcherConfig(
            watch_path=watch_dir,
            vault_path=vault_dir,
            file_patterns=[]
        )

        is_valid, errors = config.validate()

        assert is_valid is False
        assert any("pattern" in e.lower() for e in errors)

    def test_get_needs_action_path(self, temp_dirs):
        """Test getting Needs_Action path."""
        watch_dir, vault_dir = temp_dirs
        config = WatcherConfig(watch_path=watch_dir, vault_path=vault_dir)

        needs_action = config.get_needs_action_path()

        assert needs_action.name == "Needs_Action"
        assert str(vault_dir) in str(needs_action)


class TestNewFileHandler:
    """Tests for NewFileHandler class."""

    def test_matches_pattern_md(self):
        """Test matching .md files."""
        callback = MagicMock()
        handler = NewFileHandler(patterns=["*.md"], callback=callback)

        assert handler._matches_pattern(Path("test.md")) is True
        assert handler._matches_pattern(Path("test.txt")) is False

    def test_matches_pattern_multiple(self):
        """Test matching multiple patterns."""
        callback = MagicMock()
        handler = NewFileHandler(patterns=["*.md", "*.txt"], callback=callback)

        assert handler._matches_pattern(Path("test.md")) is True
        assert handler._matches_pattern(Path("test.txt")) is True
        assert handler._matches_pattern(Path("test.json")) is False


class TestFileSystemWatcher:
    """Tests for FileSystemWatcher class."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        watch_dir = tempfile.mkdtemp()
        vault_dir = tempfile.mkdtemp()
        # Create vault structure
        (Path(vault_dir) / "Needs_Action").mkdir()
        (Path(vault_dir) / "Plans").mkdir()
        (Path(vault_dir) / "Done").mkdir()
        yield watch_dir, vault_dir
        shutil.rmtree(watch_dir, ignore_errors=True)
        shutil.rmtree(vault_dir, ignore_errors=True)

    @pytest.fixture
    def mock_config(self, temp_dirs):
        """Create mock configuration."""
        watch_dir, vault_dir = temp_dirs
        config = MagicMock(spec=Config)
        config.watch_path = watch_dir
        config.vault_path = vault_dir
        config.watch_recursive = False
        config.watch_patterns = ["*.md", "*.txt"]
        return config

    def test_check_for_new_files_empty(self, mock_config):
        """Test checking empty directory."""
        watcher = FileSystemWatcher(mock_config)
        files = watcher.check_for_new_files()

        assert len(files) == 0

    def test_check_for_new_files_with_files(self, mock_config, temp_dirs):
        """Test checking directory with files."""
        watch_dir, _ = temp_dirs
        # Create test files
        (Path(watch_dir) / "task1.md").write_text("# Task 1")
        (Path(watch_dir) / "task2.txt").write_text("Task 2")

        watcher = FileSystemWatcher(mock_config)
        files = watcher.check_for_new_files()

        assert len(files) == 2

    def test_check_for_new_files_filters_patterns(self, mock_config, temp_dirs):
        """Test that file patterns are applied."""
        watch_dir, _ = temp_dirs
        # Create test files with different extensions
        (Path(watch_dir) / "task.md").write_text("# Task")
        (Path(watch_dir) / "data.json").write_text("{}")

        watcher = FileSystemWatcher(mock_config)
        files = watcher.check_for_new_files()

        assert len(files) == 1
        assert files[0].suffix == ".md"

    def test_move_files_to_needs_action(self, mock_config, temp_dirs):
        """Test moving files to Needs_Action."""
        watch_dir, vault_dir = temp_dirs
        # Create test file
        test_file = Path(watch_dir) / "task.md"
        test_file.write_text("# Task")

        watcher = FileSystemWatcher(mock_config)
        moved = watcher.move_files_to_needs_action([test_file])

        assert len(moved) == 1
        assert not test_file.exists()
        assert (Path(vault_dir) / "Needs_Action" / "task.md").exists()

    def test_move_files_handles_duplicates(self, mock_config, temp_dirs):
        """Test handling duplicate filenames."""
        watch_dir, vault_dir = temp_dirs
        # Create existing file in Needs_Action
        (Path(vault_dir) / "Needs_Action" / "task.md").write_text("Existing")

        # Create new file with same name
        test_file = Path(watch_dir) / "task.md"
        test_file.write_text("# New Task")

        watcher = FileSystemWatcher(mock_config)
        moved = watcher.move_files_to_needs_action([test_file])

        assert len(moved) == 1
        # Original should still exist
        assert (Path(vault_dir) / "Needs_Action" / "task.md").exists()
        # New file should have different name
        assert moved[0].name != "task.md"

    def test_process_watch_directory(self, mock_config, temp_dirs):
        """Test one-shot processing of watch directory."""
        watch_dir, _ = temp_dirs
        # Create test files
        (Path(watch_dir) / "task1.md").write_text("# Task 1")
        (Path(watch_dir) / "task2.md").write_text("# Task 2")

        watcher = FileSystemWatcher(mock_config)
        result = watcher.process_watch_directory()

        assert result["success"] is True
        assert result["found_count"] == 2
        assert result["moved_count"] == 2

    def test_process_watch_directory_empty(self, mock_config):
        """Test processing empty watch directory."""
        watcher = FileSystemWatcher(mock_config)
        result = watcher.process_watch_directory()

        assert result["success"] is True
        assert result["found_count"] == 0
        assert result["moved_count"] == 0
