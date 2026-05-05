-- Pipeline update history: one row per state transition per update.
-- Pivot on update_id to see full lifecycle (WAITING → INITIALIZING → RUNNING → COMPLETED/FAILED).
-- Run against the target schema: replace sdp_dev with sdp_prod or sdp_pr_<n> as needed.

SELECT
  timestamp,
  details :update_id :: STRING    AS update_id,
  details :update_progress :state :: STRING AS state
FROM dataops_lab.sdp_dev.event_log
WHERE event_type = 'update_progress'
ORDER BY timestamp DESC;
