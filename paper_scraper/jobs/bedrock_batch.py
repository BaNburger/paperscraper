"""Bedrock Batch API jobs for bulk paper scoring at 50% cost savings.

Flow:
1. Fetch papers from DB, build scoring prompts (6 dims x N papers)
2. Write JSONL input to S3
3. Submit Bedrock batch invocation job
4. Poll for completion (or run as a separate task)
5. Parse JSONL output from S3, write scores to DB
"""

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from paper_scraper.core.config import settings
from paper_scraper.core.database import get_db_session
from paper_scraper.modules.scoring.dimensions.base import PaperContext
from paper_scraper.modules.scoring.models import PaperScore
from paper_scraper.modules.scoring.prompts import render_prompt

logger = logging.getLogger(__name__)

# Bedrock Batch API constants
BATCH_JOB_PREFIX = "ps-scoring-"
DIMENSIONS = [
    "novelty",
    "ip_potential",
    "marketability",
    "feasibility",
    "commercialization",
    "team_readiness",
]


def _build_system_prompt(dimension: str) -> str:
    """Build the system prompt for a scoring dimension."""
    return (
        f"You are an expert evaluator scoring academic papers on the "
        f"'{dimension}' dimension. Return a JSON object with: "
        f"score (0-10), confidence (0-1), reasoning (string), "
        f"and details (object with supporting evidence)."
    )


def _build_scoring_prompt(paper: PaperContext, dimension: str) -> str:
    """Build the user prompt for scoring a paper on a given dimension."""
    try:
        return render_prompt(
            f"{dimension}.jinja2",
            paper=paper,
        )
    except Exception:
        # Fallback to simple prompt if template fails
        return (
            f"Score this paper on {dimension} (0-10):\n\n"
            f"Title: {paper.title}\n"
            f"Abstract: {paper.abstract or 'N/A'}\n"
            f"Keywords: {', '.join(paper.keywords) if paper.keywords else 'N/A'}\n"
        )


def _build_batch_record(
    record_id: str,
    model_id: str,
    paper: PaperContext,
    dimension: str,
) -> dict[str, Any]:
    """Build a single JSONL record for Bedrock Batch API.

    Uses the Bedrock Converse API format for batch invocations.
    """
    system_prompt = _build_system_prompt(dimension)
    user_prompt = _build_scoring_prompt(paper, dimension)

    return {
        "recordId": record_id,
        "modelInput": {
            "modelId": model_id,
            "messages": [
                {"role": "user", "content": [{"text": user_prompt}]},
            ],
            "system": [{"text": system_prompt}],
            "inferenceConfig": {
                "maxTokens": 1500,
                "temperature": 0.3,
            },
        },
    }


async def submit_bedrock_batch_scoring_task(
    ctx: dict[str, Any],
    job_id: str,
    organization_id: str,
    paper_ids: list[str],
    model_id: str | None = None,
) -> dict[str, Any]:
    """Submit a Bedrock batch scoring job.

    Steps:
    1. Fetch papers from DB
    2. Build scoring prompts (6 dims x N papers)
    3. Write JSONL to S3
    4. Submit Bedrock batch invocation job
    5. Store batch_job_arn in ScoringJob metadata

    Args:
        ctx: arq context.
        job_id: ScoringJob UUID string.
        organization_id: Organization UUID string.
        paper_ids: List of paper UUID strings to score.
        model_id: Optional Bedrock model ID override.

    Returns:
        Dict with batch job details.
    """
    import boto3

    job_uuid = UUID(job_id)
    org_uuid = UUID(organization_id)
    resolved_model = model_id or settings.AWS_BEDROCK_MODEL
    s3_bucket = settings.AWS_BEDROCK_BATCH_S3_BUCKET
    region = settings.AWS_REGION

    if not s3_bucket:
        return {"status": "error", "message": "AWS_BEDROCK_BATCH_S3_BUCKET not configured"}

    async with get_db_session() as db:
        from paper_scraper.modules.scoring.service import ScoringService

        service = ScoringService(db)
        await service.update_job_status(job_uuid, "preparing_batch")

        # 1. Fetch papers
        from sqlalchemy import select

        from paper_scraper.modules.papers.models import Paper

        result = await db.execute(
            select(Paper).where(
                Paper.id.in_([UUID(pid) for pid in paper_ids]),
            )
        )
        papers = list(result.scalars().all())

        if not papers:
            await service.update_job_status(job_uuid, "failed", error_message="No papers found")
            return {"status": "error", "message": "No papers found"}

        # 2. Build JSONL batch input
        batch_records = []
        for paper in papers:
            paper_ctx = PaperContext.from_paper(paper)
            for dim in DIMENSIONS:
                record_id = f"{paper.id}|{dim}"
                record = _build_batch_record(record_id, resolved_model, paper_ctx, dim)
                batch_records.append(record)

        jsonl_content = "\n".join(json.dumps(r) for r in batch_records)

        # 3. Upload JSONL to S3
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        s3_input_key = f"bedrock-batch/input/{job_id}_{timestamp}.jsonl"
        s3_output_prefix = f"bedrock-batch/output/{job_id}_{timestamp}/"

        s3_client = boto3.client("s3", region_name=region)
        await asyncio.to_thread(
            s3_client.put_object,
            Bucket=s3_bucket,
            Key=s3_input_key,
            Body=jsonl_content.encode("utf-8"),
            ContentType="application/jsonl",
        )

        logger.info(
            "Uploaded %d batch records to s3://%s/%s",
            len(batch_records),
            s3_bucket,
            s3_input_key,
        )

        # 4. Submit Bedrock batch job
        bedrock_client = boto3.client("bedrock", region_name=region)
        batch_job_name = f"{BATCH_JOB_PREFIX}{job_id[:8]}-{timestamp}"

        try:
            response = await asyncio.to_thread(
                bedrock_client.create_model_invocation_job,
                jobName=batch_job_name,
                modelId=resolved_model,
                roleArn=_get_batch_role_arn(),
                inputDataConfig={
                    "s3InputDataConfig": {
                        "s3Uri": f"s3://{s3_bucket}/{s3_input_key}",
                        "s3InputFormat": "JSONL",
                    }
                },
                outputDataConfig={
                    "s3OutputDataConfig": {
                        "s3Uri": f"s3://{s3_bucket}/{s3_output_prefix}",
                    }
                },
            )
        except Exception as e:
            await service.update_job_status(
                job_uuid, "failed", error_message=f"Bedrock batch submission failed: {e}"
            )
            return {"status": "error", "message": str(e)}

        batch_job_arn = response["jobArn"]

        # 5. Update job with batch ARN
        await service.update_job_status(
            job_uuid,
            "batch_submitted",
        )
        # Store batch metadata for polling
        job = await service.get_job(job_uuid, org_uuid)
        if job:
            job.arq_job_id = batch_job_arn  # Reuse field to store batch ARN
            await db.commit()

        logger.info(
            "Submitted Bedrock batch job %s for scoring job %s (%d papers, %d records)",
            batch_job_arn,
            job_id,
            len(papers),
            len(batch_records),
        )

        return {
            "status": "batch_submitted",
            "job_id": job_id,
            "batch_job_arn": batch_job_arn,
            "papers_count": len(papers),
            "records_count": len(batch_records),
            "s3_input": f"s3://{s3_bucket}/{s3_input_key}",
            "s3_output_prefix": f"s3://{s3_bucket}/{s3_output_prefix}",
        }


async def poll_bedrock_batch_results_task(
    ctx: dict[str, Any],
    job_id: str,
    organization_id: str,
    batch_job_arn: str,
) -> dict[str, Any]:
    """Poll a Bedrock batch job and process results when complete.

    Args:
        ctx: arq context.
        job_id: ScoringJob UUID string.
        organization_id: Organization UUID string.
        batch_job_arn: Bedrock batch job ARN to poll.

    Returns:
        Dict with processing results.
    """
    import boto3

    job_uuid = UUID(job_id)
    org_uuid = UUID(organization_id)
    region = settings.AWS_REGION
    s3_bucket = settings.AWS_BEDROCK_BATCH_S3_BUCKET

    bedrock_client = boto3.client("bedrock", region_name=region)

    # Check job status
    response = await asyncio.to_thread(
        bedrock_client.get_model_invocation_job,
        jobIdentifier=batch_job_arn,
    )

    status = response["status"]
    logger.info("Bedrock batch job %s status: %s", batch_job_arn, status)

    if status in ("InProgress", "Submitted", "Validating", "Scheduled"):
        # Still running — re-enqueue polling after delay
        from paper_scraper.jobs.worker import enqueue_job

        await enqueue_job(
            "poll_bedrock_batch_results_task",
            job_id,
            organization_id,
            batch_job_arn,
            _defer_by=120,  # Poll again in 2 minutes
        )
        return {"status": "polling", "batch_status": status}

    if status == "Failed":
        async with get_db_session() as db:
            from paper_scraper.modules.scoring.service import ScoringService

            service = ScoringService(db)
            error_msg = response.get("message", "Bedrock batch job failed")
            await service.update_job_status(job_uuid, "failed", error_message=error_msg)
        return {"status": "failed", "message": error_msg}

    if status != "Completed":
        return {"status": "unknown", "batch_status": status}

    # Job completed — download and parse results
    output_uri = response.get("outputDataConfig", {}).get("s3OutputDataConfig", {}).get("s3Uri", "")
    if not output_uri:
        return {"status": "error", "message": "No output URI in completed job"}

    # Parse S3 URI to get bucket and prefix
    output_key_prefix = output_uri.replace(f"s3://{s3_bucket}/", "")

    s3_client = boto3.client("s3", region_name=region)

    # List output files
    list_response = await asyncio.to_thread(
        s3_client.list_objects_v2,
        Bucket=s3_bucket,
        Prefix=output_key_prefix,
    )

    output_files = [obj["Key"] for obj in list_response.get("Contents", []) if obj["Key"].endswith(".jsonl")]

    if not output_files:
        return {"status": "error", "message": "No output files found"}

    # Parse all output files
    all_results: dict[str, dict[str, Any]] = {}  # paper_id -> {dim -> result}
    parse_errors = 0

    for output_key in output_files:
        obj_response = await asyncio.to_thread(
            s3_client.get_object,
            Bucket=s3_bucket,
            Key=output_key,
        )
        content = obj_response["Body"].read().decode("utf-8")

        for line in content.strip().split("\n"):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                record_id = record.get("recordId", "")
                if "|" not in record_id:
                    parse_errors += 1
                    continue

                paper_id_str, dimension = record_id.split("|", 1)

                # Extract the LLM response text
                model_output = record.get("modelOutput", {})
                output_content = model_output.get("output", {}).get("message", {}).get("content", [])
                response_text = ""
                for block in output_content:
                    if "text" in block:
                        response_text = block["text"]
                        break

                if not response_text:
                    parse_errors += 1
                    continue

                # Parse the JSON scoring response
                try:
                    score_data = json.loads(response_text)
                except json.JSONDecodeError:
                    # Try to extract JSON from markdown code block
                    import re

                    json_match = re.search(r"```json?\s*\n?(.*?)\n?```", response_text, re.DOTALL)
                    if json_match:
                        score_data = json.loads(json_match.group(1))
                    else:
                        parse_errors += 1
                        continue

                if paper_id_str not in all_results:
                    all_results[paper_id_str] = {}
                all_results[paper_id_str][dimension] = score_data

            except Exception as e:
                logger.warning("Failed to parse batch record: %s", e)
                parse_errors += 1

    # Write scores to DB
    completed = 0
    failed = 0

    async with get_db_session() as db:
        from paper_scraper.modules.scoring.service import ScoringService

        service = ScoringService(db)

        for paper_id_str, dim_scores in all_results.items():
            try:
                paper_uuid = UUID(paper_id_str)

                # Build score from dimension results
                score_data = {
                    "paper_id": paper_uuid,
                    "organization_id": org_uuid,
                    "model_version": f"bedrock-batch-{settings.AWS_BEDROCK_MODEL}",
                    "scored_at": datetime.now(UTC),
                }

                for dim in DIMENSIONS:
                    if dim in dim_scores:
                        raw_score = dim_scores[dim].get("score", 0)
                        score_val = max(0.0, min(10.0, float(raw_score)))
                        score_data[dim] = score_val

                # Calculate overall score (equal weights)
                dim_values = [score_data.get(d, 0.0) for d in DIMENSIONS if d in score_data]
                if dim_values:
                    score_data["overall_score"] = round(sum(dim_values) / len(dim_values), 2)
                    score_data["confidence"] = round(
                        sum(
                            dim_scores.get(d, {}).get("confidence", 0.5)
                            for d in DIMENSIONS
                            if d in dim_scores
                        )
                        / max(len(dim_values), 1),
                        2,
                    )

                paper_score = PaperScore(**score_data)
                db.add(paper_score)
                completed += 1

            except Exception as e:
                logger.warning("Failed to write score for paper %s: %s", paper_id_str, e)
                failed += 1

        await db.commit()

        # Update job status
        final_status = "completed" if failed == 0 else "completed_with_errors"
        error_msg = None
        if failed > 0 or parse_errors > 0:
            error_msg = f"{failed} papers failed, {parse_errors} parse errors"

        await service.update_job_status(
            job_uuid,
            final_status,
            completed_papers=completed,
            failed_papers=failed,
            error_message=error_msg,
        )
        await db.commit()

    logger.info(
        "Bedrock batch results processed for job %s: %d completed, %d failed, %d parse errors",
        job_id,
        completed,
        failed,
        parse_errors,
    )

    return {
        "status": final_status,
        "job_id": job_id,
        "completed": completed,
        "failed": failed,
        "parse_errors": parse_errors,
    }


def _get_batch_role_arn() -> str:
    """Get the IAM role ARN for Bedrock batch jobs.

    This role needs:
    - bedrock:InvokeModel permission
    - s3:GetObject/PutObject on the batch bucket
    """
    import os

    return os.environ.get(
        "AWS_BEDROCK_BATCH_ROLE_ARN",
        "arn:aws:iam::role/PaperScraperBedrockBatchRole",
    )
