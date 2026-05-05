import sys
import time

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.pipelines import GetUpdateResponse, UpdateInfoState

TERMINAL_STATES = {
    UpdateInfoState.COMPLETED,
    UpdateInfoState.FAILED,
    UpdateInfoState.CANCELED,
}


def main():
    if len(sys.argv) != 2:
        print("Usage: stop_pipeline.py <pipeline_name>")
        sys.exit(1)

    pipeline_name = sys.argv[1]
    w = WorkspaceClient()

    matches = [p for p in w.pipelines.list_pipelines() if p.name == pipeline_name]
    if not matches:
        print(f"No pipeline found with name '{pipeline_name}' — nothing to stop.")
        sys.exit(0)

    pipeline_id = matches[0].pipeline_id
    pipeline = w.pipelines.get(pipeline_id)

    if pipeline.latest_updates:
        latest = pipeline.latest_updates[0]
        if latest.state not in TERMINAL_STATES:
            print(f"Active update {latest.update_id} in state {latest.state} — stopping pipeline.")
            w.pipelines.stop(pipeline_id)
            for _ in range(60):
                time.sleep(5)
                pipeline = w.pipelines.get(pipeline_id)
                if not pipeline.latest_updates or pipeline.latest_updates[0].state in TERMINAL_STATES:
                    print("Pipeline stopped.")
                    sys.exit(0)
            print("Timed out waiting for pipeline to stop.")
            sys.exit(1)

    print(f"Pipeline '{pipeline_name}' has no active updates.")


if __name__ == "__main__":
    main()
