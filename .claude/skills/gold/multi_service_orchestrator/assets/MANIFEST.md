# Multi-Service Orchestrator - Asset Manifest

## Overview
This manifest documents all assets included in the Multi-Service Orchestrator skill. These assets provide the core functionality and configuration templates needed to implement multi-service orchestration.

## Assets List

### 1. `orchestrator_engine.py`
- **Type**: Core Implementation
- **Purpose**: Main orchestration engine that manages workflow execution across multiple services
- **Dependencies**: Python 3.8+, requests, redis, pyyaml, opentracing
- **Configuration**: Controlled via environment variables and workflow definition files
- **Location**: `assets/orchestrator_engine.py`

### 2. `workflow_definitions.json`
- **Type**: Configuration Template
- **Purpose**: Defines the structure and rules for multi-service workflows, including service dependencies, execution order, and error handling
- **Format**: JSON with schema validation
- **Location**: `assets/workflow_definitions.json`

### 3. `example-workflow-config.json`
- **Type**: Example Configuration
- **Purpose**: Provides a working example of how to configure various types of multi-service workflows
- **Content**: Sample workflows with different orchestration patterns and execution parameters
- **Location**: `assets/example-workflow-config.json`

### 4. `README.md`
- **Type**: Documentation
- **Purpose**: Quick start guide and overview of the Multi-Service Orchestrator skill
- **Content**: Basic usage instructions, key features, and links to detailed documentation
- **Location**: `README.md`

### 5. `SKILL.md`
- **Type**: Specification
- **Purpose**: Comprehensive specification of the Multi-Service Orchestrator skill
- **Content**: Overview, impact analysis, environment variables, network implications, blueprints, validation checklist, and anti-patterns
- **Location**: `SKILL.md`

## Directory Structure
```
.claude/skills/gold/multi_service_orchestrator/
├── SKILL.md
├── README.md
├── assets/
│   ├── orchestrator_engine.py
│   ├── workflow_definitions.json
│   ├── example-workflow-config.json
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
- requests library for HTTP communication
- redis library for state management (optional)
- pyyaml for configuration parsing
- opentracing for distributed tracing
- Standard Python libraries: json, logging, threading, asyncio, os, datetime

## License
This skill is released under the MIT License. See the LICENSE file for details.

## Maintainer
Gold Team