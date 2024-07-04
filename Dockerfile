FROM amazon/aws-lambda-python:3.12

RUN curl -o apt.deb http://security.ubuntu.com/ubuntu/pool/main/a/apt/apt_1.0.1ubuntu2.17_amd64.deb
RUN dpkg -i apt.deb

COPY . ${LAMBDA_TASK_ROOT}
COPY src/ ${LAMBDA_TASK_ROOT}/src
WORKDIR ${LAMBDA_TASK_ROOT}
RUN pip install --upgrade pip
RUN pip install poetry
RUN poetry install
RUN poetry run playwright install chromium

RUN poetry export > requirements.txt
RUN pip install -r requirements.txt