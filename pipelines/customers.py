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
    reject_cond = None
    reason_expr = None

    for name, sql in CUSTOMER_RULES.items():
        cond = ~F.expr(sql)
        reject_cond = cond if reject_cond is None else reject_cond | cond
        if reason_expr is None:
            reason_expr = F.when(cond, F.lit(name.upper()))
        else:
            reason_expr = reason_expr.when(cond, F.lit(name.upper()))

    return df.filter(reject_cond).withColumn(
        "rejection_reason",
        reason_expr.otherwise(F.lit("UNKNOWN")),
    )


def enrich_customers(df: DataFrame) -> DataFrame:
    return derive_region(df.withColumn("customer_key", F.col("customer_id")))
