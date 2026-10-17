# Snapshot-only NEXUS Fraud dashboard. No Kaggle training, GCP credentials or paid SQL.
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    WEB_DATA_BACKEND=bigquery

WORKDIR /srv/fraud
RUN groupadd --system nexus && useradd --system --gid nexus --home-dir /srv/fraud --no-create-home nexus
COPY webapp/requirements.txt ./requirements-web.txt
RUN python -m pip install --no-cache-dir -r requirements-web.txt
COPY webapp/ ./webapp/
RUN chown -R nexus:nexus /srv/fraud
USER nexus

EXPOSE 8000
# The historical evidence endpoint never calls BigQuery or external metadata services.
HEALTHCHECK --interval=30s --timeout=4s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/evidence-status',timeout=3).close()" || exit 1

CMD ["uvicorn","webapp.main:app","--host","0.0.0.0","--port","8000","--workers","1"]
