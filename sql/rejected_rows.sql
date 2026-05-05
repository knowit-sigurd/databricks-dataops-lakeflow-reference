-- All rejected rows with the failing rule reason, for both entities.
-- Replace sdp_dev with sdp_prod or sdp_pr_<n> as needed.

SELECT 'customers' AS entity, customer_id AS row_id, rejection_reason
FROM dataops_lab.sdp_dev.customers_rejected
UNION ALL
SELECT 'orders' AS entity, order_id AS row_id, rejection_reason
FROM dataops_lab.sdp_dev.orders_rejected
ORDER BY entity, row_id;
