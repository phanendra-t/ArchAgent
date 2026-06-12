"""Pydantic models for the Architectural Intent Schema."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class ProjectConfig(BaseModel):
    languages: list[str] = []
    dependency_indicators: list[dict] = []


class BoundedContext(BaseModel):
    name: str
    description: str = ""
    owns: list[str]  # glob patterns
    allowed_dependencies: list[str] = []
    forbidden_dependencies: list[str] = []
    security_boundary: bool = False


class LayerRule(BaseModel):
    name: str
    pattern: str  # glob pattern
    allowed_imports_from: list[str] = []
    forbidden_imports_from: list[str] = []
    rule: str = ""


class DependencyRule(BaseModel):
    name: str
    description: str = ""
    type: Optional[str] = None  # e.g., "acyclic"
    rule: Optional[str] = None


class CommunicationPattern(BaseModel):
    between: list[str]  # [context1, context2]
    allowed: str  # "event" | "direct"
    forbidden: Optional[str] = None
    pattern: Optional[str] = None
    reason: Optional[str] = None


class SecurityRule(BaseModel):
    context: str
    constraints: list[str]


class Principle(BaseModel):
    name: str
    description: str
    severity: str = "advisory"  # "advisory" | "warning" | "critical"


class ArchitecturalIntent(BaseModel):
    """Root model for the architecture-intent.yaml schema."""
    schema_version: str = "1.0"
    system: str
    project: ProjectConfig = ProjectConfig()
    bounded_contexts: list[BoundedContext] = []
    layers: list[LayerRule] = []
    dependency_rules: list[DependencyRule] = []
    communication_patterns: list[CommunicationPattern] = []
    security_rules: list[SecurityRule] = []
    principles: list[Principle] = []

    def get_context_for_path(self, file_path: str) -> Optional[BoundedContext]:
        """Given a file path, determine which bounded context it belongs to."""
        import fnmatch
        for ctx in self.bounded_contexts:
            for pattern in ctx.owns:
                if fnmatch.fnmatch(file_path, pattern):
                    return ctx
        return None

    def get_layer_for_path(self, file_path: str) -> Optional[LayerRule]:
        """Given a file path, determine which layer it belongs to."""
        import fnmatch
        for layer in self.layers:
            if fnmatch.fnmatch(file_path, layer.pattern):
                return layer
        return None

    def get_security_rules_for_context(self, context_name: str) -> Optional[SecurityRule]:
        """Get security rules for a given context."""
        for rule in self.security_rules:
            if rule.context == context_name:
                return rule
        return None

    def get_communication_pattern(self, ctx1: str, ctx2: str) -> Optional[CommunicationPattern]:
        """Get communication pattern between two contexts."""
        for pattern in self.communication_patterns:
            if (ctx1 in pattern.between and ctx2 in pattern.between) or "any" in pattern.between:
                return pattern
        return None
