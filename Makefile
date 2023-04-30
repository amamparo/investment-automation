install:
	rm -rf Pipfile.lock
	pipenv install -d

deploy:
	cdk deploy --require-approval never

update_watchlist:
	pipenv run python -m src.update_watchlist