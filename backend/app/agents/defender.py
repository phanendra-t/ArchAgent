"""Defender Agent — challenges findings to reduce false positives.

Acts as devil's advocate: for each finding, argues why it might NOT be a violation.
Only findings that survive the challenge are kept.
"""
from __future__ import annotations
import json
from anthropic import AsyncAnthropic
from app.models.intent import ArchitecturalIntent
from app.models.findings import Finding
from app.parser.diff_parser import ParsedDiff
from app.config import get_settings

SYSTEM_PROMPT = """You are a defender agent. Your job is to CHALLENGE architectural violation findings and determine which ones are genuine vs. false positives.

For each finding, consider:
1. Is the import/dependency actually crossing a boundary, or is it within the same context?
2. Is there a legitimate reason this dependency exists (e.g., shared interfaces, dependency injection)?
3. Is the severity appropriate, or is it over-stated?
4. Could this be an intentional architectural decision (e.g., a pragmatic exception)?

For each finding, return a verdict:
- "valid" — this is a genuine violation, keep it
- "false_positive" — this is not actually a violation, remove it
- "downgrade" — it's a valid concern but severity should be lowered

Return a JSON array of objects:
[
  {"id": "finding-id", "verdict": "valid|false_positive|downgrade", "reason": "explanation"}
]

Be fair but skeptical. Only mark as false_positive if you have a clear reason."""


async def defend_findings(
    findings: list[Finding],
    diff: ParsedDiff,
    intent: ArchitecturalIntent,
) -> list[Finding]:
    """Challenge each finding and remove false positives."""
    if not findings:
        return []

    settings = get_settings()
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    # Prepare findings for the defender
    findings_summary = json.dumps(
        [
            {
                "id": f.id,
                "title": f.title,
                "category": f.category.value,
                "severity": f.severity.value,
                "description": f.description,
                "evidence": [e.model_dump() for e in f.evidence],
                "rule_violated": f.rule_violated,
            }
            for f in findings
        ],
        indent=2,
    )

    # Provide architectural context
    intent_summary = _intent_summary(intent)

    user_message = f"""## Architectural Intent Summary
{intent_summary}

## Findings to Challenge

{findings_summary}

For each finding, determine: is this a genuine architectural violation, or a false positive?
Return your verdicts as a JSON array."""

    response = await client.messages.create(
        model=settings.llm_model,
        max_tokens=settings.max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    # Parse verdicts
    text = response.content[0].text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])

    try:
        verdicts = json.loads(text)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            verdicts = json.loads(match.group())
        else:
            # If defender fails, return all findings (safe default)
            return findings

    # Apply verdicts
    verdict_map = {v["id"]: v for v in verdicts}
    final_findings = []

    for finding in findings:
        verdict = verdict_map.get(finding.id, {})
        verdict_type = verdict.get("verdict", "valid")

        if verdict_type == "false_positive":
            # Remove this finding
            continue
        elif verdict_type == "downgrade":
            # Lower severity by one level
            finding = finding.model_copy()
            severity_order = ["critical", "high", "medium", "low", "advisory"]
            current_idx = severity_order.index(finding.severity.value)
            if current_idx < len(severity_order) - 1:
                from app.models.findings import Severity
                finding.severity = Severity(severity_order[current_idx + 1])
            final_findings.append(finding)
        else:
            # Keep as-is
            final_findings.append(finding)

    return final_findings


def _intent_summary(intent: ArchitecturalIntent) -> str:
    """Brief summary for defender context."""
    lines = []
    for ctx in intent.bounded_contexts:
        deps = ", ".join(ctx.allowed_dependencies) if ctx.allowed_dependencies else "none"
        lines.append(f"- {ctx.name}: allowed deps=[{deps}]")
    return "\n".join(lines)
