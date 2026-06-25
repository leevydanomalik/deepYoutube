from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from app import video
from app.models import VideoIn
from app.store import store
from app.video import VideoError


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Seed demo videos on a fresh database so GET /videos returns data.
    if store.count() == 0:
        video.seed()
    yield


app = FastAPI(
    title="YouTube",
    version="0.1.0",
    description="Simple SQLite-backed video catalog microservice (upload + browse)",
    lifespan=lifespan,
)


@app.exception_handler(VideoError)
async def _video_error(_request, exc: VideoError):
    return JSONResponse(status_code=exc.status, content={"detail": exc.message})


@app.get("/")
def info():
    return {
        "service": "YouTube",
        "version": "0.1.0",
        "docs": "/docs",
        "model": "video catalog",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


# --- Videos ---
@app.post("/videos", status_code=201)
def upload_video(data: VideoIn):
    """Publish (upload) a video."""
    return video.create_video(data)


@app.get("/videos")
def list_videos(
    channel: str | None = Query(None),
    q: str | None = Query(None, description="search title/description/tags"),
    visibility: str | None = Query(None),
):
    return video.list_videos(channel=channel, q=q, visibility=visibility)


@app.get("/videos/{video_id}")
def get_video(video_id: str):
    return video.get_video(video_id)


@app.post("/videos/{video_id}/view")
def add_view(video_id: str):
    """Register a view (increments the view counter)."""
    return video.add_view(video_id)


@app.post("/videos/{video_id}/like")
def like_video(video_id: str):
    return video.like(video_id)


@app.post("/videos/seed")
def seed_videos():
    return video.seed()
