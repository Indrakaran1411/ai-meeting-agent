from fastapi import FastAPI

app = FastAPI(
    title="Meeting Intelligence Agent",
    description="Enterprise Meeting & Channel Intelligence Agent API",
    version="0.1.0",
)


@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "meeting-intelligence-agent"}
