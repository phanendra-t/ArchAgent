"""Feedback storage — JSON file-based store.

Uses a simple file-based store for development speed.
Will be migrated to pgvector PostgreSQL for the reward model embeddings.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
from app.config import get_settings


def _get_store_path() -> Path:
    settings = get_settings()
    return Path(settings.data_dir) / "annotations.json"


def _load_store() -> list[dict]:
    """Load annotations from disk."""
    path = _get_store_path()
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return []


def _save_store(data: list[dict]):
    """Save annotations to disk."""
    path = _get_store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


async def save_annotation(
    finding_id: str,
    review_id: str,
    label: str,
    severity_accuracy: Optional[int] = None,
    explanation_quality: Optional[int] = None,
    actionability: Optional[int] = None,
    comment: Optional[str] = None,
    finding_text: str = "",
    finding_category: str = "",
    finding_severity: str = "",
    rule_violated: str = "",
    context_violated: str = "",
) -> None:
    """Save a human annotation."""
    store = _load_store()
    store.append({
        "finding_id": finding_id,
        "review_id": review_id,
        "label": label,
        "severity_accuracy": severity_accuracy,
        "explanation_quality": explanation_quality,
        "actionability": actionability,
        "comment": comment,
        "finding_text": finding_text,
        "finding_category": finding_category,
        "finding_severity": finding_severity,
        "rule_violated": rule_violated,
        "context_violated": context_violated,
    })
    _save_store(store)


async def get_annotation_count() -> int:
    """Get total number of annotations."""
    return len(_load_store())


async def get_all_annotations() -> list[dict]:
    """Get all stored annotations."""
    return _load_store()


async def get_annotations_by_label(label: str) -> list[dict]:
    """Get annotations filtered by label."""
    store = _load_store()
    return [a for a in store if a["label"] == label]