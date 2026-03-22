from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.cost_log import CostLog

router = APIRouter(prefix="/cost", tags=["costs"])


def _s(c):
    return {"id": c.id, "agentExecutionId": c.agentExecutionId, "modelName": c.modelName,
            "tokensIn": c.tokensIn, "tokensOut": c.tokensOut,
            "estimatedCostUsd": str(c.estimatedCostUsd), "createdAt": c.createdAt.isoformat()}


@router.get("")
async def list_costs(page: int = Query(1, ge=1), pageSize: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    q = select(CostLog).order_by(CostLog.createdAt.desc()).offset((page - 1) * pageSize).limit(pageSize)
    costs = list((await db.execute(q)).scalars().all())
    total = (await db.execute(select(func.count(CostLog.id)))).scalar_one()
    return {"data": [_s(c) for c in costs], "meta": {"total": total, "page": page, "pageSize": pageSize}}


@router.get("/summary")
async def cost_summary(db: AsyncSession = Depends(get_db)):
    total_cost = (await db.execute(select(func.sum(CostLog.estimatedCostUsd)))).scalar_one_or_none() or 0
    total_tokens_in = (await db.execute(select(func.sum(CostLog.tokensIn)))).scalar_one_or_none() or 0
    total_tokens_out = (await db.execute(select(func.sum(CostLog.tokensOut)))).scalar_one_or_none() or 0
    count = (await db.execute(select(func.count(CostLog.id)))).scalar_one()
    return {"data": {"totalCostUsd": str(total_cost), "totalTokensIn": total_tokens_in, "totalTokensOut": total_tokens_out, "totalRequests": count}}
