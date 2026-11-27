FROM python:3.12-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /bin/uv
WORKDIR /project/api
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PATH="/project/api/.venv/bin:$PATH"
COPY api/pyproject.toml api/uv.lock ./
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers"]

FROM base AS development
RUN uv sync --locked --group evaluation --no-install-project
COPY api/ ./
COPY evaluation/ /project/evaluation/

FROM base AS runtime
RUN uv sync --locked --no-dev --no-install-project
COPY api/ ./
COPY evaluation/results.json /project/evaluation/results.json
COPY evaluation/plots/ /project/evaluation/plots/
