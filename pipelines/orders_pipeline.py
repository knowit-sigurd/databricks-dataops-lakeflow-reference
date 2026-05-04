import dlt
from pyspark.sql.types import DecimalType, LongType, StringType, StructField, StructType

from orders import ORDER_RULES, enrich_orders, rejected_orders

quality_mode = spark.conf.get("quality_mode", "drop")
source_path = spark.conf.get("source_path", "./data")

expect_fn = dlt.expect_or_fail if quality_mode == "fail" else dlt.expect_or_drop

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
    )


@dlt.table(name="orders_silver", comment="Validated orders")
@expect_fn("valid_order_id", ORDER_RULES["valid_order_id"])
@expect_fn("valid_customer_id", ORDER_RULES["valid_customer_id"])
@expect_fn("valid_amount", ORDER_RULES["valid_amount"])
def orders_silver():
    return enrich_orders(dlt.read("orders_bronze"))


@dlt.table(name="orders_rejected", comment="Rejected orders with reason")
def orders_rejected():
    return rejected_orders(dlt.read("orders_bronze"))
