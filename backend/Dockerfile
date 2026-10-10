FROM python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    RUFF_CACHE_DIR=/tmp/ruff-cache

WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --require-hashes -r backend/requirements.txt

ARG LOCAL_UID=1000
ARG LOCAL_GID=1000
RUN groupadd --gid "${LOCAL_GID}" app \
    && useradd --uid "${LOCAL_UID}" --gid "${LOCAL_GID}" --create-home app

COPY --chown=app:app backend /app/backend
COPY --chown=app:app frontend /app/frontend
COPY --chown=app:app scripts /app/scripts
COPY --chown=app:app pyproject.toml /app/pyproject.toml

USER app
EXPOSE 8000
CMD ["sh", "/app/scripts/start-dev.sh"]
