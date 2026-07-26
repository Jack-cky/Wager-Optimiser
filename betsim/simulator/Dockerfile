FROM python:3.12.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /app

COPY config/config.toml ./config/config.toml
COPY betsim/shared ./betsim/shared
COPY betsim/simulator ./betsim/simulator
COPY pyproject.toml ./

RUN pip install --no-cache-dir --no-compile ".[simulator]" && \
    useradd --create-home betsim && \
    chown -R betsim:betsim /app

USER betsim

EXPOSE 5000

CMD ["taipy", "run", "betsim/simulator/main.py"]
