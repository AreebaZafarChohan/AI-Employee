"""Standard API response wrapper matching frontend {data, meta} envelope."""

from typing import Any, Optional


def api_response(data: Any, meta: Optional[dict] = None) -> dict:
    """Wrap data in the envelope the frontend expects."""
    result = {"data": data}
    if meta is not None:
        result["meta"] = meta
    else:
        result["meta"] = {}
    return result
