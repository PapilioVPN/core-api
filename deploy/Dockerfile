ARG PYTHON_IMAGE=python:3.13-slim@sha256:8d9d0b8bcf6506481eae4907c18f5e3e7902e629f5f6d684f9e7c32e85e3ddf0
FROM ${PYTHON_IMAGE} AS build
WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir '.[tasks]' && /opt/venv/bin/pip check

FROM ${PYTHON_IMAGE}
LABEL org.opencontainers.image.source="https://github.com/PapilioVPN/core-api"
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY --from=build /opt/venv /opt/venv
COPY migrations ./migrations
COPY scripts/seeders ./scripts/seeders
COPY alembic.ini config.yml.sample ./
COPY deploy/configure.py deploy/healthcheck.py ./
RUN install -d -m 0700 -o 10001 -g 10001 /app/var/media /app/var/tmp
USER 10001:10001
CMD ["papilio", "run"]
HEALTHCHECK --interval=5s --timeout=4s --start-period=5s --retries=12 CMD ["python", "/app/healthcheck.py"]
