import json
import sys
from pathlib import Path

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

CATALOG = "dataops_lab"
OPS_SCHEMA = "ops"
ASSERTIONS_TABLE = "pipeline_run_assertions"
FIXTURES = Path(__file__).parent.parent / "fixtures" / "expected_counts.json"


def run_sql(w, warehouse_id, statement):
    response = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=statement,
        wait_timeout="60s",
    )
    if response.status.state != StatementState.SUCCEEDED:
        raise RuntimeError(f"SQL failed: {response.status.error}")
    return response


def main():
    if len(sys.argv) != 3:
        print("Usage: assert_and_persist.py <schema> <warehouse_id>")
        sys.exit(1)

    schema = sys.argv[1]
    warehouse_id = sys.argv[2]
    w = WorkspaceClient()

    with open(FIXTURES) as f:
        expected_counts = json.load(f)

    failures = []
    actual_counts = {}
    for table, expected in expected_counts.items():
        resp = run_sql(w, warehouse_id, f"SELECT COUNT(*) FROM {CATALOG}.{schema}.{table}")
        actual = int(resp.result.data_array[0][0])
        actual_counts[table] = actual
        if actual != expected:
            failures.append(f"{table}: expected {expected}, got {actual}")
            print(f"  FAIL  {table}: expected {expected}, got {actual}")
        else:
            print(f"  ok    {table}: {actual}")

    status = "PASSED" if not failures else "FAILED"
    print(f"\nAssertions {status}.")

    run_sql(w, warehouse_id, f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{OPS_SCHEMA}")
    run_sql(w, warehouse_id, f"""
        CREATE TABLE IF NOT EXISTS {CATALOG}.{OPS_SCHEMA}.{ASSERTIONS_TABLE} (
            run_at   TIMESTAMP,
            schema   STRING,
            status   STRING,
            counts   STRING,
            failures STRING
        )
    """)

    counts_esc = json.dumps(actual_counts).replace("'", "''")
    failures_esc = json.dumps(failures).replace("'", "''")
    run_sql(w, warehouse_id, f"""
        INSERT INTO {CATALOG}.{OPS_SCHEMA}.{ASSERTIONS_TABLE}
        VALUES (CURRENT_TIMESTAMP, '{schema}', '{status}', '{counts_esc}', '{failures_esc}')
    """)
    print(f"Summary written to {CATALOG}.{OPS_SCHEMA}.{ASSERTIONS_TABLE}.")

    if failures:
        print("\nFailures:")
        for f in failures:
            print(f"  {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
