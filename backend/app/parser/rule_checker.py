"""Deterministic rule pre-checker.

Performs fast, regex/path-based checks BEFORE sending to the LLM.
Produces a 'suspects' list that the LLM agents then analyze in depth.
"""
from __future__ import annotations
import fnmatch
from dataclasses import dataclass, field
from app.models.intent import ArchitecturalIntent
from app.parser.diff_parser import ParsedDiff, ChangedFile


@dataclass
class Suspect:
    """A potential violation detected by deterministic rules."""
    file_path: str
    line_number: int | None
    code: str
    violation_type: str  # "cross_context_import", "layer_violation", "security_boundary"
    source_context: str | None = None
    target_context: str | None = None
    source_layer: str | None = None
    target_layer: str | None = None
    rule_reference: str = ""


@dataclass
class PreCheckResult:
    """Result of deterministic pre-checking."""
    suspects: list[Suspect] = field(default_factory=list)
    file_context_map: dict[str, str] = field(default_factory=dict)  # file_path -> context_name
    file_layer_map: dict[str, str] = field(default_factory=dict)  # file_path -> layer_name
    security_boundary_files: list[str] = field(default_factory=list)


def run_pre_check(diff: ParsedDiff, intent: ArchitecturalIntent) -> PreCheckResult:
    """Run deterministic pre-checks against the architectural intent."""
    result = PreCheckResult()

    # Map each changed file to its context and layer
    for file in diff.files:
        ctx = intent.get_context_for_path(file.path)
        if ctx:
            result.file_context_map[file.path] = ctx.name
            if ctx.security_boundary:
                result.security_boundary_files.append(file.path)

        layer = intent.get_layer_for_path(file.path)
        if layer:
            result.file_layer_map[file.path] = layer.name

    # Check imports for cross-context violations
    for imp in diff.added_imports:
        _check_cross_context_import(imp, intent, result)
        _check_layer_violation(imp, intent, result)

    return result


def _check_cross_context_import(
    imp: dict, intent: ArchitecturalIntent, result: PreCheckResult
) -> None:
    """Check if an import crosses bounded context boundaries."""
    source_file = imp["file"]
    import_source = imp["source"]

    # Determine source context
    source_ctx = intent.get_context_for_path(source_file)
    if not source_ctx:
        return

    # Try to resolve the import to a target context
    # Handle relative imports by resolving against source file path
    resolved_path = _resolve_import_path(source_file, import_source)

    target_ctx = intent.get_context_for_path(resolved_path) if resolved_path else None

    # Also try matching import source directly against context ownership patterns
    if not target_ctx:
        for ctx in intent.bounded_contexts:
            if ctx.name == source_ctx.name:
                continue
            for pattern in ctx.owns:
                # Check if the import source matches another context
                if _import_matches_context(import_source, pattern, ctx.name):
                    target_ctx = ctx
                    break
            if target_ctx:
                break

    if not target_ctx or target_ctx.name == source_ctx.name:
        return

    # Check if this dependency is forbidden
    is_forbidden = (
        target_ctx.name in source_ctx.forbidden_dependencies
        or "*" in source_ctx.forbidden_dependencies
    )
    is_allowed = target_ctx.name in source_ctx.allowed_dependencies

    if is_forbidden or (not is_allowed and source_ctx.forbidden_dependencies):
        result.suspects.append(Suspect(
            file_path=source_file,
            line_number=imp.get("line"),
            code=imp["statement"],
            violation_type="cross_context_import",
            source_context=source_ctx.name,
            target_context=target_ctx.name,
            rule_reference=f"bounded_contexts.{source_ctx.name}.forbidden_dependencies includes '{target_ctx.name}'",
        ))


def _check_layer_violation(
    imp: dict, intent: ArchitecturalIntent, result: PreCheckResult
) -> None:
    """Check if an import violates layer rules."""
    source_file = imp["file"]
    import_source = imp["source"]

    source_layer = intent.get_layer_for_path(source_file)
    if not source_layer:
        return

    # Determine target layer from the import
    resolved_path = _resolve_import_path(source_file, import_source)
    target_layer = intent.get_layer_for_path(resolved_path) if resolved_path else None

    if not target_layer or target_layer.name == source_layer.name:
        return

    # Check if importing from this layer is forbidden
    is_forbidden = (
        target_layer.name in source_layer.forbidden_imports_from
        or "*" in source_layer.forbidden_imports_from
    )
    is_allowed = target_layer.name in source_layer.allowed_imports_from

    if is_forbidden or (not is_allowed and source_layer.allowed_imports_from):
        result.suspects.append(Suspect(
            file_path=source_file,
            line_number=imp.get("line"),
            code=imp["statement"],
            violation_type="layer_violation",
            source_layer=source_layer.name,
            target_layer=target_layer.name,
            rule_reference=f"layers.{source_layer.name}.forbidden_imports_from includes '{target_layer.name}'",
        ))


def _resolve_import_path(source_file: str, import_source: str) -> str | None:
    """Resolve a relative import to a full path."""
    from pathlib import PurePosixPath

    if import_source.startswith("."):
        # Relative import — resolve against source file directory
        source_dir = PurePosixPath(source_file).parent
        resolved = (source_dir / import_source).as_posix()
        # Normalize
        parts = []
        for part in resolved.split("/"):
            if part == "..":
                if parts:
                    parts.pop()
            elif part != ".":
                parts.append(part)
        return "/".join(parts)
    elif import_source.startswith("src/") or import_source.startswith("@"):
        return import_source
    else:
        # Could be a package import — try prefixing with src/
        return f"src/{import_source.replace('.', '/')}"


def _import_matches_context(import_source: str, context_pattern: str, context_name: str) -> bool:
    """Check if an import source string matches a context's ownership pattern."""
    # Normalize: if import is relative like '../notifications/service'
    # Check if context name appears in the import path
    if context_name in import_source.lower():
        return True

    # Direct path match
    if fnmatch.fnmatch(import_source, context_pattern):
        return True

    return False
