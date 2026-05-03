import dlt
from pyspark.sql.types import LongType, StringType, StructField, StructType

from customers import CUSTOMER_RULES, enrich_customers, rejected_customers

quality_mode = spark.conf.get("quality_mode", "drop")
source_path = spark.conf.get("source_path", "./data")

expect_fn = dlt.expect_or_fail if quality_mode == "fail" else dlt.expect_or_drop

CUSTOMERS_SCHEMA = StructType([
    StructField("customer_id", LongType(), True),
    StructField("customer_name", StringType(), True),
    StructField("city", StringType(), True),
])


@dlt.table(name="customers_bronze", comment="Raw customer data")
def customers_bronze():
    return (
        spark.read.option("header", True)
        .schema(CUSTOMERS_SCHEMA)
        .csv(f"{source_path}/customers.csv")
    )


@dlt.table(name="customers_silver", comment="Validated customers")
@expect_fn("valid_customer_id", CUSTOMER_RULES["valid_customer_id"])
@expect_fn("valid_customer_name", CUSTOMER_RULES["valid_customer_name"])
def customers_silver():
    return enrich_customers(dlt.read("customers_bronze"))


@dlt.table(name="customers_rejected", comment="Rejected customer rows with reason")
def customers_rejected():
    return rejected_customers(dlt.read("customers_bronze"))
