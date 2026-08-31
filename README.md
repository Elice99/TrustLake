# TrustLake

Check it. Clean it. Understand it. Model it. Predict with it.

A data professional's workspace — from raw data to trusted analysis and machine-learning predictions, in one place.

## Governing principle

If a decision doesn't make the data more trustworthy, understandable, or usable, it waits.
See [`docs/PRD.md`](docs/PRD.md) §3 for the full rule.

## Status

**Pre-MVP. Stage 0 (Environment & Project Foundations) in progress.**
No application code exists yet — this repo currently contains project structure and documentation only.

Build sequence and current stage are tracked in the project's build roadmap (not yet added to this repo — currently held outside version control; ask before assuming it should be added here).

## Documentation

- [`docs/PRD.md`](docs/PRD.md) — product requirements (what and why)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system architecture (how)

## Repository structure

```
trustlake/
  apps/
    web/              # Next.js frontend (not yet built)
    api/               # FastAPI backend (not yet built)
  packages/
    shared-types/      # Shared TypeScript/Pydantic contract definitions (not yet built)
  infra/
    docker/             # Docker Compose service configs (not yet built)
    migrations/         # Alembic migrations (not yet built)
  docs/
    PRD.md
    ARCHITECTURE.md
```

## Local development

Not yet available — Docker Compose setup lands later in Stage 0. This section will be filled in with real, tested commands once `docker compose up` actually works from a clean clone, not before.

## Tech stack

- **Frontend:** React, Next.js, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, Recharts
- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy, PostgreSQL
- **Data & ML:** pandas, NumPy, scikit-learn, DuckDB (optional)
- **AI layer:** provider-agnostic interface — Gemini, Groq, and a required `NoAIProvider`
- **Package manager:** npm

Full rationale in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Contributing

Conventional commits (`feat:`, `fix:`, `chore:`, `docs:`). `main` is protected — work happens on `feat/`, `fix/`, or `chore/` branches.
