-- Sentinel AI ClickHouse schema (ClickHouse Cloud compatible)
-- GPS TTL default 30 days. Never tie deletion to AWS suspension deadline.

CREATE TABLE IF NOT EXISTS gps_events
(
    event_id String,
    user_id String,
    device_id String,
    event_timestamp DateTime64(3, 'UTC'),
    lat Float64,
    lon Float64,
    horizontal_accuracy_m Float64,
    source String,
    received_at DateTime64(3, 'UTC'),
    synthetic UInt8
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_timestamp)
ORDER BY (user_id, event_timestamp, event_id)
TTL toDateTime(event_timestamp) + INTERVAL 30 DAY;

CREATE TABLE IF NOT EXISTS financial_events
(
    event_id String,
    account_id String,
    user_id String,
    transaction_type String,
    channel String,
    merchant String,
    merchant_lat Nullable(Float64),
    merchant_lon Nullable(Float64),
    merchant_geo_confidence Float64,
    amount Float64,
    currency String,
    authorization_time Nullable(DateTime64(3, 'UTC')),
    posting_time DateTime64(3, 'UTC'),
    synthetic UInt8,
    metadata String
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(posting_time)
ORDER BY (user_id, posting_time, event_id);

CREATE TABLE IF NOT EXISTS security_events
(
    event_id String,
    user_id String,
    account_id String,
    event_type String,
    event_timestamp DateTime64(3, 'UTC'),
    device_id Nullable(String),
    source_lat Nullable(Float64),
    source_lon Nullable(Float64),
    details String,
    synthetic UInt8
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_timestamp)
ORDER BY (user_id, event_timestamp, event_id);

CREATE TABLE IF NOT EXISTS agent_telemetry
(
    telemetry_id String,
    incident_id String,
    user_id String,
    action String,
    status String,
    evidence_refs String,
    payload String,
    created_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(created_at)
ORDER BY (user_id, created_at, telemetry_id);
