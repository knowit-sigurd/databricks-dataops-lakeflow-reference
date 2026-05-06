-- Per-table row counts for each pipeline update.
-- Filters to final non-null counts only; excludes internal Databricks flow metrics.
-- Requires ownership of the pipeline or CAN_MANAGE permission.
-- Replace the pipeline ID with your own.

SELECT
  origin.update_id,
  origin.flow_name                                                        AS table_name,
  MAX(details:flow_progress.metrics.num_output_rows::BIGINT)              AS output_rows,
  MAX(details:flow_progress.data_quality.dropped_records::BIGINT)         AS dropped_records
FROM event_log('09d4efc7-2498-45d8-97aa-ca280edf24d3')
WHERE event_type = 'flow_progress'
  AND details:flow_progress.metrics.num_output_rows IS NOT NULL
  AND origin.flow_name NOT LIKE 'pipelines.%'
GROUP BY origin.update_id, origin.flow_name
ORDER BY origin.update_id, origin.flow_name;
