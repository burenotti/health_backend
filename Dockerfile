FROM python:3.11-slim AS base

ENV PATH="/poetry-venv/bin:${PATH}"

SHELL ["/bin/bash", "-c"]

RUN apt-get -y update \
    && python -m venv /poetry-venv \
    && source /poetry-venv/bin/activate \
    && pip install poetry

ADD pyproject.toml /project/pyproject.toml

WORKDIR /project

RUN poetry config virtualenvs.in-project true \
    && poetry lock \
    && poetry install --only main

ENV PATH="/poetry-venv/bin:${PATH}"

ADD pyproject.toml poetry.lock /project/

WORKDIR /project

RUN apt-get -y update \
    && apt-get -y upgrade \
    && poetry config virtualenvs.in-project true \
    && poetry config virtualenvs.options.no-pip true \
    && poetry config virtualenvs.options.no-setuptools true \
    && poetry install --only main --no-root

ADD . /project/

RUN poetry install

FROM gcr.io/distroless/python3-debian12:nonroot

COPY --from=base /project/.venv/lib/python3.11/site-packages/ /home/nonroot/.local/lib/python3.11/site-packages/

ADD src /project/src/

CMD ["-m", "health", "--config", "./config/config.yaml"]
