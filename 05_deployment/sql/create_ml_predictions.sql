CREATE TABLE IF NOT EXISTS data_arch_dw.ml_predictions
(
    run_id LowCardinality(String),
    model_name LowCardinality(String),
    SK_ID_CURR UInt64,
    score Float64,
    prediction UInt8,
    predicted_at DateTime DEFAULT now(),
    prediction_path String DEFAULT '',
    metrics_path String DEFAULT ''
)
-- Cluster predictions by run, model, and entity for manifest-scoped reads.
ENGINE = MergeTree()
ORDER BY (run_id, model_name, SK_ID_CURR);
