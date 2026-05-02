import dlt
from pyspark.sql.types import DoubleType, LongType, StringType, StructField, StructType

from orders import (
    enrich_orders,
    valid_orders,
    rejected_orders,
)

quality_mode = spark.conf.get("quality_mode", "drop")
source_path = spark.conf.get("source_path", "./data")

expect_fn = dlt.expect_or_fail if quality_mode == "fail" else dlt.expect_or_drop

ORDERS_SCHEMA = StructType([
    StructField("order_id", LongType(), True),
    StructField("customer_id", LongType(), True),
    StructField("amount", DoubleType(), True),
    StructField("city", StringType(), True),
])


@dlt.table(
    name="orders_bronze",
    comment="Raw orders data",
)
def orders_bronze():
    return (
        spark.read.option("header", True)
        .schema(ORDERS_SCHEMA)
        .csv(f"{source_path}/orders.csv")
    )


@dlt.table(
    name="orders_silver",
    comment="Validated orders",
)
@expect_fn("valid_amount", "amount IS NOT NULL")
def orders_silver():
    df = dlt.read("orders_bronze")

    if quality_mode == "fail":
        # In prod, let expect_or_fail enforce validity.
        # Do not pre-filter, otherwise the expectation never fails.
        return enrich_orders(df)

    # In dev / PR, keep silver clean while allowing the pipeline to succeed.
    return enrich_orders(valid_orders(df))


@dlt.table(
    name="orders_rejected",
    comment="Rejected orders with reason",
)
def orders_rejected():
    df = dlt.read("orders_bronze")

    return rejected_orders(df)
