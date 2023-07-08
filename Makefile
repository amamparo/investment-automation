install:
	rm -rf Pipfile.lock
	pipenv install -d

deploy:
	cdk deploy --require-approval never

run:
	poetry run python -m src.main

check: lint test

lint:
	poetry run pylint src aws

test:
	poetry run python -m unittest discover -s src -p '*_test.py'
