"""Main CLI entry point for AI Employee."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from ..utils.config import Config
from ..utils.logger import setup_logger, get_logger
from ..vault.vault_manager import VaultManager


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI.

    Returns:
        Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="ai-employee",
        description="Personal AI Employee Bronze Tier - Obsidian vault workflow system"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize Obsidian vault structure")
    init_parser.add_argument(
        "--vault-path",
        required=True,
        help="Path to the directory where the vault should be created"
    )

    # Configure command
    config_parser = subparsers.add_parser("configure", help="Configure system settings")
    config_parser.add_argument(
        "--watch-path",
        required=True,
        help="Directory to monitor for new input files"
    )
    config_parser.add_argument(
        "--vault-path",
        required=True,
        help="Path to the Obsidian vault"
    )

    # Process command
    process_parser = subparsers.add_parser("process", help="Process tasks from /Needs_Action")

    # Complete command
    complete_parser = subparsers.add_parser("complete", help="Move completed plan to /Done")
    complete_parser.add_argument(
        "--plan-id",
        required=True,
        help="ID of the plan to mark as complete"
    )

    # Test command
    test_parser = subparsers.add_parser("test", help="Run system verification tests")

    return parser


def cmd_init(args: argparse.Namespace) -> int:
    """Handle the init command.

    Args:
        args: Parsed command arguments.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    logger = get_logger("cli")
    logger.info(f"Initializing vault at: {args.vault_path}")

    vault_manager = VaultManager(args.vault_path)
    result = vault_manager.create_vault()

    if result["success"]:
        print(f"Vault initialized successfully at: {result['vault_path']}")
        if result["created_files"]:
            for file in result["created_files"]:
                print(f"- Created {file}")
        if result["created_folders"]:
            print(f"- Created folder structure: {', '.join(result['created_folders'])}")
        if result["skipped_files"]:
            for file in result["skipped_files"]:
                print(f"- Skipped {file}")
        return 0
    else:
        print(f"Error: Could not initialize vault at {args.vault_path}")
        for error in result["errors"]:
            print(f"Reason: {error}")
        return 1


def cmd_configure(args: argparse.Namespace) -> int:
    """Handle the configure command.

    Args:
        args: Parsed command arguments.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    logger = get_logger("cli")
    logger.info(f"Configuring system: watch={args.watch_path}, vault={args.vault_path}")

    # Validate paths
    watch_path = Path(args.watch_path)
    vault_path = Path(args.vault_path)

    errors = []
    if not watch_path.exists():
        errors.append(f"Watch path does not exist: {args.watch_path}")
    if not vault_path.exists():
        errors.append(f"Vault path does not exist: {args.vault_path}")

    if errors:
        print("Error: Could not save configuration")
        for error in errors:
            print(f"Reason: {error}")
        return 1

    # Validate vault structure
    vault_manager = VaultManager(args.vault_path)
    is_valid, validation_errors = vault_manager.validate_vault()

    if not is_valid:
        print("Error: Vault structure is invalid")
        for error in validation_errors:
            print(f"Reason: {error}")
        print("Hint: Run 'init' command first to create vault structure")
        return 1

    # Save configuration to .env file
    config_path = Path.cwd() / ".env"
    config_content = f"""# AI Employee Configuration
VAULT_PATH={vault_path.absolute()}
WATCH_PATH={watch_path.absolute()}
WATCH_RECURSIVE=false
WATCH_PATTERNS=*.md,*.txt
"""

    # Append to existing .env or create new
    mode = "a" if config_path.exists() else "w"
    with open(config_path, mode) as f:
        if mode == "a":
            f.write("\n")
        f.write(config_content)

    print("Configuration saved successfully")
    print(f"- Watching: {watch_path.absolute()}")
    print(f"- Vault: {vault_path.absolute()}")
    return 0


def cmd_process(args: argparse.Namespace) -> int:
    """Handle the process command.

    Args:
        args: Parsed command arguments.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    logger = get_logger("cli")
    logger.info("Starting task processing")

    # Load configuration
    config = Config()
    is_valid, errors = config.validate()

    if not is_valid:
        print("Error: Configuration is invalid")
        for error in errors:
            print(f"- {error}")
        print("Hint: Run 'configure' command first")
        return 1

    # Import here to avoid circular imports
    from ..vault.file_processor import FileProcessor
    from ..watcher.file_system_watcher import FileSystemWatcher

    try:
        # Process watched directory first
        if config.watch_path:
            watcher = FileSystemWatcher(config)
            new_files = watcher.check_for_new_files()
            if new_files:
                logger.info(f"Found {len(new_files)} new files in watched directory")
                watcher.move_files_to_needs_action(new_files)

        # Process files in /Needs_Action
        processor = FileProcessor(config)
        result = processor.process_needs_action_files()

        print("Processing completed")
        print(f"- Found {result.get('found_count', 0)} new tasks")
        print(f"- Processed {result.get('processed_count', 0)} tasks with Gemini")
        print(f"- Created {result.get('plan_count', 0)} plans in /Plans folder")
        print(f"- Duration: {result.get('duration', 0):.2f} seconds")

        if result.get("errors"):
            print("\nErrors:")
            for error in result["errors"]:
                print(f"- {error}")

        return 0 if result.get("success", False) else 1

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        print(f"Error during processing: {e}")
        return 1


def cmd_complete(args: argparse.Namespace) -> int:
    """Handle the complete command.

    Args:
        args: Parsed command arguments.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    logger = get_logger("cli")
    logger.info(f"Completing plan: {args.plan_id}")

    # Load configuration
    config = Config()
    is_valid, errors = config.validate()

    if not is_valid:
        print("Error: Configuration is invalid")
        for error in errors:
            print(f"- {error}")
        return 1

    # Import here to avoid circular imports
    from ..vault.file_processor import FileProcessor

    try:
        processor = FileProcessor(config)
        result = processor.move_completed_task(args.plan_id)

        if result["success"]:
            print("Task completed successfully")
            print(f"- Plan {args.plan_id} moved to /Done folder")
            print("- Status updated to completed")
            return 0
        else:
            print(f"Error: Could not complete task")
            print(f"Reason: {result.get('error', 'Unknown error')}")
            return 1

    except Exception as e:
        logger.error(f"Completion failed: {e}")
        print(f"Error: Could not complete task")
        print(f"Reason: {e}")
        return 1


def cmd_test(args: argparse.Namespace) -> int:
    """Handle the test command.

    Args:
        args: Parsed command arguments.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    logger = get_logger("cli")
    logger.info("Running system verification tests")

    results = {
        "vault_structure": {"status": "FAIL", "message": ""},
        "file_watcher": {"status": "FAIL", "message": ""},
        "gemini_processing": {"status": "FAIL", "message": ""},
        "folder_transitions": {"status": "FAIL", "message": ""},
        "security_measures": {"status": "FAIL", "message": ""}
    }

    all_passed = True

    # Test vault structure
    try:
        config = Config()
        if config.vault_path:
            vault_manager = VaultManager(config.vault_path)
            is_valid, errors = vault_manager.validate_vault()
            if is_valid:
                results["vault_structure"]["status"] = "OK"
                results["vault_structure"]["message"] = "Vault structure is valid"
            else:
                all_passed = False
                results["vault_structure"]["message"] = "; ".join(errors)
        else:
            all_passed = False
            results["vault_structure"]["message"] = "VAULT_PATH not configured"
    except Exception as e:
        all_passed = False
        results["vault_structure"]["message"] = str(e)

    # Test file watcher
    try:
        config = Config()
        if config.watch_path:
            from ..watcher.file_system_watcher import FileSystemWatcher
            watcher = FileSystemWatcher(config)
            # Just test initialization
            results["file_watcher"]["status"] = "OK"
            results["file_watcher"]["message"] = "File watcher initialized successfully"
        else:
            results["file_watcher"]["status"] = "SKIP"
            results["file_watcher"]["message"] = "WATCH_PATH not configured"
    except Exception as e:
        all_passed = False
        results["file_watcher"]["message"] = str(e)

    # Test Gemini processing
    try:
        from ..claude.claude_client import ClaudeClient
        config = Config()
        if config.gemini_api_key:
            # Just test client initialization, don't make actual API call
            client = ClaudeClient(config)
            results["gemini_processing"]["status"] = "OK"
            results["gemini_processing"]["message"] = "Gemini client initialized"
        else:
            results["gemini_processing"]["status"] = "SKIP"
            results["gemini_processing"]["message"] = "GEMINI_API_KEY not configured"
    except Exception as e:
        all_passed = False
        results["gemini_processing"]["message"] = str(e)

    # Test folder transitions
    try:
        config = Config()
        if config.vault_path:
            vault_manager = VaultManager(config.vault_path)
            folders = vault_manager.get_vault_stats()["folders"]
            results["folder_transitions"]["status"] = "OK"
            results["folder_transitions"]["message"] = "Folder structure accessible"
        else:
            all_passed = False
            results["folder_transitions"]["message"] = "VAULT_PATH not configured"
    except Exception as e:
        all_passed = False
        results["folder_transitions"]["message"] = str(e)

    # Test security measures
    try:
        from ..vault.validators import InputValidator
        validator = InputValidator()
        # Test with safe input
        is_safe, _ = validator.validate_content("# Test Task\nThis is a test.")
        if is_safe:
            results["security_measures"]["status"] = "OK"
            results["security_measures"]["message"] = "Input validation working"
        else:
            all_passed = False
            results["security_measures"]["message"] = "Input validation failed"
    except Exception as e:
        all_passed = False
        results["security_measures"]["message"] = str(e)

    # Print results
    if all_passed:
        print("All tests passed successfully")
    else:
        print("Test failures detected:")

    for test_name, result in results.items():
        status = result["status"]
        message = result["message"]
        display_name = test_name.replace("_", " ").title()
        print(f"- {display_name}: {status}" + (f" - {message}" if message else ""))

    return 0 if all_passed else 1


def main(args: Optional[list] = None) -> int:
    """Main entry point for the CLI.

    Args:
        args: Optional list of command line arguments.

    Returns:
        Exit code.
    """
    # Set up logging
    setup_logger()

    parser = create_parser()
    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        parser.print_help()
        return 0

    # Dispatch to command handler
    commands = {
        "init": cmd_init,
        "configure": cmd_configure,
        "process": cmd_process,
        "complete": cmd_complete,
        "test": cmd_test
    }

    handler = commands.get(parsed_args.command)
    if handler:
        return handler(parsed_args)
    else:
        print(f"Unknown command: {parsed_args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
