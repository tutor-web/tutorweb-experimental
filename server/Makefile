PROJECT=tutorweb

all: compile test lint

bin/pip:
	python3 -m venv .

lib/.requirements: requirements.txt bin/pip
	./bin/pip install -r requirements.txt
	touch lib/.requirements

compile: lib/.requirements
	./bin/pip install -e .
	./bin/pip install -e . ".[testing]"

test: compile
	./bin/pytest tests/

lint: lib/.requirements
	./bin/flake8 --ignore=E501 tutorweb_quizdb/ tests/

start:
	./bin/pserve development.ini

.PHONY: compile test start
