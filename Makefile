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
	@virtualenv -p python3 .venv
	@poetry install
	@pipenv install --dev
	@pipenv run pre-commit install

.PHONY: run
run:              ## Run the project.	
	$(ENV_PREFIX)/gunicorn -c gunicorn.conf.py

.PHONY: lint
lint:             ## Run pep8, black, mypy linters.
	$(ENV_PREFIX)/ruff check $(FILES) || exit $$?
	$(ENV_PREFIX)/black --check $(FILES) || exit $$?
	$(ENV_PREFIX)/mypy $(FILES) || exit $$?