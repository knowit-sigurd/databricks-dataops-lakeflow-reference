import pyspark.pipelines as dlt
import pyspark.sql.functions as F
from pyspark.sql.types import LongType, StringType, StructField, StructType

from customers import CUSTOMER_RULES, enrich_customers, rejected_customers, standardize_customers

quality_mode = spark.conf.get("quality_mode", "drop")
source_path = spark.conf.get("source_path", "./data")


def expect_for(rule_name):
    rule = CUSTOMER_RULES[rule_name]
    if rule["severity"] == "critical":
        fn = dlt.expect_or_fail if quality_mode == "fail" else dlt.expect_or_drop
    elif rule["severity"] == "business_invalid":
        fn = dlt.expect_or_drop
    else:
        fn = dlt.expect
    return fn(rule_name, rule["condition"])


CUSTOMERS_SCHEMA = StructType([
    StructField("customer_id", LongType(), True),
    StructField("customer_name", StringType(), True),
    StructField("city", StringType(), True),
    StructField("customer_email", StringType(), True),
])


@dlt.table(name="customers_bronze", comment="Raw customer data")
def customers_bronze():
    return (
        spark.read.option("header", True)
        .schema(CUSTOMERS_SCHEMA)
        .csv(f"{source_path}/customers.csv")
        .withColumn("_source_file", F.input_file_name())
        .withColumn("_ingested_at", F.current_timestamp())
        .withColumn("_ingest_run_id", F.lit(spark.conf.get("spark.databricks.clusterUsageTags.runId", "unknown")))
    )


@dlt.table(name="customers_silver", comment="Validated customers")
@expect_for("valid_customer_id")
@expect_for("valid_customer_name")
def customers_silver():
    return enrich_customers(standardize_customers(dlt.read("customers_bronze")))


@dlt.table(name="customers_rejected", comment="Rejected customer rows with reason and severity")
def customers_rejected():
    return rejected_customers(dlt.read("customers_bronze"))
