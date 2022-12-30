.PHONY: test lint format run

test:
	python -m pytest -vv

lint:
	flake8 main.py

format:
	isort -rc main.py
	black main.py

run:
	functions-framework --target=main --debug

install:
	pip install -r requirements.txt


install-dev:
	pip install -r requirements-dev.txt

install-all: install install-dev
