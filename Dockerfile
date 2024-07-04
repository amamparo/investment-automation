FROM amazon/aws-lambda-python:3.11


COPY . ${LAMBDA_TASK_ROOT}

RUN yum update -y
RUN yum install -y wget tar gcc
RUN ./install_glibc.sh

COPY src/ ${LAMBDA_TASK_ROOT}/src
WORKDIR ${LAMBDA_TASK_ROOT}
RUN pip install --upgrade pip
RUN pip install poetry
RUN poetry install

RUN poetry run playwright install chromium --with-deps

RUN poetry export > requirements.txt
RUN pip install -r requirements.txt