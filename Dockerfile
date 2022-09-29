FROM python:3.10-alpine

COPY . /app
WORKDIR /app

RUN python -m pip install -r requirements/common.txt

RUN apk update
RUN apk add git

CMD python submoduler/main.py
