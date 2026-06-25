from __future__ import annotations

from app.models import Video, VideoIn, Visibility, new_video_id, now, thumbnail_url, watch_url
from app.store import store

# Demo content so GET /videos returns something on a fresh database.
SEED_VIDEOS = [
    ("Building Agents with LangGraph", "Daya Medika Tech", "Tutorials",
     ["langgraph", "agents", "python"], 842, ["ai"]),
    ("FastAPI in 10 Minutes", "Code Indonesia", "Education",
     ["fastapi", "python", "api"], 615, []),
    ("Jakarta Street Food Tour", "Kuliner Nusantara", "Travel & Events",
     ["food", "jakarta", "travel"], 1320, []),
    ("Kubernetes for Beginners", "Cloud Native ID", "Education",
     ["kubernetes", "devops", "cloud"], 2010, []),
]


class VideoError(Exception):
    def __init__(self, status: int, message: str) -> None:
        self.status = status
        self.message = message
        super().__init__(message)


def _build(data: VideoIn) -> Video:
    vid = new_video_id()
    return Video(
        video_id=vid,
        title=data.title,
        channel=data.channel,
        description=data.description,
        tags=data.tags,
        category=data.category,
        duration_seconds=data.duration_seconds,
        visibility=data.visibility,
        views=0,
        likes=0,
        published_at=now(),
        url=watch_url(vid),
        thumbnail_url=thumbnail_url(vid),
    )


def create_video(data: VideoIn) -> Video:
    with store.lock:
        # new_video_id() collisions are astronomically unlikely; guard anyway.
        video = _build(data)
        while store.has_video(video.video_id):
            video = _build(data)
        store.add_video(video)
        return video


def get_video(video_id: str) -> Video:
    video = store.get_video(video_id)
    if video is None:
        raise VideoError(404, f"video {video_id} not found")
    return video


def list_videos(
    channel: str | None = None,
    q: str | None = None,
    visibility: str | None = None,
) -> list[Video]:
    if visibility is not None and visibility not in {v.value for v in Visibility}:
        raise VideoError(422, f"invalid visibility '{visibility}'")
    return store.list_videos(channel=channel, q=q, visibility=visibility)


def add_view(video_id: str) -> Video:
    video = store.bump(video_id, "views")
    if video is None:
        raise VideoError(404, f"video {video_id} not found")
    return video


def like(video_id: str) -> Video:
    video = store.bump(video_id, "likes")
    if video is None:
        raise VideoError(404, f"video {video_id} not found")
    return video


def seed() -> list[Video]:
    with store.lock:
        for title, channel, category, tags, duration, extra in SEED_VIDEOS:
            create_video(
                VideoIn(
                    title=title,
                    channel=channel,
                    description=f"{title} — uploaded by {channel}.",
                    tags=tags + extra,
                    category=category,
                    duration_seconds=duration,
                )
            )
    return store.list_videos()
