from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.getOrCreate()

data = [
    (1, "Alice", "Oslo"),
    (2, None, "Bergen"),
]

df = spark.createDataFrame(data, ["customer_id", "customer_name", "city"])

result = (
    df.filter("customer_name IS NOT NULL")
      .withColumn("region", F.lit("NO"))
)

result.show()