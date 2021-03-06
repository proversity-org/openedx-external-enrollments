###############################################
#
# External Enrollments commands.
#
###############################################

.DEFAULT_GOAL := help

help: ## display this help message
	@echo "Please use \`make <target>' where <target> is one of"
	@grep '^[a-zA-Z]' $(MAKEFILE_LIST) | sort | awk -F ':.*?## ' 'NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

clean: ## delete most git-ignored files
	find . -name '__pycache__' -exec rm -rf {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

requirements: ## install environment requirements
	pip install -r requirements.txt

upgrade: ## update the requirements/*.txt files with the latest packages satisfying requirements/*.in
	pip install -q pip-tools
	pip-compile --upgrade -o requirements/base.txt requirements/base.in
	pip-compile --upgrade -o requirements/test.txt requirements/test.in

quality: clean ## check coding style with pycodestyle and pylint
	pycodestyle ./openedx_external_enrollments
	pylint ./openedx_external_enrollments --rcfile=./setup.cfg
	isort --check-only --recursive --diff ./openedx_external_enrollments

test_python: clean ## Run test suite.
	pip install -r requirements/test.txt --exists-action w
	coverage run --source ./openedx_external_enrollments manage.py test
	coverage report -m --fail-under=83

validate_python: test_python quality
