PROJECT=tutorweb

all: compile test lint

bin/pip:
	python3 -m venv .

lib/.requirements: requirements.txt requirements-to-freeze.txt setup.py bin/pip
	# Install frozen requirements
	./bin/pip install -r requirements.txt
	# Make sure any new requirements are available
	./bin/pip install -r requirements-to-freeze.txt
	# Freeze the output at current state
	./bin/pip freeze | grep -v egg=tutorweb_quizdb > requirements.txt
	touch lib/.requirements

compile: lib/.requirements

test: compile
	./bin/pytest tests/

lint: lib/.requirements
	./bin/flake8 --ignore=E501 tutorweb_quizdb/ tests/

coverage: compile
	./bin/coverage run ./bin/py.test tests/
	./bin/coverage html
	ln -rs htmlcov ../client/www/htmlcov
	echo Visit http://...//htmlcov/index.html

start: compile ../install.sh ../.local-conf
	(cd .. && ./install.sh --exec server/bin/pserve server/application.ini)

.PHONY: compile test start
