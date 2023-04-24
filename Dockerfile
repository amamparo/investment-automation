FROM python:3.9-alpine

RUN pip install pipenv
COPY Pipfile .
RUN pipenv lock --clear
RUN pipenv requirements > requirements.txt
RUN pip install -r requirements.txt
COPY src src
