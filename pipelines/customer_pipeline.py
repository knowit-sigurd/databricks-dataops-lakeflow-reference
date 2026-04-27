from pyspark.sql import functions as F
import dlt


@dlt.table(
    name="customers_bronze",
    comment="Raw customer data"
)
def customers_bronze():
    data = [
        (1, "Alice", "Oslo"),
        (2, "Bob", "Bergen"),
        (3, None, "Trondheim"),
    ]

    df = spark.createDataFrame(data, ["customer_id", "customer_name", "city"])

    return (
        df.withColumn("customer_name", F.trim(F.col("customer_name")))
        .withColumn("city", F.trim(F.col("city")))
    )


@dlt.table(
    name="customers_silver",
    comment="Validated customers"
)
@dlt.expect_or_fail("valid_customer_id", "customer_id IS NOT NULL")
@dlt.expect_or_fail("valid_customer_name", "customer_name IS NOT NULL")
def customers_silver():
    df = dlt.read("customers_bronze")

    return (
        df.withColumn("customer_key", F.col("customer_id"))
        .withColumn(
            "region",
            F.when(
                F.col("city").isin("Oslo", "Bergen", "Trondheim"),
                F.lit("NO"),
            ).otherwise(F.lit("UNKNOWN")),
        )
    )