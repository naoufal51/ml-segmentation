FROM python:3.8-slim
WORKDIR /mlsegment
STOPSIGNAL SIGINT
EXPOSE 80

ENV LISTEN_PORT 80

# System dependencies
RUN apt update && apt install -y libgomp1
RUN pip3 install poetry

# Project dependencies
COPY poetry.lock pyproject.toml ./

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --no-dev

COPY . .

WORKDIR /mlsegment/src
ENTRYPOINT uvicorn mlsegment.serve.__main__:app --host 0.0.0.0 --port $LISTEN_PORT --workers 2