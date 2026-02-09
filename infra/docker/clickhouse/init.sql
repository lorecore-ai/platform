CREATE DATABASE IF NOT EXISTS events;

CREATE TABLE IF NOT EXISTS events.log
(
    timestamp DateTime DEFAULT now(),
    
    integration_id String,
    tenant_id String,

    event_type String
)
ENGINE = MergeTree
ORDER BY (tenant_id, timestamp);
