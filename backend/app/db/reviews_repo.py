"""Reviews repository — persist and query review results."""
from __future__ import annotations
import json
import hashlib
from typing import Optional
from app.db.client import get_pool


async def save_review(
    review_id: str,
    system_name: str,
    diff_text: str,
    spec_file: str,
    health_score: int,
    summary: str,
    findings: list[dict],
    suppressed_findings: list[dict],
    stats: dict,
    reward_model_active: bool,
) -> None:
    """Persist a review result to PostgreSQL."""
    pool = await get_pool()

    diff_hash = hashlib.sha256(diff_text.encode()).hexdigest()[:16]
    diff_preview = diff_text[:500] if diff_text else ""

    await pool.execute(
        """
        INSERT INTO reviews (
            review_id, system_name, diff_hash, diff_preview, spec_file,
            health_score, summary, findings, suppressed_findings, stats,
            reward_model_active
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9::jsonb, $10::jsonb, $11)
        ON CONFLICT (review_id) DO NOTHING
        """,
        review_id,
        system_name,
        diff_hash,
        diff_preview,
        spec_file,
        health_score,
        summary,
        json.dumps(findings),
        json.dumps(suppressed_findings),
        json.dumps(stats),
        reward_model_active,
    )


async def list_reviews(limit: int = 50, offset: int = 0) -> list[dict]:
    """List recent reviews (summary view, no full findings payload)."""
    pool = await get_pool()

    rows = await pool.fetch(
        """
        SELECT
            review_id, system_name, diff_hash, diff_preview, spec_file,
            health_score, summary, stats, reward_model_active, created_at
        FROM reviews
        ORDER BY created_at DESC
        LIMIT $1 OFFSET $2
        """,
        limit,
        offset,
    )

    return [
        {
            "review_id": row["review_id"],
            "system_name": row["system_name"],
            "diff_hash": row["diff_hash"],
            "diff_preview": row["diff_preview"],
            "spec_file": row["spec_file"],
            "health_score": row["health_score"],
            "summary": row["summary"],
            "stats": json.loads(row["stats"]) if row["stats"] else {},
            "reward_model_active": row["reward_model_active"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        }
        for row in rows
    ]


async def get_review(review_id: str) -> Optional[dict]:
    """Fetch full review with findings."""
    pool = await get_pool()

    row = await pool.fetchrow(
        """
        SELECT
            review_id, system_name, diff_hash, diff_preview, spec_file,
            health_score, summary, findings, suppressed_findings, stats,
            reward_model_active, created_at
        FROM reviews
        WHERE review_id = $1
        """,
        review_id,
    )

    if row is None:
        return None

    return {
        "review_id": row["review_id"],
        "system_name": row["system_name"],
        "diff_hash": row["diff_hash"],
        "diff_preview": row["diff_preview"],
        "spec_file": row["spec_file"],
        "health_score": row["health_score"],
        "summary": row["summary"],
        "findings": json.loads(row["findings"]) if row["findings"] else [],
        "suppressed_findings": json.loads(row["suppressed_findings"]) if row["suppressed_findings"] else [],
        "stats": json.loads(row["stats"]) if row["stats"] else {},
        "reward_model_active": row["reward_model_active"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
    }


async def get_review_count() -> int:
    """Get total review count."""
    pool = await get_pool()
    row = await pool.fetchrow("SELECT COUNT(*) as count FROM reviews")
    return row["count"] if row else 0
