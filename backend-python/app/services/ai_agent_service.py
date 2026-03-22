import httpx
from app.config import settings


async def generate_content(prompt: str, provider: str = "gemini") -> dict:
    if provider == "gemini" and settings.GEMINI_API_KEY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={settings.GEMINI_API_KEY}"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
            resp.raise_for_status()
            data = resp.json()
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return {"text": text, "provider": "gemini"}
    return {"text": "", "provider": provider, "error": "No API key configured"}
