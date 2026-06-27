from fastapi import FastAPI
from app.api import api_v1_router

app = FastAPI(
    title="Meeting Intelligence Agent",
    description="Enterprise Meeting & Channel Intelligence Agent API",
    version="0.1.0",
)

app.include_router(api_v1_router)


@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "meeting-intelligence-agent"}

