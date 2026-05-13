import sys
from pathlib import Path

import yaml
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

CATALOG = "dataops_lab"
CONTRACT_PATH = Path(sys.argv[0]).resolve().parent.parent / "contracts" / "customer_order_summary.yml"


def run_query(w, warehouse_id, sql):
    response = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql,
        wait_timeout="30s",
    )
    if response.status.state != StatementState.SUCCEEDED:
        raise RuntimeError(f"Query failed: {response.status.error}")
    return int(response.result.data_array[0][0])


def check_expectation(actual, expect):
    op, val = expect.strip().split(" ", 1)
    val = int(val)
    if op == ">":
        return actual > val
    if op == "=":
        return actual == val
    if op == "<":
        return actual < val
    raise ValueError(f"Unknown operator: {op}")


def main():
    if len(sys.argv) != 3:
        print("Usage: verify_contract.py <schema> <warehouse_id>")
        sys.exit(1)

    schema, warehouse_id = sys.argv[1], sys.argv[2]
    w = WorkspaceClient()

    with open(CONTRACT_PATH) as f:
        contract = yaml.safe_load(f)

    table = f"{CATALOG}.{schema}.{contract['table']}"
    failures = []

    response = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=f"DESCRIBE TABLE {table}",
        wait_timeout="30s",
    )
    if response.status.state != StatementState.SUCCEEDED:
        print(f"Could not describe {table}: {response.status.error}")
        sys.exit(1)
    actual_columns = {row[0] for row in response.result.data_array}

    for col in contract["columns"]:
        if col["name"] not in actual_columns:
            failures.append(f"Missing column: '{col['name']}'")

    for rule in contract["rules"]:
        sql = rule["sql"].replace("{table}", table)
        try:
            count = run_query(w, warehouse_id, sql)
            if not check_expectation(count, rule["expect"]):
                failures.append(
                    f"Rule failed: {rule['description']} (got {count}, expected {rule['expect']})"
                )
        except RuntimeError as e:
            failures.append(str(e))

    if failures:
        print(f"\nContract violations for {table}:")
        for msg in failures:
            print(f"  - {msg}")
        sys.exit(1)

    n_cols = len(contract["columns"])
    n_rules = len(contract["rules"])
    print(f"Contract verified: {table} ({n_cols} columns, {n_rules} rules)")


if __name__ == "__main__":
    main()
