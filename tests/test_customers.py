from pyspark.sql import Row

from customers import (
    enrich_customers,
    rejected_customers,
    standardize_customers,
    valid_customers,
)


def test_standardize_customers_trims_values(spark):
    df = spark.createDataFrame(
        [
            Row(
                customer_id=1,
                customer_name="  Alice  ",
                city="  Oslo  ",
            )
        ]
    )

    result = standardize_customers(df).collect()[0]

    assert result["customer_name"] == "Alice"
    assert result["city"] == "Oslo"


def test_valid_customers_filters_invalid_rows(spark):
    df = spark.createDataFrame(
        [
            Row(customer_id=1, customer_name="Alice", city="Oslo"),
            Row(customer_id=2, customer_name=None, city="Bergen"),
            Row(customer_id=None, customer_name="Charlie", city="Trondheim"),
        ],
        schema="customer_id INT, customer_name STRING, city STRING",
    )

    result = valid_customers(df)

    assert result.count() == 1
    assert result.collect()[0]["customer_name"] == "Alice"


def test_rejected_customers_adds_reason(spark):
    df = spark.createDataFrame(
        [
            Row(customer_id=1, customer_name=None, city="Bergen"),
        ],
        schema="customer_id INT, customer_name STRING, city STRING",
    )

    result = rejected_customers(df).collect()[0]

    assert result["rejection_reason"] == "NULL_CUSTOMER_NAME"


def test_enrich_customers_adds_customer_key_and_region(spark):
    df = spark.createDataFrame(
        [
            Row(customer_id=1, customer_name="Alice", city="Oslo"),
            Row(customer_id=2, customer_name="Bob", city="Stockholm"),
        ]
    )

    result = {
        row["customer_id"]: row.asDict()
        for row in enrich_customers(df).collect()
    }

    assert result[1]["customer_key"] == 1
    assert result[1]["region"] == "NO"
    assert result[2]["region"] == "UNKNOWN"