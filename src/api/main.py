from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.core.config import get_settings
from src.core.exceptions import JobNotFoundError, PlanNotFoundError, UnauthorizedError, InvalidTransitionError
from src.middleware.logging_middleware import RequestLoggingMiddleware
from src.api.routes import jobs, plans, approvals, websocket_route, health, metrics, analytics
from src.api.routes import tasks, activity_logs, system, audit_logs, vault, whatsapp, linkedin, files, sales, gmail, social, agent, events
from src.api.response import api_response

settings = get_settings()

app = FastAPI(
    title="AI Employee - API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

# Existing Gold Tier routers
app.include_router(health.router, tags=["Health"])
app.include_router(jobs.router, prefix="/api/v1", tags=["Jobs"])
app.include_router(plans.router, prefix="/api/v1", tags=["Plans"])
app.include_router(approvals.router, prefix="/api/v1", tags=["Approvals"])
app.include_router(websocket_route.router, tags=["WebSocket"])
app.include_router(metrics.router, prefix="/api/v1", tags=["Metrics"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])

# New dashboard routers
app.include_router(tasks.router, prefix="/api/v1", tags=["Tasks"])
app.include_router(activity_logs.router, prefix="/api/v1", tags=["Activity Logs"])
app.include_router(system.router, prefix="/api/v1", tags=["System"])
app.include_router(audit_logs.router, prefix="/api/v1", tags=["Audit Logs"])
app.include_router(vault.router, prefix="/api/v1", tags=["Vault"])
app.include_router(whatsapp.router, prefix="/api/v1", tags=["WhatsApp"])
app.include_router(linkedin.router, prefix="/api/v1", tags=["LinkedIn"])
app.include_router(files.router, prefix="/api/v1", tags=["Files"])
app.include_router(sales.router, prefix="/api/v1", tags=["Sales"])
app.include_router(gmail.router, prefix="/api/v1", tags=["Gmail"])
app.include_router(social.router, prefix="/api/v1", tags=["Social Media"])
app.include_router(agent.router, prefix="/api/v1", tags=["AI Agent"])
app.include_router(events.router, prefix="/api/v1", tags=["Watcher Events"])


@app.on_event("startup")
async def on_startup():
    from src.models.sqlite_db import create_tables
    from src.core.watcher_event_dispatcher import setup_event_handlers
    create_tables()
    await setup_event_handlers()


@app.get("/")
async def root():
    return api_response({
        "name": "AI Employee API",
        "version": "2.0.0",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "api": "/api/v1",
            "tasks": "/api/v1/tasks",
            "activity_logs": "/api/v1/activity-logs",
            "system": "/api/v1/system/state",
            "vault": "/api/v1/vault/counts",
            "sales": "/api/v1/sales/leads",
            "gmail": "/api/v1/gmail/inbox",
            "whatsapp": "/api/v1/whatsapp/messages",
            "linkedin": "/api/v1/linkedin/posts",
            "social": "/api/v1/social/generate",
        },
    })


@app.exception_handler(JobNotFoundError)
async def job_not_found_handler(request: Request, exc: JobNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(PlanNotFoundError)
async def plan_not_found_handler(request: Request, exc: PlanNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(UnauthorizedError)
async def unauthorized_handler(request: Request, exc: UnauthorizedError):
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(InvalidTransitionError)
async def invalid_transition_handler(request: Request, exc: InvalidTransitionError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})
