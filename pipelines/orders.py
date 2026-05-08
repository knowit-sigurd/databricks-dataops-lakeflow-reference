from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from common import derive_region

ORDER_RULES = {
    "valid_order_id": {
        "condition": "order_id IS NOT NULL",
        "severity": "critical",
    },
    "valid_customer_id": {
        "condition": "customer_id IS NOT NULL",
        "severity": "critical",
    },
    "valid_amount": {
        "condition": "amount IS NOT NULL",
        "severity": "business_invalid",
    },
}

RULE_VERSION = "1.0"


def rejected_orders(df: DataFrame) -> DataFrame:
    quarantine_rules = {k: v for k, v in ORDER_RULES.items() if v["severity"] != "warning"}

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


def enrich_orders(df: DataFrame) -> DataFrame:
    return derive_region(df)
