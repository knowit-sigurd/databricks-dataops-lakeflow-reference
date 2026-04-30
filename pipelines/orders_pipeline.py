import dlt

from orders import enrich_orders

quality_mode = spark.conf.get("quality_mode", "drop")
source_path = spark.conf.get("source_path", "./data")

expect_fn = dlt.expect_or_fail if quality_mode == "fail" else dlt.expect_or_drop


@dlt.table(
    name="orders_bronze",
    comment="Raw orders data",
)
def orders_bronze():
    return (
        spark.read.option("header", True)
        .option("inferSchema", True)
        .csv(f"{source_path}/orders.csv")
    )


@dlt.table(
    name="orders_silver",
    comment="Validated orders",
)
@expect_fn("valid_amount", "amount IS NOT NULL")
def orders_silver():
    df = dlt.read("orders_bronze")
    return enrich_orders(df)
