# Task 5: Monitoring / Alerting

## Overview

In Task 5, we established a comprehensive monitoring and alerting infrastructure to ensure observability, reliability, and proactive identification of performance or operational issues within the data pipeline and dashboard application.

## Technical Implementation

### Monitoring Stack

Built a robust monitoring stack with the following components orchestrated via **Docker Compose**:

* **Prometheus:** Metrics collection.
* **Grafana:** Visualization and dashboarding.
* **AlertManager:** Alerting and notifications.
* **Node Exporter:** Host-level metrics collection (CPU, memory, disk).
* **cAdvisor:** Container-level metrics collection.

### Metrics Collection and Exposition

* Integrated **Prometheus client libraries**:

  * Backend metrics exposed via `/metrics` endpoint.
  * Host-level metrics captured through Node Exporter.
  * Container metrics gathered using cAdvisor.
* **Scrape intervals** set at regular intervals (\~15 seconds) in Prometheus.

### Alerting with AlertManager

* Configured alerting rules (`rules.yml`) to monitor critical conditions:

  * Example alerts include high latency, ingestion errors, and backend failures.
* Alert notifications sent to the defined email endpoint (`admin@wearipedia.com`) via SMTP, with appropriate labels such as `severity="critical"`.
* Implemented alert grouping and inhibition rules to prevent redundant alerts.

### Dashboarding with Grafana

* Prometheus integrated as the primary data source within Grafana.
* Imported and customized community dashboards such as **Node Exporter Full** and **Docker Monitoring** to effectively monitor and visualize system performance and resource usage.
* Dashboard panels highlight metrics including CPU usage, RAM usage, network traffic, disk usage, ingestion latency, and error rates.

## Configuration & Schema

### Docker Compose Configuration

A single `docker-compose.yml` file manages the full stack, including:

* Prometheus (`http://localhost:9090`)
* Grafana (`http://localhost:3000`)
* AlertManager (`http://localhost:9093`)
* Node Exporter (`http://localhost:9100`)
* cAdvisor (`http://localhost:8080`)

Volumes mounted for persistence:

* Prometheus data
* Grafana data

### Prometheus Scrape Targets

Configured to scrape:

* Backend (`/metrics`)
* Node Exporter (`/metrics`)
* cAdvisor (`/metrics`)
* AlertManager (`/metrics`)

## Key Decisions & Justifications

### Modular Docker Compose Setup

* Ensures portability and easy deployment, with modular services that can individually scale or relocate if needed.

### Comprehensive Metric Collection

* Provides extensive visibility into application, host, and container health, critical for proactive maintenance and reliability.

### Email-based Alerting

* Chosen for simplicity and direct notification to responsible stakeholders, ensuring quick response to critical conditions.
* Email SMTP implementation is shown with Mailhog.

### Grafana Visualization

* Leveraged existing community dashboards for efficient setup and immediate value.
* Easily customizable to address specific KPI tracking relevant to the application's operations.

## Usage Instructions

### Launch Monitoring Stack

```sh
docker-compose up
```

### Access Points

* **Grafana Dashboard:** `http://localhost:3000`
* **Prometheus UI:** `http://localhost:9090`
* **AlertManager UI:** `http://localhost:9093`

### Alert Configuration

* Edit `rules.yml` to modify alerting conditions.
* Edit `alertmanager.yml` to adjust notification receivers or rules.

## Validation

* Successfully validated Prometheus scrape targets.
* Verified AlertManager's notification capability and alert firing mechanisms.
* Grafana dashboards operational and displaying accurate metrics.

## Possible Future Improvements

* Integration of additional custom metrics relevant to clinical trial use cases.
* Expansion to alternative notification channels (e.g., Slack, PagerDuty) for faster stakeholder response.
* Automatic dashboard provisioning for simplified deployment in varied environments.
* Enhanced log aggregation (e.g., Elasticsearch or Loki) integration for improved diagnostics and issue resolution.
