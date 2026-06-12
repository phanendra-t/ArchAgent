"""Feedback API — collect human annotations and manage reward model."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.models.review import FeedbackRequest, FeedbackResponse, RetrainRequest, RetrainResponse
from app.feedback.store import save_annotation, get_annotation_count
from app.reward.trainer import retrain_model
from app.config import get_settings

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """Submit human annotation for a finding."""
    settings = get_settings()

    try:
        await save_annotation(
            finding_id=request.finding_id,
            review_id=request.review_id,
            label=request.label,
            severity_accuracy=request.severity_accuracy,
            explanation_quality=request.explanation_quality,
            actionability=request.actionability,
            comment=request.comment,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save annotation: {e}")

    count = await get_annotation_count()
    reward_active = count >= settings.cold_start_threshold

    return FeedbackResponse(
        status="saved",
        annotation_count=count,
        reward_model_active=reward_active,
        message=f"Annotation saved. {count} total annotations. "
                f"{'Reward model active.' if reward_active else f'Need {settings.cold_start_threshold - count} more for reward model activation.'}",
    )


@router.post("/feedback/retrain", response_model=RetrainResponse)
async def trigger_retrain(request: RetrainRequest):
    """Manually trigger reward model retraining."""
    settings = get_settings()
    count = await get_annotation_count()

    if count < settings.cold_start_threshold:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least {settings.cold_start_threshold} annotations to train. Currently have {count}.",
        )

    try:
        metrics = await retrain_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retraining failed: {e}")

    return RetrainResponse(
        status="retrained",
        accuracy=metrics["accuracy"],
        precision=metrics["precision"],
        recall=metrics["recall"],
        f1=metrics["f1"],
        annotation_count=count,
    )


@router.get("/feedback/stats")
async def get_feedback_stats():
    """Get current feedback and reward model stats."""
    settings = get_settings()
    count = await get_annotation_count()

    return {
        "annotation_count": count,
        "cold_start_threshold": settings.cold_start_threshold,
        "reward_model_active": count >= settings.cold_start_threshold,
        "annotations_needed": max(0, settings.cold_start_threshold - count),
    }
