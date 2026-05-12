import pyspark.pipelines as dlt
import pyspark.sql.functions as F
from pyspark.sql.types import LongType, StringType, StructField, StructType

source_path = spark.conf.get("source_path", "./data")

CDC_SCHEMA = StructType([
    StructField("customer_id", LongType(), True),
    StructField("customer_name", StringType(), True),
    StructField("city", StringType(), True),
    StructField("customer_email", StringType(), True),
    StructField("change_type", StringType(), True),
    StructField("sequence_num", LongType(), True),
])


@dlt.table(name="customers_cdc_bronze", comment="Raw CDC events for customers")
def customers_cdc_bronze():
    return (
        spark.readStream
        .option("header", True)
        .schema(CDC_SCHEMA)
        .csv(f"{source_path}/customers_cdc.csv")
    )


dlt.create_streaming_table(
    "customers_current",
    comment="Current customer state — SCD1 via apply_changes()",
)

dlt.apply_changes(
    target="customers_current",
    source="customers_cdc_bronze",
    keys=["customer_id"],
    sequence_by=F.col("sequence_num"),
    apply_as_deletes=F.expr("change_type = 'DELETE'"),
    except_column_list=["change_type", "sequence_num"],
    stored_as_scd_type=1,
)
