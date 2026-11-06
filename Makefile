.PHONY: up down seed test compare rebuild-replica logs ps
DC = docker compose

up:
	$(DC) up --build -d --wait
	@echo "Frontend: http://localhost:5173  (demo / demo1234)"

down:
	$(DC) down

seed:
	$(DC) --profile tools run --rm -T tools python scripts/seed_tasks.py

test:
	$(DC) --profile test run --rm -T --build test-a python -m pytest -q tests/task_api
	$(DC) --profile test run --rm -T test-b python -m pytest -q tests/replica_consumer tests/replica_api

compare:
	$(DC) --profile tools run --rm -T tools python scripts/compare_systems.py

rebuild-replica:
	./scripts/rebuild_replica.sh

logs:
	$(DC) logs -f --tail=50

ps:
	$(DC) ps
