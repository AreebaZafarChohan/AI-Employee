from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from backend.config import get_settings
from backend.api import tasks, vault, agent, events, social, system, audit

settings = get_settings()

app = FastAPI(
    title="AI Employee Backend",
    version="1.0.0",
)

# 3. Configure CORS so Next.js can call FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(vault.router, prefix="/api/v1")
app.include_router(agent.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")
app.include_router(social.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"status": "online", "message": "AI Employee Backend is running"}

@app.on_event("startup")
async def on_startup():
    print(f"Starting AI Employee Backend on http://localhost:{settings.PORT}")
    # Initialize background loops or watchers here if needed

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
