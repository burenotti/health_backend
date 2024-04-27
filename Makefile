IMAGE_NAME = burenotti/health
TAG = latest
COMPOSE_FILE = docker-compose.yaml
CONFIG_FILE = ./config/config.yaml
COMPOSE = docker -f $(COMPOSE_FILE)

generate: _generate-schema

run:
	poetry run python -m health --config="$(CONFIG_FILE)"

test:
	poetry run pytest ./tests/

docker-build:
	$(COMPOSE) build -t "$(IMAGE_NAME):$(TAG)" .


docker-up:
	CONFIG_FILE=config.dev.yaml $(COMPOSE) up

_generate-schema:
	poetry run python -m health.generate_schema -o config/schema.json
