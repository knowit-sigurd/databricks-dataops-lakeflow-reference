-- Pipeline update history: one row per update with final state and duration.
-- Requires ownership of the pipeline or CAN_MANAGE permission.
-- Replace the pipeline ID with your own (find it in the pipeline URL or via 'databricks pipelines list').

SELECT
  origin.update_id,
  MIN(timestamp)                                          AS started_at,
  MAX(timestamp)                                          AS ended_at,
  TIMESTAMPDIFF(SECOND, MIN(timestamp), MAX(timestamp))  AS duration_seconds,
  MAX_BY(details:update_progress.state, timestamp)       AS final_state
FROM event_log('09d4efc7-2498-45d8-97aa-ca280edf24d3')
WHERE event_type = 'update_progress'
GROUP BY origin.update_id
ORDER BY started_at DESC;
