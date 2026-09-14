"""FastAPI application for DeepVerify."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.research import router as research_router


app = FastAPI(
    title="DeepVerify API",
    description="Multimodal autonomous research and fact-checking engine.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research_router)


@app.get("/health")
async def health():
    """Health check endpoint."""

    return {
        "status": "ok",
        "service": "DeepVerify",
    }