from __future__ import annotations

import secrets
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

# YouTube public video ids are 11 chars from this URL-safe alphabet.
_ID_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"


def new_video_id() -> str:
    return "".join(secrets.choice(_ID_ALPHABET) for _ in range(11))


def now() -> datetime:
    return datetime.now(timezone.utc)


def watch_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def thumbnail_url(video_id: str) -> str:
    return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"


class Visibility(str, Enum):
    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"


class VideoIn(BaseModel):
    """Payload for POST /videos (publishing/uploading a video)."""

    title: str = Field(min_length=1, max_length=200)
    channel: str = Field(min_length=1, max_length=120)
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    category: str = "People & Blogs"
    duration_seconds: int = Field(gt=0, le=86_400)  # 1s .. 24h
    visibility: Visibility = Visibility.PUBLIC


class Video(BaseModel):
    """A stored video record (returned by GET /videos and POST /videos)."""

    video_id: str
    title: str
    channel: str
    description: str
    tags: list[str]
    category: str
    duration_seconds: int
    visibility: Visibility
    views: int
    likes: int
    published_at: datetime
    url: str
    thumbnail_url: str
