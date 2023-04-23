FROM amazon/aws-lambda-python:3.9

RUN yum install git -y
RUN pip install --user --upgrade pip
RUN pip install pipenv
COPY Pipfile .
RUN pipenv lock --clear
RUN pipenv requirements > requirements.txt
RUN pip install -r requirements.txt
COPY src/ ${LAMBDA_TASK_ROOT}/src
