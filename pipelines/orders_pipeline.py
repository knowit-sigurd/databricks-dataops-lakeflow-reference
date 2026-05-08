import pyspark.pipelines as dlt
import pyspark.sql.functions as F
from pyspark.sql.types import DecimalType, LongType, StringType, StructField, StructType

from orders import ORDER_RULES, enrich_orders, rejected_orders

quality_mode = spark.conf.get("quality_mode", "drop")
source_path = spark.conf.get("source_path", "./data")


def expect_for(rule_name):
    rule = ORDER_RULES[rule_name]
    if rule["severity"] == "critical":
        fn = dlt.expect_or_fail if quality_mode == "fail" else dlt.expect_or_drop
    elif rule["severity"] == "business_invalid":
        fn = dlt.expect_or_drop
    else:
        fn = dlt.expect
    return fn(rule_name, rule["condition"])


ORDERS_SCHEMA = StructType([
    StructField("order_id", LongType(), True),
    StructField("customer_id", LongType(), True),
    StructField("amount", DecimalType(10, 2), True),
    StructField("city", StringType(), True),
])


@dlt.table(name="orders_bronze", comment="Raw orders data")
def orders_bronze():
    return (
        spark.read.option("header", True)
        .schema(ORDERS_SCHEMA)
        .csv(f"{source_path}/orders.csv")
        .withColumn("_source_file", F.col("_metadata.file_path"))
        .withColumn("_ingested_at", F.current_timestamp())
    )


@dlt.table(name="orders_silver", comment="Validated orders")
@expect_for("valid_order_id")
@expect_for("valid_customer_id")
@expect_for("valid_amount")
def orders_silver():
    return enrich_orders(dlt.read("orders_bronze"))


@dlt.table(name="orders_rejected", comment="Rejected orders with reason and severity")
def orders_rejected():
    return rejected_orders(dlt.read("orders_bronze"))
