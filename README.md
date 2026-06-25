# YouTube (simulated service)

A small FastAPI microservice simulating a YouTube-style video catalog, built to
the same template as the other `~/DOCKER/` sims (`orafin`, `sap`): SQLite-backed
store, Pydantic models, pytest, its own `Dockerfile` + `docker-compose.yml`,
published on a host port.

- Port: **8005** (Oracle 8001, SAP 8002, zksim 8003, reranker 8004).
- Interactive docs: <http://localhost:8005/docs>

## Run

```bash
cd ~/DOCKER/youtube
docker compose up -d --build      # http://localhost:8005
```

Local (without Docker):

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8005
pytest -q                         # run the test suite
```

On first start with an empty database the service **auto-seeds** a handful of
demo videos so `GET /videos` returns data immediately.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET`  | `/health` | liveness → `{"status":"ok"}` |
| `GET`  | `/` | service info |
| `POST` | `/videos` | **publish/upload a video** → `201` + the stored video |
| `GET`  | `/videos` | list videos; filters: `channel`, `q` (title/description/tags), `visibility` |
| `GET`  | `/videos/{video_id}` | **fetch one video** (`404` if missing) |
| `POST` | `/videos/{video_id}/view` | register a view (increments `views`) |
| `POST` | `/videos/{video_id}/like` | increment `likes` |
| `POST` | `/videos/seed` | (re)insert the demo videos |

### POST /videos — body

```json
{
  "title": "Building Agents with LangGraph",
  "channel": "Daya Medika Tech",
  "description": "A walkthrough.",
  "tags": ["langgraph", "agents"],
  "category": "Education",
  "duration_seconds": 842,
  "visibility": "public"
}
```

`title` (1–200 chars), `channel` (1–120 chars) and `duration_seconds`
(`1 .. 86400`) are required; `visibility` ∈ `public, unlisted, private`.

### Stored video shape

```json
{
  "video_id": "dQw4w9WgXcQ",
  "title": "...", "channel": "...", "description": "...",
  "tags": ["..."], "category": "...", "duration_seconds": 842,
  "visibility": "public", "views": 0, "likes": 0,
  "published_at": "2026-06-24T...Z",
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"
}
```

`video_id` is an 11-character YouTube-style id; `url`/`thumbnail_url` are derived
from it. IDs are generated per upload (not deterministic).

## Examples

```bash
# upload
curl -s localhost:8005/videos -H 'content-type: application/json' -d '{
  "title":"FastAPI in 10 Minutes","channel":"Code Indonesia",
  "duration_seconds":615,"tags":["fastapi"],"category":"Education"}'

# browse
curl -s localhost:8005/videos
curl -s "localhost:8005/videos?q=fastapi"
curl -s localhost:8005/videos/<video_id>
```
