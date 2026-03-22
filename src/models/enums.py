import enum


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class UserRole(str, enum.Enum):
    SUBMITTER = "submitter"
    APPROVER = "approver"


class PipelineStageType(str, enum.Enum):
    TASK_ANALYSIS = "task_analysis"
    PLAN_CREATION = "plan_creation"
    RISK_ASSESSMENT = "risk_assessment"
    FINAL_OUTPUT = "final_output"


class PipelineStageStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class ApprovalStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


class ApprovalDecision(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


class AgentType(str, enum.Enum):
    TASK_ANALYZER = "task_analyzer"
    PLANNER = "planner"
    RISK_ASSESSOR = "risk_assessor"
    OUTPUT_ASSEMBLER = "output_assembler"


class AgentExecutionStatus(str, enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
