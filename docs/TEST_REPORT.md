# Ground Up test report

Verified on Windows with Docker Desktop Linux containers, PostgreSQL 17, Python 3.12, Node.js 26, Next.js 16.4.6 and Playwright using installed Chrome. Browser tests ran against the production Next.js build and the Compose API with real PostgreSQL.

| Check | Result | Evidence |
|---|---|---|
| Docker Compose, PostgreSQL and migrations | Passed | Both services healthy. `alembic upgrade head` applied the initial and application revisions. `alembic check` reported no new upgrade operations. |
| Backend and dataset suite | 21 passed | Docker `python -m pytest -q` with isolated PostgreSQL schema. Covers components, 93.5, age tolerance, deadlines, text fallback, dataset repeatability, metrics, authentication, application uniqueness and roles. |
| Idempotent seed and reset | Passed | Normal seed preserved edited profiles and existing application records. Reset restored seeded profiles and preserved unrelated records. Export regenerated the fixture dataset in Docker. |
| Evaluation | Passed | Docker reproduced the TF-IDF benchmark. The optional local CPU run also generated Sentence-BERT scores. Four PNG plots and CSV/JSON tables were emitted. |
| Frontend checks | Passed | `npm run typecheck`, `npm run lint` and `npm run build`. |
| Runtime packaging and dependency audit | Passed | Built the production API image and loaded its bundled evaluation with networking disabled. Reinstalled from the final npm lockfile, which reported zero advisories. |
| Desktop browser | Passed | At 1440×1024, edited athlete position, skills and goals, compared backend rankings, submitted the application, refreshed history, switched to organisation, published a posting and displayed all evaluation figures. |
| Mobile browser | Passed | At 390px viewport width, tested sign-in, no eligible opportunities, browse filters, Cricket tournament gallery, detail and close. |
| Persistence across API restart | Passed | After restarting the Compose API, the football athlete was still a winger and the application to Juniperline 016 remained submitted. The opportunity was the highest-ranked result after that edit. |
| Local matcher latency | Median 2.55 ms, p95 3.05 ms | One warm pass across 200 athletes and the 300-posting corpus in the Compose API container. Includes filtering and scoring in the matcher. Database and network time are outside this timing. |

The first production build exposed Next.js dynamic hook requirements. Suspense boundaries resolved prerendering for the standalone opportunity page and shared navigation. Mobile verification exposed ambiguous browse filter labels and a dialog title layer that intercepted touch events. Explicit label associations and a dedicated close-button layer resolved both problems. An exploratory native Windows pytest run hit a temporary-directory permission error. The documented Docker test command ran the full suite against both the isolated and default stacks. A Starlette warning for the existing HTTPX test client remains during pytest.

## Screenshots from the running application

- [Athlete dashboard](screenshots/athlete-dashboard.png)
- [Opportunity gallery](screenshots/opportunity-gallery.png)
- [Match detail and apply action](screenshots/opportunity-detail.png)
- [Persisted application history](screenshots/application-history.png)
- [Organisation dashboard and application inbox](screenshots/organisation-dashboard.png)
- [ML evaluation dashboard](screenshots/evaluation-dashboard.png)
- [Mobile opportunity detail](screenshots/mobile-opportunity-detail.png)

See [Setup](SETUP.md) for exact commands. Hosted deployment, live Google OAuth and licensed identity verification are outside the local evidence.
