from pathlib import Path

ROOT_PATH = Path(__file__).resolve().parent.parent.parent.parent

MCP_SERVERS = [
    {"name": "watcher-server", "type": "stdio", "path": "mcp/watcher-server/src/index.js"},
    {"name": "whatsapp-server", "type": "stdio", "path": "mcp/whatsapp-server/src/index.js"},
    {"name": "linkedin-server", "type": "stdio", "path": "mcp/linkedin-server/src/index.js"},
    {"name": "odoo-server", "type": "stdio", "path": "mcp/odoo-server/src/index.js"},
    {"name": "email-server", "type": "stdio", "path": "mcp/email-server/src/index.js"},
    {"name": "twitter-server", "type": "stdio", "path": "mcp/twitter-server/src/index.js"},
]


def get_mcp_health() -> dict:
    from datetime import datetime, timezone
    results = []
    for s in MCP_SERVERS:
        full_path = ROOT_PATH / s["path"]
        results.append({
            "name": s["name"],
            "type": s["type"],
            "status": "healthy" if full_path.is_file() else "unhealthy",
            "path": s["path"],
            "lastChecked": datetime.now(timezone.utc).isoformat(),
        })
    healthy = sum(1 for r in results if r["status"] == "healthy")
    return {
        "servers": results,
        "summary": {"total": len(results), "healthy": healthy, "unhealthy": len(results) - healthy},
    }
