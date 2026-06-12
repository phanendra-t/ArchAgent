"""Security Boundary Reviewer Agent.

Detects violations of security boundaries and data protection rules.
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

SYSTEM_PROMPT = """You are a security boundary auditor for software architecture. Your job is to analyze code changes and identify security-related architectural violations.

You check for:
- PII/sensitive data being logged, exposed, or passed outside secure contexts
- Security boundary contexts (e.g., payments) gaining unexpected new dependencies
- Authentication/authorization bypass patterns
- Secrets or credentials in code
- Data flowing from secure contexts to insecure ones without proper sanitization

You are given:
1. Security rules from the architectural intent.
2. A PR diff showing code changes.
3. Which files are in security-boundary contexts.

Your task:
- Identify any security boundary violations in the diff.
- Focus on data flow, logging, and dependency changes in security-sensitive contexts.
- Be particularly strict about PII, credentials, and payment data.

Return a JSON array of findings. If no violations, return [].

Each finding structure:
{
  "title": "Short descriptive title",
  "description": "Detailed explanation of the security concern",
  "context": "The security context being violated",
  "evidence": [{"file_path": "...", "line_number": N, "code_snippet": "..."}],
  "impact": "Security risk if not addressed",
  "recommendation": "Specific remediation",
  "severity": "critical|high|medium|low"
}

Err on the side of caution for security issues — flag anything suspicious."""


async def review_security_boundaries(
    diff: ParsedDiff,
    intent: ArchitecturalIntent,
    pre_check: PreCheckResult,
) -> list[Finding]:
    """Use Claude to analyze security boundary violations."""
    settings = get_settings()
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    # Only analyze if there are security rules or security boundary files
    if not intent.security_rules and not pre_check.security_boundary_files:
        return []

    security_rules = _build_security_context(intent)
    diff_summary = _build_security_diff(diff, pre_check)

    user_message = f"""## Security Rules

{security_rules}

## Files in Security Boundary Contexts

{', '.join(pre_check.security_boundary_files) or 'None identified'}

## PR Diff

{diff_summary}

Analyze for security boundary violations. Return JSON array of findings."""

    response = await client.messages.create(
        model=settings.llm_model,
        max_tokens=settings.max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    return _parse_response(response.content[0].text)


def _build_security_context(intent: ArchitecturalIntent) -> str:
    lines = []
    for rule in intent.security_rules:
        lines.append(f"### Context: {rule.context}")
        for constraint in rule.constraints:
            lines.append(f"- {constraint}")
        lines.append("")
    return "\n".join(lines) if lines else "No explicit security rules defined."


def _build_security_diff(diff: ParsedDiff, pre_check: PreCheckResult) -> str:
    lines = []
    for file in diff.files:
        ctx = pre_check.file_context_map.get(file.path, "unknown")
        is_security = file.path in pre_check.security_boundary_files
        marker = " ⚠️ SECURITY BOUNDARY" if is_security else ""
        lines.append(f"### {file.path} (context: {ctx}){marker}")
        for line_num, content in file.added_lines[:50]:
            lines.append(f"+{line_num}: {content.rstrip()}")
        lines.append("")
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
            id=f"sec-{uuid.uuid4().hex[:6]}",
            category=FindingCategory.SECURITY_BOUNDARY,
            severity=Severity(raw.get("severity", "high")),
            title=raw.get("title", "Security boundary violation"),
            description=raw.get("description", ""),
            evidence=evidence,
            impact=raw.get("impact", ""),
            recommendation=raw.get("recommendation", ""),
            rule_violated=f"security_rules.{raw.get('context', '')}",
            context_violated=raw.get("context", ""),
        ))

    return findings
