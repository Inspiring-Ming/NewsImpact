# One image: API + website. Runs locally, on ECS Fargate, or (with a Lambda handler) on AWS Lambda.

# 1. Website: type-check and build static files
FROM node:22-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

# 2. Python dependencies and package
FROM python:3.15-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /app
COPY pyproject.toml uv.lock* README.md ./
RUN uv sync --no-dev --no-install-project --extra anthropic
COPY src ./src
RUN uv sync --no-dev --extra anthropic

# 3. Runtime: no build tools, non-root user
FROM python:3.15-slim
RUN useradd --create-home --uid 10001 app
COPY --from=build /opt/venv /opt/venv
COPY --from=build /app/src /app/src
COPY --from=web /web/dist /app/web/dist
COPY data /app/data
ENV PATH=/opt/venv/bin:$PATH PYTHONUNBUFFERED=1 NI_DATA_DIR=/app/data NI_WEB_DIR=/app/web/dist
WORKDIR /app
USER app
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://localhost:8000/health'); sys.exit(0)"
CMD ["uvicorn", "newsimpact.app.api:app", "--host", "0.0.0.0", "--port", "8000"]
