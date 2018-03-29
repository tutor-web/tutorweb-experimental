PROJECT=tutorweb

all: compile test

bin/pip:
	python3 -m venv .

lib/.requirements: requirements.txt bin/pip
	./bin/pip install -r requirements.txt
	touch lib/.requirements

compile: lib/.requirements
	./bin/pip install -e .

test: compile
	./bin/pytest

start:
	./bin/pserve development.ini

.PHONY: compile test start
