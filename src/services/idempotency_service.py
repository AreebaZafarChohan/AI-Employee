import hashlib
from src.events.event_bus import get_redis

IDEMPOTENCY_TTL = 86400  # 24 hours


class IdempotencyService:
    def __init__(self):
        self.redis = get_redis()

    def _make_key(self, user_id: str, task_description: str) -> str:
        content = f"{user_id}:{task_description}"
        return f"idempotency:{hashlib.sha256(content.encode()).hexdigest()}"

    def check_and_set(self, user_id: str, task_description: str) -> str | None:
        key = self._make_key(user_id, task_description)
        existing = self.redis.get(key)
        if existing:
            return existing  # Return existing job_id
        return None

    def set(self, user_id: str, task_description: str, job_id: str):
        key = self._make_key(user_id, task_description)
        self.redis.setex(key, IDEMPOTENCY_TTL, job_id)
