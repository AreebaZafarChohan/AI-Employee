# AI Employee - Bronze Tier

Personal AI Employee Bronze Tier - A local-first system that uses an Obsidian vault as its primary state store.

## Overview

The AI Employee monitors a designated directory for new input files using a file system watcher, processes these inputs through Gemini's reasoning capabilities, and manages the workflow through three vault folders:

- `/Needs_Action` - Tasks waiting to be processed
- `/Plans` - Generated plans from Gemini
- `/Done` - Completed tasks

## Prerequisites

- Python 3.8 or higher
- Access to Gemini API (with appropriate credentials)
- Obsidian installed (optional, for viewing vault)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd ai-employee

# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

## Configuration

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
GEMINI_API_KEY=your_gemini_api_key_here
VAULT_PATH=/path/to/your/obsidian/vault
WATCH_PATH=/path/to/watch/directory
```

## Quick Start

### 1. Initialize Vault

```bash
python -m src.cli.main init --vault-path /path/to/your/vault
```

### 2. Configure File Watcher

```bash
python -m src.cli.main configure --watch-path /path/to/watch --vault-path /path/to/your/vault
```

### 3. Process Tasks

```bash
python -m src.cli.main process
```

### 4. Complete Tasks

```bash
python -m src.cli.main complete --plan-id <plan-id>
```

### 5. Run Tests

```bash
python -m src.cli.main test
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize Obsidian vault structure |
| `configure` | Configure file watcher and vault paths |
| `process` | Process tasks from /Needs_Action |
| `complete` | Move completed plan to /Done |
| `test` | Run system verification tests |

## Architecture

```
src/
├── watcher/          # File system monitoring
├── vault/            # Vault management and processing
├── claude/           # Gemini API integration and agent skills
├── utils/            # Configuration, logging, utilities
└── cli/              # Command-line interface
```

## License

MIT License
