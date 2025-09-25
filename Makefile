# Makefile for PDF to Markdown Converter

# Variables
PYTHON := python
UV := uv
UV_RUN := $(UV) run $(PYTHON)
MAIN := main.py

# Default target
.DEFAULT_GOAL := help

# Help target
.PHONY: help
help:
	@echo "PDF to Markdown Converter - Make Commands"
	@echo "=========================================="
	@echo "Setup:"
	@echo "  make install     Install dependencies using uv"
	@echo "  make install-pip Install dependencies using pip"
	@echo "  make clean       Clean temporary files and cache"
	@echo ""
	@echo "Tasks:"
	@echo "  make create-full Create full pipeline task"
	@echo "  make create-pdf  Create PDF to image task"
	@echo "  make create-img  Create image to markdown task"
	@echo "  make list        List all tasks"
	@echo "  make run ID=xxx  Run task with specified ID"
	@echo "  make status ID=xxx Check status of task"
	@echo ""
	@echo "Development:"
	@echo "  make format      Format code with black"
	@echo "  make lint        Check code with ruff"
	@echo "  make test        Run tests"

# Setup targets
.PHONY: install
install:
	@echo "Installing dependencies with uv..."
	@$(UV) venv
	@$(UV) pip install -r requirements.txt
	@echo "✅ Dependencies installed!"

.PHONY: install-pip
install-pip:
	@echo "Installing dependencies with pip..."
	@pip install -r requirements.txt
	@echo "✅ Dependencies installed!"

.PHONY: setup
setup: install
	@echo "Setting up project..."
	@mkdir -p pdfs images markdowns tasks logs
	@echo "✅ Project setup complete!"

# Task management targets
.PHONY: create-full
create-full:
	@echo "Creating full pipeline task..."
	@$(UV_RUN) $(MAIN) full --create --input pdfs --output markdowns

.PHONY: create-pdf
create-pdf:
	@echo "Creating PDF to image task..."
	@$(UV_RUN) $(MAIN) pdf2img --create --input pdfs --output images

.PHONY: create-img
create-img:
	@echo "Creating image to markdown task..."
	@$(UV_RUN) $(MAIN) img2md --create --input images --output markdowns

.PHONY: list
list:
	@echo "Listing all tasks..."
	@$(UV_RUN) $(MAIN) list

.PHONY: run
run:
ifndef ID
	@echo "Error: Please specify task ID"
	@echo "Usage: make run ID=<task_id>"
else
	@echo "Running task $(ID)..."
	@$(UV_RUN) $(MAIN) run --task-id $(ID)
endif

.PHONY: status
status:
ifndef ID
	@echo "Error: Please specify task ID"
	@echo "Usage: make status ID=<task_id>"
else
	@echo "Checking status of task $(ID)..."
	@$(UV_RUN) $(MAIN) status --task-id $(ID)
endif

.PHONY: resume
resume:
ifndef ID
	@echo "Error: Please specify task ID"
	@echo "Usage: make resume ID=<task_id>"
else
	@echo "Resuming task $(ID)..."
	@$(UV_RUN) $(MAIN) run --task-id $(ID)
endif

.PHONY: cancel
cancel:
ifndef ID
	@echo "Error: Please specify task ID"
	@echo "Usage: make cancel ID=<task_id>"
else
	@echo "Cancelling task $(ID)..."
	@$(UV_RUN) $(MAIN) cancel --task-id $(ID)
endif

# Development targets
.PHONY: format
format:
	@echo "Formatting code with black..."
	@$(UV_RUN) black .

.PHONY: lint
lint:
	@echo "Linting code with ruff..."
	@$(UV_RUN) ruff check .

.PHONY: test
test:
	@echo "Running tests..."
	@$(UV_RUN) pytest

# Cleaning targets
.PHONY: clean
clean:
	@echo "Cleaning temporary files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.tmp" -delete
	@rm -rf .uv-cache
	@echo "✅ Cleaned temporary files!"

.PHONY: clean-tasks
clean-tasks:
	@echo "Cleaning task files..."
	@rm -rf tasks/*.json
	@echo "✅ Cleaned task files!"

.PHONY: clean-output
clean-output:
	@echo "Warning: This will delete all output files!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read confirm
	@rm -rf images/* markdowns/*
	@echo "✅ Cleaned output files!"

.PHONY: clean-all
clean-all: clean clean-tasks
	@echo "✅ All temporary files cleaned!"

# Quick start target
.PHONY: quick-start
quick-start: install setup
	@echo ""
	@echo "✅ Quick start complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Configure your API key in conf/conf.yaml"
	@echo "2. Place PDF files in the 'pdfs' directory"
	@echo "3. Run: make create-full"
	@echo "4. Run: make run ID=<task_id>"
