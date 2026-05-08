from pyspark.sql import Row

from orders import ORDER_RULES, enrich_orders, rejected_orders


def test_order_rules_cover_required_fields():
    assert "valid_order_id" in ORDER_RULES
    assert "valid_customer_id" in ORDER_RULES
    assert "valid_amount" in ORDER_RULES
    assert all("condition" in r and "severity" in r for r in ORDER_RULES.values())


def test_rejected_orders_excludes_valid_rows(spark):
    df = spark.createDataFrame(
        [Row(order_id=1, customer_id=1, amount=100, city="Oslo")],
        schema="order_id INT, customer_id INT, amount INT, city STRING",
    )
    assert rejected_orders(df).count() == 0


def test_rejected_orders_captures_null_amount(spark):
    df = spark.createDataFrame(
        [Row(order_id=2, customer_id=2, amount=None, city="Bergen")],
        schema="order_id INT, customer_id INT, amount INT, city STRING",
    )
    result = rejected_orders(df).collect()[0]
    assert result["rejection_reason"] == "VALID_AMOUNT"
    assert result["rejection_severity"] == "business_invalid"
    assert result["rule_version"] == "1.0"


def test_rejected_orders_captures_null_order_id(spark):
    df = spark.createDataFrame(
        [Row(order_id=None, customer_id=1, amount=100, city="Oslo")],
        schema="order_id INT, customer_id INT, amount INT, city STRING",
    )
    result = rejected_orders(df).collect()[0]
    assert result["rejection_reason"] == "VALID_ORDER_ID"
    assert result["rejection_severity"] == "critical"
    assert result["rule_version"] == "1.0"


def test_rejected_orders_captures_null_customer_id(spark):
    df = spark.createDataFrame(
        [Row(order_id=3, customer_id=None, amount=200, city="Bergen")],
        schema="order_id INT, customer_id INT, amount INT, city STRING",
    )
    result = rejected_orders(df).collect()[0]
    assert result["rejection_reason"] == "VALID_CUSTOMER_ID"


def test_rejected_orders_captures_all_failing_reasons(spark):
    df = spark.createDataFrame(
        [Row(order_id=None, customer_id=1, amount=None, city="Oslo")],
        schema="order_id INT, customer_id INT, amount INT, city STRING",
    )
    result = rejected_orders(df).collect()[0]
    assert "VALID_ORDER_ID" in result["rejection_reason"]
    assert "VALID_AMOUNT" in result["rejection_reason"]


def test_enrich_orders_adds_region(spark):
    df = spark.createDataFrame(
        [
            Row(order_id=1, amount=100, city="Oslo"),
            Row(order_id=2, amount=200, city="Stockholm"),
        ]
    )
    result = {row["order_id"]: row.asDict() for row in enrich_orders(df).collect()}
    assert result[1]["region"] == "NO"
    assert result[2]["region"] == "UNKNOWN"
