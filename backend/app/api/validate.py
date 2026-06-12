"""Validate architecture-intent.yaml endpoint."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.parser.intent_parser import parse_intent_string


router = APIRouter()


class ValidateRequest(BaseModel):
    intent_yaml: str


class ValidateResponse(BaseModel):
    valid: bool
    errors: list[str] = []
    warnings: list[str] = []
    summary: dict = {}


@router.post("/validate", response_model=ValidateResponse)
async def validate_intent(request: ValidateRequest):
    """Validate an architecture-intent.yaml file."""
    if len(request.intent_yaml) > 256_000:
        raise HTTPException(status_code=413, detail="Intent file too large (max 256KB)")

    errors: list[str] = []
    warnings: list[str] = []
    summary: dict = {}

    # Parse
    try:
        intent = parse_intent_string(request.intent_yaml)
    except Exception as e:
        return ValidateResponse(valid=False, errors=[f"YAML parse error: {e}"])

    # System name
    if not intent.system:
        errors.append("No 'system' name defined")

    # Bounded contexts
    ctx_names: list[str] = []
    if intent.bounded_contexts:
        ctx_names = [c.name for c in intent.bounded_contexts]
        summary["contexts"] = ctx_names

        if len(ctx_names) != len(set(ctx_names)):
            errors.append("Duplicate bounded context names")

        for ctx in intent.bounded_contexts:
            for dep in ctx.allowed_dependencies + ctx.forbidden_dependencies:
                if dep != "*" and dep not in ctx_names:
                    warnings.append(f"Context '{ctx.name}' references unknown dependency '{dep}'")
            if not ctx.owns:
                warnings.append(f"Context '{ctx.name}' has no ownership patterns")
    else:
        warnings.append("No bounded contexts defined")

    # Layers
    layer_names: list[str] = []
    if intent.layers:
        layer_names = [l.name for l in intent.layers]
        summary["layers"] = layer_names

        for layer in intent.layers:
            for ref in layer.allowed_imports_from + layer.forbidden_imports_from:
                if ref != "*" and ref not in layer_names:
                    warnings.append(f"Layer '{layer.name}' references unknown layer '{ref}'")
    else:
        warnings.append("No layers defined")

    # Communication patterns
    if intent.communication_patterns:
        for cp in intent.communication_patterns:
            for between in cp.between:
                if between != "any" and between not in ctx_names:
                    warnings.append(f"Communication pattern references unknown context '{between}'")

    summary["security_rules"] = len(intent.security_rules)
    summary["principles"] = len(intent.principles)

    return ValidateResponse(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        summary=summary,
    )