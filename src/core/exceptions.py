class JobNotFoundError(Exception):
    def __init__(self, job_id: str):
        self.job_id = job_id
        super().__init__(f"Job {job_id} not found")


class InvalidTransitionError(Exception):
    def __init__(self, current_status: str, target_status: str):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(f"Invalid transition from {current_status} to {target_status}")


class UnauthorizedError(Exception):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message)


class PlanNotFoundError(Exception):
    def __init__(self, plan_id: str):
        self.plan_id = plan_id
        super().__init__(f"Plan {plan_id} not found")


class DuplicateJobError(Exception):
    def __init__(self, idempotency_key: str):
        self.idempotency_key = idempotency_key
        super().__init__(f"Duplicate job submission: {idempotency_key}")


class AIError(Exception):
    """Base exception for all AI-related errors."""
    pass


class AIServiceError(AIError):
    """Exception raised when an AI service returns an error (e.g., 500)."""
    pass


class AIQuotaError(AIError):
    """Exception raised when an AI service quota is exceeded (429)."""
    pass


class AITimeoutError(AIError):
    """Exception raised when an AI service call times out."""
    pass


class AIConfigError(AIError):
    """Exception raised when AI service configuration is missing or invalid."""
    pass
