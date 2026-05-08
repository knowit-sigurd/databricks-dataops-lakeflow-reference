import sys

from databricks.sdk import WorkspaceClient


def main():
    if len(sys.argv) != 2:
        print("Usage: cleanup_orphaned_pipeline.py <pipeline_name>")
        sys.exit(1)

    name = sys.argv[1]
    w = WorkspaceClient()

    for p in w.pipelines.list_pipelines():
        if p.name == name:
            print(f"Deleting orphaned pipeline '{name}' ({p.pipeline_id})")
            w.pipelines.delete(pipeline_id=p.pipeline_id)
            return

    print(f"No pipeline named '{name}' found — skipping")


if __name__ == "__main__":
    main()
