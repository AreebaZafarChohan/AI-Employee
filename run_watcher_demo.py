"""
File Watcher Demo Script
Detects new files and moves them to Needs_Action folder
"""

import sys
import time
from pathlib import Path
from src.watcher.file_system_watcher import FileSystemWatcher
from src.watcher.watcher_config import WatcherConfig
from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)

def main():
    print("=" * 60)
    print("AI Employee - File Watcher Demo")
    print("=" * 60)
    print()
    
    # Load configuration
    config = Config()
    watcher_config = WatcherConfig.from_config(config)
    
    print(f"Watch Path: {watcher_config.watch_path}")
    print(f"Vault Path: {watcher_config.vault_path}")
    print(f"Patterns: {watcher_config.file_patterns}")
    print(f"Recursive: {watcher_config.recursive}")
    print()
    
    # Create watcher
    watcher = FileSystemWatcher(watcher_config)
    
    # Check for new files
    print("Scanning for new files...")
    print()
    
    new_files = watcher.check_for_new_files()
    
    if new_files:
        print(f"Found {len(new_files)} new file(s):")
        for file in new_files:
            print(f"   - {file}")
        print()
        
        # Move files to Needs_Action
        print("Moving files to Needs_Action folder...")
        moved_files = watcher.move_files_to_needs_action(new_files)
        
        print(f"Moved {len(moved_files)} file(s):")
        for file in moved_files:
            print(f"   -> {file}")
        print()
    else:
        print("No new files found")
        print()
    
    # Show Needs_Action folder contents
    needs_action_path = Path(config.vault_path) / "Needs_Action"
    if needs_action_path.exists():
        files = list(needs_action_path.glob("*.md"))
        print(f"Needs_Action folder contents ({len(files)} files):")
        for file in files:
            print(f"   - {file.name}")
        print()
    
    print("=" * 60)
    print("Watcher demo complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
