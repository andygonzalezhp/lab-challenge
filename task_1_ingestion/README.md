# Task 1 – Ingestion / Write Flow

A local Docker-Compose stack that **delta-loads** 30 days of synthetic Fitbit
intraday data into a TimescaleDB hypertable once per day.

---

## 1  Architecture

task_1_ingestion/
├─ docker-compose.yml
├─ ingest/
│ ├─ Dockerfile ← Python 3.11 + cron + pandas + psycopg2
│ ├─ requirements.txt
│ └─ ingest.py ← delta-loader script (runs daily 01:00)
└─ README.md 

Volumes
├─ db-data /var/lib/postgresql/data (TimescaleDB data)
└─ ingest-state /checkpoint/last_run.json (last successful run)

Bind-mount
../task_0b/data/participant_001 → /data (flattened CSV source)


| Service | Image / Build | Purpose | Persistent store |
|---------|---------------|---------|------------------|
| **db** | `timescale/timescaledb:latest-pg15` | PostgreSQL 15 + TimescaleDB (hypertable backend) | `db-data` |
| **ingestor** | `ingest/Dockerfile` | Runs **cron**; executes `ingest.py` daily<br>`01 : 00` container time | `ingest-state` |

---

## 2  Database Schema

```sql
CREATE TABLE raw_data (
  ts          TIMESTAMPTZ NOT NULL,
  participant INT          NOT NULL,
  metric      TEXT         NOT NULL,
  value       DOUBLE PRECISION,
  PRIMARY KEY (ts, participant, metric)
);
SELECT create_hypertable(
  'raw_data',
  'ts',
  if_not_exists => TRUE
);
```

Resulting row counts after seeding 30 days of synthetic data:
metric	rows	resolution
activity	30	daily summary
azm	43 200	1-minute
br	30	daily summary
hr	2 592 000	1-second
hrv	13 248	5-minute
spo2	13 248	5-minute

##3 Running the Stack

#### inside task_1_ingestion
docker compose up -d         # build & start db + ingestor (detached)

#### one-off manual run (Git Bash needs MSYS_NO_PATHCONV=1)
MSYS_NO_PATHCONV=1 docker compose run --rm ingestor \
  python /app/ingest.py

Console output on first load:
```sql
Ingested 30 rows → activity
Ingested 43,200 rows → azm
Ingested 30 rows → br
Ingested 2,592,000 rows → hr
Ingested 13,248 rows → hrv
Ingested 13,248 rows → spo2
ingestion complete
```

#### Verify counts:

docker compose exec db psql -U postgres -d wearables -c "
SELECT metric, COUNT(*) AS rows
FROM   raw_data
GROUP  BY metric
ORDER  BY metric;"

## 4 Resetting / Re-ingesting
Light reset – keep DB, rerun from CSVs

MSYS_NO_PATHCONV=1 docker compose exec ingestor \
  rm -f /checkpoint/last_run.json       # delete checkpoint
MSYS_NO_PATHCONV=1 docker compose run --rm ingestor \
  python /app/ingest.py                 # reload everything

Full reset – wipe DB and checkpoint

docker compose down -v      # drops db-data & ingest-state volumes
docker compose up -d        # fresh cluster
MSYS_NO_PATHCONV=1 docker compose run --rm ingestor python /app/ingest.py

## 5 Why TimescaleDB?

    PostgreSQL ecosystem – standard SQL, extensions, psql, pgAdmin.

    Hypertables & chunking – automatic partitioning by time + space.

    Compression – ⬇︎ 90 % storage reduction on production IoT workloads.

    Continuous aggregates – ready for Task 3 down-sampling (1 min / 1 h / 1 d).

    Prometheus exporter – integrates cleanly into Task 5 monitoring stack.