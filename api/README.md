# Ground Up API

FastAPI, Python 3.12, SQLAlchemy, PostgreSQL and Alembic. From the repository root, run `docker compose up --build -d --wait` then `docker compose exec api python -m app.seed`. FastAPI serves OpenAPI at http://localhost:8001/docs.

See [Setup](../docs/SETUP.md) for tests and the CPU Sentence-BERT experiment and [API documentation](../docs/API_DOCUMENTATION.md) for routes.
