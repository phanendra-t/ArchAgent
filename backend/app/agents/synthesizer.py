"""Synthesis Agent — merges, deduplicates, and ranks findings from all reviewers."""
from __future__ import annotations
import json
from anthropic import AsyncAnthropic
from app.models.intent import ArchitecturalIntent
from app.models.findings import Finding, Severity
from app.parser.diff_parser import ParsedDiff
from app.config import get_settings

SYSTEM_PROMPT = """You are a findings synthesis agent. You receive architectural violation findings from multiple specialized reviewers (context boundary, layer, security).

Your job:
1. DEDUPLICATE — if two findings describe the same underlying issue, merge them into one.
2. VALIDATE SEVERITY — ensure severity assignments are consistent and accurate.
3. CROSS-REFERENCE — if one finding provides context that strengthens or weakens another, note it.
4. RANK — order findings from most severe/impactful to least.

Return the deduplicated, refined list as a JSON array with the same structure as the input.
Add a "synthesis_note" field if you merged or adjusted anything.

If the input is empty or all findings are valid as-is, return them unchanged."""


async def synthesize_findings(
    findings: list[Finding],
    diff: ParsedDiff,
    intent: ArchitecturalIntent,
) -> list[Finding]:
    """Merge, deduplicate, and rank findings from all agents."""
    if not findings:
        return []

    # If only 1-2 findings, no need for synthesis
    if len(findings) <= 2:
        return findings

    settings = get_settings()
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    # Serialize findings for the LLM
    findings_json = json.dumps(
        [f.model_dump() for f in findings],
        indent=2,
        default=str,
    )

    user_message = f"""Here are {len(findings)} findings from multiple architectural reviewers:

{findings_json}

Deduplicate, validate severity, and rank them. Return a JSON array of the refined findings.
Keep the 'id' field from the original findings. Add 'synthesis_note' if you changed anything."""

    response = await client.messages.create(
        model=settings.llm_model,
        max_tokens=settings.max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    # Parse response
    text = response.content[0].text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])

    try:
        refined_raw = json.loads(text)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            refined_raw = json.loads(match.group())
        else:
            # If synthesis fails, return original findings
            return findings

    # Map back to Finding objects, preserving original data
    finding_map = {f.id: f for f in findings}
    refined_findings = []

    for raw in refined_raw:
        original_id = raw.get("id", "")
        if original_id in finding_map:
            # Update the original finding with any refinements
            original = finding_map[original_id].model_copy()
            if raw.get("severity"):
                try:
                    original.severity = Severity(raw["severity"])
                except ValueError:
                    pass
            refined_findings.append(original)
        else:
            # New finding from synthesis (merged)
            # Skip — we'll keep originals
            pass

    # If synthesis produced fewer results, use them; otherwise use originals
    return refined_findings if refined_findings else findings
