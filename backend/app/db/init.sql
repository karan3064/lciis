-- LCIIS TimescaleDB bootstrap
-- Run after SQLAlchemy has created tables (Base.metadata.create_all), or via
-- `alembic upgrade head` if migrations are introduced later.

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Convert the time-series tables into hypertables, partitioned by time.
SELECT create_hypertable('lab_results', 'collected_at', if_not_exists => TRUE);
SELECT create_hypertable('vital_readings', 'recorded_at', if_not_exists => TRUE);

-- Continuous aggregates: rolling 7-day and 30-day averages per patient/test,
-- used by the dashboard for quick trend summaries without scanning raw rows.
CREATE MATERIALIZED VIEW IF NOT EXISTS lab_results_7d
WITH (timescaledb.continuous) AS
SELECT
    patient_id,
    test_code,
    time_bucket('7 days', collected_at) AS bucket,
    avg(value) AS avg_value,
    min(value) AS min_value,
    max(value) AS max_value,
    count(*) AS sample_count
FROM lab_results
GROUP BY patient_id, test_code, bucket
WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS lab_results_30d
WITH (timescaledb.continuous) AS
SELECT
    patient_id,
    test_code,
    time_bucket('30 days', collected_at) AS bucket,
    avg(value) AS avg_value,
    min(value) AS min_value,
    max(value) AS max_value,
    count(*) AS sample_count
FROM lab_results
GROUP BY patient_id, test_code, bucket
WITH NO DATA;

SELECT add_continuous_aggregate_policy('lab_results_7d',
    start_offset => INTERVAL '90 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('lab_results_30d',
    start_offset => INTERVAL '180 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

-- Compression policy: compress lab results older than 90 days (90%+ savings
-- per the architecture doc) while keeping recent data uncompressed for fast writes.
ALTER TABLE lab_results SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'patient_id, test_code'
);
SELECT add_compression_policy('lab_results', INTERVAL '90 days', if_not_exists => TRUE);
