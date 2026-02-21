"""File operation utilities for AI Employee."""

import os
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import hashlib


class FileUtils:
    """Utility class for file operations."""

    @staticmethod
    def ensure_directory(path: str | Path) -> Path:
        """Ensure a directory exists, create if it doesn't.

        Args:
            path: Path to the directory.

        Returns:
            Path object for the directory.
        """
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    @staticmethod
    def read_file(path: str | Path, encoding: str = "utf-8") -> str:
        """Read file contents.

        Args:
            path: Path to the file.
            encoding: File encoding.

        Returns:
            File contents as string.

        Raises:
            FileNotFoundError: If file doesn't exist.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return file_path.read_text(encoding=encoding)

    @staticmethod
    def write_file(path: str | Path, content: str, encoding: str = "utf-8") -> Path:
        """Write content to file.

        Args:
            path: Path to the file.
            content: Content to write.
            encoding: File encoding.

        Returns:
            Path object for the written file.
        """
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding=encoding)
        return file_path

    @staticmethod
    def move_file(source: str | Path, destination: str | Path) -> Path:
        """Move a file to a new location.

        Args:
            source: Source file path.
            destination: Destination file path.

        Returns:
            Path object for the moved file.

        Raises:
            FileNotFoundError: If source file doesn't exist.
        """
        src_path = Path(source)
        dst_path = Path(destination)

        if not src_path.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_path), str(dst_path))
        return dst_path

    @staticmethod
    def copy_file(source: str | Path, destination: str | Path) -> Path:
        """Copy a file to a new location.

        Args:
            source: Source file path.
            destination: Destination file path.

        Returns:
            Path object for the copied file.

        Raises:
            FileNotFoundError: If source file doesn't exist.
        """
        src_path = Path(source)
        dst_path = Path(destination)

        if not src_path.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src_path), str(dst_path))
        return dst_path

    @staticmethod
    def delete_file(path: str | Path) -> bool:
        """Delete a file.

        Args:
            path: Path to the file.

        Returns:
            True if file was deleted, False if it didn't exist.
        """
        file_path = Path(path)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    @staticmethod
    def list_files(
        directory: str | Path,
        patterns: Optional[List[str]] = None,
        recursive: bool = False
    ) -> List[Path]:
        """List files in a directory.

        Args:
            directory: Directory to list.
            patterns: Optional list of glob patterns to filter files.
            recursive: Whether to search recursively.

        Returns:
            List of file paths.
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return []

        files = []
        if patterns:
            for pattern in patterns:
                if recursive:
                    files.extend(dir_path.rglob(pattern))
                else:
                    files.extend(dir_path.glob(pattern))
        else:
            if recursive:
                files = [f for f in dir_path.rglob("*") if f.is_file()]
            else:
                files = [f for f in dir_path.iterdir() if f.is_file()]

        return sorted(files)

    @staticmethod
    def get_file_hash(path: str | Path) -> str:
        """Get MD5 hash of a file.

        Args:
            path: Path to the file.

        Returns:
            MD5 hash string.

        Raises:
            FileNotFoundError: If file doesn't exist.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    @staticmethod
    def get_file_modified_time(path: str | Path) -> datetime:
        """Get file modification time.

        Args:
            path: Path to the file.

        Returns:
            Modification time as datetime.

        Raises:
            FileNotFoundError: If file doesn't exist.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        return datetime.fromtimestamp(file_path.stat().st_mtime)

    @staticmethod
    def generate_unique_filename(
        directory: str | Path,
        base_name: str,
        extension: str = ".md"
    ) -> Path:
        """Generate a unique filename in a directory.

        Args:
            directory: Directory for the file.
            base_name: Base name for the file.
            extension: File extension.

        Returns:
            Path to unique filename.
        """
        dir_path = Path(directory)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{base_name}_{timestamp}{extension}"
        return dir_path / filename
