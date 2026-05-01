from pyspark.sql import Row

from orders import (
    enrich_orders,
    rejected_orders,
    valid_orders,
)


def test_valid_orders_filters_null_amounts(spark):
    df = spark.createDataFrame(
        [
            Row(order_id=1, customer_id=1, amount=100, city="Oslo"),
            Row(order_id=2, customer_id=2, amount=None, city="Bergen"),
        ],
        schema="order_id INT, customer_id INT, amount INT, city STRING",
    )

    result = valid_orders(df)

    assert result.count() == 1
    assert result.collect()[0]["order_id"] == 1


def test_rejected_orders_adds_reason(spark):
    df = spark.createDataFrame(
        [
            Row(order_id=2, amount=None, city="Bergen"),
        ],
        schema="order_id INT, amount INT, city STRING",
    )

    result = rejected_orders(df).collect()[0]

    assert result["rejection_reason"] == "NULL_AMOUNT"


def test_enrich_orders_adds_region(spark):
    df = spark.createDataFrame(
        [
            Row(order_id=1, amount=100, city="Oslo"),
            Row(order_id=2, amount=200, city="Stockholm"),
        ]
    )

    result = {
        row["order_id"]: row.asDict()
        for row in enrich_orders(df).collect()
    }

    assert result[1]["region"] == "NO"
    assert result[2]["region"] == "UNKNOWN"