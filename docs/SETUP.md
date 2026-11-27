# Local setup

Use Docker Desktop in Linux-container mode and Node.js 24 LTS or Node.js 26. The API runs Python 3.12 inside Docker. This avoids the DLL and executable restrictions noted in the original Windows environment. The first build installs locked dependencies and pulls container images. Subsequent demo runs can use the local images, npm installation and included evaluation artifacts.

## Start and seed

From the repository root in PowerShell:

```powershell
docker compose up --build -d --wait
docker compose exec api python -m app.seed
Set-Location web
npm ci
npm run dev
```

The database is published to 127.0.0.1:5433, the API to http://localhost:8001 and the web app to http://localhost:3000. Alembic upgrades run before API startup. Compose waits for PostgreSQL and checks that the API can query the migrated database. The database uses a named volume.

Use `web/.env.example` as a template for `web/.env.local` when changing the public API URL or enabling Google login. The example URL is the default. Set `GROUNDUP_API_PORT` and `GROUNDUP_DB_PORT` in the calling environment to use other host ports, and update the frontend API URL if the API port changes. Close the other process or update CORS if the frontend must use a different port.

## Generate data and evaluate

From the repository root:

```powershell
docker compose exec api python -m app.seed --export-only
docker compose exec api python -m app.evaluate --output /project/evaluation/tfidf-run
```

Compose mounts `data/` and `evaluation/` from the repository. The second command writes a new TF-IDF-only run. Omit `--output` to replace the results served by the dashboard. Use the optional semantic setup for the four-method comparison delivered in this repository.

## Test and build

From the root, with Compose running:

```powershell
docker compose exec -e GROUNDUP_TEST_DATABASE_URL=postgresql+psycopg://groundup:groundup@db:5432/groundup api python -m pytest -q
docker compose exec api alembic check
docker compose exec api python -m app.seed --reset-demo
Set-Location web
npm ci
npm run typecheck
npm run lint
npm run build
npx playwright install chromium
npm run test:e2e
```

The API suite makes an isolated PostgreSQL schema and drops it after use. The browser suite edits the football demo profile and submits an application. It also publishes a demo opportunity. Use a fresh demo or apply the fixture reset before running the suite. Playwright can use an installed Chrome channel via `$env:PLAYWRIGHT_CHROMIUM_CHANNEL='chrome'`. Stop the dev server first if you want Playwright to launch the production web server on port 3000. To test a running server set `GROUNDUP_WEB_URL`. Set `GROUNDUP_CAPTURE_SCREENSHOTS=1` to write evidence to `docs/screenshots/`.

`docker compose exec api python -m app.seed --reset-demo` restores fixture profiles and relative deadlines and clears applications by seeded demo athletes to synthetic postings owned by fixture organisations. It preserves published demo postings, new social posts and unrelated accounts, postings and applications. Run the ordinary seed to fill missing fixtures while preserving progress. Use `docker compose stop` to stop the stack and keep the database.

## Optional CPU Sentence-BERT experiment

Use a host with working Python 3.12 or a Python 3.12 Linux/WSL environment. These commands assume the repository is available in that environment. The one-time model download requires internet access. Runtime loads local files.

```powershell
Set-Location api
uv sync --locked --group evaluation
uv pip install --torch-backend cpu -r requirements-semantic.txt
uv run --no-sync python -c "from huggingface_hub import snapshot_download; snapshot_download('sentence-transformers/all-MiniLM-L6-v2', revision='1110a243fdf4706b3f48f1d95db1a4f5529b4d41', local_dir='.models/all-MiniLM-L6-v2', allow_patterns=['*.json','*.txt','model.safetensors'])"
$env:OMP_NUM_THREADS='2'
uv run --no-sync python -m app.evaluate --sentence-bert .models/all-MiniLM-L6-v2
```

For a host API using the optional model, copy `.env.example` to `.env`, set `SIMILARITY_METHOD=sentence-bert` and `SENTENCE_BERT_MODEL=.models/all-MiniLM-L6-v2`, and start it with `uv run --no-sync uvicorn app.main:app --host localhost --port 8001`. Stop the Compose API first to free the port and keep PostgreSQL running. If the model cannot load or encode, recommendation responses use and report TF-IDF. The production image uses the lighter default configuration.

## Hosted configuration

Render builds the runtime target from the repository root and uses `render.yaml` for the API. On Vercel, set the project root to `web`, use the standard Next.js build, and set `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_GOOGLE_CLIENT_ID` for the hosted app. The API requires a separate PostgreSQL URL, a production JWT signing secret and the intended CORS origins. Use a separate production database. To authorize a real organisation, an operator sets the account's team role and organisation name. Demo endpoints remain disabled in production.
