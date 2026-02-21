# Recurring Task Scheduler - Asset Manifest

## Overview
This manifest documents all assets included in the Recurring Task Scheduler skill. These assets provide the core functionality and configuration templates needed to implement recurring task scheduling.

## Assets List

### 1. `task_scheduler.py`
- **Type**: Core Implementation
- **Purpose**: Main scheduler implementation that parses schedule rules, manages task execution, and handles state persistence
- **Dependencies**: Python 3.7+, croniter, json, logging, threading, subprocess
- **Configuration**: Controlled via environment variables and schedule rule files
- **Location**: `assets/task_scheduler.py`

### 2. `task-schedule-rules.json`
- **Type**: Configuration Template
- **Purpose**: Defines the structure and rules for recurring tasks, including schedule patterns, commands, and execution parameters
- **Format**: JSON with schema validation
- **Location**: `assets/task-schedule-rules.json`

### 3. `example-schedule-config.json`
- **Type**: Example Configuration
- **Purpose**: Provides a working example of how to configure various types of recurring tasks
- **Content**: Sample tasks with different scheduling patterns and execution parameters
- **Location**: `assets/example-schedule-config.json`

### 4. `README.md`
- **Type**: Documentation
- **Purpose**: Quick start guide and overview of the Recurring Task Scheduler skill
- **Content**: Basic usage instructions, key features, and links to detailed documentation
- **Location**: `README.md`

### 5. `SKILL.md`
- **Type**: Specification
- **Purpose**: Comprehensive specification of the Recurring Task Scheduler skill
- **Content**: Overview, impact analysis, environment variables, network implications, blueprints, validation checklist, and anti-patterns
- **Location**: `SKILL.md`

## Directory Structure
```
.claude/skills/silver/recurring_task_scheduler/
├── SKILL.md
├── README.md
├── assets/
│   ├── task_scheduler.py
│   ├── task-schedule-rules.json
│   ├── example-schedule-config.json
│   └── MANIFEST.md
└── docs/
    ├── patterns.md
    ├── impact-checklist.md
    └── gotchas.md
```

## Version Information
- **Skill Version**: 1.0.0
- **Schema Version**: 1.0
- **Compatible with Claude Code**: v2.0+

## Update History
- **v1.0.0** (2026-02-06): Initial release with core scheduler functionality

## Dependencies
- Python 3.7+
- croniter library for cron expression parsing
- Standard Python libraries: json, logging, threading, subprocess, os, datetime

## License
This skill is released under the MIT License. See the LICENSE file for details.

## Maintainer
Silver Team