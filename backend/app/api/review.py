"""Review API endpoint — thin wrapper around core.reviewer."""
from __future__ import annotations
import json
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.review import ReviewRequest
from app.models.findings import ReviewReport
from app.core.reviewer import review, ReviewOptions

router = APIRouter()


@router.post("/review", response_model=ReviewReport)
async def create_review(request: ReviewRequest):
    """Submit a PR diff for architectural review."""
    try:
        options = ReviewOptions(
            intent_path=request.intent_file,
            intent_yaml=request.intent_yaml,
        )
        report = await review(request.diff, options)
        return report
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review failed: {e}")


@router.post("/review/stream")
async def create_review_stream(request: ReviewRequest):
    """Stream review findings as they are discovered (SSE)."""

    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'status', 'message': 'Starting review...'})}\n\n"
            await asyncio.sleep(0.1)

            options = ReviewOptions(
                intent_path=request.intent_file,
                intent_yaml=request.intent_yaml,
            )
            report = await review(request.diff, options)

            # Stream each finding
            for finding in report.findings:
                yield f"data: {json.dumps({'type': 'finding', 'data': finding.model_dump()}, default=str)}\n\n"
                await asyncio.sleep(0.05)

            # Final summary
            yield f"data: {json.dumps({'type': 'complete', 'health_score': report.health_score, 'stats': report.stats.model_dump(), 'reward_model_active': report.reward_model_active})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
