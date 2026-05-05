-- Expectation pass/fail counts per rule, per flow, per pipeline update.
-- Run against the target schema: replace sdp_dev with sdp_prod or sdp_pr_<n> as needed.
-- Requires SELECT on dataops_lab.sdp_dev.event_log.

SELECT
  timestamp,
  details :update_id :: STRING                             AS update_id,
  details :flow_progress :name :: STRING                   AS flow_name,
  expectation.name                                         AS rule_name,
  expectation.passed_records                               AS passed,
  expectation.failed_records                               AS failed,
  ROUND(
    expectation.passed_records * 100.0
    / NULLIF(expectation.passed_records + expectation.failed_records, 0),
    2
  )                                                        AS pass_pct
FROM dataops_lab.sdp_dev.event_log,
  LATERAL VIEW INLINE(
    FROM_JSON(
      details :flow_progress :data_quality :expectations :: STRING,
      'array<struct<name:string,dataset:string,passed_records:bigint,failed_records:bigint>>'
    )
  ) AS expectation
WHERE event_type = 'flow_progress'
  AND details :flow_progress :status :: STRING = 'COMPLETED'
  AND details :flow_progress :data_quality IS NOT NULL
ORDER BY timestamp DESC;
