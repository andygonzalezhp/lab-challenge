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
