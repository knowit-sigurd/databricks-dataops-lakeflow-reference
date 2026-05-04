from pyspark.sql import Row

from gold import build_customer_order_summary


def test_build_customer_order_summary(spark):
    customers = spark.createDataFrame(
        [
            Row(customer_id=1, customer_name="Alice", city="Oslo", region="NO"),
            Row(customer_id=2, customer_name="Bob", city="Bergen", region="NO"),
        ]
    )

    orders = spark.createDataFrame(
        [
            Row(order_id=1, customer_id=1, amount=100, city="Oslo", region="NO"),
            Row(order_id=2, customer_id=2, amount=300, city="Bergen", region="NO"),
            Row(order_id=3, customer_id=99, amount=50, city="Unknown", region="UNKNOWN"),
        ]
    )

    result = {
        row["customer_id"]: row.asDict()
        for row in build_customer_order_summary(customers, orders).collect()
    }

    assert result[1]["order_count"] == 1
    assert result[1]["total_amount"] == 100
    assert result[2]["order_count"] == 1
    assert result[2]["total_amount"] == 300
    assert 99 not in result


def test_customer_order_summary_excludes_customer_email(spark):
    customers = spark.createDataFrame(
        [Row(customer_id=1, customer_name="Alice", city="Oslo", region="NO", customer_email="alice@example.com")]
    )
    orders = spark.createDataFrame(
        [Row(order_id=1, customer_id=1, amount=100, city="Oslo", region="NO")]
    )
    result = build_customer_order_summary(customers, orders)
    assert "customer_email" not in result.columns