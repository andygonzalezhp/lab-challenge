# Task 0.a - Data Volume Estimation

## 1. Data points estimation for Fitbit (1 second resolution, 4 metrics, 1 year)

### a. Number of data points:

* **For n=1:**

  * 31,536,000 seconds/year × 4 metrics = **126,144,000** points/year.
* **For n=1,000:**

  * 126,144,000 × 1,000 = **126,144,000,000** points/year.
* **For n=10,000:**

  * 126,144,000 × 10,000 = **1,261,440,000,000** points/year.

### b. Data points over multiple years (single participant):

* **1 year:** 126,144,000 points
* **2 years:** 252,288,000 points
* **5 years:** 630,720,000 points

---

## 2. Storage requirements for data points (3 metrics, 1 second resolution, 2 years, n=1,000)

### a. Uncompressed:

* Data points: 31,536,000 sec/year × 2 years × 3 metrics × 1,000 participants = **189,216,000,000 points**
* Assuming 16 bytes per data point (PostgreSQL):

  * It would be around **\~3.03 TB**

### b. Compressed (conservative 80% compression, e.g., TimescaleDB):

* **\~0.61 TB (608 GB)**

### i. Compression Efficiency:

* Time-series databases (like TimescaleDB) use techniques such as delta-of-deltas, run-length encoding (RLE), and Gorilla compression, making them highly efficient for data with repetitive or slowly varying values.

* Compression is less effective with high-entropy data (random or highly irregular data).

* Health data from Fitbit (heart rate, steps, sleep patterns, etc.) is highly compressible due to regular intervals and slowly changing values.

---

## 3. Realistic Metrics and Volumes for a Physical Activity & Sleep Study (1 year, n=1,000)

### a. Metrics and their highest frequency:

* **Heart rate:** every 1 second (31,536,000 points/year)
* **Steps:** every 1 minute (525,600 points/year)
* **SpO₂:** every 1 minute (525,600 points/year)
* **HRV (RMSSD):** every 5 minutes (105,120 points/year)

### b. Total Data Points for n=1,000 (1 year):

* (31,536,000 + 525,600 + 525,600 + 105,120) × 1,000 = **32,692,320,000 points**

* Uncompressed (16 bytes per point):

  * **\~523 GB**

### c. Compressed volume (assuming 80% compression):

* **\~104.6 GB**

---

## 4. Some Strategies to Optimize Query Costs:

* **Multi-resolution aggregates:** we can pre-compute aggregates (1-minute, 5-minute, hourly, daily) to reduce resolution for faster queries.
* **Chunked Pagination:** retrieve data in smaller segments to manage memory.
* **Columnar storage:** store historical data (beyond 90 days) in columnar formats (Parquet/ORC) on NAS.
* **Covering Indexes:** use indexes on participant ID and timestamp to speed queries.

---

## 5. Scaling Considerations

### a. Vertical Scaling Limits (single machine):

* **CPU:** dual-socket AMD EPYC processors (up to 128 vCPUs total)
* **Memory:** 256-512 GB DDR5 RAM
* **Storage:** up to \~64 TB SSD/NVMe (RAID configurations). But I think at least 16TB data. Also should probably be an SSD (for speed).
* **Network:** 25 GbE

### b. Horizontal Scaling Considerations (not cloud-based):

* **Data partitioning (sharding):** Spread data across multiple nodes by participant or time range.
* **Replication:** Implement read replicas for load distribution.
* **Load balancing:** Use load balancers (e.g., PgBouncer) to distribute database requests.
* **Query federation:** Use tools like Patroni to manage distributed queries across physically separate nodes.
* **Local Network:** High-speed local network (e.g., 25 GbE+) to facilitate rapid communication among machines.
