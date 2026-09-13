"""FastAPI application for DeepVerify."""

from fastapi import FastAPI

from app.api.research import router as research_router


app = FastAPI(
    title="DeepVerify API",
    description="Multimodal autonomous research and fact-checking engine.",
    version="0.1.0",
)

app.include_router(research_router)


@app.get("/health")
async def health():
    """Health check endpoint."""

    return {
        "status": "ok",
        "service": "DeepVerify",
    }