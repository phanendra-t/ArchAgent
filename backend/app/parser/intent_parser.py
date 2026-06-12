"""Parser for architecture-intent.yaml files."""
from __future__ import annotations
import yaml
from pathlib import Path
from app.models.intent import ArchitecturalIntent


def parse_intent_file(file_path: str | Path) -> ArchitecturalIntent:
    """Parse an architecture-intent.yaml file into a structured model."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Intent file not found: {file_path}")
    
    with open(path, "r") as f:
        raw = yaml.safe_load(f)
    
    return ArchitecturalIntent(**raw)


def parse_intent_string(yaml_content: str) -> ArchitecturalIntent:
    """Parse YAML content string into a structured model."""
    raw = yaml.safe_load(yaml_content)
    return ArchitecturalIntent(**raw)
