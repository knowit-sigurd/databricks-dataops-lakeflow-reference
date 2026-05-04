from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def build_customer_order_summary(
    customers_df: DataFrame,
    orders_df: DataFrame,
) -> DataFrame:
    order_summary = (
        orders_df.groupBy("customer_id")
        .agg(
            F.count("*").alias("order_count"),
            F.sum("amount").alias("total_amount"),
        )
    )

    return (
        customers_df.join(order_summary, on="customer_id", how="inner")
        # Explicit select is the schema promotion gate — new silver columns are not
        # included in gold unless there is a business output requirement for them.
        .select(
            "customer_id",
            "customer_name",
            "city",
            "region",
            "order_count",
            "total_amount",
        )
    )
