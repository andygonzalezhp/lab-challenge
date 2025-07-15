#  Quickstart Guide

This guide walks you through cloning the repo and launching eveything from initial ingestion of synthetic data to the full monitoring stack (Prometheus, Grafana, Alertmanager).

## Preliminary Information
This repo is structured like the following:
- lab-challenge/task_0a holds task 0a.
- lab-challenge/task_0b holds task 0b.
- lab-challenge/task_1_ingestion holds task 1.
- lab-challenge/task_2_ingestion started off as just task 2, but currently holds the most recent updated version, which is task 5. Thus you can find the README's for task's 2 through 5 within this folder.
- lab-challenge/task_6_diagram holds task 6.
- You can find screenshots of the application in the screenshots folder

---

## Prerequisites

- **Docker & Docker Compose v2**
- **Git & Git LFS**

Install instructions:

- [Docker Desktop](https://docs.docker.com/desktop/)
- [Git](https://git-scm.com/downloads)
- [Git LFS](https://git-lfs.com/)

Enable Git LFS after installation:
```bash
git lfs install
```

## Step 1: Clone the Repository & Get Synthetic Data
```bash
git clone https://github.com/andygonzalezhp/lab-challenge.git
cd lab-challenge

# Ensure large synthetic files are downloaded via Git LFS
git lfs pull
```
## Step 2: Initial Synthetic Data Ingestion (Task 1)

### Run from task_1_ingestion/
```bash
cd task_1_ingestion

# Build the ingestion image
docker compose build

# Run ingestion script once (loads synthetic CSV data into TimescaleDB)
docker compose run --rm ingestor \
  bash -c "python /app/ingest.py"

# Verify data was loaded
docker compose exec db psql -U postgres \
  -c "SELECT metric, COUNT(*) FROM raw_data GROUP BY metric;"

# Stop ingestion containers
docker compose down

cd ..
```

## Step 3: Launch Backend, Frontend, and Monitoring (Task 2-5)

### Run from task_2_readflow/
```bash
cd task_2_readflow

# Build and start the full stack (FastAPI, React, Prometheus, Grafana, Alertmanager)
docker compose up -d --build
```

### Verify all containers are up:
```bash
docker compose ps
```


## Step 4: Verify Everything is Running

| Service | URL |
| -------- | ------- |
| React Frontend | http://localhost:3000 |
| FastAPI Docs | http://localhost:8000/docs |
| Prometheus | http://localhost:9090 |
| AlertManager | http://localhost:9093
| Grafana | http://localhost:3001
| Mailhog (SMTP) | http://localhost:8025

Note: The credentials for Grafana are admin/admin


## And that's all! Your set.