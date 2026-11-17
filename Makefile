.PHONY: help install fmt lint typecheck arch test contracts contracts-check check dev api web-build docker mcp universe tf-check

help:           ## list every command
	@grep -E '^[a-z-]+:.*## ' Makefile | sed 's/:.*## /\t/' | expand -t 18

install:        ## Python deps (.venv) + website deps (web/node_modules)
	uv sync && cd web && npm ci

fmt:            ## auto-format and auto-fix
	uv run ruff format . && uv run ruff check --fix .

lint:           ## check formatting and code style
	uv run ruff format --check . && uv run ruff check .

typecheck:      ## static type check of src/
	uv run mypy src

arch:           ## enforce architecture boundaries (pyproject.toml [tool.importlinter])
	uv run lint-imports

test:           ## all tests with coverage
	uv run pytest --cov=newsimpact --cov-report=term-missing

contracts:      ## regenerate event schemas + the OpenAPI document and the website's typed client
	uv run python scripts/export_schemas.py
	uv run python scripts/export_openapi.py
	cd web && npm run gen:api

contracts-check: contracts  ## fail if generated contracts are out of date (CI)
	git diff --exit-code -- schemas/ web/openapi.json web/src/api/schema.ts || \
	  (echo "contracts out of date: run make contracts and commit" && exit 1)

check: lint typecheck arch test contracts-check web-build   ## everything CI runs

dev:            ## API (reload) on :8000 + website dev server on :5173 (open the website)
	(uv run uvicorn newsimpact.app.api:app --reload &) && cd web && npm run dev

api:            ## API + built website on :8000
	uv run uvicorn newsimpact.app.api:app --reload

web-build:      ## type-check and build the website into web/dist
	cd web && npm run build

docker:         ## build and run the production image on :8000, with .env and var/ state
	docker build -t newsimpact:local . && docker run --rm -p 8000:8000 \
	  $$([ -f .env ] && echo --env-file .env) -e NI_DB_PATH=/app/var/newsimpact.db \
	  -v "$$PWD/var":/app/var newsimpact:local

mcp:            ## MCP server for AI assistants (stdio), reading the same database as the website
	uv run --extra mcp python -m newsimpact.app.mcp

universe:       ## refresh data/reference/universe.json (S&P 500 + ASX 200), quarterly after the index reviews
	uv run python scripts/refresh_universe.py

tf-check:       ## validate the Terraform files
	cd infra/terraform/bootstrap && terraform fmt -check && terraform init -backend=false -input=false >/dev/null && terraform validate
