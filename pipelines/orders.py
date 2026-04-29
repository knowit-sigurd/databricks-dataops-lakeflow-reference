from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from common import derive_region


def valid_orders(df: DataFrame) -> DataFrame:
    return df.filter(F.col("amount").isNotNull())


def rejected_orders(df: DataFrame) -> DataFrame:
    return df.filter(F.col("amount").isNull()).withColumn(
        "rejection_reason",
        F.lit("NULL_AMOUNT"),
    )


def enrich_orders(df: DataFrame) -> DataFrame:
    return derive_region(df)
