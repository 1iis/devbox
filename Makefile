.PHONY: help status sync enable start restart check build shell logs ps dcup dcdn

PYTHON ?= python3
COMPOSE ?= docker compose
COMPOSE_FILE := container/docker-compose.yml
COMPOSE_PROJECT_DIR := container
RUN_DIR := /home/dev/.config/dev-env

help:
	@echo "devbox targets:"
	@echo "  status   dry-run host state report"
	@echo "  sync     converge host state without starting container"
	@echo "  enable   converge host state and enable systemd unit"
	@echo "  start    converge host state and start systemd unit"
	@echo "  restart  converge host state and restart systemd unit"
	@echo "  check    run fast local validation checks"
	@echo "  build    build container image from repo compose file"
	@echo "  shell    enter running container shell"
	@echo "  logs     show compose logs from installed runtime dir"
	@echo "  ps       show compose services from installed runtime dir"
	@echo "  dcup     docker compose up -d from installed runtime dir"
	@echo "  dcdn     docker compose down from installed runtime dir"

status:
	$(PYTHON) host/sync.py status

sync:
	$(PYTHON) host/sync.py enable

enable:
	$(PYTHON) host/sync.py enable

start:
	$(PYTHON) host/sync.py start

restart:
	$(PYTHON) host/sync.py restart

check:
	./scripts/check.sh

build:
	$(COMPOSE) -f $(COMPOSE_FILE) --project-directory $(COMPOSE_PROJECT_DIR) build

shell:
	$(COMPOSE) -f $(RUN_DIR)/docker-compose.yml --project-directory $(RUN_DIR) exec dev zsh

logs:
	$(COMPOSE) -f $(RUN_DIR)/docker-compose.yml --project-directory $(RUN_DIR) logs -f

ps:
	$(COMPOSE) -f $(RUN_DIR)/docker-compose.yml --project-directory $(RUN_DIR) ps

dcup:
	$(COMPOSE) -f $(RUN_DIR)/docker-compose.yml --project-directory $(RUN_DIR) up -d

dcdn:
	$(COMPOSE) -f $(RUN_DIR)/docker-compose.yml --project-directory $(RUN_DIR) down
