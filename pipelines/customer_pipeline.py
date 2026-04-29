import dlt
from pyspark.sql import functions as F

from databricks_dataops_lab_sdp.customers import (
    enrich_customers,
    standardize_customers,
)

quality_mode = spark.conf.get("quality_mode", "drop")
expect_fn = dlt.expect_or_fail if quality_mode == "fail" else dlt.expect_or_drop


@dlt.table(
    name="customers_bronze",
    comment="Raw customer data",
)
def customers_bronze():
    data = [
        (1, "Alice", "Oslo"),
        (2, "Bob", "Bergen"),
        (3, None, "Trondheim"),
    ]

    df = spark.createDataFrame(data, ["customer_id", "customer_name", "city"])

    return standardize_customers(df)


@dlt.table(
    name="customers_silver",
    comment="Validated customers",
)
@expect_fn("valid_customer_id", "customer_id IS NOT NULL")
@expect_fn("valid_customer_name", "customer_name IS NOT NULL")
def customers_silver():
    df = dlt.read("customers_bronze")

    return enrich_customers(df)