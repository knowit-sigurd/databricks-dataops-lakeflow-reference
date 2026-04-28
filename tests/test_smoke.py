def test_spark_session():
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.getOrCreate()
    assert spark is not None
