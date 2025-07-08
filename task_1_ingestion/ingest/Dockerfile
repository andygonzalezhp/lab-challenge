FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY cronjob /etc/cron.d/ingest-cron
COPY ingest.py .
RUN chmod 0644 /etc/cron.d/ingest-cron && crontab /etc/cron.d/ingest-cron
CMD ["cron", "-f"]
