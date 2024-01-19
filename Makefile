.ONESHELL:
ENV_PREFIX=.venv/bin
FILES="."

.PHONY: help
help:             ## Show the help.
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@fgrep "##" Makefile | fgrep -v fgrep

.PHONY: show
show:             ## Show the current environment.
	@echo "Current environment:"
	@echo "Running using $(ENV_PREFIX)"
	@poetry env info

.PHONY: init
init:             ## Initialize the project.
	@pip install -r requirements.txt
	@sudo add-apt-repository ppa:mc3man/trusty-media
	@sudo apt-get update
	@sudo apt-get install ffmpeg

.PHONY: run
run:              ## Run the production server.
	python start.py

.PHONY: lint
lint:             ## Run pep8, black, mypy linters.
	$(ENV_PREFIX)/ruff check $(FILES) || exit $$?
	$(ENV_PREFIX)/black --check $(FILES) || exit $$?
	$(ENV_PREFIX)/mypy $(FILES) || exit $$?

.PHONY: format
format:           ## Run pep8, black, mypy formatters.
	$(ENV_PREFIX)/ruff format $(FILES) || exit $$?
	$(ENV_PREFIX)/black $(FILES) || exit $$?
	$(ENV_PREFIX)/mypy $(FILES) || exit $$?

.PHONY: requirements
requirements:     ## Generate requirements.txt.
	@poetry export -f requirements.txt --output requirements.txt --without-hashes --with dev
