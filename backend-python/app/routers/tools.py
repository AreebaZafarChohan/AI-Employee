from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.tool_invocation import ToolInvocation

router = APIRouter(prefix="/tools", tags=["tools"])


def _s(t):
    return {"id": t.id, "agentExecutionId": t.agentExecutionId, "toolName": t.toolName,
            "arguments": t.arguments, "result": t.result, "riskScore": t.riskScore,
            "status": t.status, "createdAt": t.createdAt.isoformat()}


@router.get("")
async def list_tools(status: str | None = None, page: int = Query(1, ge=1), pageSize: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    q = select(ToolInvocation)
    if status:
        q = q.where(ToolInvocation.status == status)
    q = q.order_by(ToolInvocation.createdAt.desc()).offset((page - 1) * pageSize).limit(pageSize)
    tools = list((await db.execute(q)).scalars().all())
    total = (await db.execute(select(func.count(ToolInvocation.id)))).scalar_one()
    return {"data": [_s(t) for t in tools], "meta": {"total": total, "page": page, "pageSize": pageSize}}
