# Data Model: Personal AI Employee – Bronze Tier (Foundation)

## Entities

### 1. Obsidian Vault
- **Description**: The central repository containing all AI employee data, organized in Markdown files across different folders
- **Attributes**: 
  - path: String (local file system path to the vault)
  - folders: Array<String> (list of folder names: Needs_Action, Plans, Done)
  - metadata: Object (vault configuration and settings)
- **Relationships**: Contains multiple Task entities

### 2. File System Input Watcher
- **Description**: Component that monitors for new input files in a designated directory and adds them to the /Needs_Action folder
- **Attributes**:
  - watch_path: String (directory path to monitor)
  - recursive: Boolean (whether to monitor subdirectories)
  - file_patterns: Array<String> (patterns of files to watch for)
  - active: Boolean (whether the watcher is currently running)
- **Relationships**: Creates new Task entities when input files are detected

### 3. Task
- **Description**: A unit of work represented as a file in the vault, containing instructions or information for the AI employee to process
- **Attributes**:
  - id: String (unique identifier for the task)
  - title: String (human-readable title)
  - content: String (the actual task content in Markdown format)
  - status: Enum (needs_action, in_planning, completed)
  - created_at: DateTime (timestamp when task was created)
  - updated_at: DateTime (timestamp when task was last updated)
  - source_path: String (original file path if imported from file system)
  - metadata: Object (additional properties like priority, tags, etc.)
- **Relationships**: Transitions to Plan entity when processed

### 4. Plan
- **Description**: Structured approach to completing a task, created by Claude and stored as Plan.md in the /Plans folder
- **Attributes**:
  - id: String (unique identifier for the plan)
  - task_id: String (reference to the associated Task)
  - title: String (human-readable title)
  - content: String (the plan content in Markdown format)
  - status: Enum (draft, approved, in_progress, completed)
  - created_at: DateTime (timestamp when plan was created)
  - updated_at: DateTime (timestamp when plan was last updated)
  - metadata: Object (additional properties like estimated time, resources needed, etc.)
- **Relationships**: Associated with one Task entity, may lead to completed Task

### 5. Claude Agent Skills
- **Description**: Modular components that implement specific AI behaviors without inline logic
- **Attributes**:
  - name: String (unique identifier for the skill)
  - description: String (what the skill does)
  - parameters: Object (input parameters the skill accepts)
  - version: String (skill version)
  - active: Boolean (whether the skill is enabled)
- **Relationships**: Used by the Claude client to process Tasks and generate Plans

## State Transitions

### Task State Transitions
1. **needs_action** → **in_planning**: When Claude begins processing the task
2. **in_planning** → **needs_action**: If Claude fails to generate a plan
3. **in_planning** → **completed**: When Claude successfully creates a plan

### Plan State Transitions
1. **draft** → **approved**: When user approves the plan
2. **approved** → **in_progress**: When execution begins
3. **in_progress** → **completed**: When execution finishes successfully
4. **in_progress** → **draft**: If execution fails

## Validation Rules

### Task Validation
- Content must be in Markdown format
- Title must not be empty
- Content must not exceed vault storage limits
- Must pass input sanitization checks (FR-013)

### Plan Validation
- Must reference a valid Task
- Content must be in Markdown format
- Must follow structured approach requirements

### Vault Structure Validation
- Must contain /Needs_Action, /Plans, and /Done directories (FR-002)
- Files must be in Markdown format
- No secrets stored in vault (FR-011)

## Relationships

- **Vault** 1 → * **Task**: One vault contains many tasks
- **Task** 1 → 1 **Plan**: One task corresponds to one plan
- **File System Input Watcher** 1 → * **Task**: One watcher can create many tasks
- **Claude Agent Skills** * → * **Task/Plan**: Many skills can process many tasks and plans