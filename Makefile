install:
	rm -rf Pipfile.lock
	pipenv install -d

deploy:
	cdk deploy --require-approval never

local:
	pipenv run python -m src.buy_spy