from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from databricks_dataops_lab_sdp.common import derive_region


def standardize_customers(df: DataFrame) -> DataFrame:
    return (
        df.withColumn("customer_name", F.trim(F.col("customer_name")))
        .withColumn("city", F.trim(F.col("city")))
    )


def valid_customers(df: DataFrame) -> DataFrame:
    return df.filter(
        F.col("customer_id").isNotNull()
        & F.col("customer_name").isNotNull()
    )


def rejected_customers(df: DataFrame) -> DataFrame:
    return df.filter(
        F.col("customer_id").isNull()
        | F.col("customer_name").isNull()
    ).withColumn(
        "rejection_reason",
        F.when(F.col("customer_id").isNull(), F.lit("NULL_CUSTOMER_ID"))
        .when(F.col("customer_name").isNull(), F.lit("NULL_CUSTOMER_NAME"))
        .otherwise(F.lit("UNKNOWN")),
    )


def enrich_customers(df: DataFrame) -> DataFrame:
    return derive_region(df.withColumn("customer_key", F.col("customer_id")))