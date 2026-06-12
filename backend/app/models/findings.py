"""Pydantic models for review findings."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
from enum import Enum


class FindingCategory(str, Enum):
    BOUNDED_CONTEXT = "bounded_context_violation"
    LAYER_VIOLATION = "layer_violation"
    SECURITY_BOUNDARY = "security_boundary_violation"
    COMMUNICATION_PATTERN = "communication_pattern_violation"
    DEPENDENCY_RULE = "dependency_rule_violation"
    PRINCIPLE_VIOLATION = "principle_violation"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    ADVISORY = "advisory"


class Evidence(BaseModel):
    file_path: str
    line_number: Optional[int] = None
    code_snippet: str
    section_reference: Optional[str] = None  # Reference to intent YAML


class Finding(BaseModel):
    id: str
    category: FindingCategory
    severity: Severity
    title: str
    description: str
    evidence: list[Evidence]
    impact: str
    recommendation: str
    rule_violated: Optional[str] = None
    context_violated: Optional[str] = None
    confidence: float = 1.0  # 0-1, from reward model
    reward_score: Optional[float] = None  # Raw reward model score
    suppressed: bool = False  # Whether reward model suppressed this


class ReviewReport(BaseModel):
    """Complete review output."""
    review_id: str
    spec_file: str
    health_score: int  # 0-100
    summary: str
    findings: list[Finding]
    suppressed_findings: list[Finding] = []  # Findings filtered by reward model
    stats: ReviewStats
    reward_model_active: bool = False


class ReviewStats(BaseModel):
    total_findings: int
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    advisory: int = 0
    suppressed: int = 0
    avg_confidence: float = 1.0
