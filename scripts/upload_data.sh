#!/usr/bin/env bash
set -euo pipefail

TARGET=${1:-dev}

case "$TARGET" in
  prod)
    VOLUME="dbfs:/Volumes/dataops_lab/sdp_prod/raw"
    ;;
  dev|test)
    VOLUME="dbfs:/Volumes/dataops_lab/sdp_dev/raw"
    ;;
  *)
    echo "Usage: $0 [dev|test|prod]"
    exit 1
    ;;
esac

echo "Uploading data files to $VOLUME..."

databricks fs cp data/customers.csv "$VOLUME/customers.csv" --overwrite -t "$TARGET"
databricks fs cp data/orders.csv "$VOLUME/orders.csv" --overwrite -t "$TARGET"

echo "Done."
