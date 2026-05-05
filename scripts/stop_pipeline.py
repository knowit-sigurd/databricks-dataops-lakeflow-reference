import sys
import time

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.pipelines import PipelineState, UpdateInfoState

TERMINAL_UPDATE_STATES = {
    UpdateInfoState.COMPLETED,
    UpdateInfoState.FAILED,
    UpdateInfoState.CANCELED,
}

IDLE_PIPELINE_STATES = {
    PipelineState.IDLE,
    PipelineState.FAILED,
    PipelineState.DELETED,
}


def wait_for_idle(w, pipeline_id, timeout_steps=60):
    for _ in range(timeout_steps):
        time.sleep(5)
        pipeline = w.pipelines.get(pipeline_id)
        print(f"  pipeline state: {pipeline.state}")
        if pipeline.state in IDLE_PIPELINE_STATES:
            print("Pipeline is idle.")
            return
    print("Timed out waiting for pipeline to reach idle state.")
    sys.exit(1)


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
        if latest.state not in TERMINAL_UPDATE_STATES:
            print(f"Active update {latest.update_id} in state {latest.state} — stopping pipeline.")
            w.pipelines.stop(pipeline_id)

    # Always wait for IDLE regardless of whether we stopped or not,
    # in case a previous stop left the pipeline still transitioning.
    if pipeline.state not in IDLE_PIPELINE_STATES:
        print(f"Pipeline in state {pipeline.state} — waiting for idle.")
        wait_for_idle(w, pipeline_id)
    else:
        print(f"Pipeline '{pipeline_name}' is idle.")


if __name__ == "__main__":
    main()
