# Task 6 - More in Depth Horizontal Scaling

## Horizontal Scaling Considerations

When clinical trials scale beyond 1,000 participants and span multiple years, data volume, processing loads, and query demands can exceed the capability of vertically scaled solutions. Thus, horizontal scaling would become a necessity to ensure fast and sound working capabilities. 

### Key Horizontal Scaling Strategies:

#### 1. Data Partitioning (Sharding)

* **By Participant ID or Time Range:**

  * Divide the database into separate partitions, each managed by a different server.

#### 2. Database Technologies:

* **PostgreSQL + TimescaleDB:**

  * Utilize TimescaleDB's hypertables to efficiently shard and manage time-series data.

#### 3. Replication & Redundancy:

* **Read Replicas:**

  * Employ read replicas for handling high query loads, reducing strain on primary databases.
* **High Availability (HA) Clusters:**

  * Use technologies like Patroni or Pgpool-II for PostgreSQL to ensure fault tolerance and automatic failover.

#### 4. Load Balancing:

* **PgBouncer:**

  * Pool and manage database connections efficiently.
* **HAProxy or Nginx:**

  * Distribute requests evenly across multiple backend servers to optimize performance.

#### 5. Query Federation and Aggregation:

* **Patroni:**

  * Manage distributed PostgreSQL clusters.
* **Foreign Data Wrappers (FDW):**

  * Execute distributed queries transparently across multiple databases.

#### 6. Storage Management:

* **Network-Attached Storage (NAS):**

  * Centralized, scalable storage solutions for archiving less frequently accessed data.

#### 7. Infrastructure:

* **High-speed local networks (25GbE+):**

  * Critical to maintaining performance with distributed nodes.

## Architecture (Rough Diagram)

```
[Client/Application]
        |
  Load Balancer
(HAProxy/Nginx)
        |
    PgBouncer
        |
        |-------------------|
 [Shard 1]          [Shard 2] ... [Shard N]
(Postgres+         (Postgres+     (Postgres+
TimescaleDB)      TimescaleDB)   TimescaleDB)
        |-------------------|
     Patroni Cluster Management
        |
  Read Replicas
(Postgres Replica)
        |
   Data Archiving
(NAS with Parquet/ORC)
```

### Benefits of Horizontal Scaling:

* **Improved Performance:** Distribute computational and storage loads, this will ease up every cluster and improve overall performance.
* **High Availability:** Avoid single points of failure, it's also possible to have dedicated backups with this method.
* **Flexible Expansion:** Easy addition of new nodes to manage growing datasets.

### Possible Challenges and pitfalls:

* **Complexity:** More moving parts and management overhead.
* **Networking Dependencies:** Requires robust local network infrastructure.

