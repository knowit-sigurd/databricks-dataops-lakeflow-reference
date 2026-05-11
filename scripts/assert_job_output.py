import sys

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

CATALOG = "dataops_lab"
TABLES = [
    "customers_bronze",
    "customers_silver",
    "customers_rejected",
    "orders_bronze",
    "orders_silver",
    "orders_rejected",
    "customer_order_summary",
]


def count(w, warehouse_id, schema, table):
    response = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=f"SELECT COUNT(*) FROM {CATALOG}.{schema}.{table}",
        wait_timeout="30s",
    )
    if response.status.state != StatementState.SUCCEEDED:
        raise RuntimeError(f"{table}: query failed — {response.status.error}")
    return int(response.result.data_array[0][0])


def main():
    if len(sys.argv) != 3:
        print("Usage: assert_job_output.py <schema> <warehouse_id>")
        sys.exit(1)

    schema, warehouse_id = sys.argv[1], sys.argv[2]
    w = WorkspaceClient()

    counts = {}
    failures = []

    for table in TABLES:
        try:
            counts[table] = count(w, warehouse_id, schema, table)
            print(f"  {table}: {counts[table]} rows")
        except RuntimeError as e:
            failures.append(str(e))

    if failures:
        print("\nQuery failures:")
        for msg in failures:
            print(msg)
        sys.exit(1)

    # Bronze must be non-empty — empty bronze means ingestion failed
    for table in ("customers_bronze", "orders_bronze"):
        if counts[table] == 0:
            failures.append(f"{table}: empty — ingestion produced no rows")

    # Gold must be non-empty when silver has rows — catches the incremental-state trap
    # (running against an empty volume leaves silver empty and gold stale)
    silver_total = counts["customers_silver"] + counts["orders_silver"]
    if silver_total > 0 and counts["customer_order_summary"] == 0:
        failures.append("customer_order_summary: empty while silver has rows — gold join failed")

    # Critical rejections indicate a data integrity violation, not just quality trimming
    for table in ("customers_rejected", "orders_rejected"):
        response = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=(
                f"SELECT COUNT(*) FROM {CATALOG}.{schema}.{table}"
                " WHERE rejection_severity = 'critical'"
            ),
            wait_timeout="30s",
        )
        if response.status.state == StatementState.SUCCEEDED:
            n = int(response.result.data_array[0][0])
            if n > 0:
                failures.append(f"{table}: {n} critical rejection(s) — data integrity violation")

    if failures:
        print("\nAssertion failures:")
        for msg in failures:
            print(msg)
        sys.exit(1)

    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
