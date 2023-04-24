install:
	rm -rf Pipfile.lock
	pipenv install -d

deploy:
	cdk deploy --require-approval never

enqueue_underlyings:
	pipenv run python -m src.enqueue_underlyings