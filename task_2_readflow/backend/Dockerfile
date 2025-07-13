FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y build-essential libpq-dev postgresql-client \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY sql/aggregates.sql /migrations/aggregates.sql

COPY . .

EXPOSE 8000

CMD ["bash", "-c", \
  "psql postgresql://$PGUSER:$PGPASSWORD@$PGHOST:$PGPORT/$PGDATABASE -f /migrations/aggregates.sql && \
   uvicorn main:app --host 0.0.0.0 --port 8000"]
