ARG PYTHON_VERSION=3.10.14

FROM python:${PYTHON_VERSION}-slim as base

WORKDIR /wager_optimiser_frontend

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
