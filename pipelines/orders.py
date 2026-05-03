from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from common import derive_region

ORDER_RULES = {
    "valid_order_id": "order_id IS NOT NULL",
    "valid_customer_id": "customer_id IS NOT NULL",
    "valid_amount": "amount IS NOT NULL",
}


def rejected_orders(df: DataFrame) -> DataFrame:
    reject_cond = None
    reason_expr = None

    for name, sql in ORDER_RULES.items():
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


def enrich_orders(df: DataFrame) -> DataFrame:
    return derive_region(df)
