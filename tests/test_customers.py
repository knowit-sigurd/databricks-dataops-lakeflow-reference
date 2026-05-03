from pyspark.sql import Row

from customers import CUSTOMER_RULES, enrich_customers, rejected_customers, standardize_customers


def test_standardize_customers_trims_values(spark):
    df = spark.createDataFrame(
        [Row(customer_id=1, customer_name="  Alice  ", city="  Oslo  ")]
    )
    result = standardize_customers(df).collect()[0]
    assert result["customer_name"] == "Alice"
    assert result["city"] == "Oslo"


def test_customer_rules_cover_required_fields():
    assert "valid_customer_id" in CUSTOMER_RULES
    assert "valid_customer_name" in CUSTOMER_RULES


def test_rejected_customers_excludes_valid_rows(spark):
    df = spark.createDataFrame(
        [Row(customer_id=1, customer_name="Alice", city="Oslo")],
        schema="customer_id INT, customer_name STRING, city STRING",
    )
    assert rejected_customers(df).count() == 0


def test_rejected_customers_captures_null_name(spark):
    df = spark.createDataFrame(
        [Row(customer_id=2, customer_name=None, city="Bergen")],
        schema="customer_id INT, customer_name STRING, city STRING",
    )
    result = rejected_customers(df).collect()[0]
    assert result["rejection_reason"] == "VALID_CUSTOMER_NAME"


def test_rejected_customers_captures_null_id(spark):
    df = spark.createDataFrame(
        [Row(customer_id=None, customer_name="Charlie", city="Trondheim")],
        schema="customer_id INT, customer_name STRING, city STRING",
    )
    result = rejected_customers(df).collect()[0]
    assert result["rejection_reason"] == "VALID_CUSTOMER_ID"


def test_enrich_customers_adds_customer_key_and_region(spark):
    df = spark.createDataFrame(
        [
            Row(customer_id=1, customer_name="Alice", city="Oslo"),
            Row(customer_id=2, customer_name="Bob", city="Stockholm"),
        ]
    )
    result = {row["customer_id"]: row.asDict() for row in enrich_customers(df).collect()}
    assert result[1]["customer_key"] == 1
    assert result[1]["region"] == "NO"
    assert result[2]["region"] == "UNKNOWN"
