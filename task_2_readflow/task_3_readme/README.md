# Task 3: Optimizing Design for Multi-Year / Multi-User Queries

## Overview

In Task 3, I optimized the existing data architecture built in previous tasks to efficiently handle larger-scale, multi-year, and multi-user queries. This involved implementing database-side optimizations and data retrieval strategies to ensure performance and manage memory limitations typical of on-premises solutions (\~128 GB).

## Technical Implementation

### Database-Side Optimizations

#### Aggregate Tables Creation

* To minimize raw data scans and improve query performance, aggregates were created in **TimescaleDB** at different granularities:

  * `data_1m`: 1-minute aggregates
  * `data_1h`: 1-hour aggregates
  * `data_1d`: 1-day aggregates

These aggregates are automatically generated daily during ingestion via scheduled tasks, ensuring timely availability for queries.

#### Automatic Interval Resolution

* Implemented backend logic to dynamically select the appropriate aggregated hypertable based on the `start_date` and `end_date` parameters provided by queries:

  * Short spans (e.g., days): `raw_data`
  * Medium spans (e.g., weeks to months): `data_1m` or `data_1h`
  * Long spans (e.g., years): `data_1d`

### Data Retrieval Strategies

#### Pagination / Chunked Fetching

* Queries that involve substantial data volumes (multiple users, extended periods) were paginated by time windows, improving memory management by streaming smaller chunks sequentially from backend to frontend.
* Implemented logic for releasing memory after each chunk processing, ensuring low memory footprint.

#### Parquet Conversion (Optional - Partially Implemented)

* Prepared initial steps by converting data into `parquet` format for future use. Although the full implementation in the querying pipeline was incomplete due to time constraints, this setup lays groundwork for enhanced data compression and columnar storage.

## Schema Details

### Aggregate Hypertable Schemas

Each aggregate hypertable (`data_1m`, `data_1h`, `data_1d`) contains:

* `timestamp`: (TIMESTAMP) - Aggregated time interval.
* `user_id`: (INTEGER) - Participant identifier.
* `metric`: (VARCHAR) - Type of metric aggregated.

Aggregates were carefully chosen to provide essential statistical summaries for rapid analysis.

## Key Decisions & Justifications

### Aggregation Strategy

* Using aggregates dramatically reduces query response times and resource consumption for large-scale data analysis.
* Different granularities (`1m`, `1h`, `1d`) provide flexibility for the dashboard, ensuring rapid retrieval without unnecessarily detailed data.

### Dynamic Interval Selection

* Ensures optimal performance by intelligently choosing the appropriate dataset based on query parameters, balancing query speed against granularity.

### Pagination

* Essential to maintain performance and stability within the memory limitations (\~128 GB) of local servers, providing scalability for multi-year and multi-user datasets.

### Parquet (Optional, Initial Setup)

* Anticipates future needs for columnar storage and further compression. Despite being partially implemented, converting data to Parquet format prepares the system for efficient scalability and future performance improvements.

## Configuration & Usage

### Running Aggregation

Aggregation scripts are automatically triggered daily via cron jobs within the Docker container environment:

```sh
docker-compose up
```

### Query Endpoint

* Maintains previous endpoint (`/data`) with enhanced backend logic to auto-select aggregation granularity.
* Supports pagination through additional query parameters:

  * `page_size`: Number of data points per chunk.
  * `page_number`: Index of the chunk to retrieve.

### Parquet Files (Setup)

* Parquet files are stored locally, structured by `user_id` and date intervals, ready for future integration.

## Possible Next Steps

* Complete integration of Parquet files into the querying pipeline.
* Further refine data retrieval strategies based on usage analytics and resource availability.
* Expand automated testing and monitoring for continuous optimization.
