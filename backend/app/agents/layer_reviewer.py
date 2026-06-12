"""Layer Violation Reviewer Agent.

Detects violations of layered architecture rules.
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

SYSTEM_PROMPT = """You are a layered architecture auditor. Your job is to analyze code changes and identify violations of layer rules.

Common layer violations include:
- Controllers/API handlers directly accessing database/repository layer
- Domain models importing framework-specific code
- Service layer importing from API/controller layer (reverse dependency)
- Infrastructure code leaking into business logic

You are given:
1. Layer rules from the architectural intent (which layers can import from which).
2. A PR diff showing code changes.
3. Suspects flagged by the deterministic pre-checker.

Your task:
- Confirm or reject each suspect.
- Find ADDITIONAL layer violations the pre-checker missed.
- For each violation, explain the layered architecture principle being broken.

Return a JSON array of findings. If no violations, return [].

Each finding structure:
{
  "title": "Short descriptive title",
  "description": "Detailed explanation",
  "source_layer": "layer where the violating code lives",
  "target_layer": "layer being improperly accessed",
  "evidence": [{"file_path": "...", "line_number": N, "code_snippet": "..."}],
  "impact": "What architectural degradation this causes",
  "recommendation": "Specific fix",
  "severity": "critical|high|medium|low"
}

Be precise. Only flag genuine layer violations."""


async def review_layer_violations(
    diff: ParsedDiff,
    intent: ArchitecturalIntent,
    pre_check: PreCheckResult,
) -> list[Finding]:
    """Use Claude to analyze layer violations."""
    settings = get_settings()
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    # Build context
    layer_rules = _build_layer_rules(intent)
    diff_summary = _build_diff_with_layers(diff, pre_check)
    suspects = _build_layer_suspects(pre_check)

    user_message = f"""## Layer Rules

{layer_rules}

## PR Diff (with layer annotations)

{diff_summary}

## Pre-Check Layer Suspects

{suspects}

Analyze for layer violations. Return JSON array of findings."""

    response = await client.messages.create(
        model=settings.llm_model,
        max_tokens=settings.max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    return _parse_response(response.content[0].text)


def _build_layer_rules(intent: ArchitecturalIntent) -> str:
    lines = []
    for layer in intent.layers:
        lines.append(f"### Layer: {layer.name}")
        lines.append(f"Pattern: {layer.pattern}")
        if layer.allowed_imports_from:
            lines.append(f"Can import from: {', '.join(layer.allowed_imports_from)}")
        if layer.forbidden_imports_from:
            lines.append(f"Cannot import from: {', '.join(layer.forbidden_imports_from)}")
        if layer.rule:
            lines.append(f"Rule: {layer.rule}")
        lines.append("")
    return "\n".join(lines)


def _build_diff_with_layers(diff: ParsedDiff, pre_check: PreCheckResult) -> str:
    lines = []
    for file in diff.files:
        layer = pre_check.file_layer_map.get(file.path, "unknown")
        ctx = pre_check.file_context_map.get(file.path, "unknown")
        lines.append(f"### {file.path} (layer: {layer}, context: {ctx})")
        for line_num, content in file.added_lines[:50]:
            lines.append(f"+{line_num}: {content.rstrip()}")
        lines.append("")
    return "\n".join(lines)


def _build_layer_suspects(pre_check: PreCheckResult) -> str:
    suspects = [s for s in pre_check.suspects if s.violation_type == "layer_violation"]
    if not suspects:
        return "No deterministic layer suspects. Look for semantic layer violations."
    lines = []
    for s in suspects:
        lines.append(f"- {s.file_path}:{s.line_number} — `{s.code}`")
        lines.append(f"  {s.source_layer} importing from {s.target_layer} (Rule: {s.rule_reference})")
    return "\n".join(lines)


def _parse_response(response_text: str) -> list[Finding]:
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])

    try:
        raw_findings = json.loads(text)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            raw_findings = json.loads(match.group())
        else:
            return []

    findings = []
    for raw in raw_findings:
        evidence = [
            Evidence(
                file_path=ev.get("file_path", ""),
                line_number=ev.get("line_number"),
                code_snippet=ev.get("code_snippet", ""),
            )
            for ev in raw.get("evidence", [])
        ]

        findings.append(Finding(
            id=f"layer-{uuid.uuid4().hex[:6]}",
            category=FindingCategory.LAYER_VIOLATION,
            severity=Severity(raw.get("severity", "medium")),
            title=raw.get("title", "Layer violation"),
            description=raw.get("description", ""),
            evidence=evidence,
            impact=raw.get("impact", ""),
            recommendation=raw.get("recommendation", ""),
            rule_violated=f"layers.{raw.get('source_layer', '')}.forbidden_imports_from",
            context_violated=raw.get("source_layer", ""),
        ))

    return findings
