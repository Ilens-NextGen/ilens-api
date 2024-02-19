.ONESHELL:
ENV_PREFIX=.venv/bin
FILES="."
NUM_LINES=1
BK=backend
LB=loadbalancer


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
	python ilens/start.py

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

.PHONY: live_logs
live_logs:        ## Show live logs.
	@pyinfra --quiet --limit $(BK) ilens/ilens/manager/hosts.py exec -- tail -fn $(NUM_LINES) '~/projects/ilens-api/ilens_server.log'

.PHONY: deploy_web
deploy_web:           ## Deploy the project.
	@pyinfra --limit $(BK) --quiet ilens/manager/hosts.py ilens/manager/deploy_web.py

.PHONY: health_check
health_check:           ## Check the health of the project.
	@pyinfra --quiet --limit $(BK) ilens/manager/hosts.py exec -- curl -s 0:8000

.PHONY: stop_server
stop_server:           ## Stop the server.
	@pyinfra --quiet --limit $(BK) ilens/manager/hosts.py exec -- service ilens stop

.PHONY: start_server
start_server:           ## Start the server.
	@pyinfra --quiet --limit $(BK) ilens/manager/hosts.py exec -- service ilens start

.PHONY: deploy_loadbalancer
deploy_loadbalancer:           ## Deploy the loadbalancer.
	@pyinfra --limit $(LB) ilens/manager/hosts.py ilens/manager/deploy_haproxy.py

.PHONY: stop_loadbalancer
stop_loadbalancer:           ## Stop the loadbalancer.
	@pyinfra --quiet --limit $(LB) ilens/manager/hosts.py exec -- service haproxy stop

.PHONY: start_loadbalancer
start_loadbalancer:           ## Start the loadbalancer.
	@pyinfra --quiet --limit $(LB) ilens/manager/hosts.py exec -- service haproxy start