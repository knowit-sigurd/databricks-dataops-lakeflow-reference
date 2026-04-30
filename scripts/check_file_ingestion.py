### This script was only used once to check that the files were ingested correctly. It is not used in the final pipeline.

from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

customers = (
    spark.read.option("header", True)
    .option("inferSchema", True)
    .csv("data/customers.csv")
)

orders = (
    spark.read.option("header", True)
    .option("inferSchema", True)
    .csv("data/orders.csv")
)

customers.show()
customers.printSchema()

orders.show()
orders.printSchema()