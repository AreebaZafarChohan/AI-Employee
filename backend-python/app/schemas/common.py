from typing import Any
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class DataResponse(BaseModel):
    data: Any
    meta: dict[str, Any] | None = None
