import pyspark.pipelines as dlt
from pyspark.sql.functions import col, current_timestamp

source_path = spark.conf.get("autoloader_source_path")
schema_location = spark.conf.get("autoloader_schema_location")

SCHEMA_HINTS = "order_id STRING, customer_id STRING, amount DECIMAL(10,2), order_date DATE"


@dlt.table(comment="Raw orders via Auto Loader. _rescued_data captures rows that fail schema.")
def orders_autoloader_bronze():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("cloudFiles.schemaLocation", schema_location)
        .option("cloudFiles.schemaHints", SCHEMA_HINTS)
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .option("rescuedDataColumn", "_rescued_data")
        .option("header", "true")
        .load(source_path)
        .withColumn("_ingested_at", current_timestamp())
    )


@dlt.table(comment="Clean orders — rows with rescue data excluded.")
@dlt.expect_or_drop("valid_order_id", "order_id IS NOT NULL")
def orders_autoloader_silver():
    return dlt.read_stream("orders_autoloader_bronze").filter(
        col("_rescued_data").isNull()
    )


@dlt.table(comment="Malformed rows captured by Auto Loader rescue.")
def orders_autoloader_rescued():
    return dlt.read_stream("orders_autoloader_bronze").filter(
        col("_rescued_data").isNotNull()
    )
