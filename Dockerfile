FROM amazon/aws-lambda-python:3.10

COPY pyproject.toml .
RUN pip install --upgrade pip
RUN pip install poetry
RUN poetry export -f requirements.txt > requirements.txt
RUN pip install -r requirements.txt
COPY src/ ${LAMBDA_TASK_ROOT}/src