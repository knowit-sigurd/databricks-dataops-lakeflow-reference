import dlt

from orders import enrich_orders

quality_mode = spark.conf.get("quality_mode", "drop")
expect_fn = dlt.expect_or_fail if quality_mode == "fail" else dlt.expect_or_drop


@dlt.table(
    name="orders_bronze",
    comment="Raw orders data",
)
def orders_bronze():
    data = [
        (1, 100, "Oslo"),
        (2, None, "Bergen"),
        (3, 300, "Trondheim"),
    ]

    df = spark.createDataFrame(data, ["order_id", "amount", "city"])

    return df


@dlt.table(
    name="orders_silver",
    comment="Validated orders",
)
@expect_fn("valid_amount", "amount IS NOT NULL")
def orders_silver():
    df = dlt.read("orders_bronze")

    return enrich_orders(df)