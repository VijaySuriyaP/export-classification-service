.PHONY: up down test index eval load demo smoke lint
up:
	docker compose up --build -d
down:
	docker compose down --remove-orphans
test:
	docker compose run --rm --no-deps -e DATABASE_URL=sqlite:////tmp/test-exporter.db -e REDIS_REQUIRED=false -e VERIFIER_URL= api pytest -q
index:
	docker compose run --rm --no-deps -v ./corpus:/app/corpus api python -m src.indexer.cli build
eval:
	PROMPT_VERSION="$${PROMPT_VERSION:-v1}" docker compose run --rm --no-deps -v ./results:/app/results api python -m src.eval.run_eval --prompt-version "$${PROMPT_VERSION:-v1}" --base-url http://api:8000 --out results/eval.json
load:
	bash scripts/run_load.sh
demo:
	bash scripts/demo/01_walking_skeleton.sh
smoke:
	bash scripts/smoke.sh
lint:
	docker compose run --rm --no-deps api ruff check src tests scripts
