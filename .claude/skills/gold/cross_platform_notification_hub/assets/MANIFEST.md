# Cross-Platform Notification Hub - Asset Manifest

## Overview
This manifest documents all assets included in the Cross-Platform Notification Hub skill. These assets provide the core functionality and configuration templates needed to implement multi-platform notifications.

## Assets List

### 1. `notification_hub.py`
- **Type**: Core Implementation
- **Purpose**: Main notification hub engine that routes messages to appropriate platforms
- **Dependencies**: Python 3.8+, asyncio, aiohttp, redis, jinja2
- **Configuration**: Controlled via environment variables and channel configuration files
- **Location**: `assets/notification_hub.py`

### 2. `notification_channels.json`
- **Type**: Configuration Template
- **Purpose**: Defines the configuration for different notification channels (Slack, Email, Teams, SMS)
- **Format**: JSON with schema validation
- **Location**: `assets/notification_channels.json`

### 3. `example-notification-config.json`
- **Type**: Example Configuration
- **Purpose**: Provides a working example of how to configure various notification channels
- **Content**: Sample configurations with different platforms and delivery rules
- **Location**: `assets/example-notification-config.json`

### 4. `README.md`
- **Type**: Documentation
- **Purpose**: Quick start guide and overview of the Cross-Platform Notification Hub skill
- **Content**: Basic usage instructions, key features, and links to detailed documentation
- **Location**: `README.md`

### 5. `SKILL.md`
- **Type**: Specification
- **Purpose**: Comprehensive specification of the Cross-Platform Notification Hub skill
- **Content**: Overview, impact analysis, environment variables, network implications, blueprints, validation checklist, and anti-patterns
- **Location**: `SKILL.md`

## Directory Structure
```
.claude/skills/gold/cross_platform_notification_hub/
├── SKILL.md
├── README.md
├── assets/
│   ├── notification_hub.py
│   ├── notification_channels.json
│   ├── example-notification-config.json
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

## Dependencies
- Python 3.8+
- asyncio library for async processing
- aiohttp for HTTP communication
- redis library for preference storage (optional)
- jinja2 for message templating
- twilio or boto3 for SMS delivery
- Standard Python libraries: json, logging, threading, os, datetime

## License
This skill is released under the MIT License. See the LICENSE file for details.

## Maintainer
Gold Team