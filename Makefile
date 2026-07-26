.PHONY: help build push pipeline simulator down

COMPOSE_FILE := betsim/compose.yaml
COMPOSE := docker compose -f $(COMPOSE_FILE)

help:
	@echo "Available targets:"
	@echo "  make help       # Show available targets"
	@echo "  make build      # Build the simulator and pipeline container images"
	@echo "  make push       # Push the simulator and pipeline container images to Docker Hub"
	@echo "  make simulator  # Start the simulator service in detached mode"
	@echo "  make pipeline   # Run the pipeline service using the existing image"
	@echo "  make down       # Stop and remove services defined in betsim/compose.yaml"

build:
	$(COMPOSE) build

push:
	$(COMPOSE) push

pipeline:
	$(COMPOSE) run --rm --pull missing pipeline

simulator:
	$(COMPOSE) up -d --no-build simulator

down:
	$(COMPOSE) down
