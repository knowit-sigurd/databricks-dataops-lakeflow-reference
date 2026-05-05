from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from common import derive_region

CUSTOMER_RULES = {
    "valid_customer_id": "customer_id IS NOT NULL",
    "valid_customer_name": "customer_name IS NOT NULL",
}


def standardize_customers(df: DataFrame) -> DataFrame:
    return (
        df.withColumn("customer_name", F.trim(F.col("customer_name")))
        .withColumn("city", F.trim(F.col("city")))
    )


def rejected_customers(df: DataFrame) -> DataFrame:
    reject_cond = F.lit(False)
    for sql in CUSTOMER_RULES.values():
        reject_cond = reject_cond | ~F.expr(sql)

    reason_parts = [
        F.when(~F.expr(sql), F.lit(name.upper()))
        for name, sql in CUSTOMER_RULES.items()
    ]

    return df.filter(reject_cond).withColumn(
        "rejection_reason",
        F.concat_ws(", ", *reason_parts),
    )


def enrich_customers(df: DataFrame) -> DataFrame:
    return derive_region(df)
