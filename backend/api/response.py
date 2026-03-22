from typing import Any
from fastapi.responses import JSONResponse

def api_response(data: Any = None, status: str = "success", message: str = None, code: int = 200):
    return JSONResponse(
        status_code=code,
        content={
            "status": status,
            "data": data,
            "message": message
        }
    )
