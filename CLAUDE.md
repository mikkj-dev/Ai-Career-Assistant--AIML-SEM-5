# Ground Up repository guide

Read [PRD.md](PRD.md) and [ARCHITECTURE.md](ARCHITECTURE.md) before changing scope or architecture. The two M2 HTML copies and the later CSET312 PDF in `Report/` are original source documents. Keep them intact.

## Working conventions

- Update the Status section after every finished task. After context compaction, reread this file and update the status with verified work.
- The web app uses Next.js 16, Tailwind v4, Geist, Motion and Phosphor. Keep the existing zinc and pitch-green design. Before touching Next-specific APIs, read the installed docs under `web/node_modules/next/dist/docs/`.
- The API uses sync SQLAlchemy, UUIDs and timezone-aware datetimes. Add migrations for schema changes. Never log bearer tokens or store ID numbers.
- Keep `app.matching` independent of PostgreSQL. Preserve the six weights and the 93.5 worked example. Pass a consistent corpus and a fixed clock in the offline evaluation.
- Preserve unknown-age and tolerance labels. Check hard age eligibility again at application submission. Treat evaluation artifacts as generated output.
- Run Python in Docker on Windows when Smart App Control blocks executable shims or DLLs.

## Commands

```powershell
docker compose up --build -d --wait
docker compose exec api python -m app.seed
docker compose exec api python -m app.seed --export-only
docker compose exec api python -m app.evaluate --output /project/evaluation/tfidf-run
docker compose exec -e GROUNDUP_TEST_DATABASE_URL=postgresql+psycopg://groundup:groundup@db:5432/groundup api python -m pytest -q
Set-Location web
npm ci
npm run typecheck
npm run lint
npm run build
npm run test:e2e
```

See [SETUP.md](docs/SETUP.md) for optional Sentence-BERT, browser installation, ports and targeted reset. Use `api/.env.example` and `web/.env.example` for local overrides. The production API requires a strong `JWT_SECRET`, `DATABASE_URL`, `CORS_ORIGINS` and the Google client ID if using Google authentication.

## Status

The local application uses API-backed fixtures, profiles, recommendations, social posts, applications and the organisation dashboard. TF-IDF and CPU Sentence-BERT rankings were evaluated on the fixed synthetic benchmark. [TEST_REPORT.md](docs/TEST_REPORT.md) records verification. Human annotations, real KYC and hosted deployment remain open. Demo completion work is on `main` (2026-11-27); `evaluation/ground_up_ml.ipynb` is kept local, uncommitted.
