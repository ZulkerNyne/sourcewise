# Sourcewise

Source-grounded Islamic education platform, currently **Phase 0 foundations only**.
There is no tutor, retrieval engine, database, API, or website yet.

## Develop

Use Python 3.12+ and uv (CI uses uv 0.12.23). From this checkout:

```bash
uv sync --frozen
uv run --frozen pytest
uv run --frozen ruff check .
uv run --frozen ruff format --check .
```

uv creates `.venv` and installs the package in editable mode. `uv.lock` fixes the
resolved dependencies. No credentials, environment variables, or running services
are required. Do not commit `.env` or source documents without approved rights.

## Files and concepts

- `PROJECT_PLAN.md`: complete supplied specification.
- `AGENTS.md`: persistent engineering and mentorship instructions.
- `backend/app/sources/models.py`: validated source identity and citation contracts.
- `tests/unit/`: synthetic schema tests; no religious accuracy claims.
- `docs/`: architecture, roadmap, source policy, evaluation, and decisions.
- `evaluations/datasets/case.schema.json`: initial reviewed benchmark contract.
- `.github/workflows/ci.yml`: repeatable lint, formatting, and tests.

Start with [the architecture](docs/architecture.md) and [roadmap](docs/roadmap.md).
