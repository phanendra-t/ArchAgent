"""LangGraph-based multi-agent review pipeline."""
from __future__ import annotations
import uuid
import asyncio
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from app.models.intent import ArchitecturalIntent
from app.models.findings import Finding, FindingCategory, Severity, Evidence
from app.parser.diff_parser import ParsedDiff
from app.parser.rule_checker import PreCheckResult
from app.agents.context_reviewer import review_context_boundaries
from app.agents.layer_reviewer import review_layer_violations
from app.agents.security_reviewer import review_security_boundaries
from app.agents.synthesizer import synthesize_findings
from app.agents.defender import defend_findings


class ReviewState(TypedDict):
    """State passed through the review pipeline."""
    diff: ParsedDiff
    intent: ArchitecturalIntent
    pre_check: PreCheckResult
    review_id: str
    # Findings from each agent
    context_findings: list[Finding]
    layer_findings: list[Finding]
    security_findings: list[Finding]
    # Merged and refined
    synthesized_findings: list[Finding]
    final_findings: list[Finding]


async def run_review_pipeline(
    diff: ParsedDiff,
    intent: ArchitecturalIntent,
    pre_check: PreCheckResult,
    review_id: str,
) -> list[Finding]:
    """Execute the full multi-agent review pipeline."""

    # Build initial state
    initial_state: ReviewState = {
        "diff": diff,
        "intent": intent,
        "pre_check": pre_check,
        "review_id": review_id,
        "context_findings": [],
        "layer_findings": [],
        "security_findings": [],
        "synthesized_findings": [],
        "final_findings": [],
    }

    # Run the three reviewer agents in parallel
    context_task = asyncio.create_task(
        review_context_boundaries(diff, intent, pre_check)
    )
    layer_task = asyncio.create_task(
        review_layer_violations(diff, intent, pre_check)
    )
    security_task = asyncio.create_task(
        review_security_boundaries(diff, intent, pre_check)
    )

    context_findings, layer_findings, security_findings = await asyncio.gather(
        context_task, layer_task, security_task
    )

    # Synthesize: merge, dedup, assign severity
    all_findings = context_findings + layer_findings + security_findings
    synthesized = await synthesize_findings(all_findings, diff, intent)

    # Defend: challenge findings to reduce false positives
    final_findings = await defend_findings(synthesized, diff, intent)

    return final_findings
