import pyspark.pipelines as dlt

from gold import build_customer_order_summary


@dlt.table(
    name="customer_order_summary",
    comment="Gold customer order summary",
)
def customer_order_summary():
    customers_df = dlt.read("customers_silver")
    orders_df = dlt.read("orders_silver")

    return build_customer_order_summary(customers_df, orders_df)