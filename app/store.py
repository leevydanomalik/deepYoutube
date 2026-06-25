from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime

from app.models import Video, Visibility, thumbnail_url, watch_url

DB_PATH = os.environ.get("YOUTUBE_DB", "youtube.db")


class Database:
    """SQLite-backed video store.

    One ``videos`` table; tags are kept as a JSON-encoded TEXT column (a video's
    tag list is always read/written as a whole, so a child table buys nothing).
    ``url``/``thumbnail_url`` are derived from the id at read time, not stored.
    A reentrant lock serializes access to the single shared connection so
    callers can wrap check-then-write sequences atomically.
    """

    def __init__(self, path: str = DB_PATH) -> None:
        self.lock = threading.RLock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self.lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS videos (
                    video_id         TEXT PRIMARY KEY,
                    title            TEXT NOT NULL,
                    channel          TEXT NOT NULL,
                    description      TEXT NOT NULL DEFAULT '',
                    tags             TEXT NOT NULL DEFAULT '[]',
                    category         TEXT NOT NULL,
                    duration_seconds INTEGER NOT NULL,
                    visibility       TEXT NOT NULL,
                    views            INTEGER NOT NULL DEFAULT 0,
                    likes            INTEGER NOT NULL DEFAULT 0,
                    published_at     TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_videos_channel ON videos (channel);
                """
            )
            self._conn.commit()

    def _row_to_video(self, row: sqlite3.Row) -> Video:
        return Video(
            video_id=row["video_id"],
            title=row["title"],
            channel=row["channel"],
            description=row["description"],
            tags=json.loads(row["tags"]),
            category=row["category"],
            duration_seconds=row["duration_seconds"],
            visibility=Visibility(row["visibility"]),
            views=row["views"],
            likes=row["likes"],
            published_at=datetime.fromisoformat(row["published_at"]),
            url=watch_url(row["video_id"]),
            thumbnail_url=thumbnail_url(row["video_id"]),
        )

    def has_video(self, video_id: str) -> bool:
        with self.lock:
            cur = self._conn.execute("SELECT 1 FROM videos WHERE video_id = ?", (video_id,))
            return cur.fetchone() is not None

    def add_video(self, video: Video) -> None:
        with self.lock:
            self._conn.execute(
                "INSERT INTO videos (video_id, title, channel, description, tags, "
                "category, duration_seconds, visibility, views, likes, published_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    video.video_id,
                    video.title,
                    video.channel,
                    video.description,
                    json.dumps(video.tags),
                    video.category,
                    video.duration_seconds,
                    video.visibility.value,
                    video.views,
                    video.likes,
                    video.published_at.isoformat(),
                ),
            )
            self._conn.commit()

    def get_video(self, video_id: str) -> Video | None:
        with self.lock:
            row = self._conn.execute(
                "SELECT * FROM videos WHERE video_id = ?", (video_id,)
            ).fetchone()
            return self._row_to_video(row) if row else None

    def list_videos(
        self,
        channel: str | None = None,
        q: str | None = None,
        visibility: str | None = None,
    ) -> list[Video]:
        sql = "SELECT * FROM videos"
        clauses: list[str] = []
        params: list[object] = []
        if channel:
            clauses.append("channel = ?")
            params.append(channel)
        if visibility:
            clauses.append("visibility = ?")
            params.append(visibility)
        if q:
            clauses.append("(title LIKE ? OR description LIKE ? OR tags LIKE ?)")
            like = f"%{q}%"
            params.extend([like, like, like])
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY published_at DESC"
        with self.lock:
            rows = self._conn.execute(sql, params).fetchall()
            return [self._row_to_video(r) for r in rows]

    def bump(self, video_id: str, column: str) -> Video | None:
        """Increment a counter column (``views``/``likes``) by one."""
        assert column in {"views", "likes"}  # column is an internal constant
        with self.lock:
            cur = self._conn.execute(
                f"UPDATE videos SET {column} = {column} + 1 WHERE video_id = ?",
                (video_id,),
            )
            self._conn.commit()
            if cur.rowcount == 0:
                return None
            return self.get_video(video_id)

    def count(self) -> int:
        with self.lock:
            return self._conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]

    def reset(self) -> None:
        with self.lock:
            self._conn.execute("DELETE FROM videos")
            self._conn.commit()


store = Database()
