FROM amazon/aws-lambda-python:3.11

RUN curl -O -L https://npmjs.org/install.sh
RUN sh install.sh

COPY . ${LAMBDA_TASK_ROOT}
COPY src/ ${LAMBDA_TASK_ROOT}/src
WORKDIR ${LAMBDA_TASK_ROOT}
RUN pip install --upgrade pip
RUN pip install poetry
RUN poetry install

RUN poetry run playwright install chromium --with-deps

RUN poetry export > requirements.txt
RUN pip install -r requirements.txt