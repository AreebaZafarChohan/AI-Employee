import json
import logging
import redis
from src.core.config import get_settings

logger = logging.getLogger("gold_tier")

_redis_client = None


def get_redis():
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


def publish_event(event_type: str, data: dict):
    r = get_redis()
    payload = json.dumps({"type": event_type, "data": data})
    r.publish("gold_tier_events", payload)
    logger.info(f"Published event: {event_type}", extra={"event": event_type})


def subscribe_events():
    r = get_redis()
    pubsub = r.pubsub()
    pubsub.subscribe("gold_tier_events")
    return pubsub
