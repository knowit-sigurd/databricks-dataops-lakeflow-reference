from dataclasses import replace
from datetime import datetime, timezone

from databricks.bundles.core import Bundle, job_mutator, pipeline_mutator
from databricks.bundles.jobs._models.job import Job
from databricks.bundles.pipelines._models.pipeline import Pipeline


def _deployed_at() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@pipeline_mutator
def set_pipeline_context(bundle: Bundle, pipeline: Pipeline) -> Pipeline:
    tags = {**(bundle.resolve_variable(pipeline.tags) or {}), "deployed_at": _deployed_at()}
    return replace(pipeline, tags=tags)


@job_mutator
def set_job_context(bundle: Bundle, job: Job) -> Job:
    tags = {**(bundle.resolve_variable(job.tags) or {}), "deployed_at": _deployed_at()}
    return replace(job, tags=tags)
