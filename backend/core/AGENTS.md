# AGENTS.md — backend/core

Extends the root [AGENTS.md](../../AGENTS.md). Run all commands from `backend/core/` (imports are rooted at `app.`, `pytest.ini` sets `pythonpath = .`).

## Architecture

FastAPI app at `app/api/main.py`. Packages by responsibility:

| Package | Responsibility |
|---|---|
| `api/` | HTTP layer: routes (`main.py`), request/response schemas (`schemas.py`, `models.py`). Thin – delegates to orchestration. |
| `orchestration/` | Use-case services (`coral_service`, `analysis_service`, `comparison_service`) that coordinate the packages below. |
| `domain/` | SQLModel entities (`Survey`, `Observation`) and domain logic (e.g. observation comparison). |
| `persistence/` | DB engine (`database.py`), repositories, R2 object storage (`storage.py`). |
| `segmentation/` | Segmentation providers behind `SegmentationProvider`; selected by `provider_factory` via `SEGMENTATION_PROVIDER` (`coralscop` = remote worker, `fixture` = local `dev_fixtures/`). |
| `vision/`, `embedding/`, `cropping/` | Image processing, embeddings for colony matching, crop extraction. |
| `analysis/` | Measurement (ruler/scale detection), metrics, visualizations, HTML report. |
| `scripts/` | One-off operational scripts (may hit real DB/storage – don't run unprompted). |

Dependency direction: `api → orchestration → {domain, persistence, segmentation, vision, embedding, cropping, analysis}`.
A few existing imports go the other way (`domain`/`persistence` importing `app.api.models`); don't add new ones – put shared types in `domain/` instead.

## Patterns

- **DB sessions:** repositories open a short-lived session per operation with `with Session(get_engine()) as session:`. Don't hold sessions across calls or pass them around; don't return lazily-loaded relationships after the session closes.
- **New provider/backend:** implement the existing abstract interface (e.g. `SegmentationProvider`) and register it in the factory rather than branching on env vars in service code.
- **Config** comes from env vars (loaded via `python-dotenv`); give new variables a safe local default and document them in [backend/README.md](../README.md).

## Schema changes

1. Change the SQLModel entity in `app/domain/`.
2. Generate a migration: `alembic revision --autogenerate -m "<what changed>"`.
3. Review the generated file in `migrations/versions/` (autogenerate misses renames and some type changes).
4. Do **not** run `alembic upgrade head` unless asked – it targets the configured (possibly shared) database.

## Tests

- `test/` mirrors `app/` (e.g. `test/analysis/measurement/*_test.py`); add new tests there with the same layout.
- Tests must not require network, a real DB, R2 or a GPU. Use `dev_fixtures/` and the fixture segmentation provider for segmentation-dependent code.
