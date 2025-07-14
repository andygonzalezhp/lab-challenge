CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 1-minute buckets
CREATE MATERIALIZED VIEW IF NOT EXISTS data_1m
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 minute', ts)    AS bucket,
  participant,
  metric,
  AVG(value)                     AS value
FROM raw_data
GROUP BY bucket, participant, metric;

-- 1-hour buckets
CREATE MATERIALIZED VIEW IF NOT EXISTS data_1h
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 hour', ts)      AS bucket,
  participant,
  metric,
  AVG(value)                     AS value
FROM raw_data
GROUP BY bucket, participant, metric;

-- 1-day buckets
CREATE MATERIALIZED VIEW IF NOT EXISTS data_1d
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 day', ts)       AS bucket,
  participant,
  metric,
  AVG(value)                     AS value
FROM raw_data
GROUP BY bucket, participant, metric;

-- refresh every hour, keeping last 1 day of raw data
SELECT add_continuous_aggregate_policy('data_1m',
  start_offset => INTERVAL '1 day',
  end_offset   => INTERVAL '1 hour',
  schedule_interval => INTERVAL '1 hour');

-- refresh every 6 hours, keeping 7 days
SELECT add_continuous_aggregate_policy('data_1h',
  start_offset => INTERVAL '7 days',
  end_offset   => INTERVAL '1 day',
  schedule_interval => INTERVAL '6 hours');

-- refresh daily, keeping 30 days
SELECT add_continuous_aggregate_policy('data_1d',
  start_offset => INTERVAL '30 days',
  end_offset   => INTERVAL '7 days',
  schedule_interval => INTERVAL '1 day');
  