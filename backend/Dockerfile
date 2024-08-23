ARG PYTHON_VERSION=3.10.14

FROM python:${PYTHON_VERSION}-slim as base

WORKDIR /wager_optimiser_backend

RUN apt-get update && \
    apt-get install -y git default-jre

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
