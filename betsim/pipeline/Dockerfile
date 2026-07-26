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
COPY betsim/pipeline ./betsim/pipeline
COPY pyproject.toml ./

RUN apt-get update && \
    apt-get install -y --no-install-recommends git libgomp1 && \
    pip install --no-cache-dir --no-compile ".[pipeline]" && \
    pip uninstall -y nvidia-nccl-cu12 kaleido && \
    apt-get purge -y --auto-remove git && \
    rm -rf /var/lib/apt/lists/* && \
    useradd --create-home betsim && \
    chown -R betsim:betsim /app

USER betsim

CMD ["python", "-m", "betsim.pipeline.main"]
