# TrustLake — Build Log

A plain-language record of what's been built, why, and the concepts behind each decision — written so you can come back later and actually understand what happened, not just see a list of finished tasks. New entries get added as the build progresses.

---

## Stage 0 — Environment & Project Foundations

### Repo structure, Docker Compose, API/Web stubs

**What we built:** the monorepo skeleton (`apps/web`, `apps/api`, `packages/shared-types`, `infra/`, `docs/`), a minimal FastAPI "Hello, TrustLake" route, a minimal Next.js placeholder page, and a `docker-compose.yml` tying Postgres 16 + both apps together.

**Why a monorepo:** frontend and backend live in one repository instead of two, sharing one Git history and one place to open a PR that touches both sides of a feature. `packages/shared-types` exists so type definitions (e.g. what a "Dataset" looks like) can eventually be written once and used by both TypeScript and Python — not built yet, but the folder exists so the structure is ready.

**Concept: Docker & Docker Compose.** A *container* is a lightweight, isolated environment that packages your code with everything it needs to run (system libraries, the right Python/Node version) so it behaves identically on any machine — no more "works on my machine." A *Dockerfile* is the recipe for building one container image. `docker-compose.yml` is the conductor: it defines multiple containers (here: `postgres`, `api`, `web`) and how they talk to each other, and `docker compose up` builds/starts all of them together with one command.

**Concept: environment variables & fail-fast validation.** Secrets and per-environment config (database passwords, connection strings) should never be hardcoded into source code — they're injected at runtime via a `.env` file (never committed to git) read into environment variables. `app/core/config.py` uses `pydantic-settings` to read these on startup and — critically — **crash immediately with a clear error if something required is missing**, rather than silently starting with a blank secret and failing mysteriously later. This is called "fail fast," and it's a deliberate design choice, not an accident.

**Bugs hit and fixed:**
- The Next.js scaffold defaulted to fetching a font from Google's servers at *build time* — this silently breaks in any environment without internet access to Google (including some CI/Docker setups), so we switched to the system font stack instead.
- Docker containers don't have a real init system (PID 1) by default. When `uvicorn --reload`'s file-watcher subprocess died awkwardly, nothing reaped it, and the container became an unkillable "zombie." Fix: `init: true` in `docker-compose.yml`, which runs a tiny init process inside the container specifically to clean up after crashed child processes.
- Port `5432` (Postgres's default) collided first with a locally-installed Postgres 18 running as a Windows service, then with another unrelated project's Docker container also using `5433`. Final fix: TrustLake's Postgres maps to host port `5434` — the container's *internal* port is still 5432; only the host-facing door number changed.

---

## Stage 2 — Backend Foundation

### Day 1: Async SQLAlchemy engine and session management

**What we built:** the full `apps/api` folder structure (`db/`, `models/`, `schemas/`, `api/v1/routes/`, `services/`), and `app/db/session.py` — the actual connection to Postgres.

**Concept: ORM (Object-Relational Mapper).** SQLAlchemy lets you describe a database table as a Python class (a "model") instead of writing raw SQL by hand for every query. You work with Python objects; SQLAlchemy translates that into SQL behind the scenes.

**Concept: async vs. sync.** A normal ("sync") database call blocks your whole program until the database responds. An "async" call lets the program go do other work (like handling a different user's request) while waiting. FastAPI is built around async, so the database layer needs to be async too, or you lose most of the benefit. This is why `DATABASE_URL` needs the `postgresql+asyncpg://` prefix instead of plain `postgresql://` — `asyncpg` is the specific async-capable driver library that talks to Postgres.

**Concept: dependency injection via `get_db()`.** Instead of every route manually opening and closing a database connection, FastAPI routes declare "I need a `db` session" as a parameter, and `get_db()` supplies one, scoped to exactly that one request, and guarantees it's closed afterward — even if the request crashes partway through.

---

### Day 2: Alembic (database migrations)

**What we built:** Alembic, configured for async, wired to read `DATABASE_URL` from the same settings object as everything else (not duplicated in a separate config file).

**Concept: what a migration actually is.** Your database schema (which tables exist, what columns they have) needs to change over time as the app grows — but you can't just edit a table by hand on a live database with real data in it. A *migration* is a versioned, ordered script that describes exactly how to change the schema (`upgrade()`) and how to undo that change (`downgrade()`). Alembic tracks which migrations have already been applied (in a table called `alembic_version`), so running `alembic upgrade head` always brings any database — empty, partially migrated, whatever — up to the latest expected schema, reproducibly.

**Concept: autogenerate.** Alembic can compare your actual SQLAlchemy models against the real database schema and generate the migration script for you automatically, rather than you hand-writing SQL. It's not magic — it's a diff tool — so it still needs to be reviewed before trusting it.

**A design decision worth understanding:** Alembic normally runs migrations *synchronously*, but our engine is async-only. Rather than add a second ("sync") database driver just for migrations, we used Alembic's own async template, which wraps the async engine in a small sync-compatible bridge (`connection.run_sync(...)`). One less dependency, and the whole codebase stays consistently async.

---

### Day 3: Core models (`users`, `datasets`, `audit_events`) and the first real migration

**What we built:** three SQLAlchemy models, matching Pydantic schemas for API input/output, and the actual first migration that creates these tables.

**Concept: UUID vs. auto-incrementing integer primary keys.** Every database row needs a unique ID. The simple option is `1, 2, 3, ...` — but that leaks information (anyone can guess there are exactly 4,502 users by seeing ID 4502) and makes IDs predictable/guessable. We chose UUIDs instead — random-looking 128-bit identifiers — generated in Python (`uuid.uuid4()`) before the row is even sent to the database, rather than relying on Postgres to generate them, which keeps things simple and portable.

**Concept: foreign keys.** `datasets.owner_id` references `users.id` — this is a *foreign key*, and Postgres enforces it: you cannot insert a dataset pointing at a user that doesn't exist. This is the database itself protecting data integrity, not just application code being careful.

**A naming gotcha worth knowing:** SQLAlchemy's base model class uses the Python attribute name `metadata` internally for its own bookkeeping, so our `AuditEvent` model can't *also* use `metadata` as a Python attribute name — even though that's what the actual database column is called. We named the Python side `event_metadata` while keeping the real database column named `metadata`, so the schema matches the spec exactly even though the Python code reads slightly differently.

**A bug hit and fixed — and *why* it happened, not just what the fix was:** the app's database `engine` is created once, when the app starts (a single object shared for the whole program's life — this is intentional and correct for how a real running server works). But the testing tool (`pytest-asyncio`) by default gives *each individual test* its own fresh "event loop" (the async equivalent of a clock that schedules work). The first test worked fine; every test after it failed, because it tried to reuse a database connection that belonged to a different (already-finished) event loop. Fix: configure `pytest-asyncio` so all tests in one run share a single event loop, matching what the single shared `engine` actually expects.

---

### CI bug: tests failed on GitHub even though they passed locally

**What happened:** every check passed on your machine — `pytest`, `pre-commit`, `alembic upgrade head` — but GitHub Actions failed with `relation "users" does not exist`.

**Why this is a normal, expected kind of bug, not a sign anything is broken:** your local Postgres (running in Docker) has a *persistent* volume — data survives between `docker compose up`/`down` cycles, and you'd already run `alembic upgrade head` on it once, so the tables were sitting there from a previous session. GitHub Actions' Postgres, by contrast, is a **brand new, completely empty container every single run** — it has no memory of anything from a previous run. The CI workflow was installing dependencies and running tests, but never actually told Alembic to create the tables first. Locally this was invisible because the tables already existed from earlier manual testing; in CI, starting from true zero, the gap was exposed.

**The fix:** add `alembic upgrade head` as its own step in `ci.yml`, between installing dependencies and running `pytest`. Verified by deliberately dropping every table in the local test database (simulating CI's true-empty starting state) and confirming the same sequence — migrate, then test — now passes.

**The general lesson:** "it works on my machine" and "it works in a clean environment" are genuinely different claims. A persistent local setup can quietly hide a missing setup step for a long time. This is exactly why CI exists — it's the one place that always starts from nothing.

---

### Day 4: Password hashing and `/auth/register`

**What we built:** argon2 password hashing (`app/core/security.py`), a `register_user` service function, and the actual `POST /api/v1/auth/register` endpoint.

**Concept: why argon2, not something simpler.** Storing a password as plain text means anyone who reads the database (an attacker, a careless backup, a bug) instantly has every user's real password. Hashing turns a password into a one-way scrambled value — easy to check ("does this password match?") but computationally infeasible to reverse. argon2 specifically is the current recommended choice for new applications: it won the industry's open Password Hashing Competition and is deliberately slow and memory-hungry in a way that makes large-scale cracking attempts (using GPUs/specialized hardware) far more expensive than older algorithms like plain SHA-256 or even bcrypt.

**Concept: service layer vs. route layer.** `app/services/auth.py` contains the actual business logic (check for duplicate email, hash the password, create the user, log an audit event) and deliberately has zero FastAPI imports — it doesn't know or care that it's being called from an HTTP request. `app/api/v1/routes/auth.py` is the thin layer that translates HTTP concerns (the request body, the response status code) into a call to that service function, and translates the service's plain Python exception (`EmailAlreadyRegisteredError`) into the right HTTP status code (409 Conflict). This separation means the registration logic could be tested, or reused from a CLI script or background job, without needing a fake HTTP request to exercise it.

**A real architectural bug caught and fixed:** `get_db()` (built on Day 1) yielded a database session but never called `session.commit()`. This was invisible until now because Day 1–3's tests either only *read* data or managed their own commits directly — nothing had gone through a real "mutate via the API" path yet. Without this fix, a registration could return a success response to the user while the database silently discarded the change the moment the request finished (SQLAlchemy's default behavior on session cleanup is rollback, not commit). Fixed by making `get_db()` commit automatically on success and roll back on any exception — which also satisfies the architecture doc's requirement that a mutation and its audit-log entry land in one atomic transaction, for every future route, not just this one.

**Two more bugs, both about test correctness, not app correctness:**
- Testing the register endpoint by mixing FastAPI's `TestClient` (which manages its own internal event loop) with directly-`async def` tests sharing pytest's session-wide event loop caused "event loop is closed" errors — a different instance of the same underlying class of problem from Day 3's event-loop bug. Fixed by switching to `httpx.AsyncClient`, which runs everything under one consistent event loop.
- These are the first tests that *actually commit* to the database (on purpose — that's what proves the `get_db()` fix above genuinely works end-to-end). That means running `pytest` twice in a row locally hits the second run's leftover data from the first, causing a false failure. Fixed with a small cleanup step that removes known test rows before each test runs, so local re-runs always start from a known state.

---

### Day 5: JWT login, `/auth/me`, and a real security incident along the way

**What we built:** JWT issuance on login, a `get_current_user` dependency that protects routes, and `GET /api/v1/auth/me` as the first route that actually requires being logged in.

**Concept: what a JWT actually is.** A JWT (JSON Web Token) is a signed piece of text the server hands the client after a successful login. It contains a claim (here: the user's ID) and an expiration time, and it's cryptographically signed with a secret only the server knows. The client sends it back on every request that needs authentication (`Authorization: Bearer <token>`), and the server can verify it's genuine — and hasn't expired, and hasn't been tampered with — without needing to look anything up in a database first. That's the whole appeal: it's "stateless" — the token itself carries proof of who you are.

**A real decision made together: 30-minute token expiration, no refresh-token mechanism.** Shorter-lived tokens are more secure (a stolen token is useful to an attacker for less time), at the cost of needing to log in again more often. Since nothing yet depends on long browsing sessions (no frontend consuming this API exists yet), this tradeoff costs nothing right now — it only becomes a real inconvenience once there's a UI someone is actually using continuously, at which point a refresh-token mechanism would be the natural next addition.

**Concept: why "wrong password" and "email not found" return the exact same error.** If they returned different errors, an attacker (or just a curious script) could try a list of email addresses against your login endpoint and learn which ones are actually registered users — just from the error message, without ever guessing a real password. This is a well-known vulnerability class called "user enumeration." The fix costs nothing (just don't distinguish the two cases) and is standard practice for any real login system.

**A real security incident, not just a bug:** partway through this day, a real Postgres password ended up committed to `.env.example` — the *template* file, which is meant to be safely committed (unlike the real `.env`, which is gitignored). This happened because at some point the placeholder text got overwritten with an actual working value and that got pushed to GitHub. Two things worth understanding: first, a `git commit` fixing the file afterward does **not** erase the exposed value from git's history — every previous commit is still fully visible to anyone browsing the repository, permanently, unless the history itself is deliberately rewritten (a bigger, more disruptive operation). Second, rotating the actual password (changing it for real, not just editing the file) is what actually closes the exposure — the old, now-public value becomes useless rather than just harder to find. Given this was a local-only development database with no real user data at stake, a full history rewrite wasn't judged worth the disruption — but the password itself was rotated, and the general lesson carries forward: **never let a real secret exist in a file that's meant to be committed**, even one that feels low-stakes today.

**A bug hit and fixed:** the login endpoint uses `OAuth2PasswordRequestForm`, which parses form-encoded request bodies (not JSON) — this was a deliberate choice, not an accident, because it's what lets FastAPI's auto-generated `/docs` page offer a working "Authorize" button for testing protected routes by hand. But form-parsing needs a library (`python-multipart`) that wasn't in `requirements.txt` yet, so the very first attempt to boot the server after adding the login route crashed on startup. Caught immediately by actually running the server rather than assuming the code was correct because it looked right.
