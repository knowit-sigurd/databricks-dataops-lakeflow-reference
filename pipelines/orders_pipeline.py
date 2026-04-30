import dlt

from orders import (
    enrich_orders,
    valid_orders,
    rejected_orders,
)

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

    valid_df = valid_orders(df)

    return enrich_orders(valid_df)


@dlt.table(
    name="orders_rejected",
    comment="Rejected orders with reason",
)
def orders_rejected():
    df = dlt.read("orders_bronze")

    return rejected_orders(df)


@dlt.table(
    name="orders_quality_gate",
    comment="Fails production pipeline if rejected order rows exist",
)
@dlt.expect_or_fail(
    "no_rejected_order_rows",
    "quality_mode != 'fail' OR rejected_count = 0",
)
def orders_quality_gate():
    rejected_count = dlt.read("orders_rejected").count()

    return spark.createDataFrame(
        [(quality_mode, rejected_count)],
        ["quality_mode", "rejected_count"],
    )
