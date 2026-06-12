"""Core reviewer — pure orchestration logic used by both CLI and API."""
from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass, field
from app.models.intent import ArchitecturalIntent
from app.models.findings import Finding, ReviewReport, ReviewStats
from app.parser.intent_parser import parse_intent_file, parse_intent_string
from app.parser.diff_parser import parse_diff, ParsedDiff
from app.parser.rule_checker import run_pre_check, PreCheckResult
from app.agents.graph import run_review_pipeline
from app.reward.scorer import score_findings
import uuid


@dataclass
class ReviewOptions:
    """Options for a review run."""
    intent_path: str | None = None
    intent_yaml: str | None = None
    no_reward: bool = False
    review_id: str | None = None


async def review(diff_text: str, options: ReviewOptions | None = None) -> ReviewReport:
    """Run a full architectural review on a diff.
    
    This is the single entry point used by both CLI and API.
    
    Args:
        diff_text: Unified diff string
        options: Review configuration
        
    Returns:
        Complete ReviewReport with findings, scores, and stats
    """
    if options is None:
        options = ReviewOptions()

    review_id = options.review_id or str(uuid.uuid4())[:8]

    # Load architectural intent
    intent = _load_intent(options)

    # Parse the diff
    diff = parse_diff(diff_text)
    if not diff.files:
        return _empty_report(review_id)

    # Deterministic pre-check
    pre_check = run_pre_check(diff, intent)

    # Run multi-agent pipeline
    findings = await run_review_pipeline(
        diff=diff,
        intent=intent,
        pre_check=pre_check,
        review_id=review_id,
    )

    # Score with reward model (unless disabled)
    if options.no_reward:
        scored_findings = findings
        suppressed = []
        reward_active = False
    else:
        scored_findings, suppressed, reward_active = await score_findings(findings)

    # Calculate health score and stats
    health_score = calculate_health_score(scored_findings)
    stats = build_stats(scored_findings, suppressed)

    report = ReviewReport(
        review_id=review_id,
        spec_file=options.intent_path or "default",
        health_score=health_score,
        summary=generate_summary(scored_findings, health_score),
        findings=scored_findings,
        suppressed_findings=suppressed,
        stats=stats,
        reward_model_active=reward_active,
    )

    # Persist to database (non-blocking on failure)
    await persist_review(report, intent, diff_text)

    return report


async def persist_review(report: ReviewReport, intent: ArchitecturalIntent, diff_text: str) -> None:
    """Persist review to database. Fails silently — review still returns to user."""
    try:
        from app.db.reviews_repo import save_review
        await save_review(
            review_id=report.review_id,
            system_name=intent.system,
            diff_text=diff_text,
            spec_file=report.spec_file,
            health_score=report.health_score,
            summary=report.summary,
            findings=[f.model_dump(mode="json") for f in report.findings],
            suppressed_findings=[f.model_dump(mode="json") for f in report.suppressed_findings],
            stats=report.stats.model_dump(mode="json"),
            reward_model_active=report.reward_model_active,
        )
    except Exception as e:
        print(f"Warning: failed to persist review {report.review_id}: {e}")


def _load_intent(options: ReviewOptions) -> ArchitecturalIntent:
    """Load architectural intent from options."""
    if options.intent_yaml:
        return parse_intent_string(options.intent_yaml)
    
    intent_path = options.intent_path
    if not intent_path:
        # Try common default locations
        candidates = [
            "/app/architecture-intent.yaml",
            "architecture-intent.yaml",
            "architecture-intent.yml",
            ".archagent/intent.yaml",
            "../sample-system/architecture-intent.yaml",
            "sample-system/architecture-intent.yaml",
            "/app/tests/corpus/architecture-intent.yaml",
        ]
        for candidate in candidates:
            if Path(candidate).exists():
                intent_path = candidate
                break
    
    if not intent_path:
        raise FileNotFoundError(
            "No architecture-intent.yaml found. "
            "Mount one at /app/architecture-intent.yaml or use --intent flag."
        )
    
    return parse_intent_file(intent_path)


def calculate_health_score(findings: list[Finding]) -> int:
    """Calculate health score (100 = perfect, 0 = terrible)."""
    if not findings:
        return 100

    penalty = 0
    for f in findings:
        if f.suppressed:
            continue
        if f.severity.value == "critical":
            penalty += 20
        elif f.severity.value == "high":
            penalty += 12
        elif f.severity.value == "medium":
            penalty += 6
        elif f.severity.value == "low":
            penalty += 3
        else:
            penalty += 1

    return max(0, 100 - penalty)


def build_stats(findings: list[Finding], suppressed: list[Finding]) -> ReviewStats:
    """Build review statistics."""
    stats = ReviewStats(
        total_findings=len(findings),
        suppressed=len(suppressed),
    )
    for f in findings:
        if f.severity.value == "critical":
            stats.critical += 1
        elif f.severity.value == "high":
            stats.high += 1
        elif f.severity.value == "medium":
            stats.medium += 1
        elif f.severity.value == "low":
            stats.low += 1
        else:
            stats.advisory += 1

    confidences = [f.confidence for f in findings]
    stats.avg_confidence = sum(confidences) / len(confidences) if confidences else 1.0
    return stats


def generate_summary(findings: list[Finding], health_score: int) -> str:
    """Generate a human-readable summary."""
    if not findings:
        return "No architectural violations detected. The PR conforms to the defined intent."

    critical = sum(1 for f in findings if f.severity.value == "critical")
    high = sum(1 for f in findings if f.severity.value == "high")

    parts = []
    if critical:
        parts.append(f"{critical} critical")
    if high:
        parts.append(f"{high} high-severity")

    severity_text = " and ".join(parts) if parts else "minor"

    return (
        f"Found {len(findings)} architectural violations ({severity_text}). "
        f"Health score: {health_score}/100. "
        f"Review the findings below for details and remediation suggestions."
    )


def _empty_report(review_id: str) -> ReviewReport:
    """Return an empty report when no files are in the diff."""
    return ReviewReport(
        review_id=review_id,
        spec_file="none",
        health_score=100,
        summary="No files found in diff.",
        findings=[],
        suppressed_findings=[],
        stats=ReviewStats(total_findings=0),
        reward_model_active=False,
    )
