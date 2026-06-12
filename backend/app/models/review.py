"""Pydantic models for review API requests/responses."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class ReviewRequest(BaseModel):
    """Request to review a PR diff against architectural intent."""
    diff: str  # Unified diff content
    intent_yaml: Optional[str] = None  # YAML content (if not using default)
    intent_file: Optional[str] = None  # Path to YAML file
    context_files: list[str] = []  # Additional source files for context


class ReviewResponse(BaseModel):
    """Streaming review response."""
    review_id: str
    status: str  # "in_progress" | "completed" | "error"
    message: Optional[str] = None


class FeedbackRequest(BaseModel):
    """Human annotation for a finding."""
    review_id: str
    finding_id: str
    label: str  # "valid" | "false_positive" | "partial"
    severity_accuracy: Optional[int] = None  # 1-5
    explanation_quality: Optional[int] = None  # 1-5
    actionability: Optional[int] = None  # 1-5
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Response after submitting feedback."""
    status: str
    annotation_count: int  # Total annotations so far
    reward_model_active: bool
    message: str


class RetrainRequest(BaseModel):
    """Request to retrain the reward model."""
    pass


class RetrainResponse(BaseModel):
    """Response after retraining."""
    status: str
    accuracy: float
    precision: float
    recall: float
    f1: float
    annotation_count: int
