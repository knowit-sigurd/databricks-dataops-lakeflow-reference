from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from common import derive_region

ORDER_RULES = {
    "valid_order_id": "order_id IS NOT NULL",
    "valid_customer_id": "customer_id IS NOT NULL",
    "valid_amount": "amount IS NOT NULL",
}


def rejected_orders(df: DataFrame) -> DataFrame:
    reject_cond = F.lit(False)
    for sql in ORDER_RULES.values():
        reject_cond = reject_cond | ~F.expr(sql)

    reason_parts = [
        F.when(~F.expr(sql), F.lit(name.upper()))
        for name, sql in ORDER_RULES.items()
    ]

    return df.filter(reject_cond).withColumn(
        "rejection_reason",
        F.concat_ws(", ", *reason_parts),
    )


def enrich_orders(df: DataFrame) -> DataFrame:
    return derive_region(df)
