from pyspark.sql import DataFrame
from pyspark.sql import functions as F

# placeholder: real logic would use a configuration-driven lookup
NO_CITIES = {"Oslo", "Bergen", "Trondheim"}


def derive_region(df: DataFrame, city_col: str = "city") -> DataFrame:
    return df.withColumn(
        "region",
        F.when(F.col(city_col).isin(*NO_CITIES), F.lit("NO")).otherwise(F.lit("UNKNOWN")),
    )
