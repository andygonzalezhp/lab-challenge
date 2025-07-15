# Task 2: Access / Read Flow

## Overview

In this task, I built a data flow model connecting a locally hosted TimescaleDB (a PostgreSQL extension optimized for time-series data) to a frontend dashboard application for visualization and analysis. The goal was to create a simple yet robust architecture to support querying and visualizing wearable data, specifically data from a Fitbit device.

## Technical Implementation

### Provisioning Local Resources

* **Database**: Utilized the existing TimescaleDB service configured during Task 1 to store approximately 1 month of Fitbit synthetic data.
* **Schema Initialization**: On container start, an initialization script is executed to create a hypertable named `raw_data` for optimized time-series performance.

### Schema Definition

The `raw_data` hypertable schema includes:

* `timestamp`: (TIMESTAMP) - Time of data capture, used for partitioning the hypertable.
* `user_id`: (INTEGER) - Participant identifier.
* `metric`: (VARCHAR) - Type of metric (e.g., heart\_rate, steps).
* `value`: (FLOAT) - Metric value.

Hypertables were chosen due to their efficiency in handling time-series data queries and scalability with time-based partitioning.

### Backend Infrastructure

* **Language & Framework**: Backend infrastructure built using **Python** and **FastAPI** for its simplicity, efficiency, and modern features such as automatic documentation and validation.
* **Database Connection**: Used the `psycopg2` library to establish connections to the TimescaleDB database.
* **Endpoint**: Implemented a single HTTP endpoint (`/data`) designed to receive queries directly from the frontend. The endpoint accepts parameters:

  * `start_date`
  * `end_date`
  * `user_id`
  * `metric`
* Robust error handling was implemented to manage cases where any required parameters are missing or invalid, ensuring stability and reliability.

### Frontend Application

* Built using **React.js** for its flexibility and rapid UI development capabilities.
* Provides a simple UI allowing users to select:

  * `start_date`
  * `end_date`
  * `user_id`
* Fetches data asynchronously from the backend API and visualizes the result in a line chart using **Recharts**.
* Chose minimal complexity in the frontend to emphasize clarity of the data flow, keeping focus on the backend logic.

### Containerization

* **Docker Compose** used to orchestrate the local environment setup seamlessly, managing both TimescaleDB and the FastAPI backend.

## Key Decisions & Justifications

### Technology Choices

* **TimescaleDB**:

  * Selected for superior time-series performance, native PostgreSQL compatibility, and robust data compression and querying capabilities.

* **FastAPI**:

  * Chosen for its performance, ease of use, automatic documentation generation, and efficient validation of incoming request data.

* **React.js**:

  * Selected due to familiarity, strong community support, and flexibility in managing UI states and rendering complex data visualizations.

### Database Schema

* Designed schema to be minimalist and efficient, directly reflecting the necessary query parameters and data granularity.

### Error Handling

* Implemented extensive error-checking mechanisms to ensure robustness and clear user feedback, particularly important given the potential for incomplete query requests.

### Frontend Simplicity

* Aimed to clearly demonstrate data flow and integration between backend and frontend without distraction by unnecessary UI complexity, laying a foundation that can be iteratively expanded upon in subsequent tasks.

## Configuration & Usage

### Running the Application

1. Clone the repository and navigate to the task directory.
2. Run the containers:

```sh
docker-compose up
```

### API Endpoint

* Endpoint: `/data`
* Method: GET
* Parameters required:

  * `start_date` (YYYY-MM-DD)
  * `end_date` (YYYY-MM-DD)
  * `user_id` (integer)
  * `metric` (string, e.g., 'hr')

### Accessing the Frontend

* Navigate to `http://localhost:3000` to interact with the visualization dashboard.
* Navigate to `http://localhost:8000/docs` to see the FastAPI docs. 

## Possible Next Steps

* Enhanced database optimizations for multi-user and long-term data queries.
* Expanded frontend capabilities and visualization options.
* Implementing comprehensive monitoring and alerting for improved system reliability.
