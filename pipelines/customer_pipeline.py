import dlt

from customers import (
    enrich_customers,
    standardize_customers,
    valid_customers,
    rejected_customers,
)

quality_mode = spark.conf.get("quality_mode", "drop")
source_path = spark.conf.get("source_path", "./data")

expect_fn = dlt.expect_or_fail if quality_mode == "fail" else dlt.expect_or_drop


@dlt.table(
    name="customers_bronze",
    comment="Raw customer data",
)
def customers_bronze():
    df = (
        spark.read.option("header", True)
        .option("inferSchema", True)
        .csv(f"{source_path}/customers.csv")
    )

    return standardize_customers(df)


@dlt.table(
    name="customers_silver",
    comment="Validated customers",
)
@expect_fn("valid_customer_id", "customer_id IS NOT NULL")
@expect_fn("valid_customer_name", "customer_name IS NOT NULL")
def customers_silver():
    df = dlt.read("customers_bronze")

    valid_df = valid_customers(df)

    return enrich_customers(valid_df)


@dlt.table(
    name="customers_rejected",
    comment="Rejected customer rows with reason",
)
def customers_rejected():
    df = dlt.read("customers_bronze")

    return rejected_customers(df)

@dlt.table(
    name="customers_quality_gate",
    comment="Fails production pipeline if rejected customer rows exist",
)
@dlt.expect_or_fail(
    "no_rejected_customer_rows",
    "quality_mode != 'fail' OR rejected_count = 0",
)
def customers_quality_gate():
    rejected_count = dlt.read("customers_rejected").count()

    return spark.createDataFrame(
        [(quality_mode, rejected_count)],
        ["quality_mode", "rejected_count"],
    )