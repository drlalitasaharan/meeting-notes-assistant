SHELL := /bin/bash
.ONESHELL:
.DEFAULT_GOAL := ci-smoke

COMPOSE := docker compose
COMPOSE_FILES := -f docker-compose.yml
# Append overlays if present (idempotent)
ifneq ($(wildcard docker-compose.prodready.yml),)
  COMPOSE_FILES += -f docker-compose.prodready.yml
endif
ifneq ($(wildcard docker-compose.worker.yml),)
  COMPOSE_FILES += -f docker-compose.worker.yml
endif
ifneq ($(wildcard docker-compose.minio.yml),)
  COMPOSE_FILES += -f docker-compose.minio.yml
endif
ifneq ($(wildcard docker-compose.uvicorn.yml),)
  COMPOSE_FILES += -f docker-compose.uvicorn.yml
endif
ifneq ($(wildcard docker-compose.traefik.yml),)
  COMPOSE_FILES += -f docker-compose.traefik.yml
endif
ifneq ($(wildcard docker-compose.traefik-local.yml),)
  COMPOSE_FILES += -f docker-compose.traefik-local.yml
endif
ifneq ($(wildcard docker-compose.public.yml),)
  COMPOSE_FILES += -f docker-compose.public.yml
endif

.PHONY: ci-up ci-smoke ci-down

ci-up:
	$(COMPOSE) $(COMPOSE_FILES) --env-file .env.dev up -d db redis minio backend worker

ci-smoke: ci-up
	MNA_API=http://127.0.0.1:8000 \
	S3_PUBLIC_ENDPOINT=http://127.0.0.1:9000 \
	TEXT="hello from mac" DELAY=0.2 \
	bash scripts/smoke.sh

ci-down:
	$(COMPOSE) $(COMPOSE_FILES) --env-file .env.dev down -v
