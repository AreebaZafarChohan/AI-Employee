# Feature Specification: Personal AI Employee – Bronze Tier (Foundation)

**Feature Branch**: `001-ai-employee-foundation`
**Created**: 2026-02-09
**Status**: Draft
**Input**: User description: "Personal AI Employee – Bronze Tier (Foundation) Context: This system is a local-first Personal AI Employee built using Claude Code and an Obsidian vault. The goal of the Bronze tier is to prove the foundational architecture works end-to-end: Watcher → Vault → Claude Reasoning → Vault Output. Target user: - Technical student / developer - Running system locally - Comfortable with terminal, Python, Obsidian Core Objective: Build a minimum viable Digital FTE that can: - Detect new inputs - Reason about them - Write structured outputs into an Obsidian vault Success Criteria: - Obsidian vault exists with: - Dashboard.md - Company_Handbook.md - Folder structure exists: - /Needs_Action - /Plans - /Done - At least ONE working watcher (file system OR Gmail) - Claude Code can: - Read files from /Needs_Action - Create a Plan.md in /Plans - Move completed items to /Done - All AI behavior is implemented via Claude Agent Skills (no inline logic) Constraints: - Local-only execution (no cloud) - No payments - No WhatsApp automation - No social posting - No MCP actions that modify external systems - No background daemon orchestration (manual runs acceptable) Out of Scope (NOT building in Bronze): - Cloud deployment - WhatsApp integration - Banking or payments - MCP browser automation - Ralph Wiggum autonomous loops - Multi-agent orchestration - Approval workflows Non-Functional Requirements: - Simple, readable Markdown outputs - Deterministic folder transitions - No secrets stored in vault - Safe-by-default behavior Deliverables: - Working Obsidian vault - One watcher script - Demonstration of Claude Code reading + writing vault files - Clear README explaining how Bronze works"

## Clarifications

### Session 2026-02-09

- Q: Which type of input watcher should be implemented for the Bronze tier? → A: File system watcher
- Q: How should security requirements be handled for the AI employee system? → A: Define explicit security requirements
- Q: How should performance targets be addressed for the AI employee system? → A: Define basic performance targets for processing tasks
- Q: How should data retention be handled for the AI employee system? → A: Define a clear data retention policy for the vault
- Q: How should error handling be addressed for the AI employee system? → A: Define explicit error handling and retry mechanisms

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Initialize Obsidian Vault Structure (Priority: P1)

As a technical user, I want to initialize a local Obsidian vault with the required structure so that I can begin using the AI employee system.

**Why this priority**: This is the foundational setup that everything else depends on. Without the proper vault structure, no other functionality can work.

**Independent Test**: Can be fully tested by running the initialization script and verifying that all required files and folders exist with the correct structure.

**Acceptance Scenarios**:

1. **Given** a fresh installation of the AI employee system, **When** I run the initialization command, **Then** an Obsidian vault is created with Dashboard.md, Company_Handbook.md, and the folder structure /Needs_Action, /Plans, and /Done
2. **Given** an existing directory, **When** I run the initialization command, **Then** the vault structure is created without overwriting existing important files

---

### User Story 2 - Set Up File System Input Watcher (Priority: P2)

As a technical user, I want to configure a file system watcher that detects new input files so that the AI employee can respond to new tasks automatically.

**Why this priority**: This enables the core functionality of detecting new inputs, which is essential for the AI employee to work as intended.

**Independent Test**: Can be tested by configuring the file system watcher and verifying that it correctly identifies new input files and places them in the /Needs_Action folder.

**Acceptance Scenarios**:

1. **Given** a configured file system watcher, **When** a new file is added to the watched directory, **Then** it appears in the /Needs_Action folder
2. **Given** a configured file system watcher, **When** a file is modified in the watched directory, **Then** it appears in the /Needs_Action folder if it meets input criteria

---

### User Story 3 - Process Tasks with Claude Reasoning (Priority: P3)

As a technical user, I want Claude to read tasks from /Needs_Action and create structured plans in /Plans so that I can review and approve the AI's proposed actions.

**Why this priority**: This implements the core AI reasoning component that transforms raw inputs into structured plans.

**Independent Test**: Can be tested by placing a task in /Needs_Action and verifying that Claude generates a corresponding Plan.md in /Plans with appropriate content.

**Acceptance Scenarios**:

1. **Given** a task in the /Needs_Action folder, **When** Claude processes it, **Then** a Plan.md file is created in the /Plans folder with a structured approach to completing the task
2. **Given** multiple tasks in /Needs_Action, **When** Claude processes them, **Then** each gets a corresponding Plan.md in /Plans

---

### User Story 4 - Move Completed Tasks to Done (Priority: P4)

As a technical user, I want completed items to be moved to the /Done folder so that I can track what has been processed and maintain clean organization.

**Why this priority**: This completes the workflow cycle and maintains organized task management.

**Independent Test**: Can be tested by moving a completed task from /Plans to /Done and verifying the transition occurs properly.

**Acceptance Scenarios**:

1. **Given** a completed task in the /Plans folder, **When** the completion process is triggered, **Then** the task is moved to the /Done folder
2. **Given** a task that has been marked as complete, **When** the cleanup process runs, **Then** it is moved from /Plans to /Done

---

### User Story 5 - Implement AI Behavior via Agent Skills (Priority: P5)

As a technical user, I want all AI behavior to be implemented via Claude Agent Skills rather than inline logic so that the system remains modular and extensible.

**Why this priority**: This ensures the system follows the architectural principle of using agent skills for all AI behavior, making it more maintainable and extensible.

**Independent Test**: Can be tested by verifying that AI behaviors are implemented as reusable skills rather than hardcoded logic.

**Acceptance Scenarios**:

1. **Given** a required AI behavior, **When** it needs to be executed, **Then** it is handled by a dedicated Claude Agent Skill
2. **Given** a new AI behavior requirement, **When** it is implemented, **Then** it follows the agent skill pattern rather than inline logic

---

### Edge Cases

- What happens when the watcher encounters a malformed input file?
- How does the system handle Claude failing to generate a plan for a task?
- What if the vault storage reaches capacity limits?
- How does the system handle concurrent access to the same files?
- What happens if Claude generates an unsafe or inappropriate plan?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create an Obsidian vault with Dashboard.md and Company_Handbook.md during initialization
- **FR-002**: System MUST establish the folder structure with /Needs_Action, /Plans, and /Done directories
- **FR-003**: System MUST include a working file system watcher that detects new input files
- **FR-004**: Claude MUST read files from the /Needs_Action folder and process them
- **FR-005**: Claude MUST create Plan.md files in the /Plans folder with structured approaches to completing tasks
- **FR-006**: System MUST move completed items from /Plans to /Done folder
- **FR-007**: All AI behavior MUST be implemented via Claude Agent Skills (no inline logic)
- **FR-008**: System MUST run locally without requiring cloud services
- **FR-009**: System MUST generate simple, readable Markdown outputs
- **FR-010**: System MUST implement deterministic folder transitions (inputs always go to /Needs_Action, processed items go to /Plans, completed items go to /Done)
- **FR-011**: System MUST NOT store secrets in the vault
- **FR-012**: System MUST implement safe-by-default behavior to prevent harmful actions
- **FR-013**: System MUST implement input sanitization to prevent injection attacks through input files
- **FR-014**: System MUST process each input task within 30 seconds under normal system load
- **FR-015**: System MUST implement a data retention policy that keeps completed tasks in /Done folder for 30 days before archival/purge
- **FR-016**: System MUST implement error handling with automatic retries for transient failures and clear logging for debugging

### Key Entities

- **Obsidian Vault**: The central repository containing all AI employee data, organized in Markdown files across different folders
- **File System Input Watcher**: Component that monitors for new input files in a designated directory and adds them to the /Needs_Action folder
- **Task**: A unit of work represented as a file in the vault, containing instructions or information for the AI employee to process
- **Plan**: Structured approach to completing a task, created by Claude and stored as Plan.md in the /Plans folder
- **Claude Agent Skills**: Modular components that implement specific AI behaviors without inline logic

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An Obsidian vault is successfully created with Dashboard.md, Company_Handbook.md, and the folder structure /Needs_Action, /Plans, and /Done
- **SC-002**: A working file system watcher correctly detects new input files and places them in the /Needs_Action folder
- **SC-003**: Claude successfully reads files from /Needs_Action and creates Plan.md files in /Plans with structured approaches to completing tasks
- **SC-004**: Completed items are successfully moved from /Plans to /Done folder, demonstrating the complete workflow
- **SC-005**: All AI behavior is implemented via Claude Agent Skills rather than inline logic, maintaining modularity
- **SC-006**: The system operates entirely locally without requiring cloud services
- **SC-007**: All outputs are in simple, readable Markdown format that integrates well with Obsidian
- **SC-008**: The system demonstrates safe-by-default behavior with no harmful actions taken without explicit permission
- **SC-009**: The system properly sanitizes input files to prevent injection attacks
- **SC-010**: Individual tasks are processed within 30 seconds under normal system load
- **SC-011**: The system implements a data retention policy keeping completed tasks for 30 days
- **SC-012**: The system implements error handling with automatic retries for transient failures
- **SC-013**: A clear README is provided explaining how the Bronze tier implementation works
- **SC-014**: The complete end-to-end workflow (Watcher → Vault → Claude Reasoning → Vault Output) functions as designed
