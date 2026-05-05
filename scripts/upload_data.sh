#!/usr/bin/env bash
set -euo pipefail

TARGET=${1:-dev}

case "$TARGET" in
  prod)
    VOLUME="dbfs:/Volumes/dataops_lab/sdp_prod/raw"
    DATA_DIR="data/prod"
    ;;
  dev)
    VOLUME="dbfs:/Volumes/dataops_lab/sdp_dev/raw"
    DATA_DIR="data"
    ;;
  *)
    echo "Usage: $0 [dev|prod]"
    exit 1
    ;;
esac

echo "Uploading data files to $VOLUME..."

databricks fs cp "$DATA_DIR/customers.csv" "$VOLUME/customers.csv" --overwrite -t "$TARGET"
databricks fs cp "$DATA_DIR/orders.csv" "$VOLUME/orders.csv" --overwrite -t "$TARGET"

echo "Done."
