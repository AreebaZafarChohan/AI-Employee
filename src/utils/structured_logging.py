import json
import logging
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": getattr(record, "service", "api"),
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        for key in ("job_id", "stage_id", "user_id", "correlation_id", "duration_ms", "event"):
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = val
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def setup_logging(level: str = "INFO", json_output: bool = False) -> logging.Logger:
    logger = logging.getLogger("gold_tier")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    handler = logging.StreamHandler(sys.stdout)
    if json_output:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    if not logger.handlers:
        logger.addHandler(handler)
    return logger


logger = setup_logging()
