# Dynamic Workflow Adaptor - Asset Manifest

## Overview
This manifest documents all assets included in the Dynamic Workflow Adaptor skill. These assets provide the core functionality and configuration templates needed to implement dynamic workflow adaptation.

## Assets List

### 1. `workflow_adaptor.py`
- **Type**: Core Implementation
- **Purpose**: Main dynamic workflow adaptation engine that monitors events and applies workflow modifications
- **Dependencies**: Python 3.8+, asyncio, aiohttp, redis, pyyaml
- **Configuration**: Controlled via environment variables and adaptation rule files
- **Location**: `assets/workflow_adaptor.py`

### 2. `adaptation_rules.json`
- **Type**: Configuration Template
- **Purpose**: Defines the rules for adapting workflows based on events, conditions, and business logic
- **Format**: JSON with schema validation
- **Location**: `assets/adaptation_rules.json`

### 3. `example-adaptation-config.json`
- **Type**: Example Configuration
- **Purpose**: Provides a working example of how to configure various types of dynamic workflow adaptations
- **Content**: Sample adaptation rules with different triggering conditions and actions
- **Location**: `assets/example-adaptation-config.json`

### 4. `README.md`
- **Type**: Documentation
- **Purpose**: Quick start guide and overview of the Dynamic Workflow Adaptor skill
- **Content**: Basic usage instructions, key features, and links to detailed documentation
- **Location**: `README.md`

### 5. `SKILL.md`
- **Type**: Specification
- **Purpose**: Comprehensive specification of the Dynamic Workflow Adaptor skill
- **Content**: Overview, impact analysis, environment variables, network implications, blueprints, validation checklist, and anti-patterns
- **Location**: `SKILL.md`

## Directory Structure
```
.claude/skills/gold/dynamic_workflow_adaptor/
├── SKILL.md
├── README.md
├── assets/
│   ├── workflow_adaptor.py
│   ├── adaptation_rules.json
│   ├── example-adaptation-config.json
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
- redis library for state management (optional)
- pyyaml for configuration parsing
- Standard Python libraries: json, logging, threading, os, datetime

## License
This skill is released under the MIT License. See the LICENSE file for details.

## Maintainer
Gold Team