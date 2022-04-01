FROM python:3.8-slim
WORKDIR /mymodel
STOPSIGNAL SIGINT
EXPOSE 80

ENV LISTEN_PORT 80

# System dependencies
RUN apt update && apt install -y python3-testresources && apt install -y libgomp1
RUN pip3 install poetry

# Project dependencies
COPY poetry.lock pyproject.toml ./

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --no-dev

COPY . .

WORKDIR /mlsegment/src
ENTRYPOINT uvicorn mlsegment.serve.serve:app --host 0.0.0.0 --port $LISTEN_PORT --workers 2