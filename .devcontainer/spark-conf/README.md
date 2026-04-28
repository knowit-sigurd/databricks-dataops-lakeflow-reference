# Local Spark Config

This directory is intentionally used as `SPARK_CONF_DIR` by the devcontainer.

Keep local Spark defaults here only when they are safe for Spark Connect and
portable for all users of the container. Do not set static Spark configs such as
`spark.sql.warehouse.dir` here; the local Spark Connect pipeline runner may try
to apply them after session creation and fail.

The defaults in `spark-defaults.conf` enable a local Hive-compatible metastore
under `target/metastore_db`, relative to the directory where `spark-pipelines`
is run. Run commands from an example directory so each example gets its own
ignored metastore. This lets repeated local `spark-pipelines run` invocations
remember table metadata instead of leaving orphaned managed-table directories.

The actual managed table data is not in `target/metastore_db`. By default,
Spark writes managed table files under `spark-warehouse/<table-name>/` in the
example directory. Keep this split:

- `target/` is local runner state, pipeline storage, and metastore metadata.
- `spark-warehouse/` is local managed table data, including Parquet files.

Spark Connect may warn that `spark.sql.catalogImplementation` is static and
cannot be modified after session creation. The warning is expected with the
local Spark 4.1 pipeline runner; the Spark server still starts with the setting
from this file.
