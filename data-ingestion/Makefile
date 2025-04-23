# RAG Blueprint Data Ingestion Makefile
# For setting up local development and running tests

# Configuration variables
CONTAINER_ENGINE ?= podman
OLLAMA_IMAGE ?= ollama/ollama:latest
LLAMA_STACK_IMAGE ?= ghcr.io/run-llama/llama-stack:latest
PGVECTOR_IMAGE ?= ankane/pgvector:latest
MINIO_IMAGE ?= quay.io/minio/minio:latest

# Network for containers
NETWORK_NAME = rag-network

# Ports
OLLAMA_PORT = 11434
LLAMA_STACK_PORT = 8321
PGVECTOR_PORT = 5432
MINIO_PORT = 9000

# Credentials
PGVECTOR_USER = postgres
PGVECTOR_PASSWORD = postgres
PGVECTOR_DB = postgres
MINIO_ACCESS_KEY = minioadmin
MINIO_SECRET_KEY = minioadmin

# Volumes and directories
DATA_DIR = ./data/sample_documents
MINIO_DATA_DIR = ./data/minio

# Default LLM model for Ollama
DEFAULT_MODEL = llama2

.PHONY: help setup-network clean-network start-ollama start-pgvector start-minio start-llama-stack start-infra stop-infra test-local test-minio test-programmatic test-all clean

help:
	@echo "RAG Blueprint Data Ingestion Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  setup-network         - Create a container network for services"
	@echo "  clean-network         - Remove the container network"
	@echo "  start-ollama          - Start Ollama LLM service"
	@echo "  start-pgvector        - Start PGVector database"
	@echo "  start-minio           - Start MinIO object storage"
	@echo "  start-llama-stack     - Start Llama Stack server"
	@echo "  start-infra           - Start all infrastructure components"
	@echo "  stop-infra            - Stop all infrastructure components"
	@echo "  test-local            - Run tests with local files"
	@echo "  test-minio            - Run tests with MinIO"
	@echo "  test-programmatic     - Run programmatic tests"
	@echo "  test-all              - Run all tests"
	@echo "  clean                 - Stop infra and clean up resources"
	@echo ""
	@echo "To use Docker instead of Podman (default):"
	@echo "  make CONTAINER_ENGINE=docker <target>"

setup-network:
	@echo "Creating container network: $(NETWORK_NAME)"
	@$(CONTAINER_ENGINE) network inspect $(NETWORK_NAME) >/dev/null 2>&1 || \
		$(CONTAINER_ENGINE) network create $(NETWORK_NAME)

clean-network:
	@echo "Removing container network: $(NETWORK_NAME)"
	@$(CONTAINER_ENGINE) network inspect $(NETWORK_NAME) >/dev/null 2>&1 && \
		$(CONTAINER_ENGINE) network rm $(NETWORK_NAME) || true

start-ollama: setup-network
	@echo "Starting Ollama service..."
	@mkdir -p $(HOME)/.ollama
	@$(CONTAINER_ENGINE) run -d --name ollama \
		--network $(NETWORK_NAME) \
		-p $(OLLAMA_PORT):11434 \
		-v $(HOME)/.ollama:/root/.ollama \
		--restart unless-stopped \
		$(OLLAMA_IMAGE)
	@echo "Pulling default model ($(DEFAULT_MODEL))..."
	@sleep 5
	@$(CONTAINER_ENGINE) exec ollama ollama pull $(DEFAULT_MODEL)
	@echo "Ollama is running at http://localhost:$(OLLAMA_PORT)"

start-pgvector: setup-network
	@echo "Starting PGVector database..."
	@$(CONTAINER_ENGINE) run -d --name pgvector \
		--network $(NETWORK_NAME) \
		-p $(PGVECTOR_PORT):5432 \
		-e POSTGRES_USER=$(PGVECTOR_USER) \
		-e POSTGRES_PASSWORD=$(PGVECTOR_PASSWORD) \
		-e POSTGRES_DB=$(PGVECTOR_DB) \
		--restart unless-stopped \
		$(PGVECTOR_IMAGE)
	@echo "PGVector is running at localhost:$(PGVECTOR_PORT)"

start-minio: setup-network
	@echo "Starting MinIO object storage..."
	@mkdir -p $(MINIO_DATA_DIR)
	@$(CONTAINER_ENGINE) run -d --name minio \
		--network $(NETWORK_NAME) \
		-p $(MINIO_PORT):9000 \
		-p 9001:9001 \
		-e "MINIO_ROOT_USER=$(MINIO_ACCESS_KEY)" \
		-e "MINIO_ROOT_PASSWORD=$(MINIO_SECRET_KEY)" \
		-v $(MINIO_DATA_DIR):/data \
		--restart unless-stopped \
		$(MINIO_IMAGE) server /data --console-address ":9001"
	@echo "Setting up MinIO bucket..."
	@sleep 5
	@$(CONTAINER_ENGINE) run --rm --network $(NETWORK_NAME) \
		--entrypoint sh \
		$(MINIO_IMAGE) -c "wget -qO- https://dl.min.io/client/mc/release/linux-amd64/mc > /tmp/mc && chmod +x /tmp/mc && \
		/tmp/mc alias set myminio http://minio:9000 $(MINIO_ACCESS_KEY) $(MINIO_SECRET_KEY) && \
		/tmp/mc mb --ignore-existing myminio/rag-documents && \
		/tmp/mc policy set download myminio/rag-documents"
	@echo "MinIO is running at http://localhost:$(MINIO_PORT)"
	@echo "MinIO Console is running at http://localhost:9001"

start-llama-stack: setup-network
	@echo "Starting Llama Stack server..."
	@$(CONTAINER_ENGINE) run -d --name llama-stack \
		--network $(NETWORK_NAME) \
		-p $(LLAMA_STACK_PORT):8321 \
		-e "DATABASE_URI=postgresql://$(PGVECTOR_USER):$(PGVECTOR_PASSWORD)@pgvector:5432/$(PGVECTOR_DB)" \
		--restart unless-stopped \
		$(LLAMA_STACK_IMAGE)
	@echo "Llama Stack is running at http://localhost:$(LLAMA_STACK_PORT)"

start-infra: start-ollama start-pgvector start-minio start-llama-stack
	@echo "All infrastructure components are running!"
	@echo "Waiting for services to initialize..."
	@sleep 10
	@echo "Infrastructure ready!"

stop-infra:
	@echo "Stopping infrastructure components..."
	@$(CONTAINER_ENGINE) stop llama-stack ollama pgvector minio 2>/dev/null || true
	@$(CONTAINER_ENGINE) rm llama-stack ollama pgvector minio 2>/dev/null || true
	@echo "Infrastructure components stopped"

test-local:
	@echo "Running tests with local files..."
	@mkdir -p $(DATA_DIR)
	@cd tests && bash run_with_local_files.sh

test-minio:
	@echo "Running tests with MinIO..."
	@cd tests && bash run_with_minio.sh

test-programmatic:
	@echo "Running programmatic tests..."
	@cd tests && python run_local_programmatic.py

test-all: test-local test-minio test-programmatic
	@echo "All tests completed!"

clean: stop-infra clean-network
	@echo "Cleaning up resources..."
	@echo "Cleanup complete"

# Ensure local development environment is set up
dev-env: start-infra
	@echo "Local development environment is ready!"
	@echo "You can run tests using: make test-all" 