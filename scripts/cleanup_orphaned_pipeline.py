import sys

from databricks.sdk import WorkspaceClient


def matches(actual_name: str, base_name: str) -> bool:
    # DAB prefixes dev-target resources with "[dev <user>] "
    return actual_name == base_name or actual_name.endswith(f"] {base_name}")


def cleanup_pipeline(w: WorkspaceClient, base_name: str) -> None:
    # Use filter= to let the API narrow results server-side. Iterating all
    # pipelines without a filter can miss results in large workspaces.
    deleted = False
    for p in w.pipelines.list_pipelines(filter=f"name LIKE '%{base_name}%'"):
        if p.name and matches(p.name, base_name):
            print(f"Deleting orphaned pipeline '{p.name}' ({p.pipeline_id})")
            w.pipelines.delete(pipeline_id=p.pipeline_id)
            deleted = True
    if not deleted:
        print(f"No pipeline matching '{base_name}' found — skipping")


def cleanup_job(w: WorkspaceClient, base_name: str) -> None:
    deleted = False
    for j in w.jobs.list():
        if j.settings and j.settings.name and matches(j.settings.name, base_name):
            print(f"Deleting orphaned job '{j.settings.name}' ({j.job_id})")
            w.jobs.delete(job_id=j.job_id)
            deleted = True
    if not deleted:
        print(f"No job matching '{base_name}' found — skipping")


def main():
    if len(sys.argv) != 2:
        print("Usage: cleanup_orphaned_pipeline.py <deployment_suffix>")
        sys.exit(1)

    suffix = sys.argv[1]
    w = WorkspaceClient()

    cleanup_pipeline(w, f"{suffix}_medallion_pipeline")
    cleanup_job(w, f"{suffix}_medallion_operational_job")


if __name__ == "__main__":
    main()
