import dlt
from pyspark.sql import functions as F


@dlt.table(
    name="orders_bronze",
    comment="Raw orders data"
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
    comment="Validated orders"
)
@dlt.expect_or_drop("valid_amount", "amount IS NOT NULL")
def orders_silver():
    df = dlt.read("orders_bronze")

    return df.withColumn(
        "region",
        F.when(
            F.col("city").isin("Oslo", "Bergen", "Trondheim"),
            F.lit("NO"),
        ).otherwise(F.lit("UNKNOWN")),
    )