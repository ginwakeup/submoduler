FROM python:3.10-slim as base

COPY . /app
WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y curl build-essential

ENV PYTHONPATH=${PYTHONPATH}:${PWD}
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

RUN curl -sSL https://install.python-poetry.org | python

RUN poetry config virtualenvs.create false

RUN apt-get update
RUN apt-get install git -y

FROM base as prod

RUN poetry install --no-dev
CMD python submoduler/main.py
