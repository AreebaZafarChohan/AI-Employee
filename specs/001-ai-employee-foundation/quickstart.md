# Quickstart Guide: Personal AI Employee – Bronze Tier

## Prerequisites

- Python 3.8 or higher
- Access to Claude API (with appropriate credentials)
- Obsidian installed (optional, for viewing vault)

## Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd ai-employee
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Claude API Access
Create a `.env` file in the project root with your Claude API key:
```env
CLAUDE_API_KEY=your_api_key_here
```

**Note**: Store this file outside of the Obsidian vault to avoid exposing credentials.

## Initial Vault Setup

### 1. Create the Obsidian Vault
```bash
python -m src.cli.main init --vault-path /path/to/your/vault
```

This will create:
- `Dashboard.md`
- `Company_Handbook.md`
- `/Needs_Action` folder
- `/Plans` folder
- `/Done` folder

### 2. Configure the File Watcher
Edit the configuration file to specify which directory to monitor:
```bash
python -m src.cli.main configure --watch-path /path/to/watch --vault-path /path/to/your/vault
```

## Basic Usage

### 1. Add a Task
Place a Markdown file in your watched directory with your task:
```
# My New Task
I need to research the latest trends in AI development.
```

### 2. Process Tasks Manually
Run the processing workflow:
```bash
python -m src.cli.main process
```

This will:
- Check the watched directory for new files
- Move them to the `/Needs_Action` folder in your vault
- Process them with Claude to create plans in the `/Plans` folder

### 3. Review Generated Plans
Check the `/Plans` folder in your vault for generated Plan.md files.

### 4. Mark Tasks as Done
Move completed plan files to the `/Done` folder in your vault:
```bash
python -m src.cli.main complete --plan-id <plan-id>
```

## Configuration Options

### File Watcher Settings
- `watch_path`: Directory to monitor for new input files
- `file_patterns`: File patterns to watch (e.g., "*.md", "*.txt")
- `recursive`: Whether to monitor subdirectories

### Processing Settings
- `max_processing_time`: Maximum time to spend processing a single task (default: 30 seconds per FR-014)
- `retry_attempts`: Number of times to retry failed processing (per FR-016)
- `retention_days`: Days to keep completed tasks before archival (default: 30 days per FR-015)

## Troubleshooting

### Common Issues
1. **API Connection Errors**: Verify your Claude API key is correct and has sufficient permissions
2. **File Permission Errors**: Ensure the application has read/write access to the vault and watched directories
3. **Processing Timeouts**: Large or complex tasks may require more processing time; adjust settings accordingly

### Logging
Check the logs directory for detailed information about processing:
- `logs/application.log`: General application logs
- `logs/errors.log`: Error-specific logs
- `logs/process.log`: Detailed processing logs

## Verification

To verify your setup is working correctly:

1. Run the smoke test:
```bash
python -m src.cli.main test
```

2. Verify the following:
   - Obsidian vault structure exists with all required files and folders
   - File watcher detects new files in the watched directory
   - Tasks appear in the `/Needs_Action` folder
   - Claude generates plans in the `/Plans` folder
   - Completed tasks move to the `/Done` folder
   - All processing completes within 30 seconds (per FR-014)
   - Input sanitization prevents injection attacks (per FR-013)
   - Error handling works with automatic retries (per FR-016)