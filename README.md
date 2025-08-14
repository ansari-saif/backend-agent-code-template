## AI‑Powered Productivity System (FastAPI)

A FastAPI application for goal tracking, task management, progress logging, and AI‑assisted insights (Gemini). The app uses SQLModel for persistence, clean separation between models/schemas/services/routers, and includes a WebSocket endpoint and MCP integration.

### Overview

- **Tech**: FastAPI, SQLModel, Alembic, Uvicorn, Pydantic v2, websockets
- **AI**: Google Gemini via `google-generativeai` (requires `GEMINI_API_KEY`)
- **MCP**: `fastapi-mcp` mounted for tool discovery on top of HTTP API
- **DB**: SQLite by default (env‑configurable), production‑ready with PostgreSQL

### Project structure

- `app/main.py`: Application entry; mounts routers, CORS, health/root, FastAPI MCP
- `app/core/`
  - `config.py`: Loads env; `DATABASE_URL` with SQLite fallback
  - `database.py`: SQLModel engine/session; `create_db_and_tables()` on startup
- `app/models/`: SQLModel ORM tables (e.g., `user`, `goal`, `task`, `progress_log`, `ai_context`, `job_metrics`, `day_log`, `log`). Models include identifiers and timestamp fields
- `app/schemas/`: Pydantic models for request/response (strict API contracts)
- `app/services/`: Business logic (e.g., `ai_service.py`, `task_service.py`, …)
- `app/api/v1/routes/`: FastAPI routers per resource
- `migrations/`: Alembic env and versions for schema migration

### API surface

- Root
  - `GET /`: Welcome payload + feature list
  - `GET /health`: Health check
- Users (`/users`)
  - CRUD, plus `GET /users/{telegram_id}/profile`
- Goals (`/goals`)
- Tasks (`/tasks`)
  - CRUD; filtering; `PATCH /tasks/{id}/complete`
  - Discard/restore: `/tasks/{id}/discard`, `/tasks/{id}/restore`
  - Bulk create: `POST /tasks/bulk`
  - User‑scoped listings: `/tasks/user/{user_id}`, `/tasks/user/{user_id}/pending`, `/tasks/user/{user_id}/today`
- Progress Logs (`/progress-logs`)
- AI Context (`/ai-context`)
- Job Metrics (`/job-metrics`)
- Day Logs (`/day-logs`)
- Logs (`/log`)
- Prompts (`/prompts`)
- AI Service (`/ai`)
  - `POST /ai/daily-tasks` (energy‑aware suggestions)
  - `POST /ai/motivation`
  - `POST /ai/weekly-analysis`
  - `POST /ai/phase-transition`
  - `POST /ai/analyze-goals`
  - `POST /ai/career-transition`
  - `POST /ai/user/{user_id}/complete-analysis`
- WebSocket (`/api/v1/ws`)
  - `WS /api/v1/ws/{user_id}`: Receives JSON messages; supports chat broadcast and prompt processing
  - `GET /api/v1/ws/status`: Connection stats
  - `POST /api/v1/ws/notification`: Broadcast a notification to all connected clients

### Environment configuration

Create a `.env` file in project root:

```env
DATABASE_URL=sqlite:///./diary.db
GEMINI_API_KEY=your-gemini-api-key
```

Notes:
- AI endpoints require `GEMINI_API_KEY`. Without it, the app returns sensible fallbacks in some paths; direct AI calls will otherwise fail with 500.
- `DATABASE_URL` can point to PostgreSQL, e.g. `postgresql+psycopg2://user:pass@host:5432/dbname`.

### Install & run

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Docs live at `/docs` (Swagger) and `/redoc`.

### Database & migrations

- Dev: Tables auto‑created on startup via `create_db_and_tables()`
- Migrations (recommended for production):
  ```bash
  alembic revision --autogenerate -m "message"
  alembic upgrade head
  ```

### Testing

```bash
python -m pytest
python -m pytest -v --tb=short
python run_tests.py --coverage
```

### Design conventions

- **Routers** import DB tables from `app.models.*` and schemas from `app.schemas.*`; `response_model` always uses schema types
- **Models**: SQLModel tables with identifiers and timestamps; no API validation
- **Schemas**: Pydantic models (v2) for validation/serialization; include `Config.from_attributes = True` in responses
- **Services**: Pure business logic; accept `Session` + schemas/values, raise `ValueError` (400) and `LookupError` (404) as appropriate
- **Main app**: Registers routers with clear prefixes and CORS; mounts MCP via `FastApiMCP`

### WebSocket quickstart

Connect (example using `wscat`):

```bash
wscat -c ws://localhost:8000/api/v1/ws/<user_id>
```

Send a prompt message:

```json
{"message": "Summarize my progress today"}
```

### AI service overview

- Daily task generation based on energy, goals, and recent progress
- Contextual motivation messages
- Weekly insights and goal analysis
- Phase transition and career transition readiness
- Day log/progress log content helpers

All AI helpers live in `app/services/ai_service.py` and are invoked from `/ai/*` endpoints.

### Run with Docker (optional)

```bash
docker compose up --build
```

### Health checklist

- `/health` returns `{"status": "healthy"}` when the API is up
- `/docs` is reachable
- If AI endpoints return 500, verify `GEMINI_API_KEY`

---

For local dev, SQLite is fine. For staging/production, use PostgreSQL with Alembic migrations and configure `DATABASE_URL` accordingly.


