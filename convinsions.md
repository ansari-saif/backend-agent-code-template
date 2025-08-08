Project conventions

- API routers
  - Import DB tables only from `app.models/*` for persistence and queries.
  - Import request/response payload types only from `app.schemas/*`.
  - All FastAPI `response_model` annotations must point to schema types (never model classes).
  - Keep request bodies as schema types as well.

- Models (`app/models`)
  - Use `sqlmodel.SQLModel` classes that map to database tables.
  - May import enums/constants from `app.schemas/*` when they are the single source of truth for value sets.
  - Do not include API-only validation here.

- Schemas (`app/schemas`)
  - Use `pydantic.BaseModel` for request/response validation and serialization.
  - Include `class Config: from_attributes = True` (or `model_config`) where needed for ORM serialization.
  - Do not run database queries or include persistence logic.

- Services (`app/services`)
  - Pure business logic and integrations (e.g., AI providers).
  - Accept/return plain data (schemas or primitives). Do not depend on FastAPI router objects.

- Imports in routers
  - OK: `from app.models.task import Task`
  - OK: `from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse`
  - Avoid: `response_model=Task` (model) — must be `TaskResponse` (schema)

- Main app (`app/main.py`)
  - Routers are mounted under clear prefixes; they must follow the separation rules above.

This separation keeps DB schema, API contracts, and business logic independent and testable.

How to create a new API

1) Define schemas (`app/schemas/<resource>.py`)
   - Create Pydantic models: `<Resource>Create`, `<Resource>Response`, `<Resource>Update`.
   - Put shared fields in `<Resource>Base`.
   - Ensure responses include identifiers (e.g., `id`/`*_id`) and set `class Config: from_attributes = True`.
   - Keep request-only fields optional in `Update`; defaults live in the DB/model.

2) Define model (`app/models/<resource>.py`)
   - Create a `sqlmodel.SQLModel` table class with `__tablename__` and primary key.
   - Reference enums from schemas when they are the source of truth.
   - Add relationships (via `Relationship`) only if needed.

3) Create service (`app/services/<resource>_service.py`)
   - Implement pure functions that accept a `Session` and schema inputs, and return models or primitives.
   - Typical functions: `create_*`, `list_*`, `get_*`, `update_*`, `delete_*`.
   - Raise `ValueError` for bad requests (duplicates, invalid state), `LookupError` for not found.

4) Add router (`app/api/v1/routes/<resource>.py`)
   - Import DB tables from `app.models.<resource>` and payload types from `app.schemas.<resource>`.
   - Import business logic from `app.services.<resource>_service`.
   - Use `Depends(get_session)`; map `ValueError` → 400, `LookupError` → 404.
   - All `response_model` annotations must be schema types (e.g., `<Resource>Response`).

5) Wire the router (`app/main.py`)
   - `from app.api.v1.routes import <resource>` then:
     `app.include_router(<resource>.router, prefix="/<resource-plural>", tags=["<resource-plural>"])`.

6) Database migration (if model changed)
   - Create migration: `alembic revision --autogenerate -m "add <resource>"`.
   - Review the migration, then `alembic upgrade head`.

7) Tests
   - Add schema unit tests to `tests/test_schemas.py`.
   - Add integration tests under `tests/` using `TestClient` (see existing tests for patterns).
   - Reuse fixtures in `tests/conftest.py` or add new sample data factories.

Naming and imports
   - Services: `<resource>_service.py` with verbs for functions.
   - Schemas: `Create/Response/Update` suffixes; enums in schemas if shared.
   - Routes: perform request validation + error mapping; delegate business logic to services; perform DB existence checks (e.g., verify `user_id`) before service calls when appropriate.
