"""
Simple File Watcher Demo - Direct execution
"""

from pathlib import Path
import shutil

# Paths
WATCH_FOLDER = Path("D:/Gemini_Cli/hackathon/hackathon_0/AI-Employee/watch_folder")
VAULT_FOLDER = Path("D:/Gemini_Cli/hackathon/hackathon_0/AI-Employee/AI-Employee-Vault")
NEEDS_ACTION = VAULT_FOLDER / "Needs_Action"

print("=" * 60)
print("AI Employee - File Watcher Demo")
print("=" * 60)
print()

# Ensure directories exist
NEEDS_ACTION.mkdir(parents=True, exist_ok=True)

print(f"Watch Folder: {WATCH_FOLDER}")
print(f"Vault Folder: {VAULT_FOLDER}")
print(f"Needs Action: {NEEDS_ACTION}")
print()

# Find markdown files in watch folder
print("Scanning watch folder for new files...")
md_files = list(WATCH_FOLDER.glob("*.md"))

if md_files:
    print(f"Found {len(md_files)} file(s):")
    for f in md_files:
        print(f"  - {f.name}")
    print()
    
    # Move files to Needs_Action
    print("Moving files to Needs_Action folder...")
    for file in md_files:
        dest = NEEDS_ACTION / file.name
        shutil.move(str(file), str(dest))
        print(f"  Moved: {file.name} -> Needs_Action/")
    print()
    
    # Show Needs_Action contents
    print(f"Needs_Action folder now contains:")
    for f in NEEDS_ACTION.glob("*.md"):
        print(f"  - {f.name}")
    print()
else:
    print("No new files found in watch folder")
    print()

print("=" * 60)
print("Demo Complete!")
print("=" * 60)
