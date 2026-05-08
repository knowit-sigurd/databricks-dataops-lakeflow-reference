from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from common import derive_region

CUSTOMER_RULES = {
    "valid_customer_id": {
        "condition": "customer_id IS NOT NULL",
        "severity": "critical",
    },
    "valid_customer_name": {
        "condition": "customer_name IS NOT NULL",
        "severity": "business_invalid",
    },
}

RULE_VERSION = "1.0"


def standardize_customers(df: DataFrame) -> DataFrame:
    return (
        df.withColumn("customer_name", F.trim(F.col("customer_name")))
        .withColumn("city", F.trim(F.col("city")))
    )


def rejected_customers(df: DataFrame) -> DataFrame:
    quarantine_rules = {k: v for k, v in CUSTOMER_RULES.items() if v["severity"] != "warning"}

    reject_cond = F.lit(False)
    for rule in quarantine_rules.values():
        reject_cond = reject_cond | ~F.expr(rule["condition"])

    reason_parts = [
        F.when(~F.expr(rule["condition"]), F.lit(name.upper()))
        for name, rule in quarantine_rules.items()
    ]
    severity_parts = [
        F.when(~F.expr(rule["condition"]), F.lit(rule["severity"]))
        for rule in quarantine_rules.values()
    ]

    return (
        df.filter(reject_cond)
        .withColumn("rejection_reason", F.concat_ws(", ", *reason_parts))
        .withColumn("rejection_severity", F.coalesce(*severity_parts))
        .withColumn("rule_version", F.lit(RULE_VERSION))
    )


def enrich_customers(df: DataFrame) -> DataFrame:
    return derive_region(df)
