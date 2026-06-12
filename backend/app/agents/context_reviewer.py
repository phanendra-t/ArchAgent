"""Context Boundary Reviewer Agent.

Detects violations of bounded context isolation rules.
"""
from __future__ import annotations
import uuid
import json
from anthropic import AsyncAnthropic
from app.models.intent import ArchitecturalIntent
from app.models.findings import Finding, FindingCategory, Severity, Evidence
from app.parser.diff_parser import ParsedDiff
from app.parser.rule_checker import PreCheckResult
from app.config import get_settings

SYSTEM_PROMPT = """You are a bounded context isolation auditor. Your job is to analyze code changes (PR diffs) and identify violations of bounded context boundaries.

You are given:
1. An architectural intent document defining bounded contexts, their ownership, and dependency rules.
2. A PR diff showing code changes.
3. A list of "suspects" — imports that the deterministic pre-checker flagged as potentially crossing context boundaries.

Your task:
- Confirm or reject each suspect based on semantic analysis.
- Find ADDITIONAL violations that the deterministic checker missed (e.g., indirect coupling, shared state, string-based references).
- For each confirmed violation, provide:
  - A clear title
  - Which contexts are involved
  - The specific code evidence
  - Why this violates the architectural intent
  - The impact if left unfixed
  - A concrete recommendation for fixing it

Return your findings as a JSON array. If no violations exist, return an empty array [].

Each finding should have this structure:
{
  "title": "Short descriptive title",
  "description": "Detailed explanation of the violation",
  "source_context": "name of the context that has the violation",
  "target_context": "name of the context being improperly accessed",
  "evidence": [{"file_path": "...", "line_number": N, "code_snippet": "..."}],
  "impact": "What goes wrong if this isn't fixed",
  "recommendation": "Specific fix suggestion",
  "severity": "critical|high|medium|low"
}

Be precise. Only flag genuine violations. If an import is between allowed dependencies, do NOT flag it."""


async def review_context_boundaries(
    diff: ParsedDiff,
    intent: ArchitecturalIntent,
    pre_check: PreCheckResult,
) -> list[Finding]:
    """Use Claude to analyze bounded context violations."""
    settings = get_settings()
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    # Build the context for the LLM
    intent_summary = _build_intent_summary(intent)
    diff_summary = _build_diff_summary(diff, pre_check)
    suspects_summary = _build_suspects_summary(pre_check)

    user_message = f"""## Architectural Intent (Bounded Contexts)

{intent_summary}

## PR Diff

{diff_summary}

## Pre-Check Suspects (potential cross-context imports)

{suspects_summary}

Analyze the diff against the architectural intent. Identify all bounded context violations — both the suspects above and any additional ones you find. Return a JSON array of findings."""

    response = await client.messages.create(
        model=settings.llm_model,
        max_tokens=settings.max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    # Parse the response into Finding objects
    return _parse_response(response.content[0].text)


def _build_intent_summary(intent: ArchitecturalIntent) -> str:
    """Build a concise summary of bounded context rules."""
    lines = []
    for ctx in intent.bounded_contexts:
        lines.append(f"### Context: {ctx.name}")
        lines.append(f"Description: {ctx.description}")
        lines.append(f"Owns: {', '.join(ctx.owns)}")
        if ctx.allowed_dependencies:
            lines.append(f"Allowed dependencies: {', '.join(ctx.allowed_dependencies)}")
        if ctx.forbidden_dependencies:
            lines.append(f"Forbidden dependencies: {', '.join(ctx.forbidden_dependencies)}")
        if ctx.security_boundary:
            lines.append("⚠️ Security boundary")
        lines.append("")

    # Add communication patterns
    if intent.communication_patterns:
        lines.append("### Communication Patterns")
        for cp in intent.communication_patterns:
            lines.append(f"- {cp.between[0]} ↔ {cp.between[1]}: allowed={cp.allowed}, forbidden={cp.forbidden}")
            if cp.reason:
                lines.append(f"  Reason: {cp.reason}")
        lines.append("")

    return "\n".join(lines)


def _build_diff_summary(diff: ParsedDiff, pre_check: PreCheckResult) -> str:
    """Build a summary of the diff focused on context-relevant changes."""
    lines = []
    for file in diff.files:
        ctx = pre_check.file_context_map.get(file.path, "unknown")
        lines.append(f"### {file.path} (context: {ctx})")
        if file.is_new:
            lines.append("(new file)")
        # Show added lines (most relevant for violation detection)
        for line_num, content in file.added_lines[:50]:  # Cap at 50 lines per file
            lines.append(f"+{line_num}: {content.rstrip()}")
        lines.append("")
    return "\n".join(lines)


def _build_suspects_summary(pre_check: PreCheckResult) -> str:
    """Summarize the deterministic pre-check suspects."""
    if not pre_check.suspects:
        return "No deterministic suspects found. Look for semantic/indirect violations."

    lines = []
    context_suspects = [s for s in pre_check.suspects if s.violation_type == "cross_context_import"]
    for s in context_suspects:
        lines.append(f"- {s.file_path}:{s.line_number} — `{s.code}`")
        lines.append(f"  {s.source_context} → {s.target_context} (Rule: {s.rule_reference})")
    return "\n".join(lines) if lines else "No context boundary suspects."


def _parse_response(response_text: str) -> list[Finding]:
    """Parse Claude's JSON response into Finding objects."""
    # Extract JSON from the response (handle markdown code blocks)
    text = response_text.strip()
    if text.startswith("```"):
        # Remove code block markers
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])

    try:
        raw_findings = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON array in the response
        import re
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            raw_findings = json.loads(match.group())
        else:
            return []

    findings = []
    for raw in raw_findings:
        evidence = []
        for ev in raw.get("evidence", []):
            evidence.append(Evidence(
                file_path=ev.get("file_path", ""),
                line_number=ev.get("line_number"),
                code_snippet=ev.get("code_snippet", ""),
            ))

        findings.append(Finding(
            id=f"ctx-{uuid.uuid4().hex[:6]}",
            category=FindingCategory.BOUNDED_CONTEXT,
            severity=Severity(raw.get("severity", "medium")),
            title=raw.get("title", "Bounded context violation"),
            description=raw.get("description", ""),
            evidence=evidence,
            impact=raw.get("impact", ""),
            recommendation=raw.get("recommendation", ""),
            rule_violated=f"bounded_context.{raw.get('source_context', '')}.forbidden_dependencies",
            context_violated=raw.get("source_context", ""),
        ))

    return findings
