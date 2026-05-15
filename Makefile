TARGET      := dev
SUFFIX      := dev
SCHEMA      := sdp_dev
SOURCE_PATH := /Volumes/dataops_lab/sdp_dev/raw

BUNDLE_VARS := --var=deployment_suffix=$(SUFFIX) --var=target_schema=$(SCHEMA) --var=source_path=$(SOURCE_PATH)

.PHONY: help lint test ci upload validate deploy stop run job assert clean upload-autoloader stop-autoloader run-autoloader

help:
	@echo "Usage: make <target> [TARGET=dev] [SUFFIX=dev] [SCHEMA=sdp_dev]"
	@echo ""
	@echo "  lint      Run ruff linter"
	@echo "  test      Run pytest"
	@echo "  ci        Lint + test (mirrors CI)"
	@echo "  upload    Upload fixture data to UC volume"
	@echo "  validate  Validate bundle config"
	@echo "  deploy    Deploy bundle (cleans orphans + state first)"
	@echo "  stop      Stop active pipeline update and wait for IDLE"
	@echo "  run       Full-refresh medallion_pipeline"
	@echo "  job       Run the full Lakeflow job (pipeline + assert + contract)"
	@echo "  assert    Assert row counts against expected_counts.json"
	@echo "  clean               Destroy bundle and clean local state"
	@echo "  upload-autoloader   Upload v1 fixture data to autoloader volume"
	@echo "  run-autoloader      Trigger autoloader_pipeline (incremental)"

lint:
	uv run ruff check .

test:
	uv run pytest

ci: lint test

upload:
	./scripts/upload_data.sh $(TARGET) $(SCHEMA)

validate:
	databricks bundle validate -t $(TARGET) $(BUNDLE_VARS)

deploy:
	uv run python scripts/cleanup_orphaned_pipeline.py $(SUFFIX)
	rm -rf .databricks/bundle
	databricks bundle deploy -t $(TARGET) $(BUNDLE_VARS) --auto-approve

stop:
	uv run python scripts/stop_pipeline.py $(SUFFIX)_medallion_pipeline

run: stop
	databricks bundle run medallion_pipeline -t $(TARGET) $(BUNDLE_VARS) --refresh-all

job:
	databricks bundle run medallion_operational_job -t $(TARGET) $(BUNDLE_VARS)

assert:
	uv run python scripts/validate_counts.py $(SCHEMA)

clean:
	uv run python scripts/cleanup_orphaned_pipeline.py $(SUFFIX)
	databricks bundle destroy -t $(TARGET) $(BUNDLE_VARS) --auto-approve || true
	rm -rf .databricks/bundle

upload-autoloader:
	databricks fs mkdirs dbfs:/Volumes/dataops_lab/$(SCHEMA)/raw/autoloader -t $(TARGET)
	databricks fs cp data/autoloader/orders_v1.csv dbfs:/Volumes/dataops_lab/$(SCHEMA)/raw/autoloader/ --overwrite -t $(TARGET)

stop-autoloader:
	uv run python scripts/stop_pipeline.py $(SUFFIX)_autoloader_pipeline

run-autoloader: stop-autoloader
	databricks bundle run autoloader_pipeline -t $(TARGET) $(BUNDLE_VARS) --refresh-all
