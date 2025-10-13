.PHONY: test testq cov fmt lint
test:            ; docker compose exec -T backend pytest
testq:           ; docker compose exec -T backend pytest -q
cov:             ; docker compose exec -T backend pytest --cov=app --cov-report=term-missing
fmt:             ; docker compose exec -T backend sh -lc 'ruff format . && ruff check --fix .'
lint:            ; docker compose exec -T backend ruff check .
