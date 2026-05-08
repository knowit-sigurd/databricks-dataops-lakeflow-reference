import json
import os
import sys
from pathlib import Path

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

CATALOG = "dataops_lab"
FIXTURES = Path(__file__).parent.parent / "fixtures" / "expected_counts.json"


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_counts.py <schema>")
        sys.exit(1)

    schema = sys.argv[1]
    warehouse_id = os.environ["DATABRICKS_WAREHOUSE_ID"]
    w = WorkspaceClient()

    with open(FIXTURES) as f:
        expected_counts = json.load(f)

    failures = []
    for table, expected in expected_counts.items():
        response = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=f"SELECT COUNT(*) FROM {CATALOG}.{schema}.{table}",
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
