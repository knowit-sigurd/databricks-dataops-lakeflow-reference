-- Rejection counts by rule and entity.
-- Replace sdp_dev with sdp_prod or sdp_pr_<n> as needed.

SELECT 'customers' AS entity, rejection_reason, COUNT(*) AS row_count
FROM dataops_lab.sdp_dev.customers_rejected
GROUP BY rejection_reason
UNION ALL
SELECT 'orders' AS entity, rejection_reason, COUNT(*) AS row_count
FROM dataops_lab.sdp_dev.orders_rejected
GROUP BY rejection_reason
ORDER BY entity, row_count DESC;
