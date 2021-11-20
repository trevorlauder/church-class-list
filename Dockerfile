FROM python:3.10.0-slim AS base

ENV PIP_NO_CACHE_DIR=off \
    PYTHONDONTWRITEBYTECODE=1


FROM base as poetry

RUN python -m pip install poetry~=1.1


FROM poetry AS build

COPY pyproject.toml poetry.lock /

RUN python -m venv .venv
RUN poetry install --no-root --no-dev

COPY church_class_list/run.py /app/run.py


FROM base AS final

COPY --from=build .venv .venv
COPY --from=build app app

WORKDIR /app

CMD [ "../.venv/bin/python", "-u", "./run.py" ]
