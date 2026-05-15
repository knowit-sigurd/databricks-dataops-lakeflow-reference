"""Delete PR-scoped dev pipelines, jobs, and UC schemas older than AGE_DAYS days."""

import re
import sys
from datetime import datetime, timedelta, timezone

from databricks.sdk import WorkspaceClient

CATALOG = "dataops_lab"
AGE_DAYS = int(next((a for a in sys.argv[1:] if a.isdigit()), "7"))
DRY_RUN = "--dry-run" in sys.argv
PR_NAME_RE = re.compile(r"(^\[.*?\] )?pr_\d+_")
PR_SCHEMA_RE = re.compile(r"^sdp_pr_\d+$")


def epoch_ms_to_dt(epoch_ms: int) -> datetime:
    return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc)


def main() -> None:
    w = WorkspaceClient()
    cutoff = datetime.now(timezone.utc) - timedelta(days=AGE_DAYS)
    prefix = "[dry-run] " if DRY_RUN else ""
    deleted = {"pipelines": 0, "jobs": 0, "schemas": 0}

    print(f"Cutoff: resources older than {AGE_DAYS} day(s) ({cutoff.date()})\n")

    for p in w.pipelines.list_pipelines():
        if not PR_NAME_RE.search(p.name or ""):
            continue
        modified = epoch_ms_to_dt(p.last_modified or 0)
        if modified < cutoff:
            print(f"{prefix}Delete pipeline: {p.name} (last modified: {modified.date()})")
            if not DRY_RUN:
                w.pipelines.delete(pipeline_id=p.pipeline_id)
            deleted["pipelines"] += 1

    for j in w.jobs.list():
        name = (j.settings.name if j.settings else "") or ""
        if not PR_NAME_RE.search(name):
            continue
        created = epoch_ms_to_dt(j.created_time or 0)
        if created < cutoff:
            print(f"{prefix}Delete job: {name} (created: {created.date()})")
            if not DRY_RUN:
                w.jobs.delete(job_id=j.job_id)
            deleted["jobs"] += 1

    for s in w.schemas.list(catalog_name=CATALOG):
        if not PR_SCHEMA_RE.match(s.name or ""):
            continue
        created = epoch_ms_to_dt(s.created_at or 0)
        if created < cutoff:
            print(f"{prefix}Delete schema: {CATALOG}.{s.name} (created: {created.date()})")
            if not DRY_RUN:
                w.schemas.delete(full_name=f"{CATALOG}.{s.name}")
            deleted["schemas"] += 1

    print(
        f"\n{'Would delete' if DRY_RUN else 'Deleted'}: "
        f"{deleted['pipelines']} pipeline(s), "
        f"{deleted['jobs']} job(s), "
        f"{deleted['schemas']} schema(s)."
    )


if __name__ == "__main__":
    main()
