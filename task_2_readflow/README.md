# Task 2 – Access / Read Flow

This module implements **Task 2** of the Stanford Challenge: building a data flow model from a locally hosted TimescaleDB into a simple dashboard app for analysis and visualization.

---

## Overview


* **Inputs:** Synthetic Fitbit data (from Task 1 ingestion) in a `raw_data` hypertable.
* **Outputs:**

  * A Docker Compose stack running TimescaleDB, FastAPI, and React dashboard.
  * An HTTP API (`/data`) that returns time-series data.
  * A browser-based UI to plot metrics over a date range.

---

## Architecture

```text
+-----------+       +-------------+       +---------------------+
| timescaledb| <---> |  FastAPI   | <---> | React + Recharts UI |
| (raw_data) |       |  Backend   |       | (Dashboard)         |
+-----------+       +-------------+       +---------------------+
```

* **TimescaleDB**: stores raw intraday data in a hypertable `raw_data(ts, participant, metric, value)`.
* **FastAPI**: provides `/health` and `/data` endpoints to read from TimescaleDB.
* **React Dashboard**: allows selecting `start_date`, `end_date`, `metric`, `user_id`, and renders a line chart.

---

## Tech Stack

| Layer         | Technology               | Purpose                                   |
| ------------- | ------------------------ | ----------------------------------------- |
| Database      | TimescaleDB (PostgreSQL) | Hypertable storage, native compression    |
| API           | FastAPI + psycopg2       | HTTP endpoints, Swagger UI, CORS handling |
| Front-end     | React + Recharts         | Declarative UI, simple line charts        |
| Orchestration | Docker Compose (v3.9+)   | Single command to spin up all services    |

---

##  Getting Started

### Prerequisites

* Docker & Docker Compose installed on your machine.
* Completed **Task 1** ingestion so that the volume `task_1_ingestion_db-data` (or your named volume) contains \~1 month of `raw_data`.

### 1. Clone & Switch to Branch

```bash
cd ~/path/to/lab-challenge
git fetch origin
git checkout feat/task-2-readflow
```

### 2. Seed the Database (if needed)

If you are using a **new** volume:

```bash
# Run the Task 1 ingestion container once to populate data
docker compose -f task_1_ingestion/docker-compose.yml up ingestion --abort-on-container-exit
```

Otherwise, Task 2’s compose will mount the existing volume.

### 3. Launch the Stack

```bash
cd task_2_readflow
docker compose up --build
```

* **TimescaleDB** ⇒ `localhost:5432`
* **FastAPI** ⇒ `http://localhost:8000/docs` (interactive Swagger UI)
* **Dashboard** ⇒ `http://localhost:3000`

---

## Environment Variables

| Variable     | Default     | Description                        |
| ------------ | ----------- | ---------------------------------- |
| `PGHOST`     | `db`        | TimescaleDB host in Docker network |
| `PGPORT`     | `5432`      | TimescaleDB port                   |
| `PGUSER`     | `postgres`  | DB user                            |
| `PGPASSWORD` | `postgres`  | DB password                        |
| `PGDATABASE` | `wearables` | Database name                      |

You can override these in a `.env` file placed in `task_2_readflow/`.

---

## API Reference

### Health Check

```
GET /health
```

**Response**

```json
{ "status": "ok" }
```

---

### Fetch Time-Series Data

```
GET /data
```

**Query Parameters**

| Name         | Type     | Required | Description                                         |
| ------------ | -------- | -------- | --------------------------------------------------- |
| `start_date` | `date`   | Yes      | ISO date, inclusive (YYYY-MM-DD)                    |
| `end_date`   | `date`   | Yes      | ISO date, inclusive                                 |
| `metric`     | `string` | Yes      | One of `hr`, `azm`, `br`, `hrv`, `spo2`, `activity` |
| `user_id`    | `int`    | No       | Participant ID (default: `1`)                       |

**Response Model**: `TSResponse`

```json
{
  "timestamps": ["2024-01-01T00:00:00+00:00", ...],
  "values": [80.1, ...]
}
```

**Examples**

```bash
# via curl
curl "http://localhost:8000/data?start_date=2024-01-01&end_date=2024-01-07&metric=hr&user_id=1"
```

---

## Dashboard Usage

1. Open your browser at `http://localhost:3000`.
2. Select a **Metric** (e.g. `hr` for heart rate).
3. Enter a **User ID** (`1` by default).
4. Pick **Start** and **End** dates (e.g. `2024-01-01` → `2024-01-07`).
5. Click **Load**.
6. The line chart will render the time-series values for the selected range.

---

## Database Schema

Ensure your `raw_data` table is defined as:

```sql
CREATE TABLE raw_data (
  ts          TIMESTAMPTZ NOT NULL,
  participant INT         NOT NULL,
  metric      TEXT        NOT NULL,
  value       DOUBLE PRECISION,
  PRIMARY KEY (ts, participant, metric)
);

-- Convert to a hypertable
SELECT create_hypertable('raw_data', 'ts');
```

---

## 🔧 Troubleshooting

* **API 404 "no data"**: Verify your date range and metric match existing rows.
* **Port conflicts**: Ensure no other service is using ports `5432`, `8000`, or `3000`.
* **CORS errors**: FastAPI is configured with `allow_origins=["*"]` for development.

---

## Task 3 – Optimizing Design for Multi-Year / Multi-User Queries

In this task, we enhance scalability and performance for large date-range and multi-user queries by leveraging TimescaleDB continuous aggregates and smart API routing.

###  Requirements Mapping

| Requirement                                      | Implementation Summary                                                                    |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| Create precomputed summaries (1m, 1h, 1d)        | Defined `data_1m`, `data_1h`, `data_1d` continuous aggregates in `aggregates.sql`.        |
| Refresh aggregates daily at ingestion time       | Added `add_continuous_aggregate_policy` for each view to schedule hourly/daily refreshes. |
| Auto-select appropriate table based on date span | Implemented `choose_table()` in `main.py` to route to raw or aggregated tables.           |

###  Continuous Aggregates Definition

**File:** `backend/sql/aggregates.sql`

```sql
-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 1-minute aggregate
CREATE MATERIALIZED VIEW IF NOT EXISTS data_1m
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 minute', ts) AS bucket,
  participant,
  metric,
  AVG(value) AS value
FROM raw_data
GROUP BY bucket, participant, metric;

-- 1-hour aggregate
CREATE MATERIALIZED VIEW IF NOT EXISTS data_1h
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 hour', ts) AS bucket,
  participant,
  metric,
  AVG(value) AS value
FROM raw_data
GROUP BY bucket, participant, metric;

-- 1-day aggregate
CREATE MATERIALIZED VIEW IF NOT EXISTS data_1d
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 day', ts) AS bucket,
  participant,
  metric,
  AVG(value) AS value
FROM raw_data
GROUP BY bucket, participant, metric;

-- Continuous aggregate refresh policies
SELECT add_continuous_aggregate_policy('data_1m',
  start_offset      => INTERVAL '1 day',
  end_offset        => INTERVAL '1 hour',
  schedule_interval => INTERVAL '1 hour');

SELECT add_continuous_aggregate_policy('data_1h',
  start_offset      => INTERVAL '7 days',
  end_offset        => INTERVAL '1 day',
  schedule_interval => INTERVAL '6 hours');

SELECT add_continuous_aggregate_policy('data_1d',
  start_offset      => INTERVAL '30 days',
  end_offset        => INTERVAL '7 days',
  schedule_interval => INTERVAL '1 day');
```

###  Backend Routing Logic

**File:** `backend/main.py`

```python
from datetime import timedelta

def choose_table(start_date, end_date):
    diff = end_date - start_date
    if diff <= timedelta(days=1):
        return 'raw_data', 'ts'
    if diff <= timedelta(days=7):
        return 'data_1m', 'bucket'
    if diff <= timedelta(days=30):
        return 'data_1h', 'bucket'
    return 'data_1d', 'bucket'

@app.get('/data', response_model=TSResponse)
def get_data(start_date: date, end_date: date, metric: str, user_id: int = 1):
    table, ts_col = choose_table(start_date, end_date)
    sql = f"""
    SELECT {ts_col} AS ts, value
    FROM {table}
    WHERE {ts_col} BETWEEN %s AND %s
      AND participant = %s
      AND metric = %s
    ORDER BY {ts_col}
    """
    params = (start_date, end_date + timedelta(days=1), user_id, metric)
    # execute and return results as before
```

###  Testing Instructions

1. **Verify views exist:**

   ```sql
   \dv
   ```
2. **Smoke-test endpoint for various ranges:**

   ```bash
   # 2-day (raw_data)
   curl 'http://localhost:8000/data?start_date=2024-01-01&end_date=2024-01-02&metric=hr'

   # 7-day (data_1m)
   curl 'http://localhost:8000/data?start_date=2024-01-01&end_date=2024-01-08&metric=hr'

   # 30-day (data_1h)
   curl 'http://localhost:8000/data?start_date=2024-01-01&end_date=2024-01-30&metric=hr'

   # 90-day (data_1d)
   curl 'http://localhost:8000/data?start_date=2024-01-01&end_date=2024-04-01&metric=hr'
   ```
3. **Confirm result counts** match expected bucket sizes (sec/min/hr/day).

---
