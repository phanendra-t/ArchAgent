"""Reviews API — list and retrieve persisted reviews."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from app.db.reviews_repo import list_reviews, get_review, get_review_count

router = APIRouter()


@router.get("/reviews")
async def get_reviews(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List recent reviews with summary info."""
    reviews = await list_reviews(limit=limit, offset=offset)
    total = await get_review_count()

    return {
        "reviews": reviews,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/reviews/{review_id}")
async def get_review_detail(review_id: str):
    """Fetch a full review with all findings."""
    review = await get_review(review_id)
    if review is None:
        raise HTTPException(status_code=404, detail=f"Review '{review_id}' not found")
    return review
