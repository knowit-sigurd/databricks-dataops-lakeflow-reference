import os
import sys

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

EXPECTED_COUNTS = {
    "customers_bronze": 3,
    "customers_silver": 2,
    "customers_rejected": 1,
    "orders_bronze": 4,
    "orders_silver": 3,
    "orders_rejected": 1,
    "customer_order_summary": 2,
}

CATALOG = "dataops_lab"


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_counts.py <schema>")
        sys.exit(1)

    schema = sys.argv[1]
    warehouse_id = os.environ["DATABRICKS_WAREHOUSE_ID"]
    w = WorkspaceClient()

    failures = []
    for table, expected in EXPECTED_COUNTS.items():
        statement = f"SELECT COUNT(*) FROM {CATALOG}.{schema}.{table}"
        response = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=statement,
            wait_timeout="30s",
        )

        if response.status.state != StatementState.SUCCEEDED:
            failures.append(f"  {table}: query failed — {response.status.error}")
            continue

        actual = int(response.result.data_array[0][0])
        if actual != expected:
            failures.append(f"  {table}: expected {expected} rows, got {actual}")
        else:
            print(f"  ok  {table}: {actual}")

    if failures:
        print("\nAssertion failures:")
        for f in failures:
            print(f)
        sys.exit(1)

    print("\nAll row counts match.")


if __name__ == "__main__":
    main()
