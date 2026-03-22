from fastapi import APIRouter, HTTPException
from backend.api.response import api_response
import os
from pathlib import Path

router = APIRouter(prefix="/system", tags=["System"])

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return api_response({
        "status": "healthy",
        "backend": "online",
        "version": "1.0.0"
    })

@router.get("/mcp-health")
async def mcp_health_check():
    """MCP server health check"""
    # Check if MCP servers are configured
    mcp_configured = os.environ.get("MCP_CONFIG_PATH") is not None
    
    return api_response({
        "status": "healthy" if mcp_configured else "degraded",
        "mcp_servers": "configured" if mcp_configured else "not_configured",
        "message": "MCP integration ready" if mcp_configured else "MCP not configured"
    })

@router.get("/status")
async def system_status():
    """Overall system status"""
    vault_path = Path("./AI-Employee-Vault")
    
    return api_response({
        "status": "online",
        "vault_exists": vault_path.exists(),
        "vault_path": str(vault_path.absolute()),
        "components": {
            "backend": "running",
            "frontend": "connected",
            "vault": "accessible" if vault_path.exists() else "not_found"
        }
    })
