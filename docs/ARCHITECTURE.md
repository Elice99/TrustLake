# TrustLake — System Architecture

**Status:** Pre-MVP · Architecture for Stages 2–10
**Companion documents:** `TrustLake_PRD_v2.docx`, `TrustLake_Full_Build_Roadmap.md`

This document is the technical source of truth for how TrustLake is built — not what it does (that's the PRD), but how the pieces fit together and why each boundary is drawn where it is. Every architectural decision here traces back to one constraint: **the deterministic core (profiling, cleaning execution, Trust Score, readiness scores) must be provably independent of the AI layer.** Everything else is designed around protecting that boundary.

---

## 1. Architectural principles

These aren't aspirational — they're enforced at the code level, and Stage verification gates in the build roadmap test them directly.

1. **Determinism is structural, not conventional.** The Trust Engine, the cleaning execution engine, and both readiness scorers have no import path to any AI client library. This is checked by static analysis (a CI rule that fails the build if `services/trust/`, `services/cleaning/execute.py`, or the readiness scorers import anything from `services/ai/`), not just by code review discipline.
2. **Nothing mutates without a version.** The original uploaded file is immutable. Every transformation produces a new `dataset_versions` row and a new derived file. There is no code path that writes to an existing dataset file in place.
3. **Every consequential action is audited.** If it changes state or costs the user something (a transformation applied, a model trained, an AI provider called), it produces an `audit_events` row. This isn't a logging nice-to-have — PRD §48 treats it as a reproducibility requirement, and the schema treats it as a first-class table, not an afterthought bolted on later.
4. **The AI layer is a client, not a decision-maker.** Every `AIProvider` method signature takes computed evidence in and returns text out. No method returns a value that gets written to a score, a database row that isn't itself AI-content (like a saved insight), or a transformation.
5. **Service boundaries mirror the PRD's own workspace boundaries.** Cleaning, Trust Engine, Analytics, ML, and AI are five separate service modules with narrow, explicit interfaces between them — not one large "backend" module. This is what makes the Stage-by-stage build roadmap possible: each service can be built and verified in isolation.

---

## 2. High-level architecture

*(See the accompanying system architecture diagram.)*

Four tiers, strict downward dependency — a tier only calls the tier directly below it, never sideways into another domain service, never upward:

- **Client** (Next.js/React/TypeScript) — talks only to the API layer, never directly to the database or storage.
- **API layer** (FastAPI) — the single entry point. Owns authentication, request validation, rate limiting, and audit-log emission. Routes requests to the appropriate domain service; contains no business logic itself.
- **Domain services** — Cleaning, Trust Engine, Analytics & ML, AI Providers. Each owns its own logic and its own tables. Cross-service calls happen through explicit Python function interfaces within the same process in v1 (not network calls between services — that's unwarranted complexity for a single-deployable v1, per PRD §49's performance philosophy).
- **Persistence** — PostgreSQL for structured/relational data, object storage (MinIO locally, S3-compatible in production) for file bytes: raw uploads, derived dataset versions, and serialized model artifacts.

---

## 3. Service boundaries in detail

### 3.1 Ingestion & Profiling service
**Owns:** file upload handling, dataset versioning, the profiling algorithm (PRD §9).
**Reads:** object storage (file bytes).
**Writes:** `datasets`, `dataset_versions`, `profiles`.
**Never calls:** AI Providers, Trust Engine (profiling is upstream of scoring, not dependent on it).

### 3.2 Cleaning service
**Owns:** issue detection, the deterministic transformation execution engine, undo/version-chain management (PRD §11–14).
**Reads:** `profiles`, `dataset_versions`.
**Writes:** `dataset_versions` (new versions), `transformations`.
**Calls into:** AI Providers only for the *recommendation* text (PRD §16 — "recommend_cleaning"), never for execution. The recommendation is a suggestion object `{method, params, rationale}` that the user must explicitly approve before the deterministic executor runs it — the AI never calls the executor directly.

### 3.3 Trust Engine
**Owns:** the Trust Score algorithm, versioned and documented separately in `docs/TRUST_SCORE.md` (see Stage 5 of the build roadmap).
**Reads:** `profiles`, `dataset_versions`.
**Writes:** `trust_scores`.
**Never calls:** AI Providers, under any code path. This is the one service with a hard CI-enforced import boundary.

### 3.4 Analytics & ML service
**Owns:** EDA computation, Analytics Readiness scoring, ML preprocessing, model training/evaluation/tuning, ML Readiness scoring, saved models, and predictions (PRD §15, §19–34).
**Reads:** `dataset_versions`, `trust_scores` (readiness scores reuse the Trust Score's evidence pattern but are computed independently).
**Writes:** `analytics_readiness_scores`, `ml_readiness_scores`, `experiments`, `models`, `predictions`.
**Calls into:** AI Providers for insight generation, conversational analytics, model explanation, and recommendation (PRD §16–18, §29) — always with real computed results passed in as structured evidence, never letting the AI compute the underlying numbers itself.
**Internal split:** this is the largest service and is itself split into three sub-modules — `analytics/`, `ml/preprocessing/`, `ml/training/` — sharing the same database session pattern but independently testable.

### 3.5 AI Provider layer
**Owns:** the `AIProvider` interface and its implementations (PRD §43).
**Reads:** nothing from the database directly — every method receives its evidence as a function argument from the calling service.
**Writes:** nothing to the database directly. If an AI-generated insight needs to be persisted (e.g., a saved "Generate Insights" result), the *calling service* writes it, tagged clearly as AI-generated content, not the AI provider class itself.
**Hard constraints** (enforced by giving these classes no database session and no filesystem/storage client in their constructor — architecturally impossible to violate, not just discouraged):
  - No SQL execution capability
  - No arbitrary code execution
  - No write access to `trust_scores`, `dataset_versions`, `models`, or any transformation-execution path

---

## 4. Data architecture

### 4.1 Why PostgreSQL + object storage, not one or the other
Relational data (users, metadata, scores, audit trail, experiment records) needs referential integrity, transactions, and queryability — Postgres. File bytes (uploaded CSVs, derived dataset versions, serialized model artifacts) are large, immutable-once-written blobs that don't belong in row storage — object storage, referenced by URI from Postgres rows. This split is explicit in PRD §45–46 and is not renegotiated later — putting file bytes in Postgres is the most common way this kind of architecture quietly degrades.

### 4.2 Core schema (entities, not full DDL — see `infra/migrations/` for the authoritative schema)

- **users** — auth identity
- **datasets** — top-level dataset record (name, owner, created_at)
- **dataset_versions** — one row per version; `parent_version_id` forms the version chain; `storage_uri` points to object storage; never updated after creation, only inserted
- **profiles** — one row per dataset_version, the computed profiling output
- **trust_scores** — one row per dataset_version, versioned against `trust_score_version` (the algorithm version, not the data version)
- **transformations** — one row per applied cleaning step; references the `dataset_version` it was applied to and the `dataset_version` it produced
- **analytics_readiness_scores**, **ml_readiness_scores** — same pattern as `trust_scores`, scoped to their own domain
- **experiments** — one row per ML training run; holds the full reproducibility record (PRD §38): dataset_version, cleaning lineage, features, target, split config, model type, hyperparameters, evaluation metrics, timestamp
- **models** — saved/promoted models, referencing an `experiment_id`, with `storage_uri` pointing to the serialized artifact bundle (model + preprocessing pipeline together, per PRD §32)
- **predictions** — one row per prediction batch, referencing the `model_id` and the input/output file URIs
- **audit_events** — append-only; `actor_id`, `action`, `entity_type`, `entity_id`, `metadata` (jsonb), `created_at`

### 4.3 Versioning discipline
`dataset_versions` forms a linked list (via `parent_version_id`), never a tree with silent branches and never an in-place mutation. Undo (PRD §13) means creating the *current working pointer* on a `datasets` row moving back to an earlier `dataset_version_id` — it does not delete or rewrite the version it's undoing away from. This makes the full history always reconstructable, which is what Stage 4's and Stage 10's verification gates actually test.

---

## 5. API design

- **Style:** REST over JSON, versioned under `/api/v1/`. GraphQL was considered and rejected for v1 — TrustLake's data-fetching patterns are mostly resource-oriented (get this dataset's profile, get this experiment's results), not the deeply nested, client-driven query shape GraphQL is built for; REST is simpler to reason about and test at this stage.
- **Resource shape mirrors the service boundaries above** — `/datasets/*` (ingestion/profiling), `/datasets/{id}/transformations/*` (cleaning), `/datasets/{id}/trust-score` (trust engine), `/datasets/{id}/analytics/*` (analytics), `/datasets/{id}/ml/*` (ML), `/models/*` and `/models/{id}/predict` (saved models/prediction).
- **Long-running work is async by design, not by accident.** Model training and hyperparameter tuning (Stage 7) are dispatched to a background task queue (Celery/RQ or FastAPI `BackgroundTasks` for v1's scale) and return a job identifier immediately; the client polls or subscribes for status. Nothing in the API blocks a request thread on a multi-minute training run.
- **Consistent error envelope** across every endpoint: `{error: {code, message, details}}`. No endpoint leaks a raw stack trace or an unstructured 500.
- **Every mutating endpoint (POST/PUT/DELETE) emits exactly one `audit_events` row** as part of the same database transaction as the mutation itself — not as a fire-and-forget side effect that can silently fail independently of the action it's supposed to record.

---

## 6. AI architecture (the isolation boundary, concretely)

```python
class AIProvider(ABC):
    @abstractmethod
    def explain_issue(self, evidence: IssueEvidence) -> str: ...
    @abstractmethod
    def summarize_profile(self, evidence: ProfileEvidence) -> str: ...
    @abstractmethod
    def generate_insight(self, evidence: AnalyticsEvidence) -> str: ...
    @abstractmethod
    def recommend_cleaning(self, evidence: IssueEvidence) -> CleaningRecommendation: ...
    @abstractmethod
    def explain_model(self, evidence: ModelEvidence) -> str: ...
    @abstractmethod
    def recommend_model(self, evidence: MLReadinessEvidence) -> ModelRecommendation: ...
    @abstractmethod
    def explain_prediction(self, evidence: PredictionEvidence) -> str: ...
```

Every `*Evidence` type is a structured Pydantic model built *by the calling domain service* from real computed data — never assembled by the AI layer itself, and never containing a raw database session or file handle. `NoAIProvider` implements every method by returning a clear "AI is disabled" sentinel — it is not a stub that throws; the product must degrade gracefully, not error out, when AI is off (PRD §29). `GeminiProvider` and `GroqProvider` are thin adapters translating the same evidence objects into provider-specific prompts, with the "only reference the evidence provided" instruction embedded in every prompt template as a structural part of the template, not an afterthought line.

Provider selection is a per-user setting stored on the `users` row (or a session default), read once at request time by a factory function (`get_ai_provider(user) -> AIProvider`) — no service holds a long-lived reference to a specific provider instance.

---

## 7. Background processing

Two classes of async work, handled differently:

- **Fast, request-scoped async** (uploading a file, running EDA on a moderate dataset) — handled within the request/response cycle using FastAPI's native async support; no separate worker needed.
- **Slow, job-scoped async** (model training, hyperparameter tuning, large-dataset profiling) — dispatched to a task queue with persisted job state (`experiments.status`: `pending → running → completed/failed`), so a client refreshing the page or reconnecting after a dropped connection can still recover the job's status from the database, not from in-memory state that dies with the request.

---

## 8. Security architecture

- **Secrets:** environment variables only, injected at container runtime; never committed, never present in any frontend bundle (verified in Stage 10's security pass by grepping built frontend assets for known secret patterns).
- **AuthN:** token-based (JWT), short-lived access tokens with a refresh flow; passwords hashed with argon2.
- **AuthZ:** every dataset/model/experiment row is owner-scoped; every service-layer query filters by the authenticated user's ownership — enforced at the query layer, not just the API layer, so a bug in one route can't leak another user's data through a different route.
- **Upload safety:** server-side MIME/extension/size validation (never trust client-side checks alone); uploaded files are never executed or parsed with anything that evaluates code (no `eval`-adjacent CSV parsing paths).
- **AI data boundary:** the consent screen (PRD §44) gates the *first* AI call per session — no AI provider is invoked before explicit opt-in, enforced by a middleware check on every AI-routed endpoint, not just a frontend UI convention.

---

## 9. Deployment architecture

- **Local/dev:** Docker Compose — Postgres, API, web, MinIO, task queue worker, as separate services sharing a Docker network, matching the structure defined in Stage 0 of the build roadmap.
- **Staging/production:** the same container images, orchestrated by whatever platform is chosen at that stage (a single-host Compose deployment is sufficient for v1's real scale, per PRD §49 — Kubernetes is explicitly out of scope, PRD §52) — behind a reverse proxy handling TLS.
- **Migrations run as a deploy step**, not manually against production — `alembic upgrade head` is part of the release pipeline, never a developer's local terminal against a live database.
- **Object storage moves from MinIO (dev) to S3-compatible storage (prod)** with zero application code changes, because the `StorageProvider` abstraction (Stage 2) is the only thing that knows which backend it's talking to.

---

## 10. What this architecture deliberately does not include (v1)

Per PRD §52 — named here so a future contributor doesn't "helpfully" reintroduce complexity that was deliberately deferred:

- No microservices / inter-service network calls — one deployable backend, cleanly modularized internally
- No message broker (Kafka) — the task queue's own broker (Redis, typically) is sufficient for v1's job volume
- No Kubernetes — container orchestration stays simple until real scale demands otherwise
- No multi-tenant SaaS data isolation model — single-tenant-per-deployment is the v1 assumption
- No GraphQL layer, no separate BFF (backend-for-frontend) — the REST API is consumed directly

---

## Appendix — how this document relates to the others

- **PRD** (`TrustLake_PRD_v2.docx`) is the *what and why* — product behavior, user-facing rules, scope boundaries.
- **This document** is the *how* — service boundaries, schema, API shape, the concrete mechanism behind the AI safety boundary.
- **Build roadmap** (`TrustLake_Full_Build_Roadmap.md`) is the *in what order, and how do we know it's actually working* — stage sequencing and verification gates.

When any of the three conflict, the PRD wins on product behavior, this document wins on technical structure, and the roadmap wins on sequencing — but a real conflict between them is a signal to stop and reconcile the documents, not to silently pick one.
